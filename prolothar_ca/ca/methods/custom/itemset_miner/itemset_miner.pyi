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

from prolothar_ca.ca.methods.custom.itemset_miner.score import Mdl

class ItemsetMiner:
    def __init__(
            self, max_pattern_length: int = 3, downsample_itemset_majority_class: bool = False,
            crossover_found_itemsets: bool = False, random_seed: int|None = None,
            singleton_positive_support_threshold: float = 0.0,
            verbose: bool = True, pattern_score = Mdl): ...

    def find_patterns(self, positive_list: list[list[str]], negative_list: list[list[str]]) -> list[list[str]]: ...