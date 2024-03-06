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

from prolothar_ca.model.ca.dataset import CaDataset
from prolothar_ca.ca.noise_generator.noise_generator import NoiseGenerator

class NullNoiseGenerator(NoiseGenerator):
    """
    a pseudo noise generator that does not change the dataset at all
    """

    def apply(self, dataset: CaDataset):
        #as it name suggests, this noise generator does not apply any noise
        pass

    def __repr__(self):
        return 'NullNoiseGenerator()'