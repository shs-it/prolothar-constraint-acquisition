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
from libcpp.unordered_set cimport unordered_set

from prolothar_ca.model.sat.term cimport Term
from prolothar_ca.model.sat.variable cimport Variable
from prolothar_ca.model.sat.variable cimport Value
from prolothar_ca.model.sat.constraint_graph cimport ConstraintGraph
from prolothar_ca.model.sat.implication_graph cimport ImplicationGraph

cdef class CnfDisjunction:

    cdef public frozenset __term_ids
    cdef tuple __terms
    cdef Py_hash_t __hash

    cpdef bint contains_variable(self, Variable variable)
    cpdef bint contains_one_of(self, set variable_set)
    cpdef Value value(self)
    cpdef CnfDisjunction without_term(self, Term term)
    cpdef Term get_first_term(self)
    cpdef tuple get_terms(self)
    cpdef size_t get_nr_of_terms(self)
    cdef bint is_informative_implication(self)

cdef class CnfFormula:

    cdef set __disjunctions
    cdef set __variable_nr_set
    cdef set __new_disjunctions
    cdef unordered_map[int,int] __nr_of_untrue_clauses_per_example
    cdef unordered_set[int] __examples_with_updated_nr_of_untrue_clauses
    cdef ConstraintGraph __constraint_graph

    cpdef Value value(self)
    cpdef Value value_after_variable_changed(
            self, Value cnf_value_before_change,
            Variable variable)

    cpdef CnfFormula extend(self, CnfFormula other)
    cpdef CnfFormula resolve_new_clauses(self)
    cpdef CnfFormula fix_variable(self, Variable variable, bint value)
    cpdef CnfFormula fix_literal_clauses(self)
    cpdef CnfFormula without_uninformative_implications(self)
    cpdef set get_variable_nr_set(self)
    cpdef size_t get_nr_of_clauses(self)
    cpdef int get_nr_of_literal_clauses(self)
    cpdef tuple get_untrue_clauses(self)
    cpdef int get_nr_of_untrue_clauses(self)
    cpdef int get_nr_of_untrue_clauses_for_example(self, int example_id)
    cpdef int estimate_nr_of_untrue_clauses_for_example(self, int example_id, int nr_of_sampled_clauses)
    cpdef ImplicationGraph to_implication_graph(self)
    cpdef ConstraintGraph to_constraint_graph(self)
    cdef __add_disjunctions_to_constraint_graph(self, set disjunctions)
    cpdef bint contains_empty_clause(self)
    cpdef CnfFormula clauses_must_contain_one_of(self, set variable_set)
    cpdef dict compute_variables_dict(self)
    cpdef bint has_overlap(self, CnfFormula other)
    cpdef bint contains_clause(self, CnfDisjunction clause)
