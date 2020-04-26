import openpyxl
from openpyxl.worksheet import worksheet
from openpyxl.worksheet import worksheet



class SkillGridLoaderBase:
    def __init__(self, workbook_filename):
        # type: (str) -> None
        self.workbook = openpyxl.load_workbook(workbook_filename, data_only=True)  # type: workbook.Workbook

        assert "Skills Grid" in self.workbook.sheetnames
        self.skills_grid_sheet = self.workbook["Skills Grid"]  # type: worksheet.Worksheet

        assert "WnS Bill" in self.workbook.sheetnames
        # self.wns_bill = self.workbook["WnS Bill"]  # type: worksheet.Worksheet

        self.defined_names = self.workbook.defined_names
        self.bounding_box = worksheet.CellRange(self.skills_grid_sheet.print_area[0])

    def _get_cells_for_reference(self, reference_name):

        cells = []

        for sheet_name, cell_reference in self.workbook.defined_names[reference_name].destinations:
            ws = self.workbook[sheet_name]
            cells.append(ws[cell_reference])

        return cells
