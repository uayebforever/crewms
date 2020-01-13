import os
import re
import jinja2
import jinja_vanish

from crewms.jc_skills_grid import *
import crewms

@jinja_vanish.markup_escape_func
def latex_escape(text):
    result = text
    if isinstance(text, str):
        result = re.sub(r"&", r"\&", result)
    if text is None:
        result = ""
    return result

latex_jinja_env = jinja_vanish.DynAutoEscapeEnvironment(
    block_start_string='%{',
    block_end_string='}%',
    variable_start_string='\VAR{',
    variable_end_string='}',
    comment_start_string='\#{',
    comment_end_string='}',
    # line_statement_prefix='%%',
    line_comment_prefix='%#',
    trim_blocks=True,
    autoescape=True,
    escape_func=latex_escape,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(crewms.__file__), 'latex_templates')))


def jc_rank(input):
    input = str(input)
    if input == "0":
        return "Trainee"
    if input == "1":
        return "DH"
    if input == "2":
        return "ADH"
    if input == "3":
        return "LDH"
    if input == "4":
        return "DL"
    if input == "5":
        return "OF"
    return input

latex_jinja_env.filters['jc_rank'] = jc_rank

skills_grid = SkillsGrid("/Users/uayeb/Documents/Outdoors/Sailing/James Craig/Training/2018 Training and Assessment Update/" +
               "JC Training Skills Grid.xlsx")

skills_grid.reload_data()

assert len(skills_grid.watchcards) > 0

if not os.path.exists("/Users/uayeb/Desktop/Watch Card Skills List"):
    os.mkdir("/Users/uayeb/Desktop/Watch Card Skills List")


def watchcard_latex(watch_card):
    # type: (WatchCard) -> str

    template = latex_jinja_env.get_template("full_watch_card.tex")
    return template.render(card=watch_card)







with open("/Users/uayeb/Desktop/Watch Card Skills List/Move Ship.txt", "w") as f:

    for card in skills_grid.watchcards_for_bill("Move Ship"):
        assert isinstance(card, WatchCard)
        f.write("\n\n")
        f.write(card.full_report)

with open("/Users/uayeb/Desktop/Watch Card Skills List/Harbour Cruise.txt", "w") as f:

    for card in skills_grid.watchcards_for_bill("Harbour Cruise"):
        assert isinstance(card, WatchCard)
        f.write("\n\n")
        f.write(card.full_report)

with open("/Users/uayeb/Desktop/Watch Card Skills List/Day Sail.txt", "w") as f:

    for card in skills_grid.watchcards_for_bill("Day Sail"):
        assert isinstance(card, WatchCard)
        f.write("\n\n")
        f.write(card.full_report)

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

def single_evolution_skills_report(evolution_name):
    assert evolution_name in skills_grid.evolutions

    tasks = [task
             for task in skills_grid.tasks
             if task.evolution == evolution_name]

    # Skills in all tasks of this evolution:
    general_skills = find_common_skills(tasks)

    tasks_as_dict = [dict(name=task.name, rank=task.rank, skills=task.skills)
                     for task in tasks]

    # Remove general skills from individual tasks
    for task in tasks_as_dict:
        task["skills"] = set(task["skills"]) - general_skills

    report_template = latex_jinja_env.get_template("evolution_skills_report.tex")
    content = report_template.render(
        evolution=evolution_name,
        general_skills=general_skills,
        tasks=tasks_as_dict)

    return content

def report_section(bill_name):

    assert bill_name in skills_grid.bills

    content = []

    watch_bill_template = latex_jinja_env.get_template("watch_bill.tex")
    content.append("\clearpage\\section{" + bill_name + "}")
    watchcards = skills_grid.watchcards_for_bill(bill_name)

    content.append(
        watch_bill_template.render(
            watch_cards=sorted(watchcards, key=lambda x: x.card_number),
            duties=watchcards[0].duties.keys()
        )
    )

    card_content = []
    for card in skills_grid.watchcards_for_bill(bill_name):
        card_content.append("\n\n")
        card_content.append(watchcard_latex(card))
    card_section_template = latex_jinja_env.get_template("card_list_section.tex")
    content.append(card_section_template.render(content="\n".join(card_content)))

    return content

def evolution_skills_report():

    content = []

    for category in skills_grid.task_categories:
        content.append(r"\subsection{" + jinja2.escape(category) + "}")
        for evolution in set([t.evolution for t in skills_grid.tasks if t.category == category]):
            content.append(single_evolution_skills_report(evolution))

    evolution_section = latex_jinja_env.get_template("evolution_section.tex")

    return evolution_section.render(content="\n".join(content))

with open("/Users/uayeb/Desktop/Watch Card Skills List/SkillsAssignmentReport.tex", "w") as f:
    content = []

    content.append(evolution_skills_report())

    content.extend(report_section("Move Ship"))
    content.extend(report_section("Harbour Cruise"))
    content.extend(report_section("Day Sail"))


    template = latex_jinja_env.get_template("crew_report.tex")
    f.write(template.render(content="\n".join(content)))
