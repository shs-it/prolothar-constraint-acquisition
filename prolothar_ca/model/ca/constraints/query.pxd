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
from prolothar_ca.model.ca.obj cimport CaObject

cdef class Query:

    cpdef list evaluate(self, CaExample example, dict variables)
    cpdef int count_nr_of_terms(self)

cdef class AllOfTypeOrderBy(Query):
    cdef str type_name
    cdef str variable_name
    #: by is of type "str|list[str]"
    cdef by
    cdef __sort_function

    cpdef list evaluate(self, CaExample example, dict variables)