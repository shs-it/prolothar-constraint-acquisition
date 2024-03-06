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

from prolothar_ca.ca.dataset_generator.dataset_generator import CaDatasetGenerator
from prolothar_ca.model.ca.constraints.constraint import CaConstraint

from prolothar_ca.model.ca.dataset import CaDataset
from prolothar_ca.model.ca.targets import RelationTarget

class MetaplanningCaDatasetGenerator(CaDatasetGenerator):

    def __init__(
            self, directory: str, action_name_of_interest: str|None = None,
            search_new_valid_actions: bool = False,
            filter_actions_with_duplicate_parameter: bool = False,
            relations_to_ignore: set[str]|None = None,
            nr_of_target_relation_samples: int|None = None,
            nr_of_feature_relation_samples: int|None = None,
            nr_of_threads: int = 1,
            max_trajectory_files: int = -1,
            cache_parsed_trajectories: bool = False,
            disable_gc_during_parsing: bool = False,
            ignore_parameters: list[str]|None = None,
            remove_unused_objects: bool = False): ...

    def generate(
            self, nr_of_positive_examples: int,
            nr_of_negative_examples: int,
            random_seed: int|None = None) -> CaDataset: ...

    def get_ground_truth_constraints(self) -> list[CaConstraint]: ...

    def get_target(self) -> RelationTarget: ...