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

from libcpp.unordered_map cimport unordered_map

from prolothar_ca.model.sat.cnf cimport CnfDisjunction
from prolothar_ca.model.sat.term_factory cimport TermFactory
from prolothar_ca.model.sat.constraint_graph cimport ConstraintGraph
from prolothar_ca.model.sat.variable cimport Variable

from prolothar_ca.model.ca.obj cimport CaObject
from prolothar_ca.model.ca.obj cimport CaObjectType
from prolothar_ca.model.ca.constraints.query cimport Query
from prolothar_ca.model.ca.relation cimport CaRelation

cdef class CustomConstraint:
    cdef public double encoded_model_length

    cpdef set compute_cnf_clauses(self, DataGraph datagraph, TermFactory term_factory)

    cpdef CustomConstraint merge(self, CustomConstraint other)

cdef class JoinTargetConstraint:
    cdef public double encoded_model_length
    cdef public list antecedent_terms
    cdef public tuple consequent_term
    cdef public bint expected_value
    cdef Py_hash_t __hash

cdef class SingleTargetConstraint(CustomConstraint):
    cdef public list antecedent_variables
    cdef public int consequent_variable
    cdef public bint expected_value

    cpdef set compute_cnf_clauses(self, DataGraph datagraph, TermFactory term_factory)
    cpdef CustomConstraint merge(self, CustomConstraint other)
    cpdef int count_true_by_consequent(self, object dataset_np)

cdef class Partition:
    cdef public double encoded_model_length
    cdef DataGraph cached_datagraph
    cdef tuple cached_variable_groups

    cpdef tuple compute_variable_groups(self, DataGraph datagraph)
    cdef tuple _compute_variable_groups(self, DataGraph datagraph)
    cpdef to_ca_count_constraint(self, DataGraph datagraph, int lowerbound, int upperbound)

cdef class PartitionByTargetParameterFeaturesAreTrue(Partition):
    cdef int parameter_index
    cdef list feature_name_list
    cdef Py_hash_t __hash

    cdef tuple _compute_variable_groups(self, DataGraph datagraph)
    cpdef to_ca_count_constraint(self, DataGraph datagraph, int lowerbound, int upperbound)
    cdef Query __create_ca_query_for_remaining_target_relation_parameters(self, tuple target_relation_parameter_types)

cdef class PartitionByTargetParameterFeaturesAreFalse(Partition):
    cdef int parameter_index
    cdef list feature_name_list
    cdef Py_hash_t __hash

    cdef tuple _compute_variable_groups(self, DataGraph datagraph)
    cpdef to_ca_count_constraint(self, DataGraph datagraph, int lowerbound, int upperbound)
    cdef Query __create_ca_query_for_remaining_target_relation_parameters(self, tuple target_relation_parameter_types)

cdef class Count(CustomConstraint):

    cdef Partition partition
    cdef int lowerbound
    cdef int upperbound
    cdef int nr_of_target_variables
    cdef dict clause_cache
    cdef unordered_map[int,int] nr_of_untrue_clauses_for_example
    cdef public bint is_trivial

    cpdef set compute_cnf_clauses(self, DataGraph datagraph, TermFactory term_factory)
    cdef __add_cnf_clauses_for_lowerbound(self, set cnf_clauses, tuple variable_group, TermFactory term_factory)
    cdef __add_cnf_clauses_for_upperbound(self, set cnf_clauses, tuple variable_group, TermFactory term_factory)
    cpdef CustomConstraint merge(self, CustomConstraint other)
    cpdef int get_nr_of_target_variables(self)
    cpdef int get_nr_of_untrue_clauses_for_example(self, DataGraph datagraph, int example_id)
    cpdef add_edges_to_constraint_graph(self, ConstraintGraph constraint_graph, DataGraph datagraph)
    cpdef double count_nr_of_solutions(self, DataGraph datagraph)

cdef class DataGraph:

    #dict[tuple[CaObject], Variable]
    cdef dict __target_variables

    #dict[int, Variable]
    cdef dict __variables
    cdef size_t __nr_of_target_variables

    #dict[int, CaRelation]
    cdef dict __target_relations

    cdef dict __create_cnf_clause_cache
    cdef dict __get_feature_value_bounds_cache

    cdef __target_relation
    cdef __db
    cdef str __create_table_suffix
    cdef bint __create_foreign_keys

    cpdef set compute_cnf_clauses(
        self, JoinTargetConstraint target_constraint, tuple additional_joins,
        object cross_product_filter)
    cdef CnfDisjunction __create_cnf_clause(self, tuple variables, JoinTargetConstraint target_constraint)
    cpdef list query_variables(self, JoinTargetConstraint target_constraint, tuple additional_joins, object cross_product_filter)
    cdef tuple __create_variable_tuple_from_row(self, tuple row)
    cdef str __create_select_query_part(self, list target_variables)
    cdef str __create_join_query_part(self, tuple additional_joins, list target_variables)
    cdef str __create_relation_join_query_part(self, object cross_product_filter)
    cdef str __create_on_filter(self, join_table_index, list target_variables)
    cpdef dict get_target_variables(self)
    cpdef Variable get_target_variable(self, CaRelation relation)
    cpdef Variable get_target_variable_by_number(self, object variable_nr)
    cpdef tuple get_target_variables_grouped_by_parameter_with_true_features(self, int parameter_index, list feature_name_list)
    cpdef tuple get_target_variables_grouped_by_parameter_with_false_features(self, int parameter_index, list feature_name_list)
    cdef tuple __get_target_variables_by_group_query(self, str sql_query)
    cpdef clear_caches(self)
    cpdef add_object_node(self, CaObject an_object, CaObjectType object_type, bint commit=?)
    cdef add_object_nodes_from_set(self, set object_set, CaObjectType object_type)