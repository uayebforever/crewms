import re

from .data import *
from .jc_skills_grid import SkillsGrid
from .watch_bill import WatchBill

from typing import Dict, Tuple, List, Iterable

class DumbSkillToDutyMapper:

    def __init__(self, watch_bill: WatchBill, skills_grid:SkillsGrid):
        self.watch_bill = watch_bill
        self.skills_grid = skills_grid

    def map(self):

        duties = set()
        for card in self.watch_bill.cards:
            duties.update(card.duties.values())

        tasks = {(t.evolution, t.name): t for t in self.skills_grid.tasks.values()}  # type: Dict[Tuple[str, str], Task]

        for duty in duties:
            key = (duty.evolution_name, duty.name)
            if key in tasks:
                duty.tasks.append(tasks[key])
                # print("Matched duty: {}".format(duty))
                assert duty in tasks[key].duties
            else:
                print("Unmatched duty: {}".format(duty))


class HackedSkillToDutyMapper:
    """Will only match a duty to a single task!"""
    general_tasks_evolution = "General Tasks"

    def __init__(self, watch_bill: WatchBill, skills_grid: SkillsGrid):
        self.watch_bill = watch_bill
        self.skills_grid = skills_grid

    def map(self) -> List[Tuple[Duty, bool]]:

        duties = set()
        for card in self.watch_bill.cards:
            duties.update(card.duties.values())

        tasks = {(t.evolution.lower(), t.name.lower()): t for t in self.skills_grid.tasks.values()}  # type: Dict[Tuple[str, str], Task]

        duties_mapped = list()  # type: List[Tuple[Duty, bool]]
        for duty in duties:
            pass
            len(duties)
            # Check if there is a special mapper for this evolution:
            mapper_name = 'map_' + duty.evolution_name.replace(" ", "_").lower()
            was_mapped = getattr(self, mapper_name, self.map_default)(duty, tasks)
            duties_mapped.append((duty, was_mapped))
            # if was_mapped:
            #     print("Matched duty: {}".format(duty))
            # else:
            #     print("Unmatched duty: {}".format(duty))

        return duties_mapped

    def map_default(self, duty: Duty, tasks: Dict[Tuple[str, str], Task]) -> bool:
        key = (duty.evolution_name.lower(), duty.name.lower())
        if key in tasks:
            duty.tasks.append(tasks[key])
            # print("Matched duty: {}".format(duty))
            assert duty in tasks[key].duties
            return True
        else:
            # Try looking for matching task
            for task in tasks.values():
                if task.duty_match_re is not None and (task.evolution == duty.evolution_name or task.evolution == self.general_tasks_evolution):
                    try:
                        match_result = re.match(task.duty_match_re.lower(), duty.name.lower())
                    except Exception as e:
                        print("RegEx Match failed for regex: '%s', duty: %s" % (task.duty_match_re, duty))
                        raise e
                    if match_result:
                        duty.tasks.append(task)
                        return True
            if len(duty.tasks) == 0:
                # Still no match so try all hands
                return self.map_general_tasks(duty, tasks)

    # def map_person_overboard:
    #     pass

    def map_general_tasks(self, duty: Duty, tasks: Dict[Tuple[str, str], Task]) -> bool:

        key = (self.general_tasks_evolution.lower(), duty.name.lower())
        if key in tasks:
            duty.tasks.append(tasks[key])
            assert duty in tasks[key].duties
            return True
        else:
            return False
