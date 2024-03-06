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

from prolothar_common.models.diintgraph.directed_int_graph cimport DirectedIntGraph

cdef class ImplicationGraph:
    cdef DirectedIntGraph int_graph
    cdef int nr_of_variables

    cpdef add_edge(self, int node_a, int node_b)
    cpdef list find_strongly_connected_components(self)
    cpdef list get_ancestors(self, int variable_nr)
    cdef int variable_to_node_id(self, int variable_nr)
    cdef int node_to_variable_id(self, int node_id)