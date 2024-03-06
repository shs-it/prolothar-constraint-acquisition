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

from math import factorial
from itertools import product, permutations
from random import Random
from copy import deepcopy

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
from prolothar_ca.model.ca.constraints.numeric import Equal, Constant, Count, Absolute, Difference, NumericFeature
from prolothar_ca.model.ca.constraints.boolean import RelationIsTrue, RelationIsFalse
from prolothar_ca.model.ca.constraints.conjunction import Implies
from prolothar_ca.model.ca.constraints.objects import ObjectsEqual, ObjectsNotEqual

TEAM_TYPE = 'Team'
ROUND_TYPE = 'Round'
ROUND_FEATURE_NR = 'nr'
MATCH_RELATION = 'Match'

class DoubleRoundRobinCaDatasetGenerator(CaDatasetGenerator):
    """
    an artificial double round robin tournament dataset generator
    """

    def __init__(self, nr_of_teams: int):
        validate.greater_or_equal(nr_of_teams, 2)
        self.__nr_of_teams = nr_of_teams
        self.__team_permutations_for_positive_examples = None
        self.__team_permutations_for_negative_examples = None
        self.__round_objects = [
            CaObject(f'Round{i+1}', ROUND_TYPE, {ROUND_FEATURE_NR: i+1})
            for i in range(2*(self.__nr_of_teams - 1))
        ]
        self.__team_objects = [
            CaObject(f'Team{i+1}', TEAM_TYPE, {})
            for i in range(self.__nr_of_teams)
        ]
        self.__match_relation_type = CaRelationType(
            MATCH_RELATION,
            (ROUND_TYPE, TEAM_TYPE, TEAM_TYPE),
            CaBoolean()
        )
        self.__ground_truth_constraints = [
            ForAll(
                Product([
                    AllOfType(TEAM_TYPE, 'team'),
                    AllOfType(ROUND_TYPE, 'round')
                ]),
                RelationIsFalse(self.__match_relation_type, ('round', 'team', 'team'))
            ),
            ForAll(
                Filter(
                    Product([
                        AllOfType(TEAM_TYPE, 'home'),
                        AllOfType(TEAM_TYPE, 'away')
                    ]),
                    ObjectsNotEqual('home', 'away')
                ),
                Equal(
                    Count(
                        Filter(
                            AllOfType(ROUND_TYPE, 'round'),
                            RelationIsTrue(self.__match_relation_type, ('round', 'home', 'away'))
                        )
                    ),
                    Constant(1)
                )
            ),
            ForAll(
                Filter(
                    Product([
                        AllOfType(TEAM_TYPE, 'home'),
                        AllOfType(TEAM_TYPE, 'away'),
                        AllOfType(ROUND_TYPE, 'round1'),
                        AllOfType(ROUND_TYPE, 'round2')
                    ]),
                    Equal(
                        Absolute(
                            Difference(
                                NumericFeature(ROUND_TYPE, 'round1', ROUND_FEATURE_NR),
                                NumericFeature(ROUND_TYPE, 'round2', ROUND_FEATURE_NR),
                            )
                        ),
                        Constant(self.__nr_of_teams - 1)
                    )
                ),
                Implies(
                    RelationIsTrue(self.__match_relation_type, ('round1', 'home', 'away')),
                    RelationIsTrue(self.__match_relation_type, ('round2', 'away', 'home')),
                )
            )
        ]

    def generate(
            self, nr_of_positive_examples: int,
            nr_of_negative_examples: int,
            random_seed: int|None = None) -> CaDataset:
        validate.less_or_equal(nr_of_positive_examples, factorial(self.__nr_of_teams))
        self.__team_permutations_for_positive_examples = permutations(self.__team_objects, self.__nr_of_teams)
        self.__team_permutations_for_negative_examples = permutations(self.__team_objects, self.__nr_of_teams)
        return super().generate(
            nr_of_positive_examples, nr_of_negative_examples,
            random_seed=random_seed)

    def _create_empty_dataset(self) -> CaDataset:
        return CaDataset(
            {
                ROUND_TYPE: CaObjectType(
                    ROUND_TYPE,
                    {
                        ROUND_FEATURE_NR: CaNumber(),
                    }
                ),
                TEAM_TYPE: CaObjectType(TEAM_TYPE, {})
            },
            {
                MATCH_RELATION: self.__match_relation_type
            }
        )

    def _generate_positive_example(self, random_generator: Random) -> CaExample:
        return self.__generate_example_from_team_list(
            next(self.__team_permutations_for_positive_examples), True)

    def __generate_example_from_team_list(self, team_list: tuple[CaObject], is_valid: bool) -> CaExample:
        if len(team_list) % 2 == 1:
            team_list = team_list + (None,)
        example = CaExample(
            {
                TEAM_TYPE: set(self.__team_objects),
                ROUND_TYPE: set(self.__round_objects)
            },
            {}, is_valid
        )
        matches = set()
        #https://en.wikipedia.org/wiki/Round-robin_tournament#Scheduling_algorithm
        #=> circle method
        upper_circle = list(range(len(team_list) // 2))
        lower_circle = list(range(len(team_list) // 2, len(team_list)))
        for round_index in range(len(self.__round_objects) // 2):
            for i,j in zip(upper_circle, lower_circle):
                if team_list[i] is not None and team_list[j] is not None:
                    matches.add((
                        self.__round_objects[round_index],
                        team_list[i],
                        team_list[j]
                    ))
                    matches.add((
                        self.__round_objects[round_index + len(self.__round_objects) // 2],
                        team_list[j],
                        team_list[i]
                    ))
            for i in range(2,len(upper_circle)):
                upper_circle[1],upper_circle[i] = upper_circle[i],upper_circle[1]
            for i in range(1, len(upper_circle)+1):
                upper_circle[1], lower_circle[-i] = lower_circle[-i],upper_circle[1]
        for round, home_team, away_team in product(
            example.all_objects_per_type[ROUND_TYPE],
            example.all_objects_per_type[TEAM_TYPE],
            example.all_objects_per_type[TEAM_TYPE]
        ):
            relation_tuple = (round, home_team, away_team)
            example.add_relation(CaRelation(
                MATCH_RELATION, relation_tuple,
                relation_tuple in matches
            ))
        return example

    def _generate_negative_example(self, random_generator: Random) -> CaExample:
        example = self.__generate_example_from_team_list(
            next(self.__team_permutations_for_negative_examples), False)
        while True:
            example = self.__mutate_example(example, random_generator)
            if any(not c.holds(example, {}) for c in self.__ground_truth_constraints):
                return example

    def __mutate_example(self, example: CaExample, random_generator: Random) -> CaExample:
        if random_generator.choice((True, False)):
            #add or remove a match
            relation = random_generator.choice(tuple(example.relations[MATCH_RELATION]))
            example.set_relation_value(relation, not relation.value)
        else:
            #break the symmetry constraint by permutating round nrs
            nr_mapping = [r.features[ROUND_FEATURE_NR] for r in self.__round_objects]
            random_generator.shuffle(nr_mapping)
            example = deepcopy(example)
            for round_object in example.all_objects_per_type[ROUND_TYPE]:
                round_object.features[ROUND_FEATURE_NR] = nr_mapping[round_object.features[ROUND_FEATURE_NR] - 1] + 1
        return example

    def get_ground_truth_constraints(self) -> list[CaConstraint]:
        return self.__ground_truth_constraints

    def get_target(self) -> CaTarget:
        return RelationTarget(MATCH_RELATION)
