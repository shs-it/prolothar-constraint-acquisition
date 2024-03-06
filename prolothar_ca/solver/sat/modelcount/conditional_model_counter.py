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

from typing import Callable
from math import log2
from prolothar_ca.model.sat.cnf import CnfFormula
from prolothar_ca.solver.sat.modelcount.model_counter import ModelCounter

class ConditionalModelCounter(ModelCounter):
    """
    combines two ModelCounter instances where the second model counter can
    outvote the first one depending on the output of the first counter
    """
    def __init__(
            self, first_model_counter: ModelCounter, second_model_counter: ModelCounter,
            trust_first_model_counter: Callable[[int, CnfFormula], bool]):
        self.first_model_counter = first_model_counter
        self.second_model_counter = second_model_counter
        self.trust_first_model_counter = trust_first_model_counter

    def count(self, cnf: CnfFormula) -> int:
        count = self.first_model_counter.count(cnf)
        if self.trust_first_model_counter(count, cnf):
            return count
        else:
            return self.second_model_counter.count(cnf)

    def countlog2(self, cnf: CnfFormula) -> float:
        return log2(max(1, self.count(cnf)))
