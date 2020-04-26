from collections import defaultdict

# import pandas as pd
# import sqlalchemy

from openpyxl.worksheet import worksheet

from typing import List, Dict, Any

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from .skill_grid_loader_base import SkillGridLoaderBase

engine = create_engine("sqlite:///:memory:")
Session = sessionmaker(bind=engine)
session = Session()

from .data import *


Base.metadata.create_all(engine)

def append_or_last(list, value):
    # type: (list, Any) -> None
    if value is None:
        list.append(list[-1])
    else:
        list.append(value)

class LastNone:

    def __init__(self):
        self._store = dict()

    def last_if_none(self, id, value):
        if value is None:
            return self._store[id]
        else:
            self._store[id] = value
            return value


def _get_or_create_evolution(evolution_name):
    try:
        return session.query(Evolution).filter(Evolution.name == evolution_name).one()
    except:
        evolution = Evolution(name=evolution_name)
        session.add(evolution)
        return evolution



class SkillsGridLoader(SkillGridLoaderBase):

    def _load_skills(self):
        # type: () -> Dict[int, Skill]
        # Skills
        # TODO: Fix this to use "SkillsRef" reference.

        skills = dict()  # type: Dict[int, Skill]
        for row in self.skills_grid_sheet.iter_rows(min_col=1, min_row=13,
                                                    max_col=3, max_row=self.bounding_box.max_row):
            category, skill, level = row
            skill = Skill(id=category.row, category=category.value, name=skill.value, level=level.value)

            skills[skill.id] = skill

            session.add(skill)

        session.commit()
        return skills

    def _load_tasks(self):
        # type: () -> Dict[int, Task]
        # Tasks
        tl = LastNone()
        tasks = dict()  # type: Dict[int, Task]
        for column in self.skills_grid_sheet.iter_cols(min_col=5, min_row=1,
                                                       max_col=self.bounding_box.max_col, max_row=4):
            cat, evol, name, rank = column

            if name.value is None:
                continue

            task = Task(id=cat.column,
                        category=str(tl.last_if_none("category", cat.value)),
                        evolution=str(tl.last_if_none("evolution", evol.value)),
                        name=str(tl.last_if_none("name", name.value)),
                        rank=rank.value)
            tasks[task.id] = task
            session.add(
                task
            )
        session.commit()
        return tasks

    def load(self):
        # type: () -> SkillsGrid
        skills = self._load_skills()
        tasks = self._load_tasks()

        self._link_skills_to_tasks()

        skills_grid = SkillsGrid(skills=skills, tasks=tasks)

        return SkillsGrid

    def _link_skills_to_tasks(self):
        for row in self.skills_grid_sheet.iter_rows(min_col=5, min_row=14,
                                                    max_col=self.bounding_box.max_col,
                                                    max_row=self.bounding_box.max_row):
            for cell in row:
                if cell.value == "Y":
                    # Create relationship
                    skill = skill_by_id(cell.row)
                    task = task_by_id(cell.column)
                    skill.tasks.append(task)
        session.commit()
        return task_by_id


class SkillsGrid:

    def __init__(self, skills, tasks):
        # type: (Dict[int, Skill], Dict[int, Task]) -> None

        self.skills = skills  # type: Dict[int, Skill]
        self.tasks = tasks  # type: Dict[int, Task]

        self.bills = list()




    @property
    def evolutions(self):
        return set(t.evolution for t in session.query(Task).all())

    @property
    def task_categories(self):
        return [row[0] for row in session.execute(
            select([Task.__table__.c.category]).order_by(Task.__table__.c.id).distinct())]

    @property
    def watchcards(self):
        return session.query(WatchCard).all()


    def watchcards_for_bill(self, bill):
        # type: (str) -> List[WatchCard]
        return session.query(WatchCard).filter(WatchCard.bill == bill).order_by(WatchCard.card_number).all()




    def _reload_data(self):

        generic_tasks = self.reload_watch_and_station_bill_assignments()
        self.get_watch_and_station_bill_duties(None)

        for bill in generic_tasks:
            for crew_category, task in generic_tasks[bill].items():
                for card in all_crew_cards_for_category_and_bill(crew_category, bill):
                    card.tasks.append(task)
        session.commit()


    def reload_watch_and_station_bill_assignments(self):
        # Watch and Station Bill Assignments
        wsb_region = dict()
        wsb_region["min row"] = self._get_cells_for_reference("BillAssignmentRef")[0].row
        wsb_region["max row"] = self._get_cells_for_reference("SkillsRef")[0].row - 1
        wsb_region["header col"] = self._get_cells_for_reference("BillAssignmentRef")[0].column
        wsb_locations = dict()
        for row in self.skills_grid_sheet.iter_rows(
            min_row=wsb_region["min row"], min_col=wsb_region["header col"],
            max_row=wsb_region["max row"], max_col=wsb_region["header col"]):
            if row[0].value.startswith("WSB Task Assignment:"):
                wsb_locations[row[0].value[len("WSB Task Assignment:") + 1:]] = row[0].row
        # print(wsb_locations)

        self.bills = [s for s in wsb_locations]

        generic_tasks = defaultdict(dict)  # type: Dict[str, Dict[str, Task]]

        for wsb_name in wsb_locations:
            for column in self.skills_grid_sheet.iter_cols(min_col=wsb_region["header col"] + 1,
                                                           min_row=wsb_locations[wsb_name],
                                                           max_col=self.bounding_box.max_col,
                                                           max_row=wsb_locations[wsb_name]):
                cell = column[0]
                if cell.value is not None:
                    value = str(cell.value)
                    if value.startswith("All "):
                        crew_category = value[len("All "):]
                        generic_tasks[wsb_name][crew_category] = task_by_id(cell.column)
                        continue
                    for card_id in cell.value.split(","):
                        watch_card = watchcard_by_number_and_bill(card_id, wsb_name)
                        if watch_card is None:
                            watch_card = WatchCard(bill=wsb_name, card_number=card_id)
                            session.add(watch_card)

                        # print("Creating card %s" % cell.value)
                        watch_card.tasks.append(task_by_id(cell.column))
        session.commit()
        return generic_tasks

    def get_watch_and_station_bill_duties(self, wsb_locations):

        # Iterate over watch bills
        for wsb_name in self.bills:
            # start_col = wns_bill_sheet_locations[wsb_name]
            sheet = self.workbook["WnS Bill " + wsb_name]
            sheet_bounds = worksheet.CellRange(sheet.calculate_dimension())
            # Collect evolution names
            evolutions = dict()  # type: Dict[int, str]
            for column in sheet.iter_cols(min_col=6, max_col=sheet_bounds.max_col,
                                          min_row=4, max_row=4):
                cell = column[0]
                if cell.value != "!":
                    evolutions[cell.column] = cell.value
                else:
                    break

            current_crew_category = None

            # print(evolutions)
            # Iterate over watch cards
            watch_cards_seen = set()
            for row in sheet.iter_rows(min_row=5, max_row=sheet_bounds.max_row,
                                       min_col=1, max_col=1):
                cell = row[0]
                if cell.value.startswith("Area: "):
                    current_crew_category = cell.value[len("Area: "):]
                    continue
                if cell.value is not None and str(cell.value).strip() != "":
                    watch_card = watchcard_by_number_and_bill(cell.value, wsb_name)  # type: WatchCard
                    if watch_card is None:
                        print("Watch card %s on Watch and station bill %s not in skills grid." % (cell.value, wsb_name))
                        continue
                    watch_cards_seen.add(watch_card)
                    watch_card.manning_requirements = sheet.cell(row=cell.row, column=2).value
                    watch_card.crew_category = current_crew_category
                    for column in sheet.iter_cols(min_col=6, max_col=6 + len(evolutions) - 1,
                                                  min_row=cell.row, max_row=cell.row):

                        duty_cell = column[0]  # type: worksheet.Cell

                        evolution = _get_or_create_evolution(evolutions[duty_cell.column])

                        watch_card.duties[evolutions[duty_cell.column]] = \
                            Duty(name=duty_cell.value, evolution=evolution)
                    watch_card.name = sheet.cell(cell.row, 3).value

            if set(self.watchcards_for_bill(wsb_name)) != watch_cards_seen:
                print("Watch cards missing from bill %s:" % wsb_name)
                for card in set(self.watchcards_for_bill(wsb_name)).difference(watch_cards_seen):
                    print("    {0.card_number}".format(card))
                    session.delete(card)

        session.commit()


    def skills_for_task_by_id(self, id):
        # type: (int) -> List[Skill]
        # assert id in self.tasks.index, "Unknown task"
        # return self.skills[self.skills[id] == "Y"]

        # task = session.query(Task).filter(Task.id == id).one()

        return self.tasks[id].skills



    def report_watch_bill_tasks(self, watchbill):

        watchcards = session.query(WatchCard).filter(WatchCard.bill == watchbill).order_by(WatchCard.card_number).all()

        report = []

        if len(watchcards) == 0:
            report.append("No watch cards assigned to the '%s' watch bill." % watchbill)

        for card in watchcards:
            assert isinstance(card, WatchCard)
            report.append("Card {}  (required rank: {})".format(card.card_number, card.required_rank))
            for task in card.tasks:
                report.append("   " + str(task))

        return "\n".join(report)

def watchcard_by_number_and_bill(num, bill):
    # type: (str, str) -> WatchCard
    return session.query(WatchCard).filter(
        WatchCard.card_number == num, WatchCard.bill == bill).one_or_none()

def all_crew_cards_for_category_and_bill(crew_category, bill):
    return session.query(WatchCard).filter(
        WatchCard.bill == bill,
        WatchCard.crew_category == crew_category).all()

def skill_by_id(id):
    # type: (int) -> Skill
    return session.query(Skill).filter(Skill.id == id).one()

def task_by_id(id):
    # type: (int) -> Task
    return session.query(Task).filter(Task.id == id).one()
