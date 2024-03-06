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

from collections import defaultdict
from math import floor, log2
from statistics import mean

from prolothar_ca.model.sat.cnf import CnfFormula
from prolothar_ca.solver.sat.modelcount.model_counter import ModelCounter

class TwoSatFirstMomentBound(ModelCounter):
    """
    gives with high probability a lower bound on the number of solutions of a CNF
    by counting in how many terms a variable occurs on average.

    see equation 1.4 of
    https://www.researchgate.net/publication/348567065_The_number_of_satisfying_assignments_of_random_2-SAT_formulas/link/61a5fc30743d9629db252f91/download
    """

    def count(self, cnf: CnfFormula) -> int:
        return floor(2**self.__compute_log2_lower_bound(cnf))

    def countlog2(self, cnf: CnfFormula) -> float:
        return max(0, self.__compute_log2_lower_bound(cnf))

    def __compute_log2_lower_bound(self, cnf: CnfFormula) -> float:
        nr_of_variables = max(cnf.get_variable_nr_set())
        count_clauses_per_variable = {i+1: 0 for i in range(nr_of_variables)}
        for clause in cnf.iter_clauses():
            for term in clause:
                count_clauses_per_variable[term.variable.nr] += 1
        d = mean(count_clauses_per_variable.values())
        return nr_of_variables * (1 - d + d / 2 * log2(3))