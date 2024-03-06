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

from itertools import product
from math import sqrt
import numpy as np
from typing import Generator
from prolothar_common import validate

from prolothar_ca.model.pddl import Domain, Problem
from prolothar_ca.model.pddl.condition import PredicateIsTrueCondition
from prolothar_ca.model.pddl.condition import Not
from prolothar_ca.model.pddl.condition import Exists
from prolothar_ca.model.pddl.condition import And, Or
from prolothar_ca.model.pddl.effect import SetPredicateTrue, SetPredicateFalse

class Sudoku:

    def __init__(self, size: int = 9):
        """
        generates a new, empty Sudoku

        Parameters
        ----------
        size : int, optional
            size of the sudoku field, must be a quadratic number, by default 9 (3x3)
        """
        validate.greater(size, 0)
        self.__max_value = size
        self.__block_size = int(sqrt(size))
        validate.equals(self.__block_size**2, size)
        self.__rows = [
            [None for _ in range(self.__max_value)]
            for _ in range(self.__max_value)
        ]

    def get_block_size(self) -> int:
        return self.__block_size

    def get_max_value(self) -> int:
        return self.__max_value

    def __iter__(self) -> Generator[tuple[int, int, int|None],None,None]:
        """
        yields (x-coordinate starting at 0, y-coordinate starting at 0, value)
        """
        for x, row in enumerate(self.__rows):
            for y, value in enumerate(row):
                yield x,y,value

    def iter_rows(self) -> Generator[list[int|None],None,None]:
        for row in self.__rows:
            yield row

    def iter_columns(self) -> Generator[list[int|None],None,None]:
        for y in range(len(self.__rows)):
            column = [None] * len(self.__rows)
            for x,row in enumerate(self.__rows):
                column[x] = row[y]
            yield column

    def iter_blocks(self) -> Generator[list[list[int|None]],None,None]:
        for x_block in range(self.__max_value // self.__block_size):
            for y_block in range(self.__max_value // self.__block_size):
                block = []
                for x in range(self.__block_size * x_block, self.__block_size * (x_block + 1)):
                    block.append(self.__rows[x][self.__block_size * y_block:self.__block_size * (y_block + 1)])
                yield block

    def to_numpy(self) -> np.ndarray:
        """
        returns a two-dimensional numpy array of this sudoku puzzle
        """
        return np.array(self.__rows, dtype=np.float32)

    @staticmethod
    def from_numpy(array: np.ndarray):
        validate.equals(2, len(array.shape))
        validate.equals(array.shape[0], array.shape[1])
        sudoku = Sudoku(array.shape[0])
        for i in range(sudoku.get_max_value()):
            for j in range(sudoku.get_max_value()):
                value = array[i,j]
                sudoku[i,j] = None if value is None or np.isnan(value) else value
        return sudoku

    def __getitem__(self, coordinate):
        validate.equals(2, len(coordinate))
        return self.__rows[coordinate[0]][coordinate[1]]

    def __setitem__(self, coordinate, value: int|None):
        validate.equals(2, len(coordinate))
        if value is not None:
            validate.greater(value, 0)
            validate.less_or_equal(value, self.__max_value)
        self.__rows[coordinate[0]][coordinate[1]] = value

    def __repr__(self) -> str:
        return str(np.array(self.__rows))

    def is_solved(self) -> bool:
        """
        returns True iff this sudoku has assigned each cell a value and if the
        assignment is a valid solution
        """
        try:
            for _,_,value in self:
                validate.is_not_none(value)
            expected_sum = sum(range(1, self.__max_value + 1))
            for row in self.iter_rows():
                validate.equals(sum(row), expected_sum)
            for column in self.iter_columns():
                validate.equals(sum(column), expected_sum)
            for block in self.iter_blocks():
                validate.equals(np.sum(block), expected_sum)
            return True
        except ValueError:
            return False

    def to_pddl(self, problem_name: str|None = None) -> tuple[Domain, Problem]:
        """
        creates a PDDL representation of this sudoku board.
        the domain representation is the same for all instances

        Parameters
        ----------
        problem_name : str | None, optional
            name of the PDDL problem instance, by default None
            (i.e. a name will be generated, which might not be unique)

        Returns
        -------
        tuple[Domain, Problem]
            domain and problem definition of this sudoku board
        """
        domain = Domain('Sudoku')
        cell_type = domain.add_type('Cell')
        value_type = domain.add_type('CellValue')
        cell_is_empty = domain.add_predicate('cell_is_empty', [cell_type])
        cell_has_value = domain.add_predicate('cell_has_value', [cell_type, value_type])
        in_same_row = domain.add_predicate('in_same_row', [cell_type, cell_type])
        in_same_column = domain.add_predicate('in_same_column', [cell_type, cell_type])
        in_same_block = domain.add_predicate('in_same_block', [cell_type, cell_type])
        domain.add_action(
            'assign_value',
            {
                'cell': cell_type,
                'value': value_type
            },
            [
                PredicateIsTrueCondition(cell_is_empty, ['cell']),
                Not(Exists(
                    'other_cell', cell_type,
                    And([
                        Or([
                            PredicateIsTrueCondition(in_same_row, ['cell', 'other_cell']),
                            PredicateIsTrueCondition(in_same_column, ['cell', 'other_cell']),
                            PredicateIsTrueCondition(in_same_block, ['cell', 'other_cell']),
                        ]),
                        PredicateIsTrueCondition(cell_has_value, ['other_cell', 'value'])
                    ])
                )),
            ],
            [
                SetPredicateFalse(cell_is_empty, ['cell']),
                SetPredicateTrue(cell_has_value, ['cell', 'value'])
            ]
        )

        if problem_name is None:
            problem_name = f'Sudoku{self.__max_value}x{self.__max_value}'
        problem = Problem(problem_name, domain)
        value_to_object = {
            i: problem.add_object(f'number_{i}', value_type)
            for i in range(1, self.__max_value + 1)
        }
        x_y_to_cell_object = {}
        for x,y,value in self:
            cell_object = problem.add_object(f'cell_{x}_{y}', cell_type)
            x_y_to_cell_object[(x,y)] = cell_object
            if value is None:
                problem.get_intitial_state().true_predicates.add((
                    cell_is_empty, tuple([cell_object])
                ))
            else:
                problem.get_intitial_state().true_predicates.add((
                    cell_has_value, tuple([cell_object, value_to_object[value]])
                ))
        for x1,y1,_ in self:
            cell_1 = x_y_to_cell_object[(x1,y1)]
            for x2,y2,_ in self:
                cell_2 = x_y_to_cell_object[(x2,y2)]
                if x1 == x2:
                    problem.get_intitial_state().true_predicates.add((
                        in_same_row, (cell_1, cell_2)
                    ))
                if y1 == y2:
                    problem.get_intitial_state().true_predicates.add((
                        in_same_column, (cell_1, cell_2)
                    ))
                if x1 % self.__block_size == x2 % self.__block_size \
                and y1 % self.__block_size == y2 % self.__block_size:
                    problem.get_intitial_state().true_predicates.add((
                        in_same_block, (cell_1, cell_2)
                    ))
        for cell_object in x_y_to_cell_object.values():
            problem.add_goal(Not(PredicateIsTrueCondition(cell_is_empty, [cell_object.name])))

        return domain, problem

    def __hash__(self):
        return hash(repr(self))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Sudoku) and self.__rows == other.__rows
