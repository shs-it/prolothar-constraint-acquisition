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

from math import log2

from prolothar_ca.model.sat.cnf import CnfFormula
from prolothar_ca.solver.sat.modelcount.model_counter import ModelCounter

class OneSatModelCounter(ModelCounter):
    """
    very simple model counter that works only for CNFs that have exactly one term
    per clause (it is the caller's responsibility to ensure this). this
    model counter also assumes that the CNF is solvable => your responsibility to check this.
    this results in a static model count of 1
    """

    def count(self, cnf: CnfFormula) -> int:
        return 1

    def countlog2(self, cnf: CnfFormula) -> float:
        return 0
