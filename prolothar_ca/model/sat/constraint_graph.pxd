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

from prolothar_ca.model.sat.variable cimport Variable

cdef class ConstraintGraph:
    cdef dict neighbors
    cdef dict nr_to_variable

    cpdef add_node_if_not_existing(self, Variable variable)
    cpdef remove_node_with_variable_nr(self, int variable_nr)
    cpdef add_edge(self, Variable variable_a, Variable variable_b)
    cpdef bint contains_edge(self, Variable variable_a, Variable variable_b)
    cpdef remove_edge(self, Variable variable_a, Variable variable_b)
    cpdef size_t number_of_nodes(self)
    cpdef set get_neighbors(self, Variable variable)
    cpdef dict get_neighbors_dict(self)
    cpdef list connected_components(self)
    cpdef list degree_per_node(self)
    cpdef size_t get_degree(self, Variable variable)
    cpdef double compute_average_degree(self)
    cpdef set find_all_connected_variables(self, Variable variable)
    cpdef ConstraintGraph copy(self)
