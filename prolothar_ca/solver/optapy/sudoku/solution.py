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

from optapy import (
    planning_solution, problem_fact_collection_property, value_range_provider,
    planning_entity_collection_property, planning_score)
from optapy.types import HardSoftScore

from prolothar_ca.solver.optapy.sudoku.entities import Cell
from prolothar_ca.solver.optapy.sudoku.facts import CellValue

@planning_solution
class SudokuSolution:

    def __init__(self, value_list: list[CellValue], cell_list: list[Cell], score=None):
        self.value_list = value_list
        self.cell_list = cell_list
        self.score = score

    @problem_fact_collection_property(CellValue)
    @value_range_provider(range_id='valueRange')
    def get_value_list(self):
        return self.value_list

    @planning_entity_collection_property(Cell)
    def get_cell_list(self):
        return self.cell_list

    @planning_score(HardSoftScore)
    def get_score(self):
        return self.score

    def set_score(self, score):
        self.score = score
