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

from prolothar_ca.ca.methods.custom.itemset_miner.pattern cimport Singleton
from prolothar_ca.ca.methods.custom.itemset_miner.pattern cimport Pattern

cdef class PatternScore:
    cdef public Pattern pattern
    cdef public double lowerbound
    cdef public double score

    cpdef PatternScore extend_by_singleton(self, Singleton singleton, y, size_t nr_of_items)
    cpdef bint is_obsolete_extension_of(self, PatternScore parent)