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

from abc import abstractmethod

from prolothar_ca.model.ca.dataset import CaDataset
from prolothar_ca.model.ca.example import CaExample
from prolothar_ca.ca.noise_generator.noise_generator import NoiseGenerator

class SingleExampleNoiseGenerator(NoiseGenerator):

    def apply(self, dataset: CaDataset):
        self.validate_usage_on_dataset(dataset)
        for example in dataset:
            self.apply_on_example(example)

    @abstractmethod
    def validate_usage_on_dataset(self, dataset: CaDataset):
        """
        throws a ValueError if this noise generator is not applicable on the given dataset
        """

    @abstractmethod
    def apply_on_example(self, example: CaExample):
        """
        applies noise to the given example
        """