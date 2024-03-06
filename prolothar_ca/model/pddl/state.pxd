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

cdef class State:
    cdef public object problem
    cdef set __true_predicates
    cdef dict __numeric_values

    cpdef bint is_predicate_true(self, object predicate, tuple object_tuple)

    cpdef set_predicate_true(self, object predicate, tuple object_tuple)

    cpdef set_predicate_false(self, object predicate, tuple object_tuple)

    cpdef long get_numeric_fluent_value(self, object numeric_fluent, tuple object_tuple)

    cpdef set_numeric_fluent_value(self, object numeric_fluent, tuple object_tuple, long value)

    cpdef size_t get_nr_of_true_predicates(self)

    cpdef State flat_copy(self)