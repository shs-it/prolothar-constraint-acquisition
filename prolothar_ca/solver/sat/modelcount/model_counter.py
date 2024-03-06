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

class ModelCounter(ABC):
    """
    counts or estimates (depending on the subclass implementation)
    the number of satisfying assignments to the
    given boolean formula in conjunctive normal form
    """

    @abstractmethod
    def count(self, cnf: CnfFormula) -> int:
        """
        counts or estimates the number of satisfying assignments to the
        given boolean formula in conjunctive normal form

        Parameters
        ----------
        cnf : CnfFormula
            boolean formula in conjunctive normal form for which we want to
            count the number of satisfying assignments

        Returns
        -------
        int
            the number of satisfying assignments (can be estimated depending
            on the implementation) for the given CnfFormula
        """

    @abstractmethod
    def countlog2(self, cnf: CnfFormula) -> float:
        """
        counts or estimates the number of satisfying assignments to the
        given boolean formula in conjunctive normal form

        Parameters
        ----------
        cnf : CnfFormula
            boolean formula in conjunctive normal form for which we want to
            count the number of satisfying assignments

        Returns
        -------
        int
            log2 of the number of satisfying assignments (can be estimated depending
            on the implementation) for the given CnfFormula
        """


