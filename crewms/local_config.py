"""
This module handles setting and loading the local configuration details for a given instance of Python/FIDIA.


Basically, the idea is that when FIDIA is loaded within a particular instance of
Python, it can load a configuration from file.  That configuration may do things
like set up an external Mapping Database or define a set of Data Access layers.

"""
# Copyright (c) Australian Astronomical Observatory (AAO), 2018.
#
# The Format Independent Data Interface for Astronomy (FIDIA), including this
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

from typing import List, Generator, Dict, Union
import crewms

# Standard Library Imports
import configparser
import os

# Other library imports

# FIDIA Imports

# Other modules within this FIDIA sub-package

from . import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()

config = None  # type: configparser.ConfigParser

DEFAULT_CONFIG = """
[MappingDatabase]
engine = sqlite
location = 
database = :memory:
echo = False
"""

def find_config_files():
    """Identify a list of possible config files for use by CrewMS."""

    pwd = os.getcwd()
    fidia_package_dir = os.path.realpath(__file__)
    homedir = os.path.expanduser("~")
    fidia_config_dir = os.getenv('CREWMS_CONFIG_DIR', None)

    input_path_list = [
        (pwd, "crewms.ini"),
        (fidia_config_dir, "crewms.ini"),
        (homedir, ".crewms.ini"),
        (fidia_package_dir, "crewms.ini")
    ]

    output_path_list = []

    for path in input_path_list:
        if path[0] is None:
            continue
        string_path = os.path.join(*path)
        if os.path.exists(string_path):
            output_path_list.append(string_path)

    return output_path_list



def load_config(config_files):
    """Load a configuration from the supplied list of config files."""

    global config

    if config is not None:
        log.warn("CrewMS Config is being reloaded: should only be loaded once!")

    config = configparser.ConfigParser()
    config.read_string(DEFAULT_CONFIG)
    files_used = config.read(config_files)
    if log.isEnabledFor(slogging.DEBUG):
        for f in files_used:
            log.debug("Loaded CrewMS config from file: %s", f)

    return config

load_config(find_config_files())




