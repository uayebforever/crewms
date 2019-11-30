from collections import defaultdict

# import pandas as pd
# import sqlalchemy

import openpyxl
from openpyxl.worksheet import worksheet
import openpyxl


from typing import List, Dict, Any

from sqlalchemy import create_engine, Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection

engine = create_engine("sqlite:///:memory:")
Session = sessionmaker(bind=engine)
session = Session()

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

task_skill = Table("task_skill", Base.metadata,
                   Column('task_id', ForeignKey('tasks.id'), primary_key=True),
                   Column('skill_id', ForeignKey("skills.id"), primary_key=True)
                   )

task_watchcard = Table("task_watchcard", Base.metadata,
                       Column('task_id', ForeignKey('tasks.id'), primary_key=True),
                       Column('watchcard_id', ForeignKey("watchcards.id"), primary_key=True)
                       )


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    category = Column(String)
    evolution = Column(String)
    rank = Column(Integer)

    skills = relationship('Skill', secondary=task_skill, back_populates="tasks")

    @property
    def one_line_summary(self):
        return "{category} - {evolution} - {name}".format(
            name=self.name,
            category=self.category,
            evolution=self.evolution
        )

    def __repr__(self):
        return "<Task(%s - %s - %s)>" % (self.category, self.evolution, self.name)


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    category = Column(String)
    level = Column(String)

    tasks = relationship('Task', secondary=task_skill, back_populates="skills")

    @property
    def one_line_summary(self):
        return "{category}: {name}".format(
            name=self.name,
            category=self.category
        )

    def __repr__(self):
        return "<Skill(%s - %s)>" % (self.category, self.name)

class Duty(Base):
    __tablename__ = "duties"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    evolution = Column(String)
    watch_card_id = Column(Integer, ForeignKey('watchcards.id'))


class WatchCard(Base):
    __tablename__ = "watchcards"

    id = Column(Integer, primary_key=True)
    bill = Column(String)
    name = Column(String)
    card_number = Column(String)
    manning_requirements = Column(String)

    tasks = relationship('Task', secondary=task_watchcard)  # type: List[Task]
    duties = relationship('Duty',
                          collection_class=attribute_mapped_collection('evolution'))  # type: Dict[str, Duty]

    @property
    def all_skills(self):
        all_skills = set()
        for task in self.tasks:
            for skill in task.skills:
                if skill not in all_skills:
                    all_skills.add(skill)
        return all_skills

    @property
    def required_rank(self):
        return max(t.rank for t in self.tasks)

    @property
    def one_line_summary(self):
        if self.name is not None:
            name = " ({})".format(self.name)
        else:
            name = ""
        return "Watch Card {card_number}{name} for {bill} (rank {rank})".format(
            card_number=self.card_number,
            name=name,
            bill=self.bill,
            rank=self.required_rank
        )

    @property
    def full_report(self):
        text = []
        text.append("="*78)
        text.append(self.one_line_summary)
        text.append(self.evolutions_summary)
        text.append(self.tasks_summary)
        text.append(self.skills_summary)
        return "\n".join(text)

    @property
    def tasks_summary(self):
        text = []
        text.append("-"*78)
        text.append("    Tasks Required")
        text.append("-"*78)
        for task in self.tasks:
            text.append("   " + task.one_line_summary)
        return "\n".join(text)

    @property
    def evolutions_summary(self):
        text = []
        text.append("-"*78)
        text.append("    Duties")
        text.append("-"*78)
        for duty in self.duties.values():
            text.append("{0!s:>15s}: {1!s:15s}".format(duty.evolution, duty.name))
        return "\n".join(text)

    @property
    def skills_summary(self):
        text = []
        text.append("-"*78)
        text.append("    Skills Required")
        text.append("-"*78)

        all_skills = set()
        for task in self.tasks:
            for skill in task.skills:
                if skill not in all_skills:
                    all_skills.add(skill)
        for skill in all_skills:
            text.append("   " + skill.one_line_summary)
        return "\n".join(text)

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






class SkillsGrid:

    def __init__(self, workbook_filename):

        self.workbook = openpyxl.load_workbook(workbook_filename, data_only=True) #, read_only=True)

        assert "Skills Grid" in self.workbook.sheetnames
        self.skills_grid_sheet = self.workbook["Skills Grid"]  # type: worksheet.Worksheet

        assert "WnS Bill" in self.workbook.sheetnames
        # self.wns_bill = self.workbook["WnS Bill"]  # type: worksheet.Worksheet


        self.defined_names = self.workbook.defined_names



    @property
    def skills(self):
        return session.query(Skill).all()

    @property
    def tasks(self):
        return session.query(Task).all()

    @property
    def watchcards(self):
        return session.query(WatchCard).all()


    def watchcards_for_bill(self, bill):
        # type: (str) -> List[WatchCard]
        return session.query(WatchCard).filter(WatchCard.bill == bill).order_by(WatchCard.card_number).all()

    def _get_cells_for_reference(self, reference_name):

        cells = []

        for sheet_name, cell_reference in self.workbook.defined_names[reference_name].destinations:
            ws = self.workbook[sheet_name]
            cells.append(ws[cell_reference])

        return cells



    def reload_data(self):

        self.bounding_box = worksheet.CellRange(self.skills_grid_sheet.calculate_dimension())
        self.reload_tasks()
        self.reload_skills()
        wsb_locations = self.reload_watch_and_station_bill_assignments()
        self.get_watch_and_station_bill_duties(wsb_locations)


    def reload_tasks(self):
        # Tasks
        tl = LastNone()
        for column in self.skills_grid_sheet.iter_cols(min_col=5, min_row=1,
                                                       max_col=self.bounding_box.max_col, max_row=4):
            cat, evol, skill, rank = column

            task = Task(id=cat.column,
                        category=str(tl.last_if_none("category", cat.value)),
                        evolution=str(tl.last_if_none("evolution", evol.value)),
                        name=str(tl.last_if_none("name", skill.value)),
                        rank=rank.value)
            session.add(
                task
            )
        session.commit()

    def reload_skills(self):
        # Skills
        for row in self.skills_grid_sheet.iter_rows(min_col=1, min_row=14,
                                                    max_col=3, max_row=self.bounding_box.max_row):
            category, skill, level = row
            session.add(
                Skill(id=category.row,
                      category=category.value,
                      name=skill.value,
                      level=level.value)
            )
        session.commit()
        for row in self.skills_grid_sheet.iter_rows(min_col=5, min_row=14,
                                                    max_col=self.bounding_box.max_col, max_row=self.bounding_box.max_row):
            for cell in row:
                if cell.value == "Y":
                    # Create relationship
                    skill = skill_by_id(cell.row)
                    task = task_by_id(cell.column)
                    skill.tasks.append(task)
        session.commit()
        return task_by_id

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
        for wsb_name in wsb_locations:
            for column in self.skills_grid_sheet.iter_cols(min_col=wsb_region["header col"] + 1,
                                                           min_row=wsb_locations[wsb_name],
                                                           max_col=self.bounding_box.max_col,
                                                           max_row=wsb_locations[wsb_name]):
                cell = column[0]
                if cell.value is not None:
                    for card_id in cell.value.split(","):
                        watch_card = watchcard_by_number_and_bill(card_id, wsb_name)
                        if watch_card is None:
                            watch_card = WatchCard(bill=wsb_name, card_number=card_id)
                            session.add(watch_card)

                        # print("Creating card %s" % cell.value)
                        watch_card.tasks.append(task_by_id(cell.column))
        session.commit()
        return wsb_locations

    def get_watch_and_station_bill_duties(self, wsb_locations):

        # Iterate over watch bills
        for wsb_name in wsb_locations:
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

            print(evolutions)
            # Iterate over watch cards
            watch_cards_seen = set()
            for row in sheet.iter_rows(min_row=5, max_row=sheet_bounds.max_row,
                                       min_col=1, max_col=1):
                cell = row[0]
                if cell.value is not None:
                    watch_card = watchcard_by_number_and_bill(cell.value, wsb_name)  # type: WatchCard
                    if watch_card is None:
                        print("Watch card %s on Watch and station bill %s not in skills grid." % (cell.value, wsb_name))
                        continue
                    watch_cards_seen.add(watch_card)
                    watch_card.manning_requirements = sheet.cell(row=cell.row, column=2).value
                    for column in sheet.iter_cols(min_col=6, max_col=6 + len(evolutions) - 1,
                                                  min_row=cell.row, max_row=cell.row):

                        duty_cell = column[0]  # type: worksheet.Cell
                        watch_card.duties[evolutions[duty_cell.column]] = \
                            Duty(name=duty_cell.value, evolution=evolutions[duty_cell.column])
                    watch_card.name = sheet.cell(cell.row, 3).value

            if set(self.watchcards_for_bill(wsb_name)) != watch_cards_seen:
                print("Watch cards missing from bill %s:" % wsb_name)
                for card in set(self.watchcards_for_bill(wsb_name)).difference(watch_cards_seen):
                    print("    {0.card_number}".format(card))


        session.commit()


    def skills_for_task_by_id(self, id):
        # assert id in self.tasks.index, "Unknown task"
        # return self.skills[self.skills[id] == "Y"]

        task = session.query(Task).filter(Task.id == id).one()

        return task.skills



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

def skill_by_id(id):
    # type: (int) -> Skill
    return session.query(Skill).filter(Skill.id == id).one()

def task_by_id(id):
    # type: (int) -> Task
    return session.query(Task).filter(Task.id == id).one()
