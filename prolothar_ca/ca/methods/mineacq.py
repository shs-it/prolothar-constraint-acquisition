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

from dataclasses import dataclass
from random import Random
from typing import Iterable
import numpy as np
from tqdm import tqdm, trange

from prolothar_ca.ca.methods.method import CaMethod
from prolothar_ca.model.ca.constraints.boolean import Not, RelationIsTrue
from prolothar_ca.model.ca.constraints.conjunction import Implies
from prolothar_ca.model.ca.constraints.constraint import CaConstraint
from prolothar_ca.model.ca.example import CaExample
from prolothar_ca.model.ca.relation import CaRelation
from prolothar_ca.model.ca.targets import CaTarget, RelationTarget

from prolothar_ca.model.ca import CaDataset
from prolothar_ca.model.ca.variable_type import CaBoolean

@dataclass
class ImpliesWrapper:

    constraint: Implies
    antecedent_not_holds_vector: np.ndarray
    antecedent_not_holds_expected_vector: np.ndarray
    probability_antecendent_not_holds: float
    expected_probability_antecendent_not_holds: float
    consequent_holds_vector: np.ndarray
    expected_consequent_holds_vector: np.ndarray
    probability_consequent_holds: float
    expected_probability_consequent_holds: float

    def compute_probability_that_constraint_holds(self) -> float:
        return (
            self.antecedent_not_holds_vector |
            self.consequent_holds_vector
        ).sum() / len(self.antecedent_not_holds_vector)

    def compute_upper_bound_probability_that_constraint_holds(self) -> float:
        return self.probability_antecendent_not_holds + self.probability_consequent_holds

    def compute_lower_bound_probability_that_constraint_holds(self) -> float:
        return max(
            self.probability_antecendent_not_holds,
            self.probability_consequent_holds
        )

    def compute_expected_probability_that_constraint_holds(self) -> float:
        return (
            self.antecedent_not_holds_expected_vector |
            self.expected_consequent_holds_vector
        ).sum() / len(self.antecedent_not_holds_expected_vector)

    def compute_upper_bound_expected_probability_that_constraint_holds(self) -> float:
        return (
            self.expected_probability_antecendent_not_holds +
            self.expected_probability_consequent_holds
        )

    def compute_lower_bound_expected_probability_that_constraint_holds(self) -> float:
        return max(
            self.expected_probability_antecendent_not_holds,
            self.expected_probability_consequent_holds
        )

class MineAcq(CaMethod):
    """
    re-implementation of MineAcq for unsupervised constraint acquisition

    Prestwich, Steven. "Unsupervised constraint acquisition." ICTAI. 2021.
    """

    def __init__(
        self, tau: float = 1.2, rho: float = 0.01, random_seed: int|None = None,
        verbose: bool = False):
        """
        configures the parameters of MineAcq

        Parameters
        ----------
        tau : float, optional
            tau parameter of MineACQ, default is 1.2 as in the paper
        rho : float
            rho parameter of MineACQ, default is 0.01 as in the paper
        random_seed : int | None, optional
            seed of the random generator used to create the permutations, default is None
        verbose : bool, optional
            if True prints additional debug information, default is False
        """
        self.__tau = tau
        self.__rho = rho
        self.__random = Random(random_seed)
        self.__verbose = verbose

    def acquire_constraints(self, dataset: CaDataset, target: CaTarget) -> list[CaConstraint]:
        if not isinstance(target, RelationTarget):
            raise NotImplementedError(type(target))
        for relation_type in dataset.get_relation_types():
            if not isinstance(relation_type.value_type, CaBoolean):
                raise NotImplementedError(relation_type)
        pseudo_dataset = self.__generate_pseudo_dataset(dataset)
        constraint_list = []
        for candidate in self.__generate_candidate_constraints(
            dataset, pseudo_dataset, target.relation_name):
            p_c_upper_bound = candidate.compute_upper_bound_probability_that_constraint_holds()
            expected_p_c_lower_bound = candidate.compute_lower_bound_expected_probability_that_constraint_holds()
            if (1 - p_c_upper_bound) <= self.__rho or 1 - expected_p_c_lower_bound >= self.__tau * (1 - p_c_upper_bound):
                p_c = candidate.compute_probability_that_constraint_holds()
                expected_p_c = candidate.compute_expected_probability_that_constraint_holds()
                if (1 - p_c) <= self.__rho or 1 - expected_p_c >= self.__tau * (1 - p_c):
                    constraint_list.append(candidate.constraint)
        return constraint_list

    def __generate_candidate_constraints(
            self, dataset: CaDataset, pseudo_dataset: CaDataset,
            target_relation_name: str) -> Iterable[ImpliesWrapper]:
        example = next(iter(dataset))
        relation_is_true_constraint_list = []
        relation_is_true_holds_vector_list = []
        relation_is_false_holds_vector_list = []
        probability_relation_is_true_list = []
        expected_relation_is_true_holds_vector_list = []
        expected_relation_is_false_holds_vector_list = []
        expected_probability_relation_is_true_list = []
        if self.__verbose:
            print('precompute candidates marginal probabilities')
        for relation_type in tqdm(dataset.get_relation_types(), disable=not self.__verbose):
            for relation in tqdm(example.relations[relation_type.name], leave=False, disable=not self.__verbose):
                constraint = RelationIsTrue(relation_type, tuple(o.object_id for o in relation.objects))
                relation_is_true_constraint_list.append(constraint)
                holds_vector = np.array([constraint.holds(example, {}) for example in dataset])
                relation_is_true_holds_vector_list.append(holds_vector)
                relation_is_false_holds_vector_list.append(~holds_vector)
                probability_relation_is_true_list.append(holds_vector.sum() / len(holds_vector))
                expected_holds_vector = np.array([constraint.holds(
                    example, {}) for example in pseudo_dataset])
                expected_relation_is_true_holds_vector_list.append(expected_holds_vector)
                expected_relation_is_false_holds_vector_list.append(~expected_holds_vector)
                expected_probability_relation_is_true_list.append(
                    expected_holds_vector.sum() / len(expected_holds_vector))
        if relation_is_false_holds_vector_list:
            all_zero_vector = np.zeros_like(relation_is_false_holds_vector_list[0])
        if self.__verbose:
            print('generate and filter candidates')
        for i in trange(len(relation_is_true_constraint_list), disable=not self.__verbose):
            yield ImpliesWrapper(
                relation_is_true_constraint_list[i],
                all_zero_vector,
                all_zero_vector,
                0,
                0,
                relation_is_true_holds_vector_list[i],
                expected_relation_is_true_holds_vector_list[i],
                probability_relation_is_true_list[i],
                expected_probability_relation_is_true_list[i]
            )
            for j in trange(len(relation_is_true_constraint_list), leave=False, disable=not self.__verbose):
                if i != j and relation_is_true_constraint_list[j].get_relation_name() == target_relation_name:
                    yield ImpliesWrapper(
                        Implies(
                            relation_is_true_constraint_list[i],
                            relation_is_true_constraint_list[j]
                        ),
                        relation_is_false_holds_vector_list[i],
                        expected_relation_is_false_holds_vector_list[i],
                        1 - probability_relation_is_true_list[i],
                        1 - expected_probability_relation_is_true_list[i],
                        relation_is_true_holds_vector_list[j],
                        expected_relation_is_true_holds_vector_list[j],
                        probability_relation_is_true_list[j],
                        expected_probability_relation_is_true_list[j]
                    )
                    yield ImpliesWrapper(
                        Implies(
                            relation_is_true_constraint_list[i],
                            Not(relation_is_true_constraint_list[j])
                        ),
                        relation_is_false_holds_vector_list[i],
                        expected_relation_is_false_holds_vector_list[i],
                        1 - probability_relation_is_true_list[i],
                        expected_probability_relation_is_true_list[i],
                        relation_is_false_holds_vector_list[j],
                        expected_relation_is_false_holds_vector_list[j],
                        1 - probability_relation_is_true_list[j],
                        1 - expected_probability_relation_is_true_list[j]
                    )

    def __generate_pseudo_dataset(self, dataset: CaDataset) -> CaDataset:
        if self.__verbose:
            print('generate pseudo dataset needed to compute expected probabilities')
        pseudo_dataset = dataset.empty_copy()
        for example in tqdm(dataset, disable=not self.__verbose):
            shuffled_values = {
                relation_type_name: [relation.value for relation in relation_set]
                for relation_type_name, relation_set in example.relations.items()
            }
            for value_list in shuffled_values.values():
                self.__random.shuffle(value_list)
            pseudo_dataset.add_example(CaExample(
                example.all_objects_per_type,
                {
                    relation_type_name: set(
                        CaRelation(relation_type_name, relation.objects, shuffled_value)
                        for relation, shuffled_value in zip(relation_set, shuffled_values[relation_type_name])
                    )
                    for relation_type_name, relation_set in example.relations.items()
                },
                example.is_valid_solution,
                validate=False
            ), validate=False)
        return pseudo_dataset

    def __repr__(self):
        return f'MineAcq(tau={self.__tau}, rho={self.__rho})'
