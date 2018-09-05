"""
Base classes for the JC CrewMS
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
import crewms

# Python Standard Library Imports

# Other Library Imports
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import reconstructor

# CrewMS Imports

# Logging import and setup
from . import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()

# Set up SQL Alchemy in declarative base mode:
SQLAlchemyBase = declarative_base()
