import traceback

from test_data_loader import TestDataLoader


class TestMainloop:
    def __init__(self):
        self.test_data_manager = TestDataLoader()

    def mainloop(self):
        try:
            pass

        except Exception:
            traceback.print_exc()

    def start(self, symbols, start_date, end_date):
        self.test_data_manager.init_test_data_loader(symbols, start_date, end_date)

        while 1:
            if self.test_data_manager.load_next() == False:
                break
            self.mainloop()
