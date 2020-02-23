import pytest
import os
from crewms.watch_bill import *
from openpyxl.workbook.workbook import Workbook

class TestWatchBill:

    @pytest.fixture
    def workbook(self):
        return openpyxl.load_workbook(get_test_resource("modern_wns_bill.xlsx"), data_only=True)  # , read_only=True)


    def test_load_watch_bill_from_xlsx(self):

        WatchBillLoader(get_test_resource("modern_wns_bill.xlsx")).load_watch_bill_from_xlsx()


    def test_get_named_cells(self, workbook):
        # type: (Workbook) -> Any


        get_cells_for_reference(workbook, "WatchBillColumns", bounding_box=watch_bill_bounds)



def get_test_resource(filename):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), filename)
