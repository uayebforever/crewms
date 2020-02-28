from collections import defaultdict

from sqlalchemy import create_engine, Column, Integer, String, Table, ForeignKey, select
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection




import openpyxl
from openpyxl.worksheet import worksheet
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.cell.cell import Cell
from openpyxl.worksheet.cell_range import CellRange
import openpyxl

from typing import List, Iterable, Tuple, Dict

from .data import *
from .pyxl_helpers import get_cells_for_reference, get_range_for_reference

EMERGENCY_EVOLUTION_CATEGORY_NAME = "EMERGENCY PARTIES"
SEA_DUTY_CATEGORY_NAME = "SPECIAL SEA DUTIES"


class WatchBillLoader:

    def __init__(self, filename):
        self.filename = filename
        self.worksheet = None  # type: Worksheet
        self.column_iterator = None  # type: WatchBillColumnIterator

    def load_watch_bill_from_xlsx(self):
        # type: () -> WatchBill
        workbook = openpyxl.load_workbook(self.filename, data_only=True)  # , read_only=True)

        assert "WATCH BILL" in workbook.sheetnames
        self.worksheet = workbook["WATCH BILL"]

        named_ranges = workbook.defined_names
        watch_bill_bounds = worksheet.CellRange(self.worksheet.print_area[0])

        duty_names = list()

        column_cell_range = get_range_for_reference(workbook, "WatchBillColumns", bounding_box=watch_bill_bounds)

        self.column_iterator = WatchBillColumnIterator(self.worksheet, column_cell_range)

        # create evolutions
        evolutions = dict()
        evolutions.update(self._create_evolutions(EMERGENCY_EVOLUTION_CATEGORY_NAME))
        evolutions.update(self._create_evolutions(SEA_DUTY_CATEGORY_NAME))

        cards = list()

        # Iterate over rows, skipping the blank/invalid ones
        for row in range(column_cell_range.min_row + 1, watch_bill_bounds.max_row):
            row_data = self.load_row(row)
            if self.row_is_station(row_data):
                card = WatchCard()
                card.id = row
                card.card_number = row_data["Crew No."]
                card.name = row_data["Position"]


                self._add_duties_to_card_for_category(card, evolutions, row, SEA_DUTY_CATEGORY_NAME)
                self._add_duties_to_card_for_category(card, evolutions, row, EMERGENCY_EVOLUTION_CATEGORY_NAME)

                print(card.full_report)
                cards.append(card)

        return WatchBill(cards=cards)

    def _create_evolutions(self, category):
        evolutions = dict()  # type: Dict[str, Evolution]
        for _, evolution_name, _ in self.column_iterator.iterate_category(3, category):
            evolutions[evolution_name] = Evolution(name=evolution_name,
                                                   category=category)
        return evolutions

    def _add_duties_to_card_for_category(self, card, evolutions, row, category):
        for _, evolution, duty_name in self.column_iterator.iterate_category(row, category):
            duty = Duty(evolution=evolutions[evolution], name=duty_name, watch_card_id=card.id)
            evolutions[evolution].duties.append(duty)
            card.duties[evolution] = duty

    def row_is_station(self, row):
        # type: (Dict[str, Any]) -> bool
        return (row["Position"] is not None
                and str(row["Position"]).strip() != ""
                and "Watch" not in str(row["Crew No."])
                and str(row["Position"]) != "Position"
                and "".join([str(v) for v in row.values()]).strip() != "")

    def load_row(self, row):
        return {k: v for i, k, v in self.column_iterator.iterate_row(row)}




class WatchBill(object):

    def __init__(self, cards):
        # type: (List[WatchCard]) -> None
        self.cards = cards  # type: List[WatchCard]



class WatchBillColumnIterator(object):


    def __init__(self, worksheet, cell_range):
        # type: (Worksheet, CellRange) -> None

        self.worksheet = worksheet  # type: Worksheet
        self.cell_range = cell_range  # type: CellRange
        self.column_index = dict()  # type: Dict[int, Tuple[str, str]]
        self.columns = dict()  # type: Dict[str, Tuple[int, str]]
        self.columns_by_category = defaultdict(list)  # type: Dict[str, List[str]]

        category = ""  # type: str
        for row, col in next(iter(cell_range.rows)):
            category_cell_value = worksheet.cell(row - 1, col).value
            if category_cell_value is not None and str(category_cell_value).strip() != "":
                category = str(category_cell_value)
            if category is None:
                raise Exception("W&S Bill doesn't have a category above the left most column name")
            column_name = worksheet.cell(row, col).value
            self.column_index[col] = (column_name, category_cell_value)
            self.columns[column_name] = (col, category_cell_value)
            self.columns_by_category[category].append(column_name)

    def iterate_row(self, row_to_interate):
        # type: (int) -> Tuple[int, str, str]
        for col in self.worksheet.iter_cols(min_col=self.cell_range.min_col, max_col=self.cell_range.max_col,
                                              min_row=row_to_interate, max_row=row_to_interate):
            cell = col[0]
            assert isinstance(cell, Cell)
            yield cell.column, self.column_index[cell.column][0], cell.value

    # def iterate_emergency_duties(self, row_to_iterate):
    #     # type: (int) -> Tuple[int, str, str]
    #     yield from self.iterate_category(row_to_iterate, EMERGENCY_EVOLUTION_CATEGORY_NAME)
    #
    # def iterate_sea_duties(self, row_to_iterate):
    #     # type: (int) -> Tuple[int, str, str]
    #     yield from self.iterate_category(row_to_iterate, SEA_DUTY_CATEGORY_NAME)

    def iterate_category(self, row_to_iterate, category_name):
        # type: (int, str) -> Tuple[int, str, str]
        for column_name in self.columns_by_category[category_name]:
            column_number = self.columns[column_name][0]
            cell = self.worksheet.cell(row_to_iterate, column_number)
            yield column_number, column_name, cell.value
