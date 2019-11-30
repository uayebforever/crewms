import os
import jinja2

from crewms.jc_skills_grid import *
import crewms



latex_jinja_env = jinja2.Environment(
    block_start_string='%{',
    block_end_string='}%',
    variable_start_string='\VAR{',
    variable_end_string='}',
    comment_start_string='\#{',
    comment_end_string='}',
    # line_statement_prefix='%%',
    line_comment_prefix='%#',
    trim_blocks=True,
    autoescape=False,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(crewms.__file__), 'latex_templates')))


skills_grid = SkillsGrid("/Users/uayeb/Documents/Outdoors/Sailing/James Craig/Training/2018 Training and Assessment Update/" +
               "JC Training Skills Grid.xlsx")

skills_grid.reload_data()

assert len(skills_grid.watchcards) > 0

if not os.path.exists("/Users/uayeb/Desktop/Watch Card Skills List"):
    os.mkdir("/Users/uayeb/Desktop/Watch Card Skills List")


def watchcard_latex(watch_card):
    # type: (WatchCard) -> str

    pass



    template = latex_jinja_env.get_template("full_watch_card.tex")
    return template.render(
        card_name=watch_card.one_line_summary,
        duty_list=[(d.evolution, d.name) for k, d in watch_card.duties.items()],
        skills=watch_card.all_skills,
        tasks=watch_card.tasks
    )







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


with open("/Users/uayeb/Desktop/Watch Card Skills List/Move Ship.tex", "w") as f:
    content = []

    watch_bill_template = latex_jinja_env.get_template("watch_bill.tex")
    content.append("\\section{Move Ship}")
    watchcards = skills_grid.watchcards_for_bill("Move Ship")
    print(", ".join(watchcards[0].duties.keys()))
    content.append(
        watch_bill_template.render(
            watch_cards=sorted(watchcards, key=lambda x: x.card_number),
            duties=watchcards[0].duties.keys()
        )
    )

    card_content = []
    for card in skills_grid.watchcards_for_bill("Move Ship"):
        card_content.append("\n\n")
        card_content.append(watchcard_latex(card))
    card_section_template = latex_jinja_env.get_template("card_list_section.tex")
    content.append(card_section_template.render(content=card_content))

    template = latex_jinja_env.get_template("crew_report.tex")
    f.write(template.render(content="\n".join(content)))

