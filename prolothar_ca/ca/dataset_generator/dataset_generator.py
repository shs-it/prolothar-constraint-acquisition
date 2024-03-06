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
from random import Random
from tqdm import trange

from prolothar_ca.model.ca.dataset import CaDataset
from prolothar_ca.model.ca.example import CaExample
from prolothar_ca.model.ca.constraints import CaConstraint
from prolothar_ca.model.ca.targets import CaTarget

class CaDatasetGenerator(ABC):

    def generate(
        self, nr_of_positive_examples: int,
        nr_of_negative_examples: int,
        random_seed: int|None = None) -> CaDataset:
        """
        generates a new CaDataset based on Sudoku

        Parameters
        ----------
        nr_of_positive_examples : int
            nr of valid solutions that should be generated
        nr_of_negative_examples : int
            nr of invalid solution that should be generated
        random_seed : int | None, optional
            for reproducibility, by default None

        Returns
        -------
        CaDataset
            constraint acqusition dataset with the specified number of
            positive and negative examples
        """
        random_generator = Random(random_seed)
        dataset = self._create_empty_dataset()
        for _ in trange(nr_of_positive_examples, desc='generate positive examples'):
            dataset.add_example(self._generate_positive_example(random_generator))
        for _ in trange(nr_of_negative_examples, desc='generate negative examples'):
            dataset.add_example(self._generate_negative_example(random_generator))
        return dataset

    @abstractmethod
    def _create_empty_dataset(self) -> CaDataset:
        """
        create a new CaDataset. its definition depends on the subclass that
        creates a CaDataset for a specific problem
        """

    @abstractmethod
    def _generate_positive_example(self, random_generator: Random) -> CaExample:
        """
        generates a new positive example, i.e. an example that is a valid solution or action
        """

    @abstractmethod
    def _generate_negative_example(self, random_generator: Random) -> CaExample:
        """
        generates a new negative example, i.e. an example that is not valid solution or action
        """

    @abstractmethod
    def get_ground_truth_constraints(self) -> list[CaConstraint]:
        """
        returns a list of ground-truth constraints if known, otherwise
        returns an empty list
        """

    @abstractmethod
    def get_target(self) -> CaTarget:
        """
        defines the target concept of this dataset, i.e. for which we want
        to acquire the constraints
        """
