'''
    This file is part of Prolothar-Constraint-Acquisition (More Info: https://github.com/shs-it/prolothar-constraint-acquisition).

    Prolothar-Constraint-Acquisition is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Prolothar-Constraint-Acquisition is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Prolothar-Constraint-Acquisition. If not, see <https://www.gnu.org/licenses/>.
'''

import os

import pandas as pd
import dataframe_image as dfi

from prolothar_ca.ca.dataset_logger.filebased_dataset_logger import FilebasedDatasetLogger
from prolothar_ca.ca.dataset_generator.sudoku import CELL_VALUE_TYPE_NAME
from prolothar_ca.ca.dataset_generator.sudoku import CELL_VALUE_RELATION
from prolothar_ca.ca.dataset_generator.sudoku import CELL_X, CELL_Y

from prolothar_ca.model.ca.dataset import CaExample

class SudokuDatasetLogger(FilebasedDatasetLogger):
    """
    a dataset logger that is specialized for Sudoku
    """

    def _log_example(self, example: CaExample, index: int, directory: str):
        sudoku_problem_size = len(example.all_objects_per_type[CELL_VALUE_TYPE_NAME])
        cell_text = [[None for _ in range(sudoku_problem_size)] for _ in range(sudoku_problem_size)]
        for relation in example.relations[CELL_VALUE_RELATION]:
            if relation.value:
                x = relation.objects[0].features[CELL_X]
                y = relation.objects[0].features[CELL_Y]
                cell_value = relation.objects[1].object_id
                cell_text[x][y] = self.__extend_cell_text(cell_text[x][y], cell_value)
        dfi.export(
            pd.DataFrame(cell_text).fillna('').style.hide(),
            os.path.join(directory, f'{index}.png'),
            table_conversion='matplotlib'
        )

    def __extend_cell_text(self, old_cell_text: str|None, cell_value: str) -> str:
        if old_cell_text is None:
            new_cell_text = cell_value
        else:
            new_cell_text = f'{old_cell_text},{cell_value}'
        return new_cell_text


