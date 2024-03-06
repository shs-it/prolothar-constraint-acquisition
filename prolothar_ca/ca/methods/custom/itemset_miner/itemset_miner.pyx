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

cdef extern from "<float.h>":
    const double DBL_MAX
from numpy import uint8, zeros
from libc.stdint cimport uint8_t
cimport cython

from typing import List, Set
from itertools import chain
from random import Random
import numpy as np
from heapq import heappush, heappop
from tqdm import tqdm

from prolothar_common import validate

from prolothar_ca.ca.methods.custom.itemset_miner.pattern import Singleton
from prolothar_ca.ca.methods.custom.itemset_miner.pattern cimport Singleton
from prolothar_ca.ca.methods.custom.itemset_miner.pattern import Pattern
from prolothar_ca.ca.methods.custom.itemset_miner.score import Mdl

cdef class ItemsetMiner:

    def __init__(
            self, max_pattern_length: int = 3, downsample_itemset_majority_class: bool = False,
            crossover_found_itemsets: bool = False, random_seed: int|None = None,
            singleton_positive_support_threshold: float = 0.0,
            verbose: bool = True, pattern_score=Mdl):
        validate.greater(max_pattern_length, 1)
        validate.in_right_open_interval(singleton_positive_support_threshold, 0, 1)
        self.__max_pattern_length = max_pattern_length
        self.__downsample_itemset_majority_class = downsample_itemset_majority_class
        self.__verbose = verbose
        self.__pattern_score = pattern_score
        self.__random_seed = random_seed
        self.__crossover_found_itemsets = crossover_found_itemsets
        self.__singleton_positive_support_threshold = singleton_positive_support_threshold

    def find_patterns(self, positive_list: List[List[str]], negative_list: List[List[str]]) -> List[List[str]]:
        positive_list, negative_list = self.__downsample_majority_class_if_necessary(positive_list, negative_list)
        y = np.concatenate((
            np.ones((len(positive_list), ), dtype=bool),
            np.zeros((len(negative_list), ), dtype=bool)
        ))
        all_items = set(
            item for transaction in chain(positive_list, negative_list) for
            item in transaction
        )
        singleton_patterns = self.__create_singleton_patterns(positive_list, negative_list, all_items)
        if self.__verbose:
            print(f'there are {len(singleton_patterns)} singleton patterns')

        found_patterns = []
        cdef PatternScore pattern_score
        while len(y) > 0:
            pattern_score = self.__find_next_pattern(singleton_patterns, y)
            if pattern_score.pattern.item_list and pattern_score.pattern.covers_at_least_one_example():
                found_patterns.append(pattern_score.pattern)
                singleton_patterns, y = self.__remove_covered_rows(
                    pattern_score.pattern, singleton_patterns, y)
            else:
                break
        cdef list found_pattern_list = [pattern.item_list for pattern in found_patterns]
        if self.__crossover_found_itemsets and len(found_pattern_list) > 1:
            found_pattern_list = self.__do_crossover_on_found_itemsets(found_pattern_list)
        return found_pattern_list

    cdef tuple __downsample_majority_class_if_necessary(self, list positive_list, list negative_list):
        if not self.__downsample_itemset_majority_class or len(positive_list) == len(negative_list):
            return positive_list, negative_list
        if len(positive_list) > len(negative_list):
            Random(self.__random_seed).shuffle(positive_list)
            return positive_list[:len(negative_list)], negative_list
        else:
            Random(self.__random_seed).shuffle(negative_list)
            return positive_list, negative_list[:len(positive_list)]

    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.initializedcheck(False)
    cdef list __create_singleton_patterns(
        self, list positive_list, list negative_list, set all_items):
        """
        def __create_singleton_patterns(
            self, positive_list: List[List[str]], negative_list: List[List[str]],
            all_items: Set[str]) -> List[Singleton]:
        """
        cdef list singleton_patterns = []
        cdef list transaction
        cdef object progress_bar
        rejected_singletons = 0
        cdef object cover
        cdef uint8_t [:] cover_view
        cdef size_t i
        cdef size_t positive_matches
        if self.__verbose:
            progress_bar = tqdm(desc='create singletons (rejected 0)', total=len(all_items))
        for item in <set>all_items:
            i = 0
            positive_matches = 0
            cover = zeros((len(positive_list) + len(negative_list),), dtype=uint8)
            cover_view = cover
            for transaction in <list>positive_list:
                if item in transaction:
                    cover_view[i] = 1
                    positive_matches += 1
                i += 1
            if positive_matches / len(positive_list) < self.__singleton_positive_support_threshold:
                if self.__verbose:
                    rejected_singletons += 1
                    progress_bar.desc = f'create singletons (rejected {rejected_singletons})'
                    progress_bar.update()
                continue
            for transaction in <list>negative_list:
                if item in transaction:
                    cover_view[i] = 1
                i += 1
            singleton_patterns.append(Singleton(item, cover))
            if self.__verbose:
                progress_bar.update()
        return singleton_patterns

    cdef PatternScore __find_next_pattern(self, list singleton_patterns, y: np.ndarray):
        cdef list candidate_queue = []
        cdef size_t nr_of_items = len(singleton_patterns)
        empty_pattern = self.__pattern_score.create_for_empty_pattern(y, nr_of_items)
        if self.__verbose:
            print(f'find next pattern. empty pattern has score {empty_pattern.score:.2f}')
        heappush(candidate_queue, (empty_pattern.lowerbound, False, empty_pattern))
        cdef PatternScore next_candidate
        cdef double min_score = DBL_MAX
        while candidate_queue:
            _, is_leaf, next_candidate = heappop(candidate_queue)
            if is_leaf:
                if self.__verbose:
                    print(f'found next pattern {next_candidate}. {len(candidate_queue)} remaining candidates rejected.')
                return next_candidate
            #prevent waste of memory by only storing necessary candidates
            if next_candidate.score < min_score:
                min_score = next_candidate.score
                heappush(candidate_queue, (next_candidate.score, True, next_candidate))
            if len(next_candidate.pattern.item_list) != self.__max_pattern_length:
                for singleton in singleton_patterns:
                    #candidate "A and B" is the same than "B and A". We create only one of them
                    if (<Singleton>singleton).item > next_candidate.pattern.max_item:
                        child = next_candidate.extend_by_singleton(<Singleton>singleton, y, nr_of_items)
                        if len(child.pattern.item_list) == self.__max_pattern_length:
                            #it is clear that the pattern will not be extended anymore => we don't need a lowerbound
                            child.lowerbound = child.score
                        #prevent waste of memory by storing candidates with lowerbound worse
                        #than best known actual score
                        if child.lowerbound < min_score and not child.is_obsolete_extension_of(next_candidate):
                            heappush(candidate_queue, (child.lowerbound, False, child))

    def __remove_covered_rows(
            self, pattern: Pattern, singleton_patterns: List[Pattern],
            y: np.ndarray) -> tuple[List[Pattern], np.ndarray]:
        selector = pattern.cover == 0
        y = y[selector]
        for singleton in singleton_patterns:
            singleton.cover = singleton.cover[selector]
        return singleton_patterns, y

    cdef list __do_crossover_on_found_itemsets(self, list found_pattern_list):
        cdef list crossovered_list = list(found_pattern_list)
        for pattern_a in found_pattern_list:
            for pattern_b in found_pattern_list:
                if pattern_a is not pattern_b:
                    crossovered_list.extend(self.__crossover_itemsets(pattern_a, pattern_b))
        cdef set all_found_items = set()
        for pattern in found_pattern_list:
            all_found_items.update(<list>pattern)
        for item_a in all_found_items:
            for item_b in all_found_items:
                if item_a is not item_b:
                    pattern = [item_a, item_b]
                    pattern.sort()
                    if pattern not in crossovered_list:
                        crossovered_list.append(pattern)
        return crossovered_list

    cdef list __crossover_itemsets(self, list pattern_a, list pattern_b):
        cdef list crossovered_list = []
        cdef int i,j
        cdef list new_pattern
        for i in range(len(pattern_a)):
            for j in range(len(pattern_b)):
                new_pattern = []
                new_pattern.extend(pattern_a[:i])
                new_pattern.extend(pattern_a[i+1:])
                new_pattern.append(pattern_b[j])
                crossovered_list.append(new_pattern)
        return crossovered_list

