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
from math import ceil
from libc.math cimport ceil as cceil
from heapq import heapify, heappop, heappush
from itertools import chain
from more_itertools import ilen
from tqdm import tqdm
import numpy as np
from statistics import mean
from random import Random
cimport cython
from cpython.list cimport PyList_GET_SIZE

from prolothar_common.mdl_utils cimport L_N
from prolothar_common.mdl_utils cimport log2binom

from prolothar_ca.ca.methods.custom.homogenous_candidate cimport Candidate, CountCandidate
from prolothar_ca.ca.methods.custom.candidate_generator.for_all_all_parameters_cross_product import generate_for_all_all_parameters_cross_product_candidates
from prolothar_ca.ca.methods.custom.candidate_generator.for_all_one_parameter_cross_product import generate_for_all_one_parameter_cross_product_candidates
from prolothar_ca.ca.methods.custom.candidate_generator.for_all_cross_product import generate_for_all_cross_product_candidates
from prolothar_ca.ca.methods.custom.candidate_generator.count_generator import generate_count_candidates
from prolothar_ca.ca.methods.custom.mdl_score import compute_encoded_data_length_from_known_solution_with_upperbound
from prolothar_ca.ca.methods.custom.model.custom_constraint cimport JoinTargetConstraint
from prolothar_ca.ca.methods.custom.model.custom_constraint cimport SingleTargetConstraint
from prolothar_ca.ca.methods.custom.model.custom_constraint cimport CustomConstraint
from prolothar_ca.ca.methods.custom.model.custom_constraint cimport Count
from prolothar_ca.ca.methods.custom.model.custom_constraint cimport DataGraph
from prolothar_ca.ca.methods.custom.model.for_all_join_all import ForAllJoinAll
from prolothar_ca.ca.methods.custom.model.for_all_join_n import ForAllJoinN
from prolothar_ca.ca.methods.custom.itemset_miner.itemset_miner cimport ItemsetMiner
from prolothar_ca.ca.methods.custom.sat_encoding import create_homgenous_sat_encoded_dataset, SatEncodedExample
from prolothar_ca.ca.methods.custom.ca_items import pattern_to_cross_product_filter

from prolothar_ca.model.ca import CaDataset
from prolothar_ca.model.ca.obj cimport CaObject
from prolothar_ca.model.ca.constraints.constraint import CaConstraint
from prolothar_ca.model.ca.variable_type import CaNumber, CaBoolean
from prolothar_ca.model.ca.format import TargetIsBooleanRelation
from prolothar_ca.model.ca.targets import CaTarget
from prolothar_ca.model.sat.cnf import CnfFormula
from prolothar_ca.model.sat.cnf cimport CnfFormula
from prolothar_ca.model.sat.variable cimport Variable, Value
from prolothar_ca.solver.sat.modelcount.approxmc import ApproxMC
from prolothar_ca.solver.sat.modelcount.model_counter import ModelCounter
from prolothar_ca.solver.sat.solver.twosat_solver import TwoSatSolver
from prolothar_ca.solver.sat.modelcount.mc2 cimport compute_graph_lower_bound

from prolothar_ca.model.ca.relation import CaRelation, CaRelationType
from prolothar_ca.model.ca.relation cimport CaRelation
from prolothar_ca.model.sat.term_factory cimport TermFactory
from prolothar_ca.model.sat.constraint_graph import ConstraintGraph
from prolothar_ca.model.sat.constraint_graph cimport ConstraintGraph
from prolothar_ca.model.sat.implication_graph import ImplicationGraph
from prolothar_ca.model.sat.implication_graph cimport ImplicationGraph

cdef class HomogenousCustomCa:
    """
    our own approach for constraint acquisition that assumes that all
    examples have the same boolean variables => enables runtime improvements
    """
    cdef __sat_model_counter
    cdef ItemsetMiner __itemset_miner
    cdef __implication_pairs_limit
    cdef bint __assume_equal_modelcount_for_all_single_target_constraint_candidates
    cdef __random_seed
    cdef __twosat_solver
    cdef bint __verbose
    cdef int __max_nr_of_target_zeros
    cdef dict __item_cache
    cdef int __nr_of_sampled_clauses_for_error

    def __init__(
            self,
            sat_model_counter: ModelCounter = None,
            ItemsetMiner itemset_miner = None,
            implication_pairs_limit: int|None = None,
            assume_equal_modelcount_for_all_single_target_constraint_candidates: bool = False,
            verbose: bool = False,
            random_seed: int|None = None,
            max_nr_of_target_zeros: int = -1,
            nr_of_sampled_clauses_for_error: int = 0):
        if sat_model_counter is not None:
            self.__sat_model_counter = sat_model_counter
        else:
            self.__sat_model_counter = ApproxMC()
        if itemset_miner is not None:
            self.__itemset_miner = itemset_miner
        else:
            self.__itemset_miner = ItemsetMiner(verbose=verbose)
        self.__verbose = verbose
        self.__twosat_solver = TwoSatSolver()
        self.__implication_pairs_limit = implication_pairs_limit
        self.__random_seed = random_seed
        self.__assume_equal_modelcount_for_all_single_target_constraint_candidates = assume_equal_modelcount_for_all_single_target_constraint_candidates
        self.__max_nr_of_target_zeros = max_nr_of_target_zeros
        self.__item_cache = {}
        self.__nr_of_sampled_clauses_for_error = nr_of_sampled_clauses_for_error

    def acquire_constraints(self, dataset: CaDataset, target: CaTarget) -> List[CaConstraint]:
        self.__item_cache.clear()
        cdef TermFactory term_factory = TermFactory()
        discovered_constraints = []
        TargetIsBooleanRelation().validate(dataset, target)
        target_relation = dataset.get_relation_type(target.relation_name)
        first_example = next(iter(dataset))
        if self.__verbose:
            print(f'target relation is {target_relation}')
            print('create data graph')
        cdef DataGraph datagraph = DataGraph(
            first_example, dataset, target_relation,
            max_nr_of_target_zeros=self.__max_nr_of_target_zeros
        )
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
        sat_encoded_dataset = create_homgenous_sat_encoded_dataset(
            dataset, target_relation, datagraph)

        model_cost, data_cost, total_cost, discovered_constraints, model_cnf = self.__find_model_with_simple_quantified_expressions(
            dataset, nr_of_target_relation_parameter_options, sat_encoded_dataset, datagraph, term_factory)

        if self.__implication_pairs_limit is None or self.__implication_pairs_limit > 0:
            model_cost, data_cost, total_cost, discovered_constraints, model_cnf = self.__find_model_with_complex_quantified_expressions(
                dataset, sat_encoded_dataset, discovered_constraints, model_cnf, datagraph,
                term_factory, model_cost, data_cost, total_cost
            )

        model_cost, data_cost, total_cost, discovered_constraints = self.__find_model_with_count_expressions(
            dataset, target_relation, sat_encoded_dataset, datagraph, term_factory,
            discovered_constraints, model_cnf, model_cost, data_cost, total_cost
        )

        if self.__verbose:
            print(f'return model with {len(discovered_constraints)} constraints')

        return [
            constraint.to_ca_model(datagraph)
            for constraint in discovered_constraints
        ]

    def __find_model_with_complex_quantified_expressions(
            self, dataset: CaDataset, sat_encoded_dataset: List[SatEncodedExample],
            discovered_constraints: List[CustomConstraint], model_cnf: CnfFormula, datagraph: DataGraph,
            TermFactory term_factory, model_cost: float, data_cost: float, total_cost: float,
            ) -> Tuple[float, float, float, List[CustomConstraint], CnfFormula]:
        single_target_constraint_candidates, rejected_candidates = self.__find_single_target_constraint_candidates(
            sat_encoded_dataset, datagraph, term_factory, model_cnf, data_cost)
        if self.__verbose:
            print(f'found {len(single_target_constraint_candidates)} positive and {len(rejected_candidates)} negative implication candidates')

        constraint_candidates = self.__generate_quantifier_constraint_candidates_from_pairwise_implications(
            single_target_constraint_candidates, rejected_candidates, datagraph, dataset)

        return self.__process_candidate_list(
            [
                candidate for candidate in (
                    Candidate(
                        constraint, datagraph,
                        sat_encoded_dataset,
                        term_factory,
                        nr_of_sampled_clauses_for_error=self.__nr_of_sampled_clauses_for_error
                    ) for constraint in constraint_candidates
                ) if candidate.gain < 0
            ],
            discovered_constraints,
            model_cnf,
            model_cost,
            data_cost,
            total_cost,
            sat_encoded_dataset,
            datagraph.get_target_variables()
        )

    def __find_model_with_simple_quantified_expressions(
            self, dataset: CaDataset, tuple nr_of_target_relation_parameter_options,
            list sat_encoded_dataset,
            DataGraph datagraph,
            TermFactory term_factory) -> Tuple[float, float, float, List[CustomConstraint], CnfFormula]:
        if self.__verbose:
            print('find simple quantified constraints')
        model_cost = L_N(1)
        data_cost = len(dataset) * datagraph.get_nr_of_target_variables()
        total_cost = model_cost + data_cost
        constraint_list = list(generate_for_all_one_parameter_cross_product_candidates(
                dataset, datagraph.get_target_relation_type(),
                nr_of_target_relation_parameter_options))
        constraint_list.extend(generate_for_all_cross_product_candidates(
            dataset, datagraph.get_target_relation_type(),
            nr_of_target_relation_parameter_options))
        #full cross product of more than two object sets is computationally too expensive
        #and probably does not lead to meaningful constraints in practice.
        #it is also way too expensive for object sets with more than 100 objects
        if len(nr_of_target_relation_parameter_options) <= 2 and dataset.get_max_size_of_object_set() <= 100:
            constraint_list.extend(generate_for_all_all_parameters_cross_product_candidates(
                dataset, datagraph.get_target_relation_type(),
                nr_of_target_relation_parameter_options))
        cdef list candidate_queue = []
        cdef Candidate candidate
        for constraint in tqdm(constraint_list, desc='create candidates', disable=not self.__verbose):
            candidate = Candidate(
                constraint, datagraph,
                sat_encoded_dataset,
                term_factory,
                nr_of_sampled_clauses_for_error=self.__nr_of_sampled_clauses_for_error)
            if candidate.gain < 0:
                candidate_queue.append(candidate)
        model_cost, data_cost, total_cost, discovered_constraints, model_cnf = self.__process_candidate_list(
            candidate_queue, [], CnfFormula(), model_cost, data_cost, total_cost,
            sat_encoded_dataset, datagraph.get_target_variables())
        return model_cost, data_cost, total_cost, discovered_constraints, model_cnf.resolve_new_clauses()

    def __find_single_target_constraint_candidates(
            self, list sat_encoded_dataset,
            DataGraph datagraph,
            TermFactory term_factory,
            CnfFormula model_cnf,
            double data_cost) -> Tuple[List[SingleTargetConstraint], List[SingleTargetConstraint]]:
        if self.__verbose:
            print('find pairwise implication candidates')
        constraint_list, true_count_list, true_by_consequent_count_list = \
            self.__precompute_single_target_constraint_candidates(sat_encoded_dataset, datagraph)
        cdef size_t expected_true_count = mean(true_count_list)
        cdef size_t expected_true_by_consequent_count = mean(true_by_consequent_count_list)
        cdef ImplicationGraph model_implication_graph
        #the implication graph must not be empty; however, the implication graph of a CNF without clauses is empty
        if model_cnf.get_nr_of_clauses() > 0:
            model_implication_graph = model_cnf.to_implication_graph()
        else:
            model_implication_graph = ImplicationGraph(len(datagraph.get_target_variables()))
        cdef ConstraintGraph model_constraint_graph = model_cnf.to_constraint_graph()
        cdef dict variables = datagraph.get_target_variables()
        cdef CnfFormula single_target_cnf
        cdef list found_candidates = []
        cdef list rejected_candidates = []
        cdef double first_log2modelcount = 0
        cdef size_t true_count, true_by_consequent_count
        if self.__assume_equal_modelcount_for_all_single_target_constraint_candidates:
            single_target_cnf = CnfFormula(constraint_list[0].compute_cnf_clauses(datagraph, term_factory))
            with model_constraint_graph.temporary_with(single_target_cnf.to_constraint_graph()):
                first_log2modelcount = self.__sat_model_counter.countlog2(CnfFormula(
                    set(chain(model_cnf.iter_clauses(), single_target_cnf.iter_clauses())),
                    variable_nr_set = model_cnf.get_variable_nr_set().union(single_target_cnf.get_variable_nr_set()),
                    constraint_graph = model_constraint_graph
                ))
        cdef CustomConstraint constraint
        with tqdm(
                total=len(constraint_list), disable=not self.__verbose,
                desc='find pos. and neg. examples') as progressbar:
            while constraint_list:
                constraint = constraint_list.pop()
                true_count = true_count_list.pop()
                true_by_consequent_count = true_by_consequent_count_list.pop()
                if true_count > expected_true_count and true_by_consequent_count > expected_true_by_consequent_count:
                    single_target_cnf = CnfFormula(constraint.compute_cnf_clauses(datagraph, term_factory))
                    if not single_target_cnf.has_overlap(model_cnf):
                        #we want to find all constraint that can improve the data encoding
                        #we later combine these constraints to achieve a lower model cost
                        if self.__cnf_non_overlap_constraint_leads_to_lower_data_cost(
                                model_cnf, model_implication_graph, model_constraint_graph,
                                single_target_cnf, data_cost, sat_encoded_dataset, variables,
                                first_log2modelcount):
                            if self.__implication_pairs_limit is None or len(found_candidates) < self.__implication_pairs_limit:
                                found_candidates.append(constraint)
                        elif self.__implication_pairs_limit is None or len(rejected_candidates) < self.__implication_pairs_limit:
                            rejected_candidates.append(constraint)
                elif self.__implication_pairs_limit is None or len(rejected_candidates) < self.__implication_pairs_limit:
                    rejected_candidates.append(constraint)
                if self.__implication_pairs_limit is not None \
                and len(rejected_candidates) == self.__implication_pairs_limit \
                and len(found_candidates) == self.__implication_pairs_limit:
                    break
                if self.__verbose:
                    progressbar.update()
                    progressbar.desc = f'find pos. ({len(found_candidates)}/{self.__implication_pairs_limit}) and neg. ({len(rejected_candidates)}/{self.__implication_pairs_limit}) examples'
        return found_candidates, rejected_candidates

    def __precompute_single_target_constraint_candidates(
            self, list sat_encoded_dataset,
            DataGraph datagraph):
        cdef list variable_list = sorted(datagraph.get_target_variables().values(), key=lambda v: v.nr)
        dataset_np = np.array([
            [
                example[variable].value == Value.TRUE
                for variable in variable_list
            ]
            for example in sat_encoded_dataset
        ], dtype=np.intc)
        #we want to make sure that there is enough evidence
        observed_both_values_for_variable = ~np.isin(dataset_np.sum(axis=0), (0, len(variable_list)))
        cdef list constraint_list = []
        cdef list true_count_list = []
        cdef list true_by_consequent_count_list = []
        cdef SingleTargetConstraint true_implies_expected_value_constraint
        cdef list variable_nrs = list(datagraph.get_target_variables().keys())
        if self.__implication_pairs_limit is not None:
            Random(self.__random_seed).shuffle(variable_nrs)
        for i in tqdm(variable_nrs, disable=not self.__verbose, desc='precompute'):
            if observed_both_values_for_variable[i-1]:
                for j in variable_nrs:
                    if i != j and observed_both_values_for_variable[j-1]:
                        for expected_value in (True, False):
                            true_implies_expected_value_constraint = SingleTargetConstraint([i], j, expected_value, len(variable_list))
                            constraint_list.append(true_implies_expected_value_constraint)
                            true_count_list.append(true_implies_expected_value_constraint.count_true(dataset_np))
                            true_by_consequent_count_list.append(true_implies_expected_value_constraint.count_true_by_consequent(dataset_np))
        return constraint_list, true_count_list, true_by_consequent_count_list

    @cython.cdivision(True)
    cdef bint __cnf_non_overlap_constraint_leads_to_lower_data_cost(
            self,
            CnfFormula model_cnf,
            ImplicationGraph model_implication_graph,
            ConstraintGraph model_constraint_graph,
            CnfFormula single_target_cnf,
            double data_cost,
            list sat_encoded_dataset,
            dict variables,
            double first_log2modelcount):
        with model_implication_graph.temporary_with(single_target_cnf.to_implication_graph()):
            solution = self.__twosat_solver.solve_implication_graph(model_implication_graph, variables)
        if solution is None:
            return False
        cdef size_t nr_of_variables = len(variables)
        cdef double error_cost = 0
        cdef int nr_of_errors
        for i,example in enumerate(sat_encoded_dataset):
            for variable, value in (<dict>example).items():
                (<Variable>variable).value = <Value>value
            nr_of_errors = model_cnf.get_nr_of_untrue_clauses_for_example(<int>i) + single_target_cnf.get_nr_of_untrue_clauses()
            nr_of_errors = min(
                nr_of_variables // 2,
                <int>cceil(nr_of_variables - nr_of_variables * (1 - 1 / (<double>nr_of_variables))**(0.5 * nr_of_errors))
            )
            error_cost += L_N(nr_of_errors + 1) + log2binom(nr_of_variables, nr_of_errors)
            if error_cost > data_cost:
                return False
        for variable, value in (<dict>solution).items():
            (<Variable>variable).value = <Value>value
        cdef double total_cost
        if self.__assume_equal_modelcount_for_all_single_target_constraint_candidates:
            total_cost = error_cost + PyList_GET_SIZE(sat_encoded_dataset) * first_log2modelcount
        else:
            with model_constraint_graph.temporary_with(single_target_cnf.to_constraint_graph()):
                total_cost = error_cost + len(sat_encoded_dataset) * self.__sat_model_counter.countlog2(CnfFormula(
                    set(chain(model_cnf.iter_clauses(), single_target_cnf.iter_clauses())),
                    variable_nr_set = model_cnf.get_variable_nr_set().union(single_target_cnf.get_variable_nr_set()),
                    constraint_graph = model_constraint_graph
                ))
        return total_cost < data_cost

    def __generate_quantifier_constraint_candidates_from_pairwise_implications(
            self, single_target_constraint_candidates,
            rejected_candidates,
            datagraph: DataGraph, dataset: CaDataset) -> List[CustomConstraint]:
        target_relation_cardinality = len(datagraph.get_target_relation_type().parameter_types)
        first_example = next(iter(dataset))
        nr_of_target_relation_parameter_options = tuple(
            len(first_example.all_objects_per_type[parameter_type])
            for parameter_type in datagraph.get_target_relation_type().parameter_types
        )
        nr_of_numeric_features_per_parameter = tuple(
            dataset.get_nr_of_numeric_features(parameter_type)
            for parameter_type in datagraph.get_target_relation_type().parameter_types
        ) * 2
        nr_of_boolean_features_per_parameter = tuple(
            dataset.get_nr_of_boolean_features(parameter_type)
            for parameter_type in datagraph.get_target_relation_type().parameter_types
        ) * 2
        antecedent = [tuple(range(target_relation_cardinality))]
        all_join_consequent = tuple(range(target_relation_cardinality, 2 * target_relation_cardinality))
        constraint_candidates = []
        true_positive_join_all_transaction_list, true_positive_join_one_transaction_lists, \
        false_positive_join_all_transaction_list, false_positive_join_one_transaction_lists, \
        true_negative_join_all_transaction_list, true_negative_join_one_transaction_lists, \
        false_negative_join_all_transaction_list, false_negative_join_one_transaction_lists = \
            self.__create_transactions_from_single_target_constraint_candidates(
                single_target_constraint_candidates, rejected_candidates,
                datagraph, dataset, target_relation_cardinality)
        found_patterns_true_false_join_all = self.__generate_true_false_join_all_candidates(
            target_relation_cardinality, nr_of_target_relation_parameter_options,
            nr_of_numeric_features_per_parameter, nr_of_boolean_features_per_parameter,
            antecedent, all_join_consequent,
            constraint_candidates, false_positive_join_all_transaction_list,
            false_negative_join_all_transaction_list)
        self.__generate_true_true_join_all_candidates(
            target_relation_cardinality, nr_of_target_relation_parameter_options,
            nr_of_numeric_features_per_parameter, nr_of_boolean_features_per_parameter,
            antecedent, all_join_consequent,
            constraint_candidates, true_positive_join_all_transaction_list,
            true_negative_join_all_transaction_list)
        self.__generate_true_false_join_one_candidates(
            target_relation_cardinality, nr_of_target_relation_parameter_options,
            nr_of_numeric_features_per_parameter, nr_of_boolean_features_per_parameter, antecedent,
            constraint_candidates, false_positive_join_one_transaction_lists,
            false_negative_join_one_transaction_lists, found_patterns_true_false_join_all)
        self.__generate_true_true_join_one_candidates(
            target_relation_cardinality, nr_of_target_relation_parameter_options,
            nr_of_numeric_features_per_parameter, nr_of_boolean_features_per_parameter, antecedent,
            constraint_candidates, true_positive_join_one_transaction_lists,
            true_negative_join_one_transaction_lists)
        if self.__verbose:
            print(f'found {len(constraint_candidates)} unpruned item set based candidates')
        return constraint_candidates

    def __generate_true_true_join_one_candidates(
            self, target_relation_cardinality, nr_of_target_relation_parameter_options,
            nr_of_numeric_features_per_parameter, nr_of_boolean_features_per_parameter,
            antecedent, constraint_candidates,
            true_positive_join_one_transaction_lists, true_negative_join_one_transaction_lists):
        for join_index, true_positive_join_one_transaction_list in enumerate(true_positive_join_one_transaction_lists):
            true_negative_join_one_transaction_list = true_negative_join_one_transaction_lists[join_index]
            nr_of_numeric_features_per_parameter_for_join_index = (
                nr_of_numeric_features_per_parameter[:target_relation_cardinality] +
                (nr_of_numeric_features_per_parameter[join_index],)
            )
            nr_of_boolean_features_per_parameter_for_join_index = (
                nr_of_boolean_features_per_parameter[:target_relation_cardinality] +
                (nr_of_boolean_features_per_parameter[join_index],)
            )
            if self.__verbose:
                print((
                    f'generate true->true join one (index={join_index}) candidates. '
                    f'{len(true_positive_join_one_transaction_list)} positive and '
                    f'{len(true_negative_join_one_transaction_list)} negative examples'
                ))
            one_join_consequent = list(antecedent[0])
            one_join_consequent[join_index] = target_relation_cardinality
            one_join_consequent = tuple(one_join_consequent)
            if true_positive_join_one_transaction_list and true_negative_join_one_transaction_list:
                for pattern in self.__itemset_miner.find_patterns(
                        true_positive_join_one_transaction_list, true_negative_join_one_transaction_list):
                    constraint_candidates.append(ForAllJoinN(
                        join_index, 1,
                        pattern_to_cross_product_filter(
                            pattern, target_relation_cardinality+1,
                            nr_of_numeric_features_per_parameter_for_join_index,
                            nr_of_boolean_features_per_parameter_for_join_index
                        ),
                        JoinTargetConstraint(
                            antecedent, one_join_consequent, True, nr_of_target_relation_parameter_options
                        ),
                        target_relation_cardinality
                    ))

    def __generate_true_false_join_one_candidates(
            self, target_relation_cardinality: int, nr_of_target_relation_parameter_options: Tuple[int],
            nr_of_numeric_features_per_parameter: Tuple[int],
            nr_of_boolean_features_per_parameter: Tuple[int],
            antecedent: List[Tuple[int]],
            constraint_candidates: List[CustomConstraint],
            false_positive_join_one_transaction_lists, false_negative_join_one_transaction_lists,
            found_patterns_true_false_join_all):
        for join_index, false_positive_join_one_transaction_list in enumerate(false_positive_join_one_transaction_lists):
            false_negative_join_one_transaction_list = false_negative_join_one_transaction_lists[join_index]
            nr_of_numeric_features_per_parameter_for_join_index = (
                nr_of_numeric_features_per_parameter[:target_relation_cardinality] +
                (nr_of_numeric_features_per_parameter[join_index],)
            )
            nr_of_boolean_features_per_parameter_for_join_index = (
                nr_of_boolean_features_per_parameter[:target_relation_cardinality] +
                (nr_of_boolean_features_per_parameter[join_index],)
            )
            if self.__verbose:
                print((
                    f'generate true->false join one (index={join_index}) candidates. '
                    f'{len(false_positive_join_one_transaction_list)} positive and '
                    f'{len(false_negative_join_one_transaction_list)} negative examples'
                ))
            one_join_consequent = list(antecedent[0])
            one_join_consequent[join_index] = target_relation_cardinality
            one_join_consequent = tuple(one_join_consequent)
            if false_positive_join_one_transaction_list and false_negative_join_one_transaction_list:
                for pattern in self.__itemset_miner.find_patterns(
                        false_positive_join_one_transaction_list,
                        false_negative_join_one_transaction_lists[join_index]
                        ) + found_patterns_true_false_join_all:
                    try:
                        constraint_candidates.append(ForAllJoinN(
                            join_index, 1,
                            pattern_to_cross_product_filter(
                                pattern, target_relation_cardinality+1,
                                nr_of_numeric_features_per_parameter_for_join_index,
                                nr_of_boolean_features_per_parameter_for_join_index
                            ),
                            JoinTargetConstraint(
                                antecedent, one_join_consequent, False, nr_of_target_relation_parameter_options
                            ),
                            target_relation_cardinality
                        ))
                    except IndexError:
                        #the join_all patterns might lead to invalid indices
                        pass

    def __generate_true_true_join_all_candidates(
            self, target_relation_cardinality, nr_of_target_relation_parameter_options,
            nr_of_numeric_features_per_parameter, nr_of_boolean_features_per_parameter,
            antecedent, all_join_consequent, constraint_candidates,
            true_positive_join_all_transaction_list, true_negative_join_all_transaction_list):
        if self.__verbose:
            print((
                'generate true->true join all candidates. '
                f'{len(true_positive_join_all_transaction_list)} positive and '
                f'{len(true_negative_join_all_transaction_list)} negative examples'
            ))
        if true_positive_join_all_transaction_list and true_negative_join_all_transaction_list:
            for pattern in self.__itemset_miner.find_patterns(
                    true_positive_join_all_transaction_list,
                    true_negative_join_all_transaction_list):
                constraint_candidates.append(ForAllJoinAll(
                    pattern_to_cross_product_filter(
                        pattern, 2*target_relation_cardinality,
                        nr_of_numeric_features_per_parameter,
                        nr_of_boolean_features_per_parameter
                    ),
                    JoinTargetConstraint(
                        antecedent, all_join_consequent, True, nr_of_target_relation_parameter_options
                    ),
                    target_relation_cardinality
                ))

    def __generate_true_false_join_all_candidates(
            self, target_relation_cardinality, nr_of_target_relation_parameter_options,
            nr_of_numeric_features_per_parameter, nr_of_boolean_features_per_parameter,
            antecedent, all_join_consequent, constraint_candidates,
            false_positive_join_all_transaction_list, false_negative_join_all_transaction_list):
        if self.__verbose:
            print((
                'generate true->false join all candidates. '
                f'{len(false_positive_join_all_transaction_list)} positive and '
                f'{len(false_negative_join_all_transaction_list)} negative examples'
            ))
        cdef list found_patterns = []
        if false_positive_join_all_transaction_list and false_negative_join_all_transaction_list:
            found_patterns = self.__itemset_miner.find_patterns(
                false_positive_join_all_transaction_list,
                false_negative_join_all_transaction_list
            )
            for pattern in found_patterns:
                constraint_candidates.append(ForAllJoinAll(
                    pattern_to_cross_product_filter(
                        pattern, 2*target_relation_cardinality,
                        nr_of_numeric_features_per_parameter,
                        nr_of_boolean_features_per_parameter
                    ),
                    JoinTargetConstraint(
                        antecedent, all_join_consequent, False, nr_of_target_relation_parameter_options
                    ),
                    target_relation_cardinality
                ))
        return found_patterns

    def __create_transactions_from_single_target_constraint_candidates(
            self, single_target_constraint_candidates: List[SingleTargetConstraint],
            rejected_candidates: List[SingleTargetConstraint], datagraph: DataGraph,
            dataset: CaConstraint, target_relation_cardinality: int):
        if self.__verbose:
            print('create features for implication candidates')
        true_positive_join_all_transaction_list = []
        true_positive_join_one_transaction_lists = [[] for _ in range(target_relation_cardinality)]
        false_positive_join_all_transaction_list = []
        false_positive_join_one_transaction_lists = [[] for _ in range(target_relation_cardinality)]
        true_negative_join_all_transaction_list = []
        true_negative_join_one_transaction_lists = [[] for _ in range(target_relation_cardinality)]
        false_negative_join_all_transaction_list = []
        false_negative_join_one_transaction_lists = [[] for _ in range(target_relation_cardinality)]
        for constraint in tqdm(single_target_constraint_candidates, disable=not self.__verbose, desc='positive set'):
            self.__add_pairwise_implication_to_transactions(
                constraint, datagraph, dataset, true_positive_join_all_transaction_list,
                true_positive_join_one_transaction_lists, false_positive_join_all_transaction_list,
                false_positive_join_one_transaction_lists)
        for constraint in tqdm(rejected_candidates, disable=not self.__verbose, desc='negative set'):
            self.__add_pairwise_implication_to_transactions(
                constraint, datagraph, dataset, true_negative_join_all_transaction_list,
                true_negative_join_one_transaction_lists, false_negative_join_all_transaction_list,
                false_negative_join_one_transaction_lists)
        return (
            true_positive_join_all_transaction_list, true_positive_join_one_transaction_lists,
            false_positive_join_all_transaction_list,false_positive_join_one_transaction_lists,
            true_negative_join_all_transaction_list, true_negative_join_one_transaction_lists,
            false_negative_join_all_transaction_list,false_negative_join_one_transaction_lists
        )

    def __add_pairwise_implication_to_transactions(
            self, constraint: SingleTargetConstraint, datagraph: DataGraph, dataset: CaDataset,
            true_join_all_transaction_list: list, true_join_one_transaction_lists: list,
            false_join_all_transaction_list: list, false_join_one_transaction_lists: list):
        antecedent_relation = datagraph.get_target_relation(constraint.antecedent_variables[0])
        consequent_relation = datagraph.get_target_relation(constraint.consequent_variable)
        parameters_differ = tuple(
            o1.object_id != o2.object_id for o1, o2 in
            zip(antecedent_relation.objects, consequent_relation.objects)
        )
        if all(parameters_differ):
            transaction = self.__pairwise_implication_to_all_join_all_transaction(
                antecedent_relation, consequent_relation, dataset, datagraph
            )
            if constraint.expected_value:
                true_join_all_transaction_list.append(transaction)
            else:
                false_join_all_transaction_list.append(transaction)
        elif ilen(x for x in parameters_differ if x) == 1:
            join_index = parameters_differ.index(True)
            transaction = self.__pairwise_implication_to_all_join_one_transaction(
                antecedent_relation, consequent_relation, dataset, datagraph,
                join_index
            )
            if constraint.expected_value:
                true_join_one_transaction_lists[join_index].append(transaction)
            else:
                false_join_one_transaction_lists[join_index].append(transaction)

    cdef object __create_item(self, object item):
        # we avoid the memory footprint of duplicated strings/items
        try:
            return self.__item_cache[item]
        except KeyError:
            self.__item_cache[item] = item
            return item

    def __pairwise_implication_to_all_join_all_transaction(
            self, CaRelation antecedent_relation, CaRelation consequent_relation,
            dataset: CaDataset, DataGraph datagraph) -> List[str]:
        cdef list transaction = []
        cdef int i,j,k
        cdef CaObject left_object, right_object
        for i, left_object in enumerate(antecedent_relation.objects):
            for j, right_object in enumerate(consequent_relation.objects):
                if left_object.type_name == right_object.type_name:
                    k = j + (<int>len(consequent_relation.objects))
                    if left_object.object_id == right_object.object_id:
                        transaction.append(self.__create_item(f'{i} = {k}'))
                    feature_definition = dataset.get_object_type(left_object.type_name).feature_definition
                    for first_feature_name, first_feature_type in feature_definition.items():
                        first_feature_left = left_object.features[first_feature_name]
                        first_feature_right = right_object.features[first_feature_name]
                        for second_feature_name, second_feature_type in feature_definition.items():
                            self.__append_pairwise_feature_items_to_transaction(
                                transaction, i, k, first_feature_name, second_feature_name,
                                first_feature_type, second_feature_type,
                                first_feature_left, left_object.features[second_feature_name],
                                first_feature_right, right_object.features[second_feature_name],
                                left_object.type_name, datagraph)
        return transaction

    def __append_pairwise_feature_items_to_transaction(
            self, transaction: List[str], i: int, j: int,
            first_feature_name: str, second_feature_name: str,
            first_feature_type, second_feature_type,
            first_feature_left, second_feature_left,
            first_feature_right, second_feature_right,
            type_name: str, datagraph: DataGraph):
        if isinstance(first_feature_type, CaNumber) and isinstance(second_feature_type, CaNumber):
            self.__append_numerical_comparisons_to_transaction(
                transaction, first_feature_left, second_feature_right,
                f'{i}.{first_feature_name}', f'{j}.{second_feature_name}'
            )
            if first_feature_name == second_feature_name:
                min_value, max_value = datagraph.get_feature_value_bounds(type_name, first_feature_name)
                int_min_value, int_max_value = int(min_value), int(max_value)
                if min_value == int_min_value and int_min_value >= 0:
                    min_divisor = max(2, int_min_value + 1)
                    max_divisor = ceil(int_max_value / 2)+1
                    if max_divisor - min_divisor < 50:
                        step_size = 1
                    else:
                        step_size = (max_divisor - min_divisor) // 10
                    for divisor in range(min_divisor, max_divisor, step_size):
                        self.__append_numerical_comparisons_to_transaction(
                            transaction, int(first_feature_left) // divisor,
                            int(second_feature_right) // divisor,
                            f'{i}.{first_feature_name}//{divisor}',
                            f'{j}.{second_feature_name}//{divisor}',
                            add_inequalities=False
                        )
                    for possible_sum in range(2*int_min_value,2*int_max_value+1):
                        self.__append_numerical_comparisons_to_transaction(
                            transaction, first_feature_left + first_feature_right,
                            possible_sum,
                            f'{i}.{first_feature_name}+{j}.{first_feature_name}',
                            str(possible_sum),
                            add_inequalities=False
                        )
                    if int_max_value - int_min_value < 50:
                        step_size = 1
                    else:
                        step_size = int_max_value-int_min_value // 50
                    for possible_abs_difference in range(1,int_max_value-int_min_value,step_size):
                        self.__append_numerical_comparisons_to_transaction(
                            transaction, abs(first_feature_left - first_feature_right),
                            possible_abs_difference,
                            f'|{i}.{first_feature_name}-{j}.{first_feature_name}|',
                            str(possible_abs_difference),
                            add_inequalities=True
                        )
            else:
                first_difference_feature = first_feature_left - second_feature_left
                second_difference_feature = first_feature_right - second_feature_right
                self.__append_numerical_comparisons_to_transaction(
                    transaction, first_difference_feature, second_difference_feature,
                    f'{i}.{first_feature_name}-{i}.{second_feature_name}',
                    f'{j}.{first_feature_name}-{j}.{second_feature_name}',
                )
                self.__append_numerical_comparisons_to_transaction(
                    transaction, abs(first_difference_feature), abs(second_difference_feature),
                    f'|{i}.{first_feature_name}-{i}.{second_feature_name}|',
                    f'|{j}.{first_feature_name}-{j}.{second_feature_name}|',
                )
                first_difference = first_feature_left - first_feature_right
                second_difference = second_feature_left - second_feature_right
                self.__append_numerical_comparisons_to_transaction(
                    transaction, first_difference, second_difference,
                    f'{i}.{first_feature_name}-{j}.{first_feature_name}',
                    f'{i}.{second_feature_name}-{j}.{second_feature_name}',
                )
                self.__append_numerical_comparisons_to_transaction(
                    transaction, abs(first_difference), abs(second_difference),
                    f'|{i}.{first_feature_name}-{j}.{first_feature_name}|',
                    f'|{i}.{second_feature_name}-{j}.{second_feature_name}|',
                )
        elif isinstance(first_feature_type, CaBoolean) and isinstance(second_feature_type, CaBoolean):
            self.__append_boolean_comparisons_to_transaction(
                transaction, first_feature_left, second_feature_right,
                f'{i}.{first_feature_name}', f'{j}.{second_feature_name}'
            )

    def __append_numerical_comparisons_to_transaction(
            self, transaction: List[str], first_value, second_value,
            first_label, second_label, add_inequalities: bool = True):
        if add_inequalities:
            if first_value <= second_value:
                transaction.append(self.__create_item(f'{first_label} <= {second_label}'))
            else:
                transaction.append(self.__create_item(f'{first_label} > {second_label}'))
            if second_value <= first_value:
                transaction.append(self.__create_item(f'{second_label} <= {first_label}'))
            else:
                transaction.append(self.__create_item(f'{second_label} > {first_label}'))
        if second_value == first_value:
            transaction.append(self.__create_item(f'{first_label} = {second_label}'))

    def __append_boolean_comparisons_to_transaction(
            self, transaction: List[str], first_value: bool, second_value: bool,
            first_label: str, second_label: str):
        if first_value and second_value:
            transaction.append(self.__create_item(f'{first_label} & {second_label}'))

    def __pairwise_implication_to_all_join_one_transaction(
            self, antecedent_relation: CaRelation, consequent_relation: CaRelation,
            dataset: CaDataset, datagraph: DataGraph, join_index: int) -> List[str]:
        transaction = []
        left_object = antecedent_relation.objects[join_index]
        right_object = consequent_relation.objects[join_index]
        feature_definition = dataset.get_object_type(left_object.type_name).feature_definition
        j = len(antecedent_relation.objects)
        for first_feature_name, first_feature_type in feature_definition.items():
            first_feature_left = left_object.features[first_feature_name]
            first_feature_right = right_object.features[first_feature_name]
            for second_feature_name, second_feature_type in feature_definition.items():
                self.__append_pairwise_feature_items_to_transaction(
                    transaction, join_index, j, first_feature_name, second_feature_name,
                    first_feature_type, second_feature_type,
                    first_feature_left, left_object.features[second_feature_name],
                    first_feature_right, right_object.features[second_feature_name],
                    left_object.type_name, datagraph)
        return transaction

    def __process_candidate_list(
            self, list candidate_queue, list model,
            CnfFormula model_cnf, double model_cost, double data_cost, double total_cost,
            list sat_encoded_dataset,
            dict variables) -> Tuple[float, float, float, List[CustomConstraint], CnfFormula]:
        heapify(candidate_queue)
        # we have defined in the Candidate class the model is empty in iteration 1
        cdef int iteration = 1 if not model else 2
        if self.__verbose:
            print(f'start with {len(candidate_queue)} candidates, L(D,M) = {total_cost:.2f}')
        cdef Candidate candidate
        while candidate_queue:
            candidate = <Candidate>heappop(candidate_queue)
            if candidate.iteration == iteration:
                if candidate.replaced_constraint is not None:
                    model[candidate.replaced_constraint_index] = candidate.constraint
                else:
                    model.append(candidate.constraint)
                model_cnf = candidate.model_cnf
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
                    iteration, model, model_cost, model_cnf,
                    sat_encoded_dataset, total_cost, variables, self.__sat_model_counter)
                if candidate.gain < 0:
                    heappush(candidate_queue, candidate)
                elif self.__verbose:
                    print(f'rejected candidate "{candidate.constraint}", delta L(D,M) = {candidate.gain:.2f}, {len(candidate_queue)} candidates left')
        return model_cost, data_cost, total_cost, model, model_cnf

    def __find_model_with_count_expressions(
            self, dataset: CaDataset, target_relation: CaRelationType,
            sat_encoded_dataset: List[SatEncodedExample], DataGraph datagraph, TermFactory term_factory,
            discovered_constraints: List[CustomConstraint], model_cnf: CnfFormula,
            model_cost: float, data_cost: float,
            total_cost: float) -> Tuple[float, float, float, List[CustomConstraint]]:
        #make sure that we gain from all caches
        model_cnf = model_cnf.resolve_new_clauses()
        if self.__verbose:
            print('start search for count constraints')
        cdef list candidate_list = []
        cdef CountCandidate candidate
        #we only keep valid examples to make count expressions less noise-sensitive
        sat_encoded_dataset = [
            example for i,example in enumerate(sat_encoded_dataset)
            if model_cnf.get_nr_of_untrue_clauses_for_example(i) == 0
        ]
        if not sat_encoded_dataset:
            return model_cost, data_cost, total_cost, discovered_constraints
        data_cost = compute_encoded_data_length_from_known_solution_with_upperbound(
            model_cnf, sat_encoded_dataset, datagraph.get_target_variables(),
            self.__sat_model_counter, sat_encoded_dataset[0], total_cost)
        total_cost = model_cost + data_cost
        for constraint in tqdm(list(generate_count_candidates(
                dataset,
                sat_encoded_dataset,
                datagraph, target_relation)),
                disable=not self.__verbose, desc='create candidate list'):
            candidate = CountCandidate(constraint, model_cnf, sat_encoded_dataset, datagraph)
            if candidate.gain < 0:
                candidate_list.append(candidate)
        model_cost, data_cost, total_cost, discovered_constraints = self.__process_count_candidate_list(
            candidate_list, discovered_constraints, model_cnf.to_constraint_graph(),
            model_cost, data_cost, total_cost,
            sat_encoded_dataset, datagraph)
        pruned_constraint_list = []
        if self.__verbose:
            print('prune trivial count constraints')
        for constraint in discovered_constraints:
            if not isinstance(constraint, Count) \
            or not constraint.is_trivial:
                pruned_constraint_list.append(constraint)
            elif self.__verbose:
                print(f'prune trivial constraint "{constraint}"')
        return model_cost, data_cost, total_cost, pruned_constraint_list

    def __process_count_candidate_list(
            self, list candidate_queue, list model_without_count_constraints, ConstraintGraph constraint_graph,
            double model_cost, double data_cost, double total_cost, list sat_encoded_dataset,
            DataGraph datagraph) -> Tuple[float, float, float, List[CustomConstraint]]:
        heapify(candidate_queue)
        # we have defined in the Candidate class the model is empty in iteration 1
        cdef int iteration = 1 if not model_without_count_constraints else 2
        if self.__verbose:
            print(f'start with {len(candidate_queue)} count candidates, L(D,M) = {total_cost:.2f}')
        cdef CountCandidate candidate
        cdef int total_nr_of_constraints_in_model = <int>len(model_without_count_constraints)
        cdef list count_constraint_list = []
        cdef list model_count_list = [compute_graph_lower_bound(constraint_graph)]
        while candidate_queue:
            candidate = <CountCandidate>heappop(candidate_queue)
            if candidate.iteration == iteration:
                if candidate.replaced_constraint is not None:
                    count_constraint_list[candidate.replaced_constraint_index] = candidate.count_constraint
                    model_count_list[candidate.replaced_constraint_index+1] = candidate.model_count
                else:
                    count_constraint_list.append(candidate.count_constraint)
                    model_count_list.append(candidate.model_count)
                total_nr_of_constraints_in_model += 1
                model_cost = candidate.model_cost
                data_cost = candidate.data_cost
                total_cost = candidate.total_cost
                if self.__verbose:
                    print((
                        f'gained {abs(candidate.gain):.2f} bits with candidate "{candidate.count_constraint}", '
                        f'{len(candidate_queue)} candidates left, L(D,M) = {total_cost:.2f}'
                    ))
                iteration += 1
            else:
                candidate.update_gain(
                    iteration, total_nr_of_constraints_in_model, count_constraint_list,
                    model_cost, sat_encoded_dataset, datagraph,
                    total_cost, model_count_list)
                if candidate.gain < 0:
                    heappush(candidate_queue, candidate)
                elif self.__verbose:
                    print(f'rejected candidate "{candidate.count_constraint}", delta L(D,M) = {candidate.gain:.2f}, {len(candidate_queue)} candidates left')
        return model_cost, data_cost, total_cost, model_without_count_constraints + count_constraint_list

    def __repr__(self):
        return 'CustomCa'
