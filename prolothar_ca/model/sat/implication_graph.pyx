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

cimport cython
from cython.operator cimport dereference, preincrement
from libcpp.list cimport list as cpplist

cdef class TemporaryWithContextManager:
    cdef ImplicationGraph original
    cdef ImplicationGraph extension
    cdef cpplist[int] added_edges_from
    cdef cpplist[int] added_edges_to
    def __init__(self, ImplicationGraph original, ImplicationGraph extension):
        self.original = original
        self.extension = extension
    def __enter__(self):
        cdef int i, j
        for i in range(self.extension.nr_of_variables):
            for j in self.extension.int_graph.get_ancestors(i):
                if not self.original.int_graph.contains_edge(i, j):
                    self.original.int_graph.add_edge(i, j)
                    self.added_edges_from.push_back(i)
                    self.added_edges_to.push_back(j)
    def __exit__(self, type, value, traceback):
        cdef cpplist[int].iterator it_from = self.added_edges_from.begin()
        cdef cpplist[int].iterator it_to = self.added_edges_to.begin()
        while it_from != self.added_edges_from.end():
            self.original.int_graph.remove_edge(dereference(it_from), dereference(it_to))
            preincrement(it_from)
            preincrement(it_to)

cdef class ImplicationGraph:

    def __cinit__(self, int nr_of_variables):
        self.int_graph = DirectedIntGraph(2 * nr_of_variables)
        self.nr_of_variables = nr_of_variables

    cpdef add_edge(self, int node_a, int node_b):
        self.int_graph.add_edge(
            self.variable_to_node_id(node_a),
            self.variable_to_node_id(node_b)
        )

    @cython.wraparound(False)
    @cython.nonecheck (False)
    @cython.boundscheck(False)
    cpdef list find_strongly_connected_components(self):
        cdef list components = self.int_graph.find_strongly_connected_components()
        cdef component
        cdef int i
        for component in components:
            for i in range(len(<list>component)):
                (<list>component)[i] = self.node_to_variable_id((<int>(<list>component)[i]))
        return components

    cpdef list get_ancestors(self, int variable_nr):
        cdef list ancestors = []
        cdef int node_id
        for node_id in self.int_graph.get_ancestors(self.variable_to_node_id(variable_nr)):
            ancestors.append(self.node_to_variable_id(node_id))
        return ancestors

    cdef int variable_to_node_id(self, int variable_nr):
        if variable_nr < 0:
            return -variable_nr - 1 + self.nr_of_variables
        else:
            return variable_nr - 1

    cdef int node_to_variable_id(self, int node_id):
        if node_id < self.nr_of_variables:
            return node_id + 1
        else:
            return -(node_id - self.nr_of_variables + 1)

    def temporary_with(self, ImplicationGraph other):
        return TemporaryWithContextManager(self, other)

