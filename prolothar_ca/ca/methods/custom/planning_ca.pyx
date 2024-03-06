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

from typing import Tuple, List
from random import Random
from heapq import heapify, heappop, heappush
from tqdm import tqdm

from prolothar_common.mdl_utils cimport L_N

from prolothar_ca.ca.methods.custom.heterogenous_candidate cimport Candidate
from prolothar_ca.ca.methods.custom.candidate_generator.for_all_cross_product import generate_for_all_cross_product_candidates
from prolothar_ca.ca.methods.custom.model.custom_constraint cimport CustomConstraint
from prolothar_ca.ca.methods.custom.model.custom_constraint cimport DataGraph
from prolothar_ca.ca.methods.custom.model.for_all_no_join import ForAll
from prolothar_ca.ca.methods.custom.model.custom_constraint cimport JoinTargetConstraint
from prolothar_ca.ca.methods.custom.sat_encoding import create_heterogenous_sat_encoded_dataset
from prolothar_ca.ca.methods.custom.itemset_miner.itemset_miner cimport ItemsetMiner
from prolothar_ca.ca.methods.custom.ca_items import pattern_to_cross_product_filter

from prolothar_ca.model.ca import CaDataset
from prolothar_ca.model.ca.example cimport CaExample
from prolothar_ca.model.ca.obj cimport CaObject
from prolothar_ca.model.ca.relation cimport CaRelation
from prolothar_ca.model.ca.constraints.constraint import CaConstraint
from prolothar_ca.model.ca.relation cimport CaRelationType
from prolothar_ca.model.ca.format import TargetIsBooleanRelation
from prolothar_ca.model.ca.targets import CaTarget
from prolothar_ca.model.sat.cnf cimport CnfFormula
from prolothar_ca.solver.sat.modelcount.one_sat import OneSatModelCounter

from prolothar_ca.model.ca.relation import CaRelationType
from prolothar_ca.model.sat.term_factory cimport TermFactory


cdef class PlanningCustomCa:
    """
    our own approach for constraint acquisition that does not assume that all
    examples have the same boolean variables => disables runtime improvements
    """
    cdef bint __verbose
    cdef ItemsetMiner __itemset_miner
    cdef int __max_nr_of_unobserved_transactions_per_example
    cdef __random_seed

    def __init__(
            self, verbose: bool = False, ItemsetMiner itemset_miner = None,
            max_nr_of_unobserved_transactions_per_example: int = 0,
            random_seed: int|None = None):
        self.__verbose = verbose
        if itemset_miner is not None:
            self.__itemset_miner = itemset_miner
        else:
            self.__itemset_miner = ItemsetMiner(
                verbose=verbose, random_seed=random_seed,
                crossover_found_itemsets=True
            )
        self.__max_nr_of_unobserved_transactions_per_example = max_nr_of_unobserved_transactions_per_example
        self.__random_seed = random_seed

    def acquire_constraints(self, dataset: CaDataset, target: CaTarget) -> List[CaConstraint]:
        cdef TermFactory term_factory = TermFactory()
        discovered_constraints = []
        TargetIsBooleanRelation().validate(dataset, target)
        target_relation = dataset.get_relation_type(target.relation_name)
        first_example = next(iter(dataset))
        if self.__verbose:
            print('create data graphs')
        datagraph_list = [DataGraph(example, dataset, target_relation) for example in dataset]
        nr_of_variables_per_type = {
            object_type: len(object_set)
            for object_type, object_set in first_example.all_objects_per_type.items()
        }
        nr_of_target_relation_parameter_options = tuple(
            nr_of_variables_per_type[object_type]
            for object_type in target_relation.parameter_types
        )
        if self.__verbose:
            print('create sat encoded dataset')
        sat_encoded_dataset = create_heterogenous_sat_encoded_dataset(
            dataset, target_relation, datagraph_list)

        model_cost, data_cost, total_cost, discovered_constraints, model_cnf_list = self.__find_model_with_simple_quantified_expressions(
            dataset, nr_of_target_relation_parameter_options, sat_encoded_dataset, datagraph_list, target_relation, term_factory)

        model_cost, data_cost, total_cost, discovered_constraints, model_cnf_list = self.__find_model_with_complex_quantified_expressions(
            dataset, nr_of_target_relation_parameter_options, sat_encoded_dataset, datagraph_list, target_relation, term_factory,
            model_cost, data_cost, total_cost, discovered_constraints, model_cnf_list)

        if self.__verbose:
            print(f'return model with {len(discovered_constraints)} constraints')

        return [
            constraint.to_ca_model(datagraph_list[0])
            for constraint in discovered_constraints
        ]

    def __find_model_with_simple_quantified_expressions(
            self, dataset: CaDataset, nr_of_target_relation_parameter_options: Tuple[int],
            list sat_encoded_dataset,
            list datagraph_list, CaRelationType target_relation,
            TermFactory term_factory) -> Tuple[float, float, float, List[CustomConstraint], CnfFormula]:
        if self.__verbose:
            print('find simple quantified constraints')
        model_cost = L_N(1)
        data_cost = 0
        for datagraph in datagraph_list:
            data_cost += (<DataGraph>datagraph).get_nr_of_target_variables()
        total_cost = model_cost + data_cost
        constraint_list = list(generate_for_all_cross_product_candidates(
            dataset, target_relation, nr_of_target_relation_parameter_options,
            create_feature_distance_candidates=True, is_for_planning_dataset=True))
        cdef list candidate_queue = []
        cdef Candidate candidate
        for constraint in tqdm(constraint_list, desc='create candidates', disable=not self.__verbose):
            candidate = Candidate(
                constraint, datagraph_list,
                sat_encoded_dataset,
                term_factory)
            if candidate.gain < 0:
                candidate_queue.append(candidate)
        model_cost, data_cost, total_cost, discovered_constraints, model_cnf_list = self.__process_candidate_list(
            candidate_queue, [],
            [CnfFormula() for _ in sat_encoded_dataset],
            model_cost, data_cost, total_cost,
            sat_encoded_dataset,
            datagraph_list,
            term_factory
        )
        return (
            model_cost, data_cost, total_cost, discovered_constraints,
            [model_cnf.resolve_new_clauses() for model_cnf in model_cnf_list]
        )

    def __find_model_with_complex_quantified_expressions(
            self, dataset: CaDataset, nr_of_target_relation_parameter_options: Tuple[int],
            list sat_encoded_dataset,
            list datagraph_list, CaRelationType target_relation,
            TermFactory term_factory,
            double model_cost, double data_cost, double total_cost,
            discovered_constraints: List[CaConstraint],
            model_cnf_list: List[CnfFormula]) -> Tuple[float, float, float, List[CustomConstraint], CnfFormula]:
        if self.__max_nr_of_unobserved_transactions_per_example < 1:
            return model_cost, data_cost, total_cost, discovered_constraints, model_cnf_list
        if self.__verbose:
            print('find complex quantified constraints')
        cdef list observed_transaction_list = []
        cdef list not_observed_transaction_list = []
        cdef list false_relations_of_example
        cdef CaExample example
        cdef CaRelation relation
        random = Random(self.__random_seed)
        for example in dataset:
            false_relations_of_example = []
            for relation in <set>(example.relations[target_relation.name]):
                if relation.value:
                    observed_transaction_list.append(self.__create_transaction(relation))
                else:
                    false_relations_of_example.append(relation)
            if len(false_relations_of_example) > self.__max_nr_of_unobserved_transactions_per_example:
                random.shuffle(false_relations_of_example)
                false_relations_of_example = false_relations_of_example[:self.__max_nr_of_unobserved_transactions_per_example]
            for relation in false_relations_of_example:
                not_observed_transaction_list.append(self.__create_transaction(relation))
        cdef list candidate_list = self.__create_pattern_based_constraint_candidates(
            dataset, sat_encoded_dataset, datagraph_list, target_relation,
            term_factory, nr_of_target_relation_parameter_options,
            not_observed_transaction_list, observed_transaction_list
        )
        model_cost, data_cost, total_cost, discovered_constraints, model_cnf_list = self.__process_candidate_list(
            candidate_list, discovered_constraints,
            model_cnf_list,
            model_cost, data_cost, total_cost,
            sat_encoded_dataset,
            datagraph_list,
            term_factory
        )
        return (
            model_cost, data_cost, total_cost, discovered_constraints,
            [model_cnf.resolve_new_clauses() for model_cnf in model_cnf_list]
        )

    cdef list __create_pattern_based_constraint_candidates(
            self, dataset: CaDataset, list sat_encoded_dataset,
            list datagraph_list, CaRelationType target_relation,
            TermFactory term_factory,
            nr_of_target_relation_parameter_options: Tuple[int],
            list observed_transaction_list, list not_observed_transaction_list):
        nr_of_numeric_features_per_parameter = tuple(
            dataset.get_nr_of_numeric_features(parameter_type)
            for parameter_type in target_relation.parameter_types
        )
        nr_of_boolean_features_per_parameter = tuple(
            dataset.get_nr_of_boolean_features(parameter_type)
            for parameter_type in target_relation.parameter_types
        )
        cdef list candidate_list = []
        cdef JoinTargetConstraint relation_is_false = JoinTargetConstraint(
            [], tuple(range(len(nr_of_target_relation_parameter_options))), False,
            nr_of_target_relation_parameter_options
        )
        cdef Candidate candidate
        cdef list pattern_list = self.__itemset_miner.find_patterns(
            not_observed_transaction_list, observed_transaction_list)
        cdef set item_set = set()
        for pattern in list(pattern_list):
            if len(pattern) > 1:
                for item in pattern:
                    if item not in item_set:
                        item_set.add(item)
                        pattern_list.append([item])
        for pattern in pattern_list:
            candidate = Candidate(
                ForAll(
                    pattern_to_cross_product_filter(
                        pattern,
                        len(nr_of_target_relation_parameter_options),
                        nr_of_numeric_features_per_parameter,
                        nr_of_boolean_features_per_parameter
                    ),
                    relation_is_false
                ),
                datagraph_list,
                sat_encoded_dataset,
                term_factory
            )
            if candidate.gain < 0:
                candidate_list.append(candidate)
        return candidate_list

    cdef list __create_transaction(self, CaRelation relation):
        cdef list transaction = []
        cdef CaObject object_i, object_j
        cdef size_t i, j
        for i, object_i in enumerate(relation.objects):
            for feature_name_i, feature_value_i in object_i.features.items():
                if isinstance(feature_value_i, bool):
                    if feature_value_i:
                        transaction.append(f'{i}.{feature_name_i}')
                else:
                    for j, object_j in enumerate(relation.objects[i+1:]):
                        j += i + 1
                        for feature_name_j, feature_value_j in object_j.features.items():
                            if not isinstance(feature_value_j, bool):
                                if feature_value_i == feature_value_j:
                                    transaction.append(f'{i}.{feature_name_i} = {j}.{feature_name_j}')
                                elif feature_value_i < feature_value_j:
                                    transaction.append(f'{i}.{feature_name_i} < {j}.{feature_name_j}')
                                else:
                                    transaction.append(f'{i}.{feature_name_i} > {j}.{feature_name_j}')
        return transaction

    def __process_candidate_list(
            self, list candidate_queue, list model,
            list model_cnf_list, double model_cost, double data_cost, double total_cost,
            list sat_encoded_dataset,
            list datagraph_list,
            TermFactory term_factory) -> Tuple[float, float, float, List[CustomConstraint], CnfFormula]:
        heapify(candidate_queue)
        # we have defined in the Candidate class the model is empty in iteration 1
        cdef int iteration = 1 if not model else 2
        if self.__verbose:
            print(f'start with {len(candidate_queue)} candidates, L(D,M) = {total_cost:.2f}')
        cdef Candidate candidate
        cdef object model_counter = OneSatModelCounter()
        while candidate_queue:
            candidate = <Candidate>heappop(candidate_queue)
            if candidate.iteration == iteration:
                if candidate.replaced_constraint is not None:
                    model[candidate.replaced_constraint_index] = candidate.constraint
                else:
                    model.append(candidate.constraint)
                model_cnf_list = candidate.model_cnf_list
                model_cost = candidate.model_cost
                data_cost = candidate.data_cost
                total_cost = candidate.total_cost
                if self.__verbose:
                    print((
                        f'gained {abs(candidate.gain):.2f} bits with candidate "{candidate.constraint}", '
                        f'{len(candidate_queue)} candidates left, L(D,M) = {total_cost:.2f}'
                    ))
                iteration += 1
            else:
                candidate.update_gain(
                    iteration, model, model_cost, model_cnf_list,
                    sat_encoded_dataset, total_cost, model_counter)
                if candidate.gain < 0:
                    heappush(candidate_queue, candidate)
                else:
                    if self.__verbose:
                        print(
                            f'rejected candidate "{candidate.constraint}" '
                            f'replacing {candidate.replaced_constraint_index}, '
                            f'delta L(D,M) = {candidate.gain:.2f}, '
                            f'{len(candidate_queue)} candidates left'
                        )
        return model_cost, data_cost, total_cost, model, model_cnf_list

    def __repr__(self):
        return 'CustomCa'
