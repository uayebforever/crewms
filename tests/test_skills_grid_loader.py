import pytest
import os

from crewms.skill_grid_loader_base import SkillGridLoaderBase

class TestSkillsGridLoader(object):

    def test_validate_spreadsheet(self):
        loader = SkillGridLoaderBase(get_test_resource("jc_skills_grid.xlsm"))

        loader.validate_spreadsheet()

    def test_iter_col(self):

        loader = SkillGridLoaderBase(get_test_resource("jc_skills_grid.xlsm"))

        loader.iter_cols("SkillsRef")


def get_test_resource(filename):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), filename)


