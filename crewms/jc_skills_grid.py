from collections import defaultdict

import pandas as pd
import sqlalchemy

import openpyxl
from openpyxl.worksheet import worksheet


from sqlalchemy import create_engine, Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
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

    skills = relationship('Skill', secondary=task_skill, back_populates="tasks")

    def __repr__(self):
        return "<Task(%s - %s - %s)>" % (self.category, self.evolution, self.name)


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    category = Column(String)
    level = Column(String)

    tasks = relationship('Task', secondary=task_skill, back_populates="skills")

    def __repr__(self):
        return "<Skill(%s - %s)>" % (self.category, self.name)

class WatchCard(Base):
    __tablename__ = "watchcards"

    id = Column(Integer, primary_key=True)
    bill = Column(String)
    name = Column(String)
    card_number = Column(String)

    tasks = relationship('Task', secondary=task_watchcard)

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

    @property
    def skills(self):
        return session.query(Skill).all()

    @property
    def tasks(self):
        return session.query(Task).all()

    @property
    def watchcards(self):
        return session.query(WatchCard).all()

    def reload_data(self):

        bounding_box = worksheet.CellRange(self.skills_grid_sheet.calculate_dimension())

        # Tasks

        tl = LastNone()

        for column in self.skills_grid_sheet.iter_cols(min_col=5, min_row=1,
                                                   max_col=bounding_box.max_col, max_row=4):
            cat, evol, skill, rank = column

            task = Task(id=cat.column, category=str(tl.last_if_none("category", cat.value)),
                        evolution=str(tl.last_if_none("evolution", evol.value)),
                        name=str(tl.last_if_none("name", skill.value)))
            session.add(
                task
            )

        session.commit()

        # Skills

        for row in self.skills_grid_sheet.iter_rows(min_col=1, min_row=14,
                                                    max_col=3, max_row=bounding_box.max_row):
            category, skill, level = row
            session.add(
                Skill(id=category.row,
                      category=category.value,
                      name=skill.value,
                      level=level.value)
            )

        session.commit()

        skill_by_id = lambda id: session.query(Skill).filter(Skill.id == id).one()
        task_by_id = lambda id: session.query(Task).filter(Task.id == id).one()


        for row in self.skills_grid_sheet.iter_rows(min_col=5, min_row=14,
                                                    max_col=bounding_box.max_col, max_row=bounding_box.max_row):
            for cell in row:
                if cell.value == "Y":
                    # Create relationship
                    skill = skill_by_id(cell.row)
                    task = task_by_id(cell.column)
                    skill.tasks.append(task)


        # Watch and Station Bill Assignments

        wsb_locations = dict()
        for row in self.skills_grid_sheet["C5:C10"]:
            if row[0].value.startswith("WSB Task Assignment:"):
                wsb_locations[row[0].value[len("WSB Task Assignment:")+1:]] = row[0].row

        # print(wsb_locations)

        watchcard_by_number_and_bill = lambda num, bill: session.query(WatchCard).filter(
            WatchCard.card_number == num, WatchCard.bill == bill).one_or_none()


        for wsb_name in wsb_locations:
            for column in self.skills_grid_sheet.iter_cols(min_col=5, min_row=wsb_locations[wsb_name],
                                                       max_col=bounding_box.max_col, max_row=wsb_locations[wsb_name]):
                cell = column[0]
                if cell.value is not None:
                    watch_card = watchcard_by_number_and_bill(cell.value, wsb_name)
                    if watch_card is None:
                        watch_card = WatchCard(bill=wsb_name, card_number=cell.value)
                        session.add(watch_card)

                    # print("Creating card %s" % cell.value)
                    watch_card.tasks.append(task_by_id(cell.column))


        session.commit()

    def skills_for_task_by_id(self, id):
        # assert id in self.tasks.index, "Unknown task"
        # return self.skills[self.skills[id] == "Y"]

        task = session.query(Task).filter(Task.id == id).one()

        return task.skills



    def report_watch_bill_tasks(self, watchbill):

        watchcards = session.query(WatchCard).filter(WatchCard.bill == watchbill).order_by(WatchCard.card_number).all()

        report = []

        for card in watchcards:
            assert isinstance(card, WatchCard)
            report.append(card.card_number)
            for task in card.tasks:
                report.append("   " + str(task))

        return "\n".join(report)
