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

from prolothar_ca.ca.dataset_logger.filebased_dataset_logger import FilebasedDatasetLogger
from prolothar_ca.ca.dataset_generator.multiple_knapsack import ITEM_TYPE, KNAPSACK_TYPE, SIZE_FEATURE, WEIGHT_FEATURE, ASSIGNED_RELATION

from prolothar_ca.model.ca.dataset import CaExample

class MultipleKnapsackDatasetLogger(FilebasedDatasetLogger):
    """
    a dataset logger that is specialized for multiple knapsaack
    """

    def _log_example(self, example: CaExample, index: int, directory: str):
        with open(os.path.join(directory, f'{index}.txt'), 'w') as f:
            f.write(f'Nr of items: {len(example.all_objects_per_type[ITEM_TYPE])}\n')
            for knapsack in sorted(example.all_objects_per_type[KNAPSACK_TYPE], key=lambda k: k.object_id):
                items_str = ' | '.join(
                    f'{item.object_id} ({item.features[WEIGHT_FEATURE]})'
                    for item in example.all_objects_per_type[ITEM_TYPE]
                    if example.get_relation_value(ASSIGNED_RELATION, (knapsack, item))
                )
                f.write(f'{knapsack.object_id} ({knapsack.features[SIZE_FEATURE]}): {items_str}\n')
