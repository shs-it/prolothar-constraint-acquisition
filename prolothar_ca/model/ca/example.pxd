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

from prolothar_ca.model.ca.obj cimport CaObject
from prolothar_ca.model.ca.relation cimport CaRelation

cdef class CaExample:
    #dict[str, set[CaObject]]
    cdef public dict all_objects_per_type
    #dict[str, set[CaRelation]]
    cdef public dict relations
    cdef public bint is_valid_solution
    cdef dict __relation_value_per_type_and_objects
    cdef dict __objects_per_type_and_id

    cdef __reinit(self)
    cpdef CaObject get_object_by_type_and_id(self, type_name, object_id)
    cdef bint get_boolean_relation_value(self, relation_type_name, parameters)
    cpdef add_relation(self, CaRelation relation, bint validate = ?)
    cpdef remove_all_objects_not_in_set(self, set objects_to_keep)