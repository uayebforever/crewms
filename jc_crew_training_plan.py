

from crewms import Skill, Task


if __name__ == "__main__":


    # Tasks for setting square sails

    setting_squares = {
        "Set the Fore Course": [
            "Handle Clew Garnets",
            "Handle Leechlines",
            "Handle Buntlines",
            "Handle Tacks",
            "Handle Sheets",
            "Handle Lifts",
            "Call Evolution"
        ],
        "Set the Fore or Main Lower Topsail": [
            "Handle Sheets",
            "Handle Clews",
            "Handle Buntlines",
            "Call Evolution"
        ],
        "Set the Fore or Main Upper Topsail": [
            "Handle Buntlines",
            "Handle Downhauls",
            "Handle Windward Brace",
            "Handle Halyard",
            "Ease Topgallant Sheets",
            "Call Evolution"
        ],
        "Set the Fore/Main Topgallant": [
            "Handle Buntlines",
            "Handle Clews",
            "Handle Lee Brace",
            "Handle Halyard",
            "Handle Sheets",
            "Ease Royal Sheets",
            "Call Evolution"
        ]

    }

    for activity, tasks in setting_squares:
        for t in tasks:
            Task(activity, t)

    # Skills associated with line handling


