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

from statistics import mean
from math import log2
from prolothar_ca.model.sat.cnf import CnfFormula
from prolothar_ca.solver.sat.modelcount.model_counter import ModelCounter

class AverageModelCounter(ModelCounter):
    """
    combines multiple ModelCounter instances by taking their average
    """
    def __init__(self, model_counter_list: list[ModelCounter]):
        self.model_counter_list = model_counter_list

    def count(self, cnf: CnfFormula) -> int:
        return round(mean(
            model_counter.count(cnf)
            for model_counter in self.model_counter_list
        ))

    def countlog2(self, cnf: CnfFormula) -> float:
        return log2(max(1, mean(
            model_counter.count(cnf)
            for model_counter in self.model_counter_list
        )))
