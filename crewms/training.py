"""
Training: All the things related to training and assessment of crew
"""
# Copyright (c) Andrew Green, 2018.
#
# The JC Crew Management System, including this
# file, is free software: you can redistribute it and/or modify it under the terms
# of the GNU Affero General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function, unicode_literals

from typing import Dict, List, Type, Union, Tuple, Any
# import crewms

# Python Standard Library Imports

# Other Library Imports
import sqlalchemy as sa
from sqlalchemy.orm import reconstructor, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection

# CrewMS Imports
from . import bases


# Logging import and setup
from . import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()


# Many-to-many association tables

task_skills_association_table = sa.Table(
    'task_skill', bases.SQLAlchemyBase.metadata,
    sa.Column('task_id', sa.Integer, sa.ForeignKey('tasks.id')),
    sa.Column('skill_id', sa.Integer, sa.ForeignKey('skills.id'))
)




class Task(bases.SQLAlchemyBase):

    __tablename__ = "tasks"

    id = sa.Column("id", sa.Integer, sa.Sequence('tasks_seq'), primary_key=True)

    skills = relationship(
        "Skill",
        secondary=task_skills_association_table,
        back_populates="tasks"
        )


class Skill(bases.SQLAlchemyBase):

    __tablename__ = "skills"

    id = sa.Column("id", sa.Integer, sa.Sequence('skills_seq'), primary_key=True)

    tasks = relationship(
        "Task",
        secondary=task_skills_association_table,
        back_populates="skills"
    )


class TrainingUnit(object):

    __tablename__ = "training_units"

    _database_id = sa.Column(sa.Integer, sa.Sequence('training_units_seq'), primary_key=True)


