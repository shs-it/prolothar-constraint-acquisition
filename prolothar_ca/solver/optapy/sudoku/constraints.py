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

from optapy import constraint_provider
from optapy.types import Joiners, HardSoftScore, ConstraintFactory

from prolothar_ca.solver.optapy.sudoku.entities import Cell

def create_constraint_provider(
        block_size: int,
        row_constraint_active: bool = True,
        column_constraint_active: bool = True,
        block_constraint_active: bool = True):
    @constraint_provider
    def create_constraints(constraint_factory: ConstraintFactory):
        constraint_list = []
        if row_constraint_active:
            constraint_list.append(all_values_in_same_row_must_be_different(constraint_factory))
        if column_constraint_active:
            constraint_list.append(all_values_in_same_column_must_be_different(constraint_factory))
        if block_constraint_active:
            constraint_list.append(create_all_values_in_same_block_must_be_different(block_size)(constraint_factory))
        return constraint_list
    return create_constraints

def all_values_in_same_row_must_be_different(constraint_factory: ConstraintFactory):
    return constraint_factory.for_each_unique_pair(Cell,
        Joiners.equal(lambda cell: cell.x_coordinate),
        Joiners.equal(lambda cell: cell.value.number)
    ).penalize("Duplicate value in row", HardSoftScore.ONE_HARD)

def all_values_in_same_column_must_be_different(constraint_factory: ConstraintFactory):
    return constraint_factory.for_each_unique_pair(Cell,
        Joiners.equal(lambda cell: cell.y_coordinate),
        Joiners.equal(lambda cell: cell.value.number)
    ).penalize("Duplicate value in column", HardSoftScore.ONE_HARD)

def create_all_values_in_same_block_must_be_different(block_size: int):
    def all_values_in_same_block_must_be_different(constraint_factory: ConstraintFactory):
        return constraint_factory.for_each_unique_pair(Cell,
            Joiners.equal(lambda cell: cell.x_coordinate // block_size),
            Joiners.equal(lambda cell: cell.y_coordinate // block_size),
            Joiners.equal(lambda cell: cell.value.number)
        ).penalize("Duplicate value in block", HardSoftScore.ONE_HARD)
    return all_values_in_same_block_must_be_different
