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

class CaFormat(ABC):
    """
    defines the format of a constraint acquisition task. this includes the
    expected format of a dataset and the target concept. the format is used to
    validate input for a constraint acquisition method.
    """

    def __init__(self, base_format: 'CaFormat' = None):
        self.__base_format = base_format

    def validate(self, dataset: CaDataset, target: CaTarget):
        """
        raises an InvalidCaFormat error if the dataset and target deviate from
        the expected format
        """
        if self.__base_format is not None:
            self.__base_format.validate(dataset, target)

    @abstractmethod
    def _validate(self, dataset: CaDataset, target: CaTarget):
        """
        raises an InvalidCaFormat error if the dataset and target deviate from
        the expected format
        """