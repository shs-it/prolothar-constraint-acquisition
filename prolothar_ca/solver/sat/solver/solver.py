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

from abc import ABC, abstractmethod

from prolothar_ca.model.sat.cnf import CnfFormula
from prolothar_ca.model.sat.variable import Variable, Value

class SatSolver(ABC):
    """
    abstract interface of a SAT solver
    """

    @abstractmethod
    def solve_cnf(self, cnf: CnfFormula) -> dict[Variable, Value]|None:
        """
        solves the given boolean formula in conjunctive normal form

        Parameters
        ----------
        cnf : CnfFormula
            boolean formula in conjunctive normal form

        Returns
        -------
        dict[Variable, Value]|None
            None if there is no solution, otherwise an assignment that satisfies
            the given formula
        """

    @abstractmethod
    def is_cnf_satisfiable(self, cnf: CnfFormula) -> bool:
        """
        returns True iff there is a solution to the given CnfFormula
        """
