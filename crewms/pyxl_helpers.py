
from openpyxl.workbook.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.worksheet.cell_range import CellRange
from openpyxl.cell.cell import Cell
from typing import Any, Sequence, Tuple



def get_cells_for_reference(workbook, reference_name, bounding_box=None):
    # type: (Workbook, str, CellRange) -> Tuple[Cell]

    for sheet_name, cell_reference in workbook.defined_names[reference_name].destinations:
        range = CellRange(cell_reference)
        if bounding_box is not None:
            range = range.intersection(bounding_box)
        ws = workbook[sheet_name]  # type: Worksheet
        coord = range.coord
        return ws[coord]  # type: Tuple[Cell]

def get_range_for_reference(workbook, reference_name, bounding_box=None):
    # type: (Workbook, str, CellRange) -> CellRange

    for sheet_name, cell_reference in workbook.defined_names[reference_name].destinations:
        cell_range = CellRange(cell_reference)
        if bounding_box is not None:
            cell_range = cell_range.intersection(bounding_box)
        cell_range.title = sheet_name
        return cell_range
