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

class DatasetLogger(ABC):
    """
    interface for loggers that save a CaDataset for later inspection
    """

    @abstractmethod
    def log_dataset(self, dataset: CaDataset, dataset_name: str):
        """
        logs the given dataset for later inspection

        Parameters
        ----------
        dataset : CaDataset
            the dataset to be logged for later inspection
        dataset_name : str
            identifying name of the dataset that will appear in the log
        """