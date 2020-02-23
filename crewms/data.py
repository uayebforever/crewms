

from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection

from typing import Dict, List

__all__ = ["Base", "Task", "Skill", "Duty", "WatchCard", 'Evolution']

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

    watch_card_id = Column(Integer, ForeignKey('watchcards.id'))
    evolution_id = Column(Integer, ForeignKey("evolutions.id"))

    evolution = relationship('Evolution', back_populates='duties')  # type: Evolution

    @property
    def evolution_name(self):
        return self.evolution.name

class Evolution(Base):
    __tablename__ = "evolutions"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    category = Column(String)

    duties = relationship('Duty', back_populates='evolution')  # type: List[Duty]


class WatchCard(Base):
    __tablename__ = "watchcards"

    id = Column(Integer, primary_key=True)
    bill = Column(String)
    name = Column(String)
    card_number = Column(String)
    crew_category = Column(String)
    manning_requirements = Column(String)

    tasks = relationship('Task', secondary=task_watchcard)  # type: List[Task]
    duties = relationship('Duty',
                          collection_class=attribute_mapped_collection('evolution_name'),
                          cascade="all, delete-orphan")  # type: Dict[str, Duty]

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
        if len(self.tasks) == 0:
            return None
        else:
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
            text.append("{0!s:>15s}: {1!s:15s}".format(duty.evolution_name, duty.name))
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

