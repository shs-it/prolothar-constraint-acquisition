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

from optapy import planning_entity, planning_id, planning_variable, planning_pin

from prolothar_ca.solver.optapy.sudoku.facts import CellValue

@planning_entity
class Cell:

    def __init__(self, x_coordinate: int, y_coordinate: int, value: CellValue = None, pinned: bool = False):
        self.cell_id = f'({x_coordinate},{y_coordinate})'
        self.x_coordinate = x_coordinate
        self.y_coordinate = y_coordinate
        self.value = value
        self.pinned = pinned

    @planning_id
    def get_id(self):
        return self.cell_id

    @planning_variable(CellValue, value_range_provider_refs=['valueRange'])
    def get_value(self):
        return self.value

    def set_value(self, value):
        self.value = value

    @planning_pin
    def is_pinned(self) -> bool:
        return self.pinned

    def __repr__(self) -> str:
        return f'Cell({self.x_coordinate}, {self.y_coordinate}, {self.value})'

