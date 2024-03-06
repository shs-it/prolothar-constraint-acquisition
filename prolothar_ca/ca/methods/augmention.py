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

from copy import deepcopy
from prolothar_common import validate

from prolothar_ca.ca.methods.method import CaMethod
from prolothar_ca.model.ca.constraints.constraint import CaConstraint
from prolothar_ca.model.ca.targets import BooleanRelationListTarget, CaTarget
from prolothar_common.random_utils import BufferingChoice

from prolothar_ca.model.ca import CaDataset

class NegativeExamplesAugmentationAdaptor(CaMethod):
    """
    adapter that enables usage of supervised constraint acquisition methods in
    an unsupervised setting (only positive examples). the adapter creates as many
    random examples as existing examples in the dataset and assumes they are
    invalid solutions
    """

    def __init__(self, supervised_ca_method: CaMethod, random_seed: int|None = None):
        """
        configures the parameters of Hassle

        Parameters
        ----------
        supervised_ca_method : CaMethod
            the actual constraint aquisition method
        random_seed : int | None, optional
            seed for the random generator that is used to create synthetic
            negative examples, by default None
        """
        validate.is_not_none(supervised_ca_method)
        self.__supervised_ca_method = supervised_ca_method
        self.__coin_flip = BufferingChoice([True, False], [0.5, 0.5], seed=random_seed)

    def acquire_constraints(self, dataset: CaDataset, target: CaTarget) -> list[CaConstraint]:
        extended_dataset, target_relations_names = target.transform_to_boolean_relations(dataset)
        extended_dataset = deepcopy(extended_dataset)
        positive_example = next(iter(extended_dataset))
        for _ in (e for e in extended_dataset if e.is_valid_solution):
            random_example = deepcopy(positive_example)
            for target_relation_name in target_relations_names:
                for target_relation in random_example.relations[target_relation_name]:
                    target_relation.value = self.__coin_flip.next_sample()
            #here we assume, that a random example has an almost 100% chance of being invalid
            random_example.is_valid_solution = False
            extended_dataset.add_example(random_example)
        return self.__supervised_ca_method.acquire_constraints(
            extended_dataset, BooleanRelationListTarget(target_relations_names))

    def __repr__(self):
        return f'NegAugm({self.__supervised_ca_method})'
