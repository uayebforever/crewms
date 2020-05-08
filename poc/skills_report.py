import os
import re
import jinja2

from crewms.jc_skills_grid import *
from crewms.reporting import jc_rank, label_form, latex_jinja_env
from crewms import reporting
from crewms.skill_watch_bill_mappers import DumbSkillToDutyMapper, HackedSkillToDutyMapper
from crewms.watch_bill import WatchBillLoader, WatchBill


from crewms.jc_skills_grid import session

def watchcard_latex(watch_card):
    # type: (WatchCard) -> str

    template = latex_jinja_env.get_template("full_watch_card.tex")
    return template.render(card=watch_card)

def watchcard_latex_summarised(watch_card, render_skills=False):
    # type: (WatchCard, bool) -> str

    tasks_structured = dict()
    tasks = watch_card.tasks
    for task in tasks:
        tasks_structured[task.category] = defaultdict(list)
    for task in tasks:
        tasks_structured[task.category][task.evolution].append(task)

    skills_structured = defaultdict(list)
    for skill in watch_card.all_skills:
        skills_structured[skill.category].append(skill)

    template = latex_jinja_env.get_template("watch_card_simplified.tex")
    return template.render(card=watch_card, tasks_structured=tasks_structured, skills_structured=skills_structured,
                           render_skills=render_skills)



#
# with open("/Users/uayeb/Desktop/Watch Card Skills List/Move Ship.txt", "w") as f:
#
#     for card in skills_grid.watchcards_for_bill("Move Ship"):
#         assert isinstance(card, WatchCard)
#         f.write("\n\n")
#         f.write(card.full_report)
#
# with open("/Users/uayeb/Desktop/Watch Card Skills List/Harbour Cruise.txt", "w") as f:
#
#     for card in skills_grid.watchcards_for_bill("Harbour Cruise"):
#         assert isinstance(card, WatchCard)
#         f.write("\n\n")
#         f.write(card.full_report)
#
# with open("/Users/uayeb/Desktop/Watch Card Skills List/Day Sail.txt", "w") as f:
#
#     for card in skills_grid.watchcards_for_bill("Day Sail"):
#         assert isinstance(card, WatchCard)
#         f.write("\n\n")
#         f.write(card.full_report)

def find_common_skills(task_list):
    # type: (List[Task]) -> Set[Skill]
    skills = set()
    for task in task_list:
        if len(task.skills) > 0:
            if len(skills) > 0:
                skills.intersection_update(task.skills)
            else:
                skills = set(task.skills)
    return skills

def single_evolution_skills_report(category_name, evolution_name):
    assert category_name in skills_grid.task_categories
    assert evolution_name in skills_grid.evolutions

    tasks = [task
             for task in skills_grid.tasks.values()
             if task.evolution == evolution_name and task.category == category_name]  # type: List[Task]

    # Skills in all tasks of this evolution:
    general_skills = find_common_skills(tasks)

    tasks_as_dict = [dict(id=task.id, category=task.category, evolution=task.evolution,
                          name=task.name, rank=task.rank, skills=task.skills)
                     for task in tasks]  # type: List[Dict[str, Any]]

    # Remove general skills from individual tasks
    for task in tasks_as_dict:
        task["skills"] = set(task["skills"]) - general_skills

    report_template = latex_jinja_env.get_template("evolution_skills_report.tex")
    content = report_template.render(
        evolution=evolution_name,
        general_skills=general_skills,
        tasks=tasks_as_dict)

    return content

def card_id_key_for_sorting(key):
    # type: (WatchCard) -> str
    match = re.match(r"([a-z])([A-Z]+)([0-9]+)", key.card_number)
    if match:
        formatkey = "{bill} {watch} {num:0>2s}".format(
            bill=match.group(1), watch=match.group(2), num=match.group(3))
        return formatkey
    else:
        return key.card_number


def report_section(bill_name, watchcards):
    # type: (str, List[WatchCard]) -> List[str]

    content = []

    content.append("\clearpage\\section{" + bill_name + "}")

    content.append(reporting.watch_and_station_bill(watchcards, card_id_key_for_sorting))

    card_content = []
    for card in watchcards:
        card_content.append("\n\n")
        card_content.append(watchcard_latex_summarised(card, render_skills=True))
    card_section_template = latex_jinja_env.get_template("card_list_section.tex")
    content.append(card_section_template.render(content="\n".join(card_content)))

    return content

def watch_bill_report(watch_bill: WatchBill) -> List[str]:

    content = []

    bill_name = "Watch Bill"

    content.append("\clearpage\\section{" + bill_name + "}")

    # content.append(reporting.watch_and_station_bill(watchcards, card_id_key_for_sorting))



    card_content = []
    for card in watch_bill.cards:
        card_content.append("\n\n")
        card_content.append(watchcard_latex_summarised(card, render_skills=True))
    card_section_template = latex_jinja_env.get_template("card_list_section.tex")
    content.append(card_section_template.render(content="\n".join(card_content)))

    return content

def evolution_skills_report(skills_grid: SkillsGrid):

    content = []

    for category in skills_grid.task_categories:
        content.append(r"\needspace{5\baselineskip}")
        content.append(r"\subsection{" + jinja2.escape(category) + "}")
        evolutions_in_category = [row[0] for row in
                                  session.execute(
                                      select([Task.__table__.c.evolution])
                                            .where(Task.__table__.c.category == category)
                                            .order_by(Task.__table__.c.id).distinct()
                                  )]
        for evolution in evolutions_in_category:
            content.append(single_evolution_skills_report(category, evolution))

    evolution_section = latex_jinja_env.get_template("evolution_section.tex")

    return evolution_section.render(content="\n".join(content))


if __name__ == "__main__":
    skills_grid = SkillsGridLoader("/Users/uayeb/Documents/Outdoors/Sailing/James Craig/Training/2018 Training and Assessment Update/" +
                   "JC Training Skills Grid.xlsm").load()


    # assert len(skills_grid.watchcards) > 0

    if not os.path.exists("/Users/uayeb/Desktop/Watch Card Skills List"):
        os.mkdir("/Users/uayeb/Desktop/Watch Card Skills List")



    with open("/Users/uayeb/Desktop/Watch Card Skills List/SkillsAssignmentReport.tex", "w") as f:
        content = []

        content.append(evolution_skills_report(skills_grid))

        # for bill in ("Move Ship", "Harbour Cruise", "Day Sail"):
        #     content.extend(report_section(bill, skills_grid.watchcards_for_bill(bill)))

        watch_bill = WatchBillLoader(os.path.join(os.path.dirname(__file__), "modern_wns_bill.xlsx")).load_watch_bill_from_xlsx()

        duties_mapped = HackedSkillToDutyMapper(watch_bill, skills_grid).map()
        session.commit()

        for duty, mapped in duties_mapped:
            if duty.evolution_name.startswith("Oil"):
                if mapped:
                    print("Mapped duty {} to tasks: {}".format(duty, duty.tasks))
                else:
                    print("Unmapped" + " duty: " + str(duty))

        content.extend(watch_bill_report(watch_bill))

        template = latex_jinja_env.get_template("crew_report.tex")
        f.write(template.render(content="\n".join(content)))
