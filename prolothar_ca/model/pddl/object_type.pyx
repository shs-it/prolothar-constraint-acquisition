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

cdef class ObjectType:

    def __init__(self, str name, ObjectType parent = None):
        self.name = name
        self.parent = parent

    def __eq__(self, other):
        return isinstance(other, ObjectType) and self.name == other.name

    def __hash__(self):
        return hash((self.name, self.parent))

    cpdef int count_nr_of_parents(self):
        cdef int nr_of_parents = 0
        if self.parent is not None:
            nr_of_parents = 1 + self.parent.count_nr_of_parents()
        return nr_of_parents

    cpdef bint is_of_type(self, ObjectType other):
        if self.name == other.name:
            return True
        if self.parent is None:
            return False
        return self.parent.is_of_type(other)

    def __repr__(self):
        return f'ObjectType({self.parent}, {self.name})'

cdef class NoType(ObjectType):
    def __init__(self):
        super().__init__('object')
