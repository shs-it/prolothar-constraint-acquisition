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

from math import sqrt
import os
from random import Random
import sys
import numpy as np

from prolothar_common.timeout import timeout

from prolothar_ca.ca.dataset_generator.dataset_generator import CaDatasetGenerator
from prolothar_ca.model.ca.constraints.boolean import RelationIsTrue
from prolothar_ca.model.ca.constraints.conjunction import And
from prolothar_ca.model.ca.constraints.constraint import CaConstraint
from prolothar_ca.model.ca.constraints.numeric import Constant, Count, Equal, IntegerDivision, Modulo, NumericFeature
from prolothar_ca.model.ca.constraints.quantifier import ForAll
from prolothar_ca.model.ca.constraints.query import AllOfType, Filter, Product

from prolothar_ca.model.ca.dataset import CaDataset
from prolothar_ca.model.ca.example import CaExample
from prolothar_ca.model.ca.obj import CaObject, CaObjectType
from prolothar_ca.model.ca.relation import CaRelation, CaRelationType
from prolothar_ca.model.ca.targets import RelationTarget
from prolothar_ca.model.ca.variable_type import CaBoolean, CaNumber
from prolothar_ca.model.sudoku import Sudoku
from prolothar_ca.solver.specific.sudoku.pysudoku import SudokuSolver

CELL_TYPE_NAME = 'Cell'
CELL_VALUE_TYPE_NAME = 'CellValue'
CELL_VALUE_RELATION = 'cell_has_value'
CELL_X = 'x'
CELL_Y = 'y'
CELL_BLOCK_NR = 'b'

@timeout(10)
def solve_sudoku(sudoku: Sudoku) -> Sudoku:
    return SudokuSolver().solve(sudoku)

class SudokuCaDatasetGenerator(CaDatasetGenerator):

    def __init__(
            self, size: int = 9, only_return_unique_examples: bool = True, cache_dir: str = None,
            include_block_feature: bool = False):
        """
        creates a new SudokuCaDatasetGenerator

        Parameters
        ----------
        size : int, optional
            size of the sudoku field (by default 9, i.e. 3x3 blocks)
        only_return_unique_examples : bool, optional
            if False, examples with the same assignment can be generated, by default True
        cache_dir : str, optional
            can be used for caching => speed-up and better reproducibility, by default None
        include_block_feature : bool, optional
            if True, cells get an additional feature for their block numer.
            otherwise they only get row and column feature, by default False
        """
        self.__size = size
        self.__block_size = int(sqrt(self.__size))
        self.__cell_value_relation = CaRelationType(
            CELL_VALUE_RELATION,
            (CELL_TYPE_NAME, CELL_VALUE_TYPE_NAME),
            CaBoolean()
        )
        self.__only_return_unique_examples = only_return_unique_examples
        self.__include_block_feature = include_block_feature
        self.__generated_positive_sudokus: set[Sudoku] = set()
        self.__generated_negative_sudokus: set[Sudoku] = set()
        self.__cache_dir = cache_dir
        self.__cached_negative_sudokus: list[Sudoku] = []
        self.__cached_positive_sudokus: list[Sudoku] = []
        if self.__cache_dir:
            os.makedirs(self.__cache_dir, exist_ok=True)
            for cached_sudoku_file in os.listdir(self.__cache_dir):
                sudoku = Sudoku.from_numpy(np.loadtxt(os.path.join(self.__cache_dir, cached_sudoku_file)))
                if sudoku.is_solved():
                    self.__cached_positive_sudokus.append(sudoku)
                else:
                    self.__cached_negative_sudokus.append(sudoku)
        if self.__cached_positive_sudokus:
            self.__first_solved_sudoku = self.__cached_positive_sudokus[0]
        else:
            self.__first_solved_sudoku = Sudoku(size)
            self.__first_solved_sudoku = SudokuSolver().solve(self.__first_solved_sudoku)
            if not self.__first_solved_sudoku.is_solved():
                raise NotImplementedError('could not create an initial sudoku solution')

    def get_cell_value_relation_type(self) -> CaRelationType:
        return self.__cell_value_relation

    def _create_empty_dataset(self) -> CaDataset:
        cell_feature_definition = {
            CELL_X: CaNumber(),
            CELL_Y: CaNumber(),
        }
        if self.__include_block_feature:
            cell_feature_definition[CELL_BLOCK_NR] = CaNumber()
        return CaDataset(
            {
                CELL_TYPE_NAME: CaObjectType(
                    CELL_TYPE_NAME,
                    cell_feature_definition
                ),
                CELL_VALUE_TYPE_NAME: CaObjectType(CELL_VALUE_TYPE_NAME, {})
            },
            {
                CELL_VALUE_RELATION: self.__cell_value_relation
            }
        )

    def _generate_positive_example(self, random_generator: Random) -> CaExample:
        #in very rare circumstances, it can be that the solver does not find a valid solution in time
        positive_example_found = False
        read_from_cache = True
        nr_of_iterations = 0
        while not positive_example_found:
            if self.__cached_positive_sudokus:
                sudoku = self.__cached_positive_sudokus.pop()
            elif random_generator.choice([True, False]):
                sudoku = self.__permutate_numbers_in_sudoku(self.__first_solved_sudoku, random_generator)
                read_from_cache = False
            else:
                sudoku = self.__generate_sudoku_with_n_random_values(
                    random_generator, random_generator.randint(1, 9))
                try:
                    sudoku = solve_sudoku(sudoku)
                except KeyboardInterrupt:
                    #solver has raised a timeout
                    #if the sudoku is not solved, it will be filtered out
                    #and we try again
                    pass
                read_from_cache = False

            positive_example_found = sudoku.is_solved() and (
                not self.__only_return_unique_examples
                or sudoku not in self.__generated_positive_sudokus)
            nr_of_iterations += 1
            if nr_of_iterations > 100:
                print(f'warning: no new positive example found after {nr_of_iterations}')
        if not read_from_cache:
            self.__write_sudoku_to_cache_if_cache_enabled(sudoku)
        if self.__only_return_unique_examples:
            self.__generated_positive_sudokus.add(sudoku)
        return self.sudoku_to_example(sudoku, True)

    def __generate_sudoku_with_one_random_value(self, random_generator: Random) -> Sudoku:
        sudoku = Sudoku(self.__size)
        self.__set_a_random_cell_of_sudoku_to_a_random_value(sudoku, random_generator)
        return sudoku

    def __generate_sudoku_with_n_random_values(self, random_generator: Random, n: int) -> Sudoku:
        sudoku = Sudoku(self.__size)
        for _ in range(n):
            self.__set_a_random_cell_of_sudoku_to_a_random_value(sudoku, random_generator)
        return sudoku

    def __permutate_numbers_in_sudoku(self, sudoku: Sudoku, random_generator: Random) -> Sudoku:
        permutated_values = [i+1 for i in range(self.__size)]
        random_generator.shuffle(permutated_values)
        permutated_values = {
            i+1: value for i, value in enumerate(permutated_values)
        }
        permutated_sudoku = Sudoku(self.__size)
        for i,j,value in sudoku:
            permutated_sudoku[i,j] = permutated_values[value]
        return permutated_sudoku

    def __set_a_random_cell_of_sudoku_to_a_random_value(
            self, sudoku: Sudoku, random_generator: Random,
            none_included: bool = False):
        value_range = list(range(1, self.__size + 1))
        if none_included:
            value_range.append(None)
        sudoku[
            random_generator.randint(0, self.__size - 1),
            random_generator.randint(0, self.__size - 1)
        ] = random_generator.choice(value_range)

    def _generate_negative_example(self, random_generator: Random, nr_of_failed_iterations: int = 0) -> CaExample:
        if self.__cached_negative_sudokus:
            sudoku = self.__cached_negative_sudokus.pop()
            read_from_cache = True
        else:
            sudoku = random_generator.choice([
                self._generate_invalid_sudoku_by_changing_one_cell_of_a_valid_sudoku,
                self._generate_invalid_sudoku_that_only_violates_block_constraints,
            ])(random_generator)
            read_from_cache = False
        if self.__only_return_unique_examples:
            if sudoku in self.__generated_negative_sudokus:
                if nr_of_failed_iterations > 100:
                    print(f'warning: no new negative example found after {nr_of_failed_iterations}')
                return self._generate_negative_example(random_generator, nr_of_failed_iterations + 1)
            self.__generated_negative_sudokus.add(sudoku)
        if not read_from_cache:
            self.__write_sudoku_to_cache_if_cache_enabled(sudoku)
        return self.sudoku_to_example(sudoku, False)

    def _generate_invalid_sudoku_by_changing_one_cell_of_a_valid_sudoku(self, random_generator: Random) -> Sudoku:
        sudoku = SudokuSolver().solve(self.__generate_sudoku_with_one_random_value(random_generator))
        while sudoku.is_solved():
            self.__set_a_random_cell_of_sudoku_to_a_random_value(
                sudoku, random_generator, none_included=True)
        return sudoku

    def _generate_invalid_sudoku_that_only_violates_block_constraints(self, random_generator: Random) -> Sudoku:
        if random_generator.choice([True,False]):
            return self._generate_block_violating_sudoku_by_row_and_col_permutation(random_generator)
        else:
            return self._generate_block_violating_sudoku_by_number_permutation(random_generator)

    def _generate_block_violating_sudoku_by_number_permutation(self, random_generator: Random) -> Sudoku:
        number_permutation = list(range(self.__size))
        random_generator.shuffle(number_permutation)
        block_constraint_violating_sudoku = Sudoku(self.__size)
        for i in range(self.__size):
            for j in range(self.__size):
                block_constraint_violating_sudoku[i,j] = number_permutation[(i + j) % self.__size] + 1
        return block_constraint_violating_sudoku

    def _generate_block_violating_sudoku_by_row_and_col_permutation(self, random_generator: Random) -> Sudoku:
        rows = [
            [None for _ in range(self.__size)]
            for _ in range(self.__size)
        ]
        for i in range(self.__size):
            for j in range(self.__size):
                rows[i][j] = (i + j) % 4 + 1
        sudoku = Sudoku.from_numpy(np.array(rows))
        for _ in range(100):
            sudoku = self.__permutate_sudoku(sudoku, random_generator)
            if not sudoku.is_solved():
                return sudoku
        raise NotImplementedError('unexpectedly could not create invalid sudoku example')

    def __permutate_sudoku(self, sudoku: Sudoku, random_generator: Random) -> Sudoku:
        np_random = np.random.default_rng(random_generator.randint(0, sys.maxsize))
        rows = sudoku.to_numpy()
        np_random.shuffle(rows)
        rows = np.transpose(rows)
        np_random.shuffle(rows)
        return Sudoku.from_numpy(rows)

    def __write_sudoku_to_cache_if_cache_enabled(self, sudoku: Sudoku):
        if self.__cache_dir:
            np.savetxt(
                os.path.join(self.__cache_dir, f'{len(os.listdir(self.__cache_dir))}.txt'),
                sudoku.to_numpy()
            )

    def sudoku_to_example(self, sudoku: Sudoku, is_valid_solution: bool) -> CaExample:
        objects_per_type = {
            CELL_TYPE_NAME: set([
                self.__create_cell_ca_object(x,y) for x,y,_ in sudoku
            ]),
            CELL_VALUE_TYPE_NAME: set([
                CaObject(
                    str(value), CELL_VALUE_TYPE_NAME, {}
                ) for value in range(1, sudoku.get_max_value() + 1)
            ])
        }
        return CaExample(
            objects_per_type,
            {
                CELL_VALUE_RELATION: set([
                    CaRelation(
                        CELL_VALUE_RELATION,
                        (cell, cell_value),
                        sudoku[cell.features[CELL_X], cell.features[CELL_Y]] == int(cell_value.object_id)
                    ) for cell in objects_per_type[CELL_TYPE_NAME]
                    for cell_value in objects_per_type[CELL_VALUE_TYPE_NAME]
                ])
            },
            is_valid_solution
        )

    def __create_cell_ca_object(self, x: int, y: int) -> CaObject:
        feature_dict = {CELL_X: x, CELL_Y: y}
        if self.__include_block_feature:
            feature_dict[CELL_BLOCK_NR] = (
                x // self.__block_size * self.__block_size +
                y // self.__block_size
            )
        return CaObject(
            f'cell_{x}_{y}', CELL_TYPE_NAME,
            feature_dict
        )

    def get_ground_truth_constraints(self) -> list[CaConstraint]:
        return [
            #each cell must have exactly one number assigned
            ForAll(
                AllOfType(CELL_TYPE_NAME, 'cell'),
                Equal(
                    Count(
                        Filter(
                            AllOfType(CELL_VALUE_TYPE_NAME, 'number'),
                            RelationIsTrue(self.__cell_value_relation, ('cell', 'number')),
                        )
                    ),
                    Constant(1)
                )
            ),
            #each number must occur exactly once in a row
            ForAll(
                AllOfType(CELL_VALUE_TYPE_NAME, 'number'),
                Equal(
                    Count(
                        Filter(
                            Product([
                                AllOfType(CELL_TYPE_NAME, 'cell_a'),
                                AllOfType(CELL_TYPE_NAME, 'cell_b'),
                            ]),
                            And([
                                RelationIsTrue(self.__cell_value_relation, ('cell_a', 'number')),
                                RelationIsTrue(self.__cell_value_relation, ('cell_b', 'number')),
                                Equal(
                                    NumericFeature(CELL_TYPE_NAME, 'cell_a', CELL_X),
                                    NumericFeature(CELL_TYPE_NAME, 'cell_b', CELL_X)
                                )
                            ])
                        )
                    ),
                    Constant(1)
                )
            ),
            #each number must occur exactly once in a column
            ForAll(
                AllOfType(CELL_VALUE_TYPE_NAME, 'number'),
                Equal(
                    Count(
                        Filter(
                            Product([
                                AllOfType(CELL_TYPE_NAME, 'cell_a'),
                                AllOfType(CELL_TYPE_NAME, 'cell_b'),
                            ]),
                            And([
                                RelationIsTrue(self.__cell_value_relation, ('cell_a', 'number')),
                                RelationIsTrue(self.__cell_value_relation, ('cell_b', 'number')),
                                Equal(
                                    NumericFeature(CELL_TYPE_NAME, 'cell_a', CELL_Y),
                                    NumericFeature(CELL_TYPE_NAME, 'cell_b', CELL_Y)
                                )
                            ])
                        )
                    ),
                    Constant(1)
                )
            ),
            #each number must occur exactly once in a block
            ForAll(
                AllOfType(CELL_VALUE_TYPE_NAME, 'number'),
                Equal(
                    Count(
                        Filter(
                            Product([
                                AllOfType(CELL_TYPE_NAME, 'cell_a'),
                                AllOfType(CELL_TYPE_NAME, 'cell_b'),
                            ]),
                            And([
                                RelationIsTrue(self.__cell_value_relation, ('cell_a', 'number')),
                                RelationIsTrue(self.__cell_value_relation, ('cell_b', 'number')),
                                Equal(
                                    IntegerDivision(
                                        NumericFeature(CELL_TYPE_NAME, 'cell_a', CELL_X),
                                        Constant(self.__block_size)
                                    ),
                                    IntegerDivision(
                                        NumericFeature(CELL_TYPE_NAME, 'cell_b', CELL_X),
                                        Constant(self.__block_size)
                                    )
                                ),
                                Equal(
                                    IntegerDivision(
                                        NumericFeature(CELL_TYPE_NAME, 'cell_a', CELL_Y),
                                        Constant(self.__block_size)
                                    ),
                                    IntegerDivision(
                                        NumericFeature(CELL_TYPE_NAME, 'cell_b', CELL_Y),
                                        Constant(self.__block_size)
                                    )
                                )
                            ])
                        )
                    ),
                    Constant(1)
                )
            )
        ]

    def get_target(self) -> RelationTarget:
        return RelationTarget(CELL_VALUE_RELATION)