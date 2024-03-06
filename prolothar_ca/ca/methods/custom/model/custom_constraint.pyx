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

from math import floor
from itertools import chain
import sqlite3
from libc.math cimport log2
import numpy as np
from scipy.special.cython_special cimport binom
from random import Random

from cpython.tuple cimport PyTuple_GET_ITEM, PyTuple_New, PyTuple_GET_SIZE, PyTuple_SET_ITEM
from cpython.dict cimport PyDict_GetItem
from cpython.list cimport PyList_GET_SIZE
from cpython.set cimport PySet_GET_SIZE
from cpython.ref cimport Py_INCREF
from cython.operator import dereference

from prolothar_common.collections.tuple_utils cimport all_splits_of_size_k

from prolothar_common.mdl_utils cimport log2binom, L_N

from prolothar_ca.model.ca.dataset import CaDataset
from prolothar_ca.model.ca.example cimport CaExample
from prolothar_ca.model.ca.relation import CaRelation, CaRelationType
from prolothar_ca.model.ca.variable_type cimport CaVariableType
from prolothar_ca.model.ca.constraints.constraint import CaConstraint
from prolothar_ca.model.ca.constraints.constraint cimport CaConstraint
from prolothar_ca.model.ca.constraints.boolean import RelationIsFalse, RelationIsTrue
from prolothar_ca.model.ca.constraints.boolean import BooleanFeatureIsTrue, BooleanFeatureIsFalse
from prolothar_ca.model.ca.constraints.conjunction import Implies, And
from prolothar_ca.model.ca.constraints.quantifier import ForAll
from prolothar_ca.model.ca.constraints.query import AllOfType, Filter, Product
from prolothar_ca.model.ca.constraints.numeric import Count as CaCount, Between, Constant
from prolothar_ca.model.sat.variable cimport Variable, Value
from prolothar_ca.model.sat.term cimport Term

from prolothar_ca.ca.methods.custom.model.cross_product_filter import CrossProductFilter
from prolothar_ca.ca.methods.custom.model.datagraph_sql_constants import COLUMN_VARIABLEN_NR
from prolothar_ca.ca.methods.custom.model.datagraph_sql_constants import COLUMN_RELATION_NR
from prolothar_ca.ca.methods.custom.model.datagraph_sql_constants import COLUMN_OBJECT_ID
from prolothar_ca.ca.methods.custom.model.datagraph_sql_constants import COLUMN_RELATION_VALUE

cdef double CONSTRAINT_TYPE_COST = log2(3)

cdef class Partition:

    def __init__(self, double encoded_model_length):
        self.encoded_model_length = encoded_model_length
        self.cached_datagraph = None

    cpdef tuple compute_variable_groups(self, DataGraph datagraph):
        """
        returns a tuple[tuple[Variable]] that contains tuples of grouped variables
        defined by this partition. repeating calls for the same datagraph are cached.
        """
        if datagraph is self.cached_datagraph:
            return self.cached_variable_groups
        else:
            self.cached_datagraph = datagraph
            self.cached_variable_groups = self._compute_variable_groups(datagraph)
            return self.cached_variable_groups

    cdef tuple _compute_variable_groups(self, DataGraph datagraph):
        """
        returns a tuple[tuple[Variable]] that contains tuples of grouped variables
        defined by this partition.
        """
        raise NotImplementedError()

    cpdef to_ca_count_constraint(self, DataGraph datagraph, int lowerbound, int upperbound):
        """
        converts this constraint into a CaConstraint model constraint.
        returns a CaConstraint
        """
        raise NotImplementedError()

cdef class PartitionByTargetParameterFeaturesAreTrue(Partition):

    def __init__(self, int parameter_index, int target_relation_cardinality, list feature_name_list, int nr_of_boolean_features):
        super().__init__(log2(target_relation_cardinality) + log2binom(nr_of_boolean_features, len(feature_name_list)))
        self.parameter_index = parameter_index
        self.feature_name_list = feature_name_list
        self.__hash = hash((self.parameter_index, tuple(self.feature_name_list)))

    cdef tuple _compute_variable_groups(self, DataGraph datagraph):
        return datagraph.get_target_variables_grouped_by_parameter_with_true_features(self.parameter_index, self.feature_name_list)

    cpdef to_ca_count_constraint(self, DataGraph datagraph, int lowerbound, int upperbound):
        cdef tuple target_relation_parameter_types = datagraph.get_target_relation_type().parameter_types
        cdef tuple parameter_object_ids = PyTuple_New(PyList_GET_SIZE(target_relation_parameter_types))
        cdef int i
        cdef parameter_i
        for i in range(PyTuple_GET_SIZE(target_relation_parameter_types)):
            parameter_i = f'x{i}'
            Py_INCREF(parameter_i)
            PyTuple_SET_ITEM(parameter_object_ids, i, parameter_i)
        cdef Query for_all_query = AllOfType(target_relation_parameter_types[self.parameter_index], f'x{self.parameter_index}')
        if len(self.feature_name_list) == 1:
            for_all_query = Filter(for_all_query, BooleanFeatureIsTrue(
                target_relation_parameter_types[self.parameter_index],
                f'x{self.parameter_index}',
                self.feature_name_list[0]
            ))
        elif len(self.feature_name_list) > 1:
            for_all_query = Filter(for_all_query, And([
                BooleanFeatureIsTrue(
                    target_relation_parameter_types[self.parameter_index],
                    f'x{self.parameter_index}',
                    feature_name
                )
                for feature_name in self.feature_name_list
            ]))
        return ForAll(
            for_all_query,
            Between(
                Constant(lowerbound),
                CaCount(Filter(
                    self.__create_ca_query_for_remaining_target_relation_parameters(target_relation_parameter_types),
                    RelationIsTrue(
                        datagraph.get_target_relation_type(),
                        parameter_object_ids
                    )
                )),
                Constant(upperbound)
            )
        )

    cdef Query __create_ca_query_for_remaining_target_relation_parameters(self, tuple target_relation_parameter_types):
        if len(target_relation_parameter_types) <= 1:
            raise NotImplementedError(self)
        elif len(target_relation_parameter_types) == 2:
            index = (self.parameter_index + 1) % len(target_relation_parameter_types)
            return AllOfType(target_relation_parameter_types[index], f'x{index}')
        else:
            return Product([
                AllOfType(target_relation_parameter_types[index], f'x{index}')
                for index in range(len(target_relation_parameter_types))
                if index != self.parameter_index
            ])

    def __repr__(self):
        return f'PartitionByTargetParameterFeaturesAreTrue({self.parameter_index} , {self.feature_name_list})'

    def __hash__(self):
        return self.__hash

    def __eq__(self, other):
        return isinstance(other, PartitionByTargetParameterFeaturesAreTrue) \
        and self.parameter_index == (<PartitionByTargetParameterFeaturesAreTrue> other).parameter_index \
        and self.feature_name_list == (<PartitionByTargetParameterFeaturesAreTrue> other).feature_name_list

cdef class PartitionByTargetParameterFeaturesAreFalse(Partition):

    def __init__(self, int parameter_index, int target_relation_cardinality, list feature_name_list, int nr_of_boolean_features):
        super().__init__(log2(target_relation_cardinality) + log2binom(nr_of_boolean_features, len(feature_name_list)))
        self.parameter_index = parameter_index
        self.feature_name_list = feature_name_list
        self.__hash = hash((self.parameter_index, tuple(self.feature_name_list)))

    cdef tuple _compute_variable_groups(self, DataGraph datagraph):
        return datagraph.get_target_variables_grouped_by_parameter_with_false_features(self.parameter_index, self.feature_name_list)

    cpdef to_ca_count_constraint(self, DataGraph datagraph, int lowerbound, int upperbound):
        cdef tuple target_relation_parameter_types = datagraph.get_target_relation_type().parameter_types
        cdef tuple parameter_object_ids = PyTuple_New(PyList_GET_SIZE(target_relation_parameter_types))
        cdef int i
        cdef parameter_i
        for i in range(PyTuple_GET_SIZE(target_relation_parameter_types)):
            parameter_i = f'x{i}'
            Py_INCREF(parameter_i)
            PyTuple_SET_ITEM(parameter_object_ids, i, parameter_i)
        cdef Query for_all_query = AllOfType(target_relation_parameter_types[self.parameter_index], f'x{self.parameter_index}')
        if len(self.feature_name_list) == 1:
            for_all_query = Filter(for_all_query, BooleanFeatureIsFalse(
                target_relation_parameter_types[self.parameter_index],
                f'x{self.parameter_index}',
                self.feature_name_list[0]
            ))
        elif len(self.feature_name_list) > 1:
            for_all_query = Filter(for_all_query, And([
                BooleanFeatureIsFalse(
                    target_relation_parameter_types[self.parameter_index],
                    f'x{self.parameter_index}',
                    feature_name
                )
                for feature_name in self.feature_name_list
            ]))
        return ForAll(
            for_all_query,
            Between(
                Constant(lowerbound),
                CaCount(Filter(
                    self.__create_ca_query_for_remaining_target_relation_parameters(target_relation_parameter_types),
                    RelationIsTrue(
                        datagraph.get_target_relation_type(),
                        parameter_object_ids
                    )
                )),
                Constant(upperbound)
            )
        )

    cdef Query __create_ca_query_for_remaining_target_relation_parameters(self, tuple target_relation_parameter_types):
        if len(target_relation_parameter_types) <= 1:
            raise NotImplementedError()
        elif len(target_relation_parameter_types) == 2:
            index = (self.parameter_index + 1) % len(target_relation_parameter_types)
            return AllOfType(target_relation_parameter_types[index], f'x{index}')
        else:
            return Product([
                AllOfType(target_relation_parameter_types[index], f'x{index}')
                for index in range(len(target_relation_parameter_types))
                if index != self.parameter_index
            ])

    def __repr__(self):
        return f'PartitionByTargetParameterFeaturesAreFalse({self.parameter_index} , {self.feature_name_list})'

    def __hash__(self):
        return self.__hash

    def __eq__(self, other):
        return isinstance(other, PartitionByTargetParameterFeaturesAreFalse) \
        and self.parameter_index == (<PartitionByTargetParameterFeaturesAreFalse> other).parameter_index \
        and self.feature_name_list == (<PartitionByTargetParameterFeaturesAreFalse> other).feature_name_list

cdef class CustomConstraint():

    def __init__(self, double encoded_model_length):
        self.encoded_model_length = CONSTRAINT_TYPE_COST + encoded_model_length

    cpdef set compute_cnf_clauses(self, DataGraph datagraph, TermFactory term_factory):
        """
        creates the CNF clauses for computing the encoded length of the data

        returns set[CnfDisjunction]
        """
        raise NotImplementedError(type(self))

    cpdef CustomConstraint merge(self, CustomConstraint other):
        """
        tries to create a shorter representation for "self AND other". if this is
        possible, the shorter representation is returned, otherwise None.
        """
        raise NotImplementedError()

    def to_ca_model(self, DataGraph datagraph) -> CaConstraint:
        """
        converts this constraint into the corresponding CaConstraint
        """
        raise NotImplementedError()

cdef class Count(CustomConstraint):

    def __init__(
            self, Partition partition, int lowerbound, int upperbound, int nr_of_target_variables,
            dict clause_cache, bint is_trivial = False):
        super().__init__(
            partition.encoded_model_length +
            log2(nr_of_target_variables) +
            L_N(upperbound - lowerbound + 1)
        )
        self.partition = partition
        self.lowerbound = lowerbound
        self.upperbound = upperbound
        self.nr_of_target_variables = nr_of_target_variables
        self.clause_cache = clause_cache
        self.is_trivial = is_trivial

    cpdef set compute_cnf_clauses(self, DataGraph datagraph, TermFactory term_factory):
        cdef tuple variable_group_tuple = self.partition.compute_variable_groups(datagraph)
        cdef set cnf_clauses = set()
        hash_key_lower_bound = (self.partition, self.lowerbound, 0)
        try:
            cnf_clauses.update(self.clause_cache[hash_key_lower_bound])
        except KeyError:
            lower_bound_clauses = set()
            for variable_group in variable_group_tuple:
                self.__add_cnf_clauses_for_lowerbound(lower_bound_clauses, <tuple>variable_group, term_factory)
            self.clause_cache[hash_key_lower_bound] = lower_bound_clauses
            cnf_clauses.update(lower_bound_clauses)

        hash_key_upper_bound = (self.partition, self.upperbound, 1)
        try:
            cnf_clauses.update(self.clause_cache[hash_key_upper_bound])
        except KeyError:
            upper_bound_clauses = set()
            for variable_group in variable_group_tuple:
                self.__add_cnf_clauses_for_upperbound(upper_bound_clauses, <tuple>variable_group, term_factory)
            self.clause_cache[hash_key_upper_bound] = upper_bound_clauses
            cnf_clauses.update(upper_bound_clauses)
        return cnf_clauses

    cdef __add_cnf_clauses_for_lowerbound(self, set cnf_clauses, tuple variable_group, TermFactory term_factory):
        cdef tuple term_list
        cdef int i
        if self.lowerbound > 0:
            if self.lowerbound == PyTuple_GET_SIZE(variable_group):
                for i, variable in enumerate(variable_group):
                    cnf_clauses.add(CnfDisjunction((Term.__new__(Term, <Variable>variable),)))
            else:
                for split in all_splits_of_size_k(variable_group, PyTuple_GET_SIZE(variable_group) - self.lowerbound):
                    antecedent_variables = PyTuple_GET_ITEM(split, 0)
                    consequent_variables = PyTuple_GET_ITEM(split, 1)
                    for must_be_positive_variable in <tuple>consequent_variables:
                        term_list = PyTuple_New(PyTuple_GET_SIZE(<tuple>antecedent_variables)+1)
                        for i, variable in enumerate(<tuple>antecedent_variables):
                            term = term_factory.create_term(<Variable>variable, False)
                            Py_INCREF(term)
                            PyTuple_SET_ITEM(term_list, i, term)
                        term = term_factory.create_term(<Variable>must_be_positive_variable, False)
                        Py_INCREF(term)
                        PyTuple_SET_ITEM(term_list, PyTuple_GET_SIZE(term_list)-1, term)
                        cnf_clauses.add(CnfDisjunction(term_list))

    cdef __add_cnf_clauses_for_upperbound(self, set cnf_clauses, tuple variable_group, TermFactory term_factory):
        cdef tuple antecedent_terms
        cdef int i
        if self.upperbound == 0:
            antecedent_terms = PyTuple_New(PyTuple_GET_SIZE(variable_group))
            for i, variable in enumerate(variable_group):
                term = term_factory.create_term(<Variable>variable, True)
                Py_INCREF(term)
                PyTuple_SET_ITEM(antecedent_terms, i, term)
            cnf_clauses.add(CnfDisjunction(antecedent_terms))
        else:
            for split in all_splits_of_size_k(variable_group, self.upperbound):
                antecedent_variables = PyTuple_GET_ITEM(split, 0)
                consequent_variables = PyTuple_GET_ITEM(split, 1)
                for must_be_negative_variable in <tuple>consequent_variables:
                    antecedent_terms = PyTuple_New(PyTuple_GET_SIZE(<tuple>antecedent_variables)+1)
                    for i, variable in enumerate(<tuple>antecedent_variables):
                        term = term_factory.create_term(<Variable>variable, True)
                        Py_INCREF(term)
                        PyTuple_SET_ITEM(antecedent_terms, i, term)
                    term = term_factory.create_term(<Variable>must_be_negative_variable, True)
                    Py_INCREF(term)
                    PyTuple_SET_ITEM(antecedent_terms, PyTuple_GET_SIZE(antecedent_terms)-1, term)
                    cnf_clauses.add(CnfDisjunction(antecedent_terms))

    cpdef add_edges_to_constraint_graph(self, ConstraintGraph constraint_graph, DataGraph datagraph):
        cdef tuple casted_variable_group
        cdef int i,j
        cdef Variable variable_i
        for variable_group in self.partition.compute_variable_groups(datagraph):
            casted_variable_group = <tuple>variable_group
            for i in range(PyTuple_GET_SIZE(casted_variable_group)):
                variable_i = <Variable>PyTuple_GET_ITEM(casted_variable_group, i)
                for j in range(i+1, PyTuple_GET_SIZE(casted_variable_group)):
                    constraint_graph.add_edge(
                        variable_i, <Variable>PyTuple_GET_ITEM(casted_variable_group, j))

    cpdef int get_nr_of_untrue_clauses_for_example(self, DataGraph datagraph, int example_id):
        cdef unordered_map[int,int].iterator nr_of_untrue_clauses_iterator = self.nr_of_untrue_clauses_for_example.find(example_id)
        cdef int nr_of_untrue_clauses = 0
        cdef int nr_of_true_variables_in_group
        if nr_of_untrue_clauses_iterator != self.nr_of_untrue_clauses_for_example.end():
            return dereference(nr_of_untrue_clauses_iterator).second
        else:
            for variable_group in self.partition.compute_variable_groups(datagraph):
                nr_of_true_variables_in_group = 0
                for variable in <tuple>variable_group:
                    if (<Variable>variable).value == Value.TRUE:
                        nr_of_true_variables_in_group += 1
                if not (self.lowerbound <= nr_of_true_variables_in_group <= self.upperbound):
                    nr_of_untrue_clauses += 1
            self.nr_of_untrue_clauses_for_example[example_id] = nr_of_untrue_clauses
            return nr_of_untrue_clauses

    cpdef CustomConstraint merge(self, CustomConstraint other):
        # this is a slight abuse of the merge method but enables replacement
        # of count constraints with a larger than necessary span between bounds
        cdef Count other_casted
        if isinstance(other, Count):
            other_casted = <Count>other
            if other_casted.partition == self.partition:
            # and other_casted.lowerbound >= self.lowerbound \
            # and other_casted.upperbound <= self.upperbound:
                return other_casted
        return None

    cpdef int get_nr_of_target_variables(self):
        return self.nr_of_target_variables

    def to_ca_model(self, datagraph) -> CaConstraint:
        return self.partition.to_ca_count_constraint(datagraph, self.lowerbound, self.upperbound)

    cpdef double count_nr_of_solutions(self, DataGraph datagraph):
        cdef tuple variable_groups = self.partition.compute_variable_groups(datagraph)
        cdef size_t nr_of_variables_per_group = len((<tuple>variable_groups)[0])
        cdef double nr_of_solutions = 0
        cdef int nr_of_true_variables
        for nr_of_true_variables in range(self.lowerbound, self.upperbound+1):
            nr_of_solutions += binom(nr_of_variables_per_group, nr_of_true_variables)
        cdef set used_variables = set()
        for variable_group in variable_groups:
            used_variables.update(variable_group)
        return nr_of_solutions * len(variable_groups) + 2**(self.nr_of_target_variables - len(used_variables))

    def __repr__(self):
        return f'Count({self.partition}, {self.lowerbound}, {self.upperbound})'

cdef class JoinTargetConstraint:

    def __init__(self, list antecedent_terms, tuple consequent_term, bint expected_value, tuple nr_of_target_relation_parameter_options):
        cdef int nr_of_antecedent_terms = <int>len(antecedent_terms)
        self.encoded_model_length = L_N(nr_of_antecedent_terms + 1) + 1
        for nr_of_options in nr_of_target_relation_parameter_options:
            self.encoded_model_length += log2(nr_of_options) * (nr_of_antecedent_terms + 1)
        self.antecedent_terms = antecedent_terms
        self.consequent_term = consequent_term
        self.expected_value = expected_value
        if self.antecedent_terms:
            self.__hash = hash((self.antecedent_terms[0], self.consequent_term, self.expected_value))
        else:
            self.__hash = hash((self.consequent_term, self.expected_value))

    def __repr__(self):
        if self.expected_value:
            return f'{self.antecedent_terms} -> {self.consequent_term}'
        else:
            return f'{self.antecedent_terms} -> !{self.consequent_term}'

    def __eq__(self, other: JoinTargetConstraint):
        return (
            self.antecedent_terms == other.antecedent_terms and
            self.consequent_term == other.consequent_term and
            self.expected_value == other.expected_value
        )

    def __hash__(self):
        return self.__hash

    def to_ca_model(self, target_relation_type: CaRelationType, variable_names: list[str]) -> CaConstraint:
        if self.expected_value:
            consequent_term = RelationIsTrue(target_relation_type, tuple(map(variable_names.__getitem__, self.consequent_term)))
        else:
            consequent_term = RelationIsFalse(target_relation_type, tuple(map(variable_names.__getitem__, self.consequent_term)))
        if not self.antecedent_terms:
            return consequent_term
        elif len(self.antecedent_terms) == 1:
            return Implies(
                RelationIsTrue(target_relation_type, tuple(map(variable_names.__getitem__, self.antecedent_terms[0]))),
                consequent_term
            )
        else:
            raise NotImplementedError()

cdef class SingleTargetConstraint(CustomConstraint):

    def __init__(
            self, list antecedent_variables, int consequent_variable,
            bint expected_value, int nr_of_variables):
        super().__init__(
            L_N(len(antecedent_variables) + 1) +
            log2binom(nr_of_variables, len(antecedent_variables) + 1) + 1
        )
        self.antecedent_variables = antecedent_variables
        self.consequent_variable = consequent_variable
        self.expected_value = expected_value

    cpdef set compute_cnf_clauses(self, DataGraph datagraph, TermFactory term_factory):
        if len(self.antecedent_variables) != 1:
            raise NotImplementedError()
        cdef Variable antecedent_variable = datagraph.get_target_variable_by_number(self.antecedent_variables[0])
        cdef Variable consequent_variable = datagraph.get_target_variable_by_number(self.consequent_variable)
        return {CnfDisjunction((
            term_factory.create_term(antecedent_variable, True),
            term_factory.create_term(consequent_variable, not self.expected_value),
        ))}

    def to_ca_model(self, DataGraph datagraph):
        target_relation = datagraph.get_target_relation_type()
        if len(self.antecedent_variables) != 1:
            raise NotImplementedError()
        antecedent_constraint = RelationIsTrue(
            target_relation,
            tuple(o.object_id for o in datagraph.get_target_relation(self.antecedent_variables[0]).objects)
        )
        if self.expected_value:
            consequent_constraint = RelationIsTrue(
                target_relation,
                tuple(o.object_id for o in datagraph.get_target_relation(self.consequent_variable).objects)
            )
        else:
            consequent_constraint = RelationIsFalse(
                target_relation,
                tuple(o.object_id for o in datagraph.get_target_relation(self.consequent_variable).objects)
            )
        return Implies(antecedent_constraint, consequent_constraint)

    cpdef CustomConstraint merge(self, CustomConstraint other):
        return None

    def count_true(self, dataset_np: np.ndarray) -> int:
        """
        counts how of this constraint is satisfied in the given numpy encoded
        dataset. each row in the dataset is an example and the columns correpond
        to the variables with values 0 (False) or 1 (True). the first column
        belongs to variable with nr 1, second column is variable 2 and so on.
        """
        cdef int[:,:] dataset_view = dataset_np
        cdef int i
        cdef size_t count = 0
        cdef int consequent_variable = self.consequent_variable - 1
        cdef int antecedent_variable
        cdef bint expected_value = self.expected_value
        for i in range(dataset_np.shape[0]):
            if dataset_view[i,consequent_variable] == expected_value:
                count += 1
            else:
                for antecedent_variable in self.antecedent_variables:
                    if not dataset_view[i,antecedent_variable-1]:
                        count += 1
                        break
        return count

    cpdef int count_true_by_consequent(self, dataset_np: np.ndarray):
        """
        counts how of this constraint is satisfied if the antecedent condition is true
        in the given numpy encoded dataset. in other words: counts how often
        both antecedent and consequent condition are satisfied.
        each row in the dataset is an example and the columns correpond
        to the variables with values 0 (False) or 1 (True). the first column
        belongs to variable with nr 1, second column is variable 2 and so on.
        """
        consequent_condition = dataset_np[:,self.consequent_variable-1]
        if not self.expected_value:
            consequent_condition = np.logical_not(consequent_condition)
        if self.antecedent_variables:
            antecedent_condition = dataset_np[:,self.antecedent_variables[0]-1]
            for variable in self.antecedent_variables[1:]:
                antecedent_condition = np.logical_and(dataset_np[:, variable-1])
            return np.logical_and(antecedent_condition, consequent_condition).sum()
        else:
            return consequent_condition.sum()

    def __repr__(self):
        if self.expected_value:
            return f'{self.antecedent_variables} -> {self.consequent_variable}'
        else:
            return f'{self.antecedent_variables} -> !{self.consequent_variable}'

    def __eq__(self, other):
        return (
            self.antecedent_variables == other.antecedent_variables and
            self.consequent_variable == other.consequent_variable and
            self.expected_value == other.expected_value
        )

cdef class DataGraph:

    def __init__(
            self, CaExample example, dataset: CaDataset, target_relation: CaRelationType,
            db_module = sqlite3, max_nr_of_target_zeros: int = -1):
        self.__target_variables = {}
        self.__variables = {}
        self.__target_relations = {}
        self.__target_relation = target_relation
        self.__db = db_module.connect(':memory:')
        if db_module is sqlite3:
            self.__db.create_function('FLOOR', 1, floor)
            self.__create_table_suffix = ' WITHOUT ROWID'
            self.__create_foreign_keys = True
        else:
            self.__create_table_suffix = ''
            self.__create_foreign_keys = False
        self.__create_cnf_clause_cache = {}
        self.__get_feature_value_bounds_cache = {}

        cdef set object_set
        for object_type_name, object_set in example.all_objects_per_type.items():
            object_type = dataset.get_object_type(object_type_name)
            self.add_object_type(<CaObjectType>object_type)
            self.add_object_nodes_from_set(object_set, <CaObjectType>object_type)

        for relation_name, relation_set in example.relations.items():
            relation_type = dataset.get_relation_type(relation_name)
            if relation_name == target_relation.name:
                self.add_target_relation_type(relation_type)
                if max_nr_of_target_zeros == -1:
                    for relation in relation_set:
                        self.add_target_relation_node(relation, relation_type)
                else:
                    relation_list = list(relation_set)
                    Random().shuffle(relation_list)
                    for relation in relation_set:
                        if dataset.is_relation_true_for_any_example(relation.name, relation.objects):
                            self.add_target_relation_node(relation, relation_type)
                        elif max_nr_of_target_zeros > 0:
                            self.add_target_relation_node(relation, relation_type)
                            max_nr_of_target_zeros -= 1
            else:
                self.add_relation_type(relation_type)
                for i,relation in enumerate(relation_set):
                    self.add_relation_node(relation, i, relation_type)

        if db_module is sqlite3:
            self.__db.execute('PRAGMA optimize')

        self.__nr_of_target_variables = len(self.__target_variables)

    cpdef clear_caches(self):
        self.__create_cnf_clause_cache.clear()
        self.__get_feature_value_bounds_cache().clear()

    def __del__(self):
        self.__db.close()

    def add_object_type(self, CaObjectType object_type):
        self.__db.execute(''.join((
            f'CREATE TABLE {object_type.name} (',
            f'{COLUMN_OBJECT_ID} TEXT PRIMARY KEY',
            ', ' if object_type.feature_definition else '',
            ', '.join(
                f'{feature_name} {feature_type.get_sqlite_type_name()}'
                for feature_name, feature_type in object_type.feature_definition.items()
            ),
            f'){self.__create_table_suffix};'
        )))
        for feature_name in object_type.feature_definition.keys():
            self.__db.execute(' '.join((
                f'CREATE INDEX {object_type.name}_{feature_name}_index',
                f'ON {object_type.name}({feature_name})'
            )))
            self.__db.execute(' '.join((
                f'CREATE INDEX {object_type.name}_id_{feature_name}_index',
                f'ON {object_type.name}({COLUMN_OBJECT_ID},{feature_name})'
            )))
            for other_feature_name in object_type.feature_definition.keys():
                if feature_name != other_feature_name:
                    self.__db.execute(' '.join((
                        f'CREATE INDEX {object_type.name}_{feature_name}_{other_feature_name}_index',
                        f'ON {object_type.name}({feature_name},{other_feature_name})'
                    )))
                    self.__db.execute(' '.join((
                        f'CREATE INDEX {object_type.name}_id_{feature_name}_{other_feature_name}_index',
                        f'ON {object_type.name}({COLUMN_OBJECT_ID},{feature_name},{other_feature_name})'
                    )))

        self.__db.commit()

    cpdef add_object_node(self, CaObject an_object, CaObjectType object_type, bint commit=True):
        cdef list feature_names = []
        cdef list feature_values = []
        for feature_name, feature_value in an_object.features.items():
            feature_names.append(feature_name)
            feature_values.append((<CaVariableType>(PyDict_GetItem(object_type.feature_definition, feature_name))).format_value_sqlite(feature_value))
        self.__db.execute(''.join((
            'INSERT INTO ', an_object.type_name, ' (',
            COLUMN_OBJECT_ID,
            ', ' if object_type.feature_definition else '',
            ', '.join(feature_names),
            ') VALUES (',
            "'", an_object.object_id, "'",
            ', ' if object_type.feature_definition else '',
            ', '.join(feature_values),
            ');'
        )))
        if commit:
            self.__db.commit()

    cdef add_object_nodes_from_set(self, set object_set, CaObjectType object_type):
        if not object_set:
            return
        cdef list feature_names = list(object_type.feature_definition.keys())
        cdef tuple values_to_insert = PyTuple_New(PySet_GET_SIZE(object_set))
        cdef tuple values
        cdef object feature_value
        cdef int i,j
        for i,an_object in enumerate(object_set):
            values = PyTuple_New(PyList_GET_SIZE(feature_names)+1)
            Py_INCREF((<CaObject>an_object).object_id)
            PyTuple_SET_ITEM(values, 0, (<CaObject>an_object).object_id)
            for j,feature_name in enumerate(feature_names):
                feature_value = <object>PyDict_GetItem((<CaObject>an_object).features, feature_name)
                Py_INCREF(feature_value)
                PyTuple_SET_ITEM(values, j+1, feature_value)
            Py_INCREF(values)
            PyTuple_SET_ITEM(values_to_insert, i, values)
        self.__db.executemany(''.join((
            'INSERT INTO ', object_type.name, ' (',
            COLUMN_OBJECT_ID,
            ', ' if object_type.feature_definition else '',
            ', '.join(feature_names),
            ') VALUES (',
            ', '.join(['?'] * (len(feature_names) + 1)),
            ');'
        )), values_to_insert)
        self.__db.commit()

    def add_relation_type(self, relation_type: CaRelationType):
        create_table_sql_command = ''.join((
            f'CREATE TABLE {relation_type.name} (',
            f'{COLUMN_RELATION_NR} INTEGER PRIMARY KEY, ',
            f'{COLUMN_RELATION_VALUE} {relation_type.value_type.get_sqlite_type_name()}',
            ', ' if relation_type.parameter_types else '',
            ', '.join(
                f'{self.__relation_table_parameter_name(i)} TEXT'
                for i in range(len(relation_type.parameter_types))
            ),
            ', ' if relation_type.parameter_types and self.__create_foreign_keys else '',
            ', '.join(
                f'FOREIGN KEY ({self.__relation_table_parameter_name(i)}) REFERENCES {parameter_type}({COLUMN_OBJECT_ID})'
                for i, parameter_type in enumerate(relation_type.parameter_types)
            ) if self.__create_foreign_keys else '',
            f'){self.__create_table_suffix};'
        ))
        try:
            self.__db.execute(create_table_sql_command)
        except Exception as e:
            print(create_table_sql_command)
            raise ValueError(f'relation_type with "{relation_type.name}" probably has the name of a protected sql keyword') from e
        for i in range(len(relation_type.parameter_types)):
            self.__db.execute(' '.join((
                f'CREATE INDEX {relation_type.name}_fkindex_{i}',
                f'ON {relation_type.name}({self.__relation_table_parameter_name(i)})'
            )))
        self.__db.execute(' '.join((
            f'CREATE INDEX {relation_type.name}_index_relationnr',
            f'ON {relation_type.name}({COLUMN_RELATION_NR})'
        )))
        if relation_type.parameter_types:
            self.__db.execute(' '.join((
                f'CREATE INDEX {relation_type.name}_fkindex_all',
                f'ON {relation_type.name}({",".join(self.__relation_table_parameter_name(i) for i in range(len(relation_type.parameter_types)))})'
            )))
        self.__db.commit()

    def add_relation_node(self, relation: CaRelation, relation_nr: int, relation_type: CaRelationType):
        if relation.objects:
            self.__db.execute(''.join((
                f'INSERT INTO {relation.name} (',
                f'{COLUMN_RELATION_NR}, {COLUMN_RELATION_VALUE}, ',
                ', '.join(self.__relation_table_parameter_name(i) for i in range(len(relation.objects))),
                ') VALUES (',
                f'{relation_nr}, ',
                relation_type.value_type.format_value_sqlite(relation.value), ', ',
                ', '.join(f"'{an_object.object_id}'" for an_object in relation.objects),
                ');'
            )))
        else:
            self.__db.execute(''.join((
                f'INSERT INTO {relation.name} ({COLUMN_RELATION_NR}, {COLUMN_RELATION_VALUE}) VALUES (',
                f'{relation_nr}, ',
                relation_type.value_type.format_value_sqlite(relation.value),
                ');'
            )))
        self.__db.commit()

    def add_target_relation_type(self, relation_type: CaRelationType):
        self.__db.execute(''.join((
            f'CREATE TABLE {relation_type.name} (',
            f'{COLUMN_VARIABLEN_NR} INTEGER PRIMARY KEY, ',
            f'{COLUMN_RELATION_VALUE} INTEGER, ',
            ', '.join(
                f'{self.__relation_table_parameter_name(i)} TEXT'
                for i in range(len(relation_type.parameter_types))
            ),
            ', ' if self.__create_foreign_keys else '',
            ', '.join(
                f'FOREIGN KEY ({self.__relation_table_parameter_name(i)}) REFERENCES {parameter_type}({COLUMN_OBJECT_ID})'
                for i, parameter_type in enumerate(relation_type.parameter_types)
            ) if self.__create_foreign_keys else '',
            f'){self.__create_table_suffix};'
        )))
        for i in range(len(relation_type.parameter_types)):
            self.__db.execute(' '.join((
                f'CREATE INDEX {relation_type.name}_fkindex_{i}',
                f'ON {relation_type.name}({self.__relation_table_parameter_name(i)})'
            )))
        self.__db.execute(' '.join((
            f'CREATE INDEX {relation_type.name}_index_variablenr',
            f'ON {relation_type.name}({COLUMN_VARIABLEN_NR})'
        )))
        self.__db.execute(' '.join((
            f'CREATE INDEX {relation_type.name}_fkindex_all',
            f'ON {relation_type.name}({",".join(self.__relation_table_parameter_name(i) for i in range(len(relation_type.parameter_types)))})'
        )))
        self.__db.commit()

    def add_target_relation_node(self, relation: CaRelation, relation_type: CaRelationType):
        variable = Variable(
            len(self.__target_variables) + 1,
            Value.TRUE if relation.value else Value.FALSE
        )
        self.__target_variables[relation.objects] = variable
        self.__target_relations[variable.nr] = relation
        self.__variables[variable.nr] = variable
        self.__db.execute(''.join((
            f'INSERT INTO {relation.name} (',
            f'{COLUMN_VARIABLEN_NR}, {COLUMN_RELATION_VALUE}, ',
            ', '.join(self.__relation_table_parameter_name(i) for i in range(len(relation.objects))),
            ') VALUES (',
            f'{variable.nr}, ',
            relation_type.value_type.format_value_sqlite(relation.value), ', ',
            ', '.join(f"'{an_object.object_id}'" for an_object in relation.objects),
            ');'
        )))
        self.__db.commit()

    def get_nr_of_target_variables(self) -> int:
        return self.__nr_of_target_variables

    cpdef Variable get_target_variable(self, CaRelation relation):
        return <Variable>self.__target_variables[relation.objects]

    cpdef Variable get_target_variable_by_number(self, object variable_nr):
        return <Variable>self.__variables[variable_nr]

    cpdef dict get_target_variables(self):
        return self.__variables

    def get_target_relation_type(self) -> CaRelationType:
        return self.__target_relation

    def get_target_relation(self, variable_nr: int) -> CaRelation:
        return self.__target_relations[variable_nr]

    cpdef set compute_cnf_clauses(
            self, JoinTargetConstraint target_constraint, tuple additional_joins,
            cross_product_filter: CrossProductFilter):
        cdef set clauses = set()
        for variables in self.query_variables(target_constraint, additional_joins, cross_product_filter):
            clauses.add(self.__create_cnf_clause(<tuple>variables, target_constraint))
        return clauses

    cdef CnfDisjunction __create_cnf_clause(self, tuple variables, JoinTargetConstraint target_constraint):
        hash_key = (variables, target_constraint)
        cdef Term consequent_term
        cdef CnfDisjunction cnf_disjunction
        try:
            return <CnfDisjunction>self.__create_cnf_clause_cache[hash_key]
        except KeyError:
            consequent_term = Term.__new__(Term, <Variable>PyTuple_GET_ITEM(variables, PyTuple_GET_SIZE(variables)-1), negated=not target_constraint.expected_value)
            if not target_constraint.antecedent_terms:
                cnf_disjunction = CnfDisjunction((consequent_term,))
            elif PyList_GET_SIZE(target_constraint.antecedent_terms) == 1:
                cnf_disjunction = CnfDisjunction((
                    Term.__new__(Term, <Variable>PyTuple_GET_ITEM(variables, 0), negated=True),
                    consequent_term
                ))

            else:
                raise NotImplementedError()
            self.__create_cnf_clause_cache[hash_key] = cnf_disjunction
            return cnf_disjunction

    cpdef list query_variables(self, JoinTargetConstraint target_constraint, tuple additional_joins, cross_product_filter: CrossProductFilter):
        cdef list target_variables = [*target_constraint.antecedent_terms]
        target_variables.append(target_constraint.consequent_term)
        sql_query = ' '.join((
            self.__create_select_query_part(target_variables),
            self.__create_join_query_part(additional_joins, target_variables),
            self.__create_relation_join_query_part(cross_product_filter),
            self.__create_where_query_part(additional_joins, cross_product_filter),
            ';'
        ))
        cursor = self.__db.execute(sql_query)
        # cursor.arraysize = min(self.__nr_of_target_variables ** 2, LONG_MAX)
        cdef list variable_result_list = <list>cursor.fetchall()
        cdef size_t i
        for i,row in enumerate(variable_result_list):
            variable_result_list[i] = self.__create_variable_tuple_from_row(<tuple>row)
        return variable_result_list

    cdef tuple __create_variable_tuple_from_row(self, tuple row):
        cdef size_t i
        cdef object variable_i
        for i in range(PyTuple_GET_SIZE(row)):
            variable_i = <object>PyDict_GetItem(self.__variables, <object>PyTuple_GET_ITEM(row, i))
            Py_INCREF(variable_i)
            PyTuple_SET_ITEM(row, i, variable_i)
        return row

    cdef str __create_select_query_part(self, list target_variables):
        return ' '.join((
            'SELECT',
            ', '.join(
                f'{self.__target_table_variable_name(i)}.{COLUMN_VARIABLEN_NR}'
                for i in range(len(target_variables))
            ),
            'FROM',
            ', '.join(
                f'{self.__target_relation.name} AS {self.__target_table_variable_name(i)}'
                for i in range(len(target_variables))
            )
        ))

    cdef str __create_join_query_part(self, tuple additional_joins, list target_variables):
        return ' '.join(
            (
                f'INNER JOIN {self.__target_relation.parameter_types[relation_index]} '
                f'{self.__join_table_variable_name(i)} ON {self.__create_on_filter(i, target_variables)}'
            )
            for i, relation_index in enumerate(chain(
                range(len(self.__target_relation.parameter_types)), additional_joins))
        )

    cdef str __create_relation_join_query_part(self, cross_product_filter):
        return ' '.join(set(
            cross_product_filter.yield_relation_join_sql_statements(self.__join_table_variable_name)
        ))

    cdef str __create_on_filter(self, join_table_index, list target_variables):
        join_table_object_name = f'{self.__join_table_variable_name(join_table_index)}.{COLUMN_OBJECT_ID}'
        join_criterion_list = []
        for target_variable_index, variable_objects in enumerate(target_variables):
            try:
                target_table_object_name = (
                    f'{self.__target_table_variable_name(target_variable_index)}.'
                    f'{self.__relation_table_parameter_name(variable_objects.index(join_table_index))}'
                )
                join_criterion_list.append(f'{join_table_object_name} = {target_table_object_name}')
            except ValueError:
                #the join table index does not occur in parameter list of target variable
                #=> we do not need to add a join filter for these two tables
                pass
        return ' AND '.join(join_criterion_list)

    def __create_where_query_part(self, additional_joins: tuple[int], cross_product_filter: CrossProductFilter) -> str:
        nr_of_target_parameters = len(self.__target_relation.parameter_types)
        return ''.join((
            'WHERE ',
            ' AND '.join(
                chain((
                    f'{self.__join_table_variable_name(i)}.{COLUMN_OBJECT_ID} != {self.__join_table_variable_name(nr_of_target_parameters + j)}.{COLUMN_OBJECT_ID}'
                    for j,i in enumerate(additional_joins)
                ), cross_product_filter.yield_sql_where_clauses(self.__join_table_variable_name))
            )
        ))

    def __target_table_variable_name(self, i: int) -> str:
        return f't{i}'

    def __join_table_variable_name(self, i: int) -> str:
        return f'x{i}'

    def __relation_table_parameter_name(self, i: int) -> str:
        return f'p{i}'

    def get_feature_value_bounds(self, object_type: str, feature_name: str) -> tuple:
        hash_key = (object_type, feature_name)
        try:
            return self.__get_feature_value_bounds_cache[hash_key]
        except KeyError:
            feature_bounds = self.__db.execute(f'SELECT MIN({feature_name}), MAX({feature_name}) FROM {object_type}').fetchone()
            self.__get_feature_value_bounds_cache[hash_key] = feature_bounds
            return feature_bounds

    cpdef tuple get_target_variables_grouped_by_parameter_with_true_features(self, int parameter_index, list feature_name_list):
        cdef str feature_name_list_query_part = ''
        if feature_name_list:
            where_query_list = []
            for feature_name in feature_name_list:
                where_query_list.append(f'{feature_name} = 1')
            where_query_part = " AND ".join(where_query_list)
            feature_name_list_query_part = (
                f'INNER JOIN {self.__target_relation.parameter_types[parameter_index]} '
                f'ON {self.__relation_table_parameter_name(parameter_index)} = {COLUMN_OBJECT_ID} '
                f'WHERE {where_query_part} '
            )
        return self.__get_target_variables_by_group_query((
            f'SELECT GROUP_CONCAT({COLUMN_VARIABLEN_NR}) FROM {self.__target_relation.name} '
            f'{feature_name_list_query_part}'
            f'GROUP BY {self.__relation_table_parameter_name(parameter_index)}'
        ))

    cpdef tuple get_target_variables_grouped_by_parameter_with_false_features(self, int parameter_index, list feature_name_list):
        cdef str feature_name_list_query_part = ''
        if feature_name_list:
            where_query_list = []
            for feature_name in feature_name_list:
                where_query_list.append(f'{feature_name} = 0')
            where_query_part = " AND ".join(where_query_list)
            feature_name_list_query_part = (
                f'INNER JOIN {self.__target_relation.parameter_types[parameter_index]} '
                f'ON {self.__relation_table_parameter_name(parameter_index)} = {COLUMN_OBJECT_ID} '
                f'WHERE {where_query_part} '
            )
        return self.__get_target_variables_by_group_query((
            f'SELECT GROUP_CONCAT({COLUMN_VARIABLEN_NR}) FROM {self.__target_relation.name} '
            f'{feature_name_list_query_part}'
            f'GROUP BY {self.__relation_table_parameter_name(parameter_index)}'
        ))

    cdef tuple __get_target_variables_by_group_query(self, str sql_query):
        cdef list raw_result_list = (<list>self.__db.execute(sql_query).fetchall())
        cdef tuple variable_group_tuple = PyTuple_New(PyList_GET_SIZE(raw_result_list))
        cdef tuple variable_tuple
        cdef list variable_nr_str_list
        cdef int i,j
        for j,raw_result in enumerate(raw_result_list):
            variable_nr_str_list = <list>((<str>(PyTuple_GET_ITEM(raw_result, 0))).split(','))
            variable_tuple = PyTuple_New(PyList_GET_SIZE(variable_nr_str_list))
            for i,variable_nr_str in enumerate(variable_nr_str_list):
                variable_i = <object>PyDict_GetItem(self.__variables, int(variable_nr_str))
                Py_INCREF(variable_i)
                PyTuple_SET_ITEM(variable_tuple, i, variable_i)
            Py_INCREF(variable_tuple)
            PyTuple_SET_ITEM(variable_group_tuple, j, variable_tuple)
        return variable_group_tuple
