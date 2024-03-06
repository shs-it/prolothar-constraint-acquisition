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

import os
from abc import abstractmethod

from prolothar_ca.ca.dataset_logger.dataset_logger import DatasetLogger

from prolothar_ca.model.ca.dataset import CaDataset, CaExample

class FilebasedDatasetLogger(DatasetLogger):
    """
    template for dataset loggers that log to files
    """

    def __init__(self, directory: str):
        """
        creates a new FilebasedDatasetLogger with a given directory to save
        the log files

        Parameters
        ----------
        directory : str
            directory in which this logger saves its log files
        """
        self.__directory = directory

    def get_directory_for_positive_examples(self) -> str:
        return self.__directory_for_positive_examples

    def get_directory_for_negative_examples(self) -> str:
        return self.__directory_for_negative_examples

    def log_dataset(self, dataset: CaDataset, dataset_name: str):
        dataset_directory = self.get_dataset_directory(dataset_name)
        os.mkdir(dataset_directory)
        positive_directory = self.get_positive_examples_directory(dataset_name)
        os.mkdir(positive_directory)
        negative_directory = self.get_negative_examples_directory(dataset_name)
        os.mkdir(negative_directory)
        for i,example in enumerate(dataset):
            if example.is_valid_solution:
                self._log_example(example, i, positive_directory)
            else:
                self._log_example(example, i, negative_directory)

    def get_dataset_directory(self, dataset_name: str) -> str:
        return os.path.join(self.__directory, dataset_name)

    def get_positive_examples_directory(self, dataset_name: str) -> str:
        return os.path.join(self.get_dataset_directory(dataset_name), 'positive_examples')

    def get_negative_examples_directory(self, dataset_name: str) -> str:
        return os.path.join(self.get_dataset_directory(dataset_name), 'negative_examples')

    @abstractmethod
    def _log_example(self, example: CaExample, index: int, directory: str):
        """
        log the given example to the given directory into a file.
        index is a unique number for the given example in this directory.
        """




