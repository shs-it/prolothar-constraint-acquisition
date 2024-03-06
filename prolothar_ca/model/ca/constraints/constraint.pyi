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

from prolothar_ca.model.ca.dataset import CaDataset, CaExample
from prolothar_ca.model.ca.obj import CaObject

class CaConstraint:

    def holds(self, example: CaExample, variables: dict[str, CaObject]) -> bool:
        """
        decides whether this constraint is fullfilled at the current state of the world

        Parameters
        ----------
        example : dict[str, set[CaObject]]
            represents the current state of the world with all its objects and relations
        variables : dict[str, CaObject]
            named variables that can be used in constraints. constraints can
            use placeholder names instead of real object ids

        Returns
        -------
        bool
            True if the constraints holds at the current state of the world
        """
        ...

    def is_more_restrictive(self, other: 'CaConstraint') -> bool:
        """
        returns True if the object space for which this constraint holds is a subspace
        of another constraint
        """
        ...

    def compute_probability_that_constraint_holds(self, dataset: CaDataset) -> float:
        """
        returns number of examples in the dataset for which the constraint holds
        divided by the total number of examples in the dataset.
        """
        ...

    def count_nr_of_terms(self) -> int:
        """
        counts the number of terms in this constraints. see the individual
        subclasses for the definition how to count terms.
        """
        ...

    def count_nr_of_preconditions(self) -> int:
        """
        counts the number of preconditions in this constraints assuming it is
        used in an AI planning domain. see the individual
        subclasses for the definition how to count terms.
        """
        ...
