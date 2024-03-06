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

from collections import defaultdict
from networkx import Graph as NxGraph
from cpython.dict cimport PyDict_Size, PyDict_GetItem, PyDict_Contains, PyDict_SetItem
from cpython.tuple cimport PyTuple_GET_ITEM
from cpython.set cimport PySet_Add

cdef class TemporaryWithContextManager:
    cdef ConstraintGraph original
    cdef ConstraintGraph extension
    cdef list added_edges
    def __init__(self, ConstraintGraph original, ConstraintGraph extension):
        self.original = original
        self.extension = extension
        self.added_edges = []
    def __enter__(self):
        for variable_from, neighbors in self.extension.get_neighbors_dict().items():
            for variable_to in <set>neighbors:
                if not self.original.contains_edge(<Variable>variable_to, <Variable>variable_from):
                    self.original.add_edge(<Variable>variable_to, <Variable>variable_from)
                    self.added_edges.append((variable_to, variable_from))
    def __exit__(self, type, value, traceback):
        for edge in self.added_edges:
            self.original.remove_edge(
                <Variable>PyTuple_GET_ITEM(edge, 0),
                <Variable>PyTuple_GET_ITEM(edge, 1)
            )

cdef class ConstraintGraph:

    def __init__(self, dict neighbors = None, dict nr_to_variable = None):
        if neighbors is None:
            self.neighbors = {}
        else:
            self.neighbors = neighbors
        if nr_to_variable is None:
            self.nr_to_variable = {}
        else:
            self.nr_to_variable = nr_to_variable

    cpdef size_t number_of_nodes(self):
        return PyDict_Size(self.neighbors)

    cpdef add_node_if_not_existing(self, Variable variable):
        if not PyDict_Contains(self.neighbors, variable):
            PyDict_SetItem(self.neighbors, variable, set())
            PyDict_SetItem(self.nr_to_variable, variable.nr, variable)

    cpdef add_edge(self, Variable variable_a, Variable variable_b):
        neighbors_a = PyDict_GetItem(self.neighbors, variable_a)
        if neighbors_a != NULL:
            PySet_Add(<object>neighbors_a, variable_b)
        else:
            PyDict_SetItem(self.neighbors, variable_a, {variable_b})
            PyDict_SetItem(self.nr_to_variable, variable_a.nr, variable_a)
        neighbors_b = PyDict_GetItem(self.neighbors, variable_b)
        if neighbors_b != NULL:
            PySet_Add(<object>neighbors_b, variable_a)
        else:
            PyDict_SetItem(self.neighbors, variable_b, {variable_a})
            PyDict_SetItem(self.nr_to_variable, variable_b.nr, variable_b)

    cpdef remove_edge(self, Variable variable_a, Variable variable_b):
        (<set>self.neighbors[variable_a]).discard(variable_b)
        (<set>self.neighbors[variable_b]).discard(variable_a)

    cpdef bint contains_edge(self, Variable variable_a, Variable variable_b):
        try:
            return variable_b in (<set>self.neighbors[variable_a])
        except KeyError:
            return False

    cpdef dict get_neighbors_dict(self):
        return self.neighbors

    cpdef remove_node_with_variable_nr(self, int variable_nr):
        cdef set neighbors
        try:
            variable = self.nr_to_variable.pop(variable_nr)
            neighbors = <set>self.neighbors.pop(variable)
            for neighbor in neighbors:
                (<set>self.neighbors[neighbor]).discard(variable)
        except KeyError:
            #node already removed
            pass

    cpdef set get_neighbors(self, Variable variable):
        return <set>self.neighbors[variable]

    cpdef list connected_components(self):
        cdef list components = []
        cdef set seen = set()
        for variable in <dict>self.neighbors:
            if variable not in seen:
                component = self.find_all_connected_variables(variable)
                seen.update(component)
                components.append(component)
        return components

    cpdef set find_all_connected_variables(self, Variable variable):
        cdef set connected = set()
        cdef set marked = set()
        marked.add(variable)
        cdef list next_variable_list = [variable]
        cdef next_variable
        while next_variable_list:
            next_variable = next_variable_list.pop()
            connected.add(next_variable)
            for neighbor in (<set>self.neighbors[next_variable]):
                if neighbor not in marked:
                    marked.add(neighbor)
                    next_variable_list.append(neighbor)
        return connected

    cpdef list degree_per_node(self):
        """
        returns a list of tuples (variable: Variable, degree: int)
        """
        return [
            (node, len(neighbors))
            for node, neighbors in self.neighbors.items()
        ]

    cpdef size_t get_degree(self, Variable variable):
        return len(self.neighbors[variable])

    cpdef double compute_average_degree(self):
        """
        computes the average number of neighbors per node
        """
        cdef size_t double_of_nr_of_edges = 0
        for neighborset in self.neighbors.values():
            double_of_nr_of_edges += len(<set>neighborset)
        return double_of_nr_of_edges / self.number_of_nodes()

    def to_networkx(self) -> NxGraph:
        graph = NxGraph()
        for variable, neighborset in self.neighbors.items():
            for neighbor in neighborset:
                graph.add_edge(variable, neighbor)
        return graph

    cpdef ConstraintGraph copy(self):
        cdef dict copied_neighbors = {}
        for node, neighbor_set in self.neighbors.items():
            copied_neighbors[node] = set(neighbor_set)
        return ConstraintGraph(copied_neighbors, dict(self.nr_to_variable))

    def temporary_with(self, ConstraintGraph other):
        return TemporaryWithContextManager(self, other)
