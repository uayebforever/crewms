import pytest

from crewms.jc_skills_grid import *

@pytest.fixture
def skills_grid():
    return SkillsGrid("/Users/uayeb/Documents/Outdoors/Sailing/James Craig/Training/2018 Training and Assessment Update/" +
               "JC Training Skills Grid.xlsx")

def test_workbook_open(skills_grid):
    print(skills_grid)
    print(skills_grid.workbook)
    print(skills_grid.skills_grid_sheet)
    # assert False

def test_reload_data(skills_grid):

    skills_grid._reload_data()
    # print(sg.skills)
    # assert isinstance(sg.skills, pd.DataFrame)
    # print(sg.tasks)
    # assert isinstance(sg.tasks, pd.DataFrame)
    # assert False

def test_skills_for_task(skills_grid):
#
    skill_list = skills_grid.skills_for_task_by_id(5)
    print(skill_list)
    assert len(skill_list) < len(skills_grid.skills)
#
    # assert False

def test_tasks_for_card(skills_grid):

    card_list = skills_grid.watchcards

    a_card = card_list[0]

    assert isinstance(a_card, WatchCard)

    print(a_card)

    print(a_card.tasks)

    assert len(a_card.tasks) > 1

    # assert False


def test_report_watch_bill_tasks(skills_grid):

    assert len(skills_grid.watchcards) > 0

    report = skills_grid.report_watch_bill_tasks("Move Ship")

    print(report)
    assert len(report) > 0


    # assert False
