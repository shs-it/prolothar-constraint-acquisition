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
from prolothar_ca.model.ca.variable_type import CaBoolean
from prolothar_ca.model.ca.constraints.quantifier import ForAll
from prolothar_ca.model.ca.constraints.query import Product, AllOfType, Filter
from prolothar_ca.model.ca.constraints.numeric import Count, Equal, Constant
from prolothar_ca.model.ca.constraints.boolean import RelationIsTrue, RelationIsFalse
from prolothar_ca.model.ca.constraints.conjunction import Implies

NODE_TYPE = 'Node'
COLOR_TYPE = 'Color'
HAS_EDGE_RELATION = 'has_edge'
HAS_COLOR_RELATION = 'has_color'

class GraphColorCaDatasetGenerator(CaDatasetGenerator):
    """
    generates synthetic examples of a multiple knapsack dataset.
    we have a N knapsacks with a limited size and items with value and weight.
    an assignment is valid if the total weight of the items does not exceed
    the size of the knapsack.
    """

    def __init__(
            self, nr_of_nodes: int = 10, nr_of_edges: int = 20,
            create_negative_examples_by_deleting_color: bool = True,
            create_negative_examples_by_adding_color: bool = True,
            create_negative_examples_by_changing_color: bool = True,
            random_seed: int|None = None):
        validate.greater_or_equal(nr_of_nodes, 1)
        validate.greater_or_equal(nr_of_edges, 0)
        max_nr_of_edges = nr_of_nodes * (nr_of_nodes - 1) // 2
        self.__nr_of_edges = nr_of_edges
        validate.less_or_equal(nr_of_edges, max_nr_of_edges)
        validate.is_true(
            create_negative_examples_by_deleting_color or
            create_negative_examples_by_adding_color or
            create_negative_examples_by_changing_color,
            msg='enable at least one possibility to create negative examples'
        )
        self.__create_negative_examples_by_deleting_color = create_negative_examples_by_deleting_color
        self.__create_negative_examples_by_adding_color = create_negative_examples_by_adding_color
        self.__create_negative_examples_by_changing_color = create_negative_examples_by_changing_color
        random_generator = Random(random_seed)
        self.__node_objects = [
            CaObject(
                f'{NODE_TYPE}{i+1}', NODE_TYPE, {}
            )
            for i in range(nr_of_nodes)
        ]
        self.__color_objects = [
            CaObject(
                f'{COLOR_TYPE}{i+1}', COLOR_TYPE, {}
            )
            for i in range(nr_of_nodes)
        ]
        self.__edge_relation_set = set()
        is_connected_list = [True] * nr_of_edges + [False] * (max_nr_of_edges - nr_of_edges)
        random_generator.shuffle(is_connected_list)
        for i,node_a in enumerate(self.__node_objects):
            for node_b in self.__node_objects[i+1:]:
                self.__edge_relation_set.add(CaRelation(HAS_EDGE_RELATION, (node_a, node_b), is_connected_list[i]))
                self.__edge_relation_set.add(CaRelation(HAS_EDGE_RELATION, (node_b, node_a), is_connected_list[i]))
            self.__edge_relation_set.add(CaRelation(HAS_EDGE_RELATION, (node_a, node_a), False))
        self.__color_relation_type = CaRelationType(
            HAS_COLOR_RELATION,
            (NODE_TYPE, COLOR_TYPE),
            CaBoolean()
        )
        self.__edge_relation_type = CaRelationType(
            HAS_EDGE_RELATION,
            (NODE_TYPE, NODE_TYPE),
            CaBoolean()
        )
        self.__ground_truth_constraints = [
            ForAll(
                AllOfType(NODE_TYPE, 'node'),
                Equal(
                    Count(Filter(
                        AllOfType(COLOR_TYPE, 'color'),
                        RelationIsTrue(self.__color_relation_type, ('node', 'color'))
                    )),
                    Constant(1)
                )
            ),
            ForAll(
                Filter(
                    Product([
                        AllOfType(NODE_TYPE, 'node1'),
                        AllOfType(NODE_TYPE, 'node2'),
                        AllOfType(COLOR_TYPE, 'color'),
                    ]),
                    RelationIsTrue(self.__edge_relation_type, ('node1', 'node2'))
                ),
                Implies(
                    RelationIsTrue(self.__color_relation_type, ('node1', 'color')),
                    RelationIsFalse(self.__color_relation_type, ('node2', 'color'))
                )
            )
        ]

    def _create_empty_dataset(self) -> CaDataset:
        return CaDataset(
            {
                NODE_TYPE: CaObjectType(NODE_TYPE, {}),
                COLOR_TYPE: CaObjectType(COLOR_TYPE, {}),
            },
            {
                HAS_COLOR_RELATION: self.__color_relation_type,
                HAS_EDGE_RELATION: self.__edge_relation_type
            }
        )

    def _generate_positive_example(self, random_generator: Random) -> CaExample:
        return self.__create_example(self.__generate_valid_color_assignment(random_generator), True)

    def __generate_valid_color_assignment(self, random_generator: Random) -> dict[CaObject, CaObject]:
        assigned_color_per_node = {node: None for node in self.__node_objects}
        edge_set = set(relation.objects for relation in self.__edge_relation_set if relation.value)
        randomly_sorted_color_objects = list(self.__color_objects)
        random_generator.shuffle(randomly_sorted_color_objects)
        for node in self.__node_objects:
            for color in randomly_sorted_color_objects:
                if all(
                        assigned_color_per_node[n] is None or assigned_color_per_node[n] != color
                        for n in self.__node_objects if (node, n) in edge_set
                ):
                    assigned_color_per_node[node] = color
                    break
        return assigned_color_per_node

    def __create_example(self, assigned_color_per_node: dict[CaObject, CaObject], is_valid: bool) -> CaExample:
        return CaExample(
            {
                NODE_TYPE: set(self.__node_objects),
                COLOR_TYPE: set(self.__color_objects)
            },
            {
                HAS_EDGE_RELATION: self.__edge_relation_set,
                HAS_COLOR_RELATION: set(
                    CaRelation(
                        HAS_COLOR_RELATION, (node, color),
                        assigned_color_per_node[node] is not None and assigned_color_per_node[node] == color
                    )
                    for node, color in product(self.__node_objects, self.__color_objects)
                )
            },
            is_valid
        )

    def _generate_negative_example(self, random_generator: Random) -> CaExample:
        color_assignment = self.__generate_valid_color_assignment(random_generator)
        if self.__create_negative_examples_by_deleting_color and random_generator.choice((True, False, False)):
            #produce a node without a color
            color_assignment[random_generator.choice(self.__node_objects)] = None
            return self.__create_example(color_assignment, False)
        elif self.__create_negative_examples_by_adding_color \
        and (self.__nr_of_edges == 0 or random_generator.choice((True, False))):
            #produce a node with two colors
            example = self.__create_example(color_assignment, False)
            false_relation_list = [r for r in example.relations[HAS_COLOR_RELATION] if not r.value]
            example.set_relation_value(random_generator.choice(false_relation_list), True)
            return example
        elif self.__create_negative_examples_by_changing_color and self.__nr_of_edges > 0:
            #change color of a node to the color of a neighbor
            while True:
                color_assignment[random_generator.choice(self.__node_objects)] = random_generator.choice(self.__color_objects)
                example = self.__create_example(color_assignment, False)
                if any(not c.holds(example, {}) for c in self.__ground_truth_constraints):
                    return example
        else:
            raise NotImplementedError('could not generate negative example')

    def get_ground_truth_constraints(self) -> list[CaConstraint]:
        return self.__ground_truth_constraints

    def get_target(self) -> CaTarget:
        return RelationTarget(HAS_COLOR_RELATION)
