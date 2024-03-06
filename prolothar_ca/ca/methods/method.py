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

from prolothar_ca.model.ca.dataset import CaDataset
from prolothar_ca.model.ca.targets import CaTarget
from prolothar_ca.model.ca.constraints import CaConstraint

class CaMethod(ABC):
    """
    interface for constraint acquisition methods, i.e. methods that discover
    constraints for optimization / satisfiability problems from valid and invalid
    example solutions
    """

    @abstractmethod
    def acquire_constraints(self, dataset: CaDataset, target: CaTarget) -> list[CaConstraint]:
        """
        discovers constraints that separate positive (valid) from negative (invalid)
        examples in the given dataset. some implementations might only accept
        positive examples while others strictly require the presence of both.

        Parameters
        ----------
        dataset : CaDataset
            a dataset contain examples, which consist of a set of objects with
            features and boolean or numeric relations between objects
        target : CaTarget
            the target concept of an optimization or satisfiability problem
            behind the dataset

        Returns
        -------
        list[CaConstraint]
            a list of constraints on features of objects in the dataset and
            relations between objects that separate positive (valid) from
            negative (invalid) examples

        Raises
        ------
        NotImplementedError
            if the constraint acquisition method does not accept the format of
            the given dataset
        """

    @abstractmethod
    def __repr__(self):
        """
        a representation of the name and parameters of the method used in
        experiment logs and plots
        """