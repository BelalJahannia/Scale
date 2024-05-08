import pandas as pd
from os import path

# TODO: Verification pending
class Reporter:
    def __init__(self):
        self.database = pd.DataFrame()
        self.col_names = []

        # Flags
        self.database_valid = False

    #
    def set_col_names(self, col_names_list=[]):
        self.col_names = col_names_list
        if not self.database_valid:
            self.database= pd.DataFrame(columns=col_names_list)
        else:
            self.database.columns = col_names_list

    #
    def add_row_to_table(self, row_items_list=[]):
        assert len(row_items_list) == len(self.col_names), 'The number of elements do not match the cols in the table'

        temp_df = pd.DataFrame([row_items_list], columns=self.col_names)
        self.database = pd.concat([self.database, temp_df])
        self.database_valid = True

    #
    def read_table_from_csv(self, csv_filename='', header=0):
        assert path.isfile(csv_filename)

        self.database = pd.read_csv(csv_filename, header=header)
        self.database_valid = True

    #
    def write_table_to_csv(self, csv_filename=''):
        assert self.database_valid, 'No data to write'

        self.database.to_csv(csv_filename, index=False)
