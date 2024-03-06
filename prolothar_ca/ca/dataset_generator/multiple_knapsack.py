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
from random import Random

from prolothar_common import validate
from prolothar_ca.ca.dataset_generator.dataset_generator import \
    CaDatasetGenerator
from prolothar_ca.model.ca.constraints.constraint import CaConstraint
from prolothar_ca.model.ca.dataset import CaDataset
from prolothar_ca.model.ca.example import CaExample
from prolothar_ca.model.ca.obj import CaObject, CaObjectType
from prolothar_ca.model.ca.relation import CaRelation, CaRelationType
from prolothar_ca.model.ca.targets import CaTarget, RelationTarget
from prolothar_ca.model.ca.variable_type import CaBoolean, CaNumber
from prolothar_ca.model.ca.constraints.quantifier import ForAll
from prolothar_ca.model.ca.constraints.query import Product, AllOfType, Filter
from prolothar_ca.model.ca.constraints.numeric import AggregateSum, LessOrEqual, NumericFeature
from prolothar_ca.model.ca.constraints.boolean import RelationIsTrue, RelationIsFalse
from prolothar_ca.model.ca.constraints.conjunction import Implies
from prolothar_ca.model.ca.constraints.objects import ObjectsNotEqual

KNAPSACK_TYPE = 'Knapsack'
ITEM_TYPE = 'Item'
SIZE_FEATURE = 'size'
WEIGHT_FEATURE = 'weight'
VALUE_FEATURE = 'value'
ASSIGNED_RELATION = 'assigned'

class MultipleKnapsackCaDatasetGenerator(CaDatasetGenerator):
    """
    generates synthetic examples of a multiple knapsack dataset.
    we have a N knapsacks with a limited size and items with value and weight.
    an assignment is valid if the total weight of the items does not exceed
    the size of the knapsack.
    """

    def __init__(
            self, nr_of_items: int = 10, nr_of_knapsacks: int = 3,
            min_knapsack_size: int = 1, max_knapsack_size: int = 10,
            min_weight: int = 1, max_weight: int = 10,
            min_value: int = 1, max_value: int = 10,
            random_seed: int|None = None,
            termination_probability: float = 0):
        validate.greater_or_equal(nr_of_items, 1)
        validate.greater_or_equal(nr_of_knapsacks, 1)
        validate.greater_or_equal(min_knapsack_size, 1)
        validate.greater_or_equal(max_knapsack_size, min_knapsack_size)
        validate.greater_or_equal(min_weight, 1)
        validate.greater_or_equal(max_weight, min_weight)
        validate.greater_or_equal(max_value, min_value)
        validate.in_closed_interval(termination_probability, 0, 1)
        random_generator = Random(random_seed)
        self.__knapsack_objects = [
            CaObject(
                f'{KNAPSACK_TYPE}{i+1}', KNAPSACK_TYPE,
                {SIZE_FEATURE: random_generator.randint(min_knapsack_size, max_knapsack_size)}
            )
            for i in range(nr_of_knapsacks)
        ]
        self.__item_objects = [
            CaObject(
                f'{ITEM_TYPE}{i+1}', ITEM_TYPE,
                {
                    WEIGHT_FEATURE: random_generator.randint(min_weight, max_weight),
                    VALUE_FEATURE: random_generator.randint(min_value, max_value)
                }
            )
            for i in range(nr_of_items)
        ]
        self.__target_relation_type = CaRelationType(
            ASSIGNED_RELATION,
            (KNAPSACK_TYPE, ITEM_TYPE),
            CaBoolean()
        )
        self.__ground_truth_constraints = [
            ForAll(
                Filter(
                    Product([
                        AllOfType(KNAPSACK_TYPE, 'knapsack1'),
                        AllOfType(KNAPSACK_TYPE, 'knapsack2'),
                        AllOfType(ITEM_TYPE, 'item'),
                    ]),
                    ObjectsNotEqual('knapsack1', 'knapsack2'),
                ),
                Implies(
                    RelationIsTrue(self.__target_relation_type, ('knapsack1', 'item')),
                    RelationIsFalse(self.__target_relation_type, ('knapsack2', 'item')),
                )
            ),
            ForAll(
                AllOfType(KNAPSACK_TYPE, 'knapsack'),
                LessOrEqual(
                    AggregateSum(
                        NumericFeature(ITEM_TYPE, 'item', WEIGHT_FEATURE),
                        Filter(
                            AllOfType(ITEM_TYPE, 'item'),
                            RelationIsTrue(self.__target_relation_type, ('knapsack', 'item')),
                        ),
                    ),
                    NumericFeature(KNAPSACK_TYPE, 'knapsack', SIZE_FEATURE)
                )
            )
        ]
        self.__termination_probability = termination_probability

    def _create_empty_dataset(self) -> CaDataset:
        return CaDataset(
            {
                KNAPSACK_TYPE: CaObjectType(
                    KNAPSACK_TYPE,
                    {
                        SIZE_FEATURE: CaNumber(),
                    }
                ),
                ITEM_TYPE: CaObjectType(
                    ITEM_TYPE,
                    {
                        WEIGHT_FEATURE: CaNumber(),
                        VALUE_FEATURE: CaNumber()
                    }
                )
            },
            {
                ASSIGNED_RELATION: self.__target_relation_type
            }
        )

    def _generate_positive_example(self, random_generator: Random) -> CaExample:
        remaining_item_objects = list(self.__item_objects)
        random_generator.shuffle(remaining_item_objects)
        assigned_weight_per_knapsack = {knapsack: 0 for knapsack in self.__knapsack_objects}
        assigned_items_per_knapsack = {knapsack: set() for knapsack in self.__knapsack_objects}
        while remaining_item_objects:
            knapsack = random_generator.choice(self.__knapsack_objects)
            item = remaining_item_objects.pop()
            if assigned_weight_per_knapsack[knapsack] + item.features[WEIGHT_FEATURE] > knapsack.features[SIZE_FEATURE]:
                if random_generator.random() < self.__termination_probability:
                    break
            else:
                assigned_weight_per_knapsack[knapsack] += item.features[WEIGHT_FEATURE]
                assigned_items_per_knapsack[knapsack].add(item)
        return self.__create_example(assigned_items_per_knapsack, True)

    def __create_example(self, assigned_items_per_knapsack: dict[CaObject, set[CaObject]], is_valid: bool) -> CaExample:
        return CaExample(
            {
                KNAPSACK_TYPE: set(self.__knapsack_objects),
                ITEM_TYPE: set(self.__item_objects)
            },
            {
                ASSIGNED_RELATION: set(
                    CaRelation(ASSIGNED_RELATION, (knapsack, item), item in assigned_items_per_knapsack[knapsack])
                    for knapsack, item in product(self.__knapsack_objects, self.__item_objects)
                )
            },
            is_valid
        )

    def _generate_negative_example(self, random_generator: Random) -> CaExample:
        example = self._generate_positive_example(random_generator)
        example.is_valid_solution = False
        assignments = list(example.relations[ASSIGNED_RELATION])
        while all(c.holds(example, {}) for c in self.__ground_truth_constraints):
            example.set_relation_value(
                random_generator.choice(assignments),
                True
            )
        return example

    def get_ground_truth_constraints(self) -> list[CaConstraint]:
        return self.__ground_truth_constraints

    def get_target(self) -> CaTarget:
        return RelationTarget(ASSIGNED_RELATION)
