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

from cpython.ref cimport PyObject
from cpython.dict cimport PyDict_GetItem, PyDict_SetItem

cdef class TermFactory:

    def __init__(self):
        self.positive_terms_cache = {}
        self.negative_terms_cache = {}

    cpdef Term create_term(self, Variable variable, bint negated):
        cdef dict cache
        if negated:
            cache = self.negative_terms_cache
        else:
            cache = self.positive_terms_cache
        cdef PyObject* term = PyDict_GetItem(cache, variable)
        cdef Term new_term
        if term != NULL:
            return <Term>term
        else:
            new_term = Term.__new__(Term, variable, negated)
            PyDict_SetItem(cache, variable, new_term)
            return new_term
