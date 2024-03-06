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
from cython.parallel import prange
from cpython.list cimport PyList_GET_SIZE
from libc.stdint cimport uint8_t
import numpy as np

from prolothar_common.mdl_utils cimport log2binom

cdef class PatternScore:

    def __init__(self, Pattern pattern, double lowerbound, double score):
        self.pattern = pattern
        self.lowerbound = lowerbound
        self.score = score

    cpdef PatternScore extend_by_singleton(self, Singleton singleton, y, size_t nr_of_items):
        raise NotImplementedError()

    cpdef bint is_obsolete_extension_of(self, PatternScore parent):
        raise NotImplementedError()

    def __lt__(self, other: 'PatternScore'):
        return self.score < other.score or (
            self.score == other.score and
            PyList_GET_SIZE(self.pattern.item_list) < PyList_GET_SIZE(other.pattern.item_list)
        )

    def __repr__(self):
        return f'{self.pattern.item_list}, score={self.score:.2f}, LB={self.lowerbound:.2f}'

cdef class Mdl(PatternScore):
    cdef double data_cost

    def __cinit__(self, Pattern pattern, uint8_t[:] y, size_t nr_of_items):
        cdef double model_cost = log2binom(<int>nr_of_items, <int>PyList_GET_SIZE(pattern.item_list))
        self.pattern = pattern
        self.lowerbound = model_cost + self.__compute_lower_bound_on_data_cost(pattern.cover, y)
        self.data_cost = self.__compute_data_cost(pattern.cover, y)
        self.score = model_cost + self.data_cost

    cpdef Mdl extend_by_singleton(self, Singleton singleton, y, size_t nr_of_items):
        return Mdl.__new__(Mdl, self.pattern.extend_by_singleton(singleton), y, nr_of_items)

    cpdef bint is_obsolete_extension_of(self, PatternScore parent):
        return self.data_cost == (<Mdl>parent).data_cost

    @staticmethod
    def create_for_empty_pattern(y, size_t nr_of_items) -> 'Mdl':
        return Mdl.__new__(
            Mdl, Pattern([], '', np.ones_like(y)),
            y, nr_of_items
        )

    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.nonecheck(False)
    cdef double __compute_lower_bound_on_data_cost(self, uint8_t[:] cover, uint8_t[:] y):
        cdef int lower_bound_nr_of_errors = 0
        cdef int i
        for i in prange(y.shape[0], nogil=True):
            #since the model can only be extended by conjunction, uncovered
            #instances cannot be fixed => lower bound on error
            if cover[i] == 0 and y[i] == 1:
                lower_bound_nr_of_errors += 1
        return log2binom(<int>y.shape[0], lower_bound_nr_of_errors)

    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.nonecheck(False)
    cdef double __compute_data_cost(self, uint8_t[:] cover, uint8_t[:] y):
        cdef int nr_of_errors = 0
        cdef int i
        for i in prange(y.shape[0], nogil=True):
            if cover[i] != y[i]:
                nr_of_errors += 1
        return log2binom(<int>y.shape[0], nr_of_errors)

cdef class Precision(PatternScore):
    def __init__(self, Pattern pattern, y, size_t nr_of_items):
        cdef int predicted_positives = pattern.cover.sum()
        if predicted_positives == 0:
            super().__init__(pattern, 0, 0)
        else:
            super().__init__(
                pattern, -1,
                -np.logical_and(pattern.cover, y).sum() / <double>predicted_positives
            )
    cpdef Precision extend_by_singleton(self, Singleton singleton, y, size_t nr_of_items):
        return Precision(self.pattern.extend_by_singleton(singleton), y, nr_of_items)

    cpdef bint is_obsolete_extension_of(self, PatternScore parent):
        return self.score == parent.score and self.lowerbound == parent.lowerbound

    @staticmethod
    def create_for_empty_pattern(y, size_t nr_of_items) -> 'Precision':
        return Precision.__new__(
            Precision, Pattern([], '', np.ones_like(y)),
            y, nr_of_items
        )

cdef class Effect(PatternScore):
    def __init__(self, Pattern pattern, y, size_t nr_of_items, float alpha = 0.5):
        cdef int true_positives = np.logical_and(pattern.cover, y).sum()
        cdef int false_negatives = np.logical_and(np.logical_not(pattern.cover), y).sum()
        cdef int predicted_positives = np.sum(pattern.cover)
        cdef int predicted_negatives = y.shape[0] - predicted_positives
        super().__init__(
            pattern,
            -max(
                ((alpha+1) / (alpha+2)) -
                ((true_positives+false_negatives-alpha+1) / (y.shape[0]-alpha+2))
                for alpha in range(true_positives+1)
            ),
            -(
                ((true_positives+1) / (predicted_positives+2)) -
                ((false_negatives+1) / (predicted_negatives+2))
            )
        )
    cpdef Effect extend_by_singleton(self, Singleton singleton, y, size_t nr_of_items):
        return Effect(self.pattern.extend_by_singleton(singleton), y, nr_of_items)

    cpdef bint is_obsolete_extension_of(self, PatternScore parent):
        return self.score == parent.score and self.lowerbound == parent.lowerbound

    @staticmethod
    def create_for_empty_pattern(y, size_t nr_of_items) -> 'Effect':
        return Effect.__new__(
            Effect, Pattern([], '', np.ones_like(y)),
            y, nr_of_items
        )