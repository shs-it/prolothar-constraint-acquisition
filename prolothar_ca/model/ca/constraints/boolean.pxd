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

from prolothar_ca.model.ca.constraints.constraint cimport CaConstraint
from prolothar_ca.model.ca.example cimport CaExample
from prolothar_ca.model.ca.relation cimport CaRelationType

cdef class RelationIsTrue(CaConstraint):
    cdef public CaRelationType __relation_type
    #tuple[str]
    cdef public tuple __object_id_list

    cpdef bint holds(self, CaExample example, dict variables)

    cpdef str get_relation_name(self)

cdef class RelationIsFalse(CaConstraint):
    cdef public CaRelationType __relation_type
    #tuple[str]
    cdef public tuple __object_id_list

    cpdef bint holds(self, CaExample example, dict variables)

cdef class Not(CaConstraint):
    cdef CaConstraint __constraint

    cpdef bint holds(self, CaExample example, dict variables)

cdef class BooleanFeatureIsTrue(CaConstraint):
    cdef str __object_type
    cdef str __object_id
    cdef str __feature_name

    cpdef bint holds(self, CaExample example, dict variables)

cdef class BooleanFeatureIsFalse(CaConstraint):
    cdef str __object_type
    cdef str __object_id
    cdef str __feature_name

    cpdef bint holds(self, CaExample example, dict variables)