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

from numpy import uint8, zeros
cimport cython
from libc.stdint cimport uint8_t
from cython.parallel import prange

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.initializedcheck(False)
cdef compute_combined_cover(uint8_t[:] cover_a, uint8_t[:] cover_b):
    combined_cover = zeros((cover_a.shape[0],), dtype=uint8)
    cdef uint8_t [:] combined_cover_view = combined_cover
    cdef int i
    for i in prange(cover_a.shape[0], nogil=True):
        if cover_a[i] == 1 and cover_b[i] == 1:
            combined_cover_view[i] = 1
    return combined_cover

cdef class Singleton:
    def __init__(self, str item, cover):
        self.item = item
        self.cover = cover

cdef class Pattern:
    def __cinit__(self, list item_list, str max_item, cover):
        self.item_list = item_list
        self.cover = cover
        self.max_item = max_item

    cpdef Pattern extend_by_singleton(self, Singleton singleton):
        #https://stackoverflow.com/questions/47859482/what-is-the-fastest-way-to-make-a-shallow-copy-of-list-in-python3-5
        cdef list extended_item_list = [*self.item_list]
        extended_item_list.append(singleton.item)
        return Pattern.__new__(Pattern,
            extended_item_list,
            singleton.item,
            compute_combined_cover(self.cover, singleton.cover)
        )

    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.initializedcheck(False)
    cpdef bint covers_at_least_one_example(self):
        cdef uint8_t[:] cover_view = self.cover
        cdef int i
        for i in range(cover_view.shape[0]):
            if cover_view[i] == 1:
                return True
        return False