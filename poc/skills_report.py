from crewms.jc_skills_grid import *


skills_grid = SkillsGrid("/Users/uayeb/Documents/Outdoors/Sailing/James Craig/Training/2018 Training and Assessment Update/" +
               "JC Training Skills Grid.xlsx")

skills_grid.reload_data()

assert len(skills_grid.watchcards) > 0

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
