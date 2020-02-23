import os
import re

import jinja2


import crewms
from crewms.data import WatchCard
import jinja_vanish

from typing import List, Callable


@jinja_vanish.markup_escape_func
def latex_escape(text):
    # type: (str) -> str
    result = text
    if isinstance(text, str):
        result = re.sub(r"&", r"\&", result)
    if text is None:
        result = ""
    return result


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


def label_form(input):
    # type: (str) -> str
    return re.sub(r"\W", "", input)


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

latex_jinja_env.filters['jc_rank'] = jc_rank
latex_jinja_env.filters['label_form'] = label_form

def watch_and_station_bill(watchcards, sort_key_function):
    # type: (List[WatchCard], Callable) -> str
    watch_bill_template = latex_jinja_env.get_template("watch_bill.tex")

    return watch_bill_template.render(
            watch_cards=sorted(watchcards, key=sort_key_function),
            duties=watchcards[0].duties.keys()
        )
