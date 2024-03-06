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

from random import Random
from nqueens import Queen
from itertools import permutations

from prolothar_common import validate
from prolothar_ca.ca.dataset_generator.dataset_generator import CaDatasetGenerator
from prolothar_ca.model.ca.constraints.boolean import RelationIsTrue, Not
from prolothar_ca.model.ca.constraints.conjunction import And, Or
from prolothar_ca.model.ca.constraints.constraint import CaConstraint
from prolothar_ca.model.ca.constraints.numeric import Absolute, Constant, Count, Difference, Equal, LessOrEqual, Modulo, NumericFeature
from prolothar_ca.model.ca.constraints.objects import ObjectsNotEqual
from prolothar_ca.model.ca.constraints.quantifier import ForAll
from prolothar_ca.model.ca.constraints.query import AllOfType, Filter, Product

from prolothar_ca.model.ca.dataset import CaDataset
from prolothar_ca.model.ca.example import CaExample
from prolothar_ca.model.ca.obj import CaObject, CaObjectType
from prolothar_ca.model.ca.relation import CaRelation, CaRelationType
from prolothar_ca.model.ca.targets import CaTarget, RelationTarget
from prolothar_ca.model.ca.variable_type import CaBoolean, CaNumber

QUEEN_TYPE_NAME = 'Queen'
SQUARE_TYPE_NAME = 'Square'
QUEEN_ON_SQUARE_RELATION = 'queen_on_square'

class NQueensCaDatasetGenerator(CaDatasetGenerator):
    """
    https://en.wikipedia.org/wiki/Eight_queens_puzzle#Counting_solutions_for_other_sizes_n
    """

    def __init__(self, n: int = 8, include_queen_permutations: bool = True, random_seed: int|None = None):
        """
        creates a new dataset generator for the n queens problem

        Parameters
        ----------
        n : int, optional
            number of queens and size of the chess field, by default 8, i.e. a normal chess field
        include_queen_permutations : boolean, optional
            whether the set of valid solutions should include permutation of queens, by default True
        random_seed : int|None, optional
            seed for random number generator used to create queen nr permutations, by default None
        """
        self.__n = n
        self.__include_queen_permutations = include_queen_permutations
        self.__queen_position_relation = CaRelationType(
            QUEEN_ON_SQUARE_RELATION,
            (QUEEN_TYPE_NAME, SQUARE_TYPE_NAME),
            CaBoolean()
        )
        self.__queen = Queen(n)
        self.__random = Random(random_seed)
        self.__all_solutions = self.__initialize_all_solutions(self.__queen.queen_data)
        self.__current_solution_index = 0
        self.__ground_truth_constraints = [
            #only one queen per square
            ForAll(
                AllOfType(SQUARE_TYPE_NAME, 's'),
                LessOrEqual(
                    Count(
                        Filter(
                            AllOfType(QUEEN_TYPE_NAME, 'q'),
                            RelationIsTrue(self.__queen_position_relation, ('q', 's')),
                        )
                    ),
                    Constant(1)
                )
            ),
            #every queen must stand on exactly one square
            ForAll(
                AllOfType(QUEEN_TYPE_NAME, 'q'),
                Equal(
                    Count(
                        Filter(
                            AllOfType(SQUARE_TYPE_NAME, 's'),
                            RelationIsTrue(self.__queen_position_relation, ('q', 's')),
                        )
                    ),
                    Constant(1)
                )
            ),
            #queens must not attack each other
            ForAll(
                Filter(
                    Product([
                        AllOfType(SQUARE_TYPE_NAME, 's1'),
                        AllOfType(SQUARE_TYPE_NAME, 's2'),
                        AllOfType(QUEEN_TYPE_NAME, 'q1'),
                        AllOfType(QUEEN_TYPE_NAME, 'q2')
                    ]),
                    And([
                        ObjectsNotEqual('s1', 's2'),
                        ObjectsNotEqual('q1', 'q2'),
                        RelationIsTrue(self.__queen_position_relation, ('q1', 's1')),
                        RelationIsTrue(self.__queen_position_relation, ('q2', 's2'))
                    ])
                ),
                Not(Or([
                    Equal(
                        NumericFeature(SQUARE_TYPE_NAME, 's1', 'x'),
                        NumericFeature(SQUARE_TYPE_NAME, 's2', 'y')
                    ),
                    Equal(
                        NumericFeature(SQUARE_TYPE_NAME, 's1', 'x'),
                        NumericFeature(SQUARE_TYPE_NAME, 's2', 'y')
                    ),
                    Equal(
                        Absolute(Difference(
                            NumericFeature(SQUARE_TYPE_NAME, 's1', 'x'),
                            NumericFeature(SQUARE_TYPE_NAME, 's2', 'x')
                        )),
                        Absolute(Difference(
                            NumericFeature(SQUARE_TYPE_NAME, 's1', 'y'),
                            NumericFeature(SQUARE_TYPE_NAME, 's2', 'y')
                        ))
                    )
                ]))
            )
        ]

    def __initialize_all_solutions(self, raw_solutions: list[list[list[int]]]):
        all_solutions = []
        if self.__include_queen_permutations:
            for raw_solution in raw_solutions:
                for queen_nr_permutation in permutations(range(1, self.__n+1), self.__n):
                    queen_nr_permutation = list(queen_nr_permutation)
                    all_solutions.append(self.__create_solution_from_queen_nr_permutation(
                        raw_solution, queen_nr_permutation))
        else:
            queen_nr_permutation = list(range(1, self.__n + 1))
            self.__random.shuffle(queen_nr_permutation)
            for raw_solution in raw_solutions:
                all_solutions.append(self.__create_solution_from_queen_nr_permutation(
                    raw_solution, list(queen_nr_permutation)))
        return all_solutions

    def __create_solution_from_queen_nr_permutation(
            self, raw_solution: list[list[int]], queen_nr_permutation: list[int]) -> list[list[int]]:
        return [
            [
                queen_nr_permutation.pop() if value == 1 else 0 for value in row
            ]
            for row in raw_solution
        ]

    def generate(
            self, nr_of_positive_examples: int,
            nr_of_negative_examples: int,
            random_seed: int|None = None) -> CaDataset:
        max_nr_of_solutions = len(self.__all_solutions)
        validate.less_or_equal(
            nr_of_positive_examples, max_nr_of_solutions,
            msg=f'There are only {max_nr_of_solutions} solutions '
            f'({"with" if self.__include_queen_permutations else "without"} permutation of queens) '
            f'for {self.__n}-Queens, '
            f'but {nr_of_positive_examples} are demanded'
        )
        Random(random_seed).shuffle(self.__all_solutions)
        self.__current_solution_index = 0
        return super().generate(
            nr_of_positive_examples, nr_of_negative_examples,
            random_seed=random_seed)

    def _create_empty_dataset(self) -> CaDataset:
        return CaDataset(
            {
                SQUARE_TYPE_NAME: CaObjectType(
                    SQUARE_TYPE_NAME,
                    {
                        'x': CaNumber(),
                        'y': CaNumber(),
                    }
                ),
                QUEEN_TYPE_NAME: CaObjectType(QUEEN_TYPE_NAME, {})
            },
            {
                QUEEN_ON_SQUARE_RELATION: self.__queen_position_relation
            }
        )

    def _generate_positive_example(self, random_generator: Random) -> CaExample:
        solution = self.__all_solutions[self.__current_solution_index]
        self.__current_solution_index += 1
        return self.__solution_to_example(solution, True)

    def __solution_to_example(self, solution: list[list[int]], is_valid_solution: bool) -> CaExample:
        queen_list = [CaObject(f'queen{i}', QUEEN_TYPE_NAME, {}) for i in range(self.__n)]
        example = CaExample(
            {
                SQUARE_TYPE_NAME: set(
                    CaObject(f'square_{x}_{y}', SQUARE_TYPE_NAME, {'x': x, 'y': y})
                    for x, row in enumerate(solution)
                    for y, _ in enumerate(row)
                ),
                QUEEN_TYPE_NAME: set(queen_list)
            },
            {},
            is_valid_solution
        )
        for square in example.all_objects_per_type[SQUARE_TYPE_NAME]:
            for i,queen in enumerate(queen_list):
                example.add_relation(CaRelation(
                    QUEEN_ON_SQUARE_RELATION,
                    (queen, square),
                    solution[square.features['x']][square.features['y']] == i+1
                ))
        return example

    def _generate_negative_example(self, random_generator: Random) -> CaExample:
        possible_positions = list(self.__queen.pos)
        while True:
            random_generator.shuffle(possible_positions)
            solution = [[0 for _ in range(self.__n)] for _ in range(self.__n)]
            i = 1
            for x,y in possible_positions[:self.__n]:
                solution[x][y] = i
                i += 1
            example = self.__solution_to_example(solution, False)
            if any(not c.holds(example, {}) for c in self.__ground_truth_constraints):
                return example

    def get_ground_truth_constraints(self) -> list[CaConstraint]:
        return self.__ground_truth_constraints

    def get_target(self) -> CaTarget:
        return RelationTarget(QUEEN_ON_SQUARE_RELATION)