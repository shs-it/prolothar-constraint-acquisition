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

from prolothar_ca.ca.methods.custom.itemset_miner.score cimport PatternScore

cdef class ItemsetMiner:
    cdef int __max_pattern_length
    cdef bint __verbose
    cdef bint __downsample_itemset_majority_class
    cdef bint __crossover_found_itemsets
    cdef __pattern_score
    cdef __random_seed
    cdef float __singleton_positive_support_threshold

    cdef PatternScore __find_next_pattern(self, list singleton_patterns, y)
    cdef tuple __downsample_majority_class_if_necessary(self, list positive_list, list negative_list)
    cdef list __do_crossover_on_found_itemsets(self, list found_pattern_list)
    cdef list __crossover_itemsets(self, list pattern_a, list pattern_b)
    cdef list __create_singleton_patterns(self, list positive_list, list negative_list, set all_items)