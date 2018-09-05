# -*- coding: utf-8 -*-

"""Top-level package for CrewMS."""

__author__ = """Andy Green"""
__email__ = 'uayeb.forever@gmail.com'
__version__ = '0.1.0'

# Set up global application state first:

#     Load configuration information (from fidia.ini files if found), and
#     make it available:
from crewms.local_config import config

#     Connect to the persistence database as defined by the config
#     information (or use the default in-memory persistance database). Then
#     get the database Session factory to be used for this instance of
#     FIDIA.
from crewms.database_tools import mappingdb_session


import crewms.training

from crewms.training import Skill, Task


from crewms.database_tools import check_create_update_database
check_create_update_database()
