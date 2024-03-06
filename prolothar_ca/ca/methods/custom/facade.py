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

from prolothar_ca.ca.methods.method import CaMethod
from prolothar_ca.solver.sat.modelcount.mc2 import MC2
from prolothar_ca.model.ca import CaDataset
from prolothar_ca.model.ca.constraints.constraint import CaConstraint
from prolothar_ca.model.ca.targets import CaTarget
from prolothar_ca.ca.methods.custom.itemset_miner import ItemsetMiner
from prolothar_ca.ca.methods.custom.homogenous_ca import HomogenousCustomCa
from prolothar_ca.ca.methods.custom.planning_ca import PlanningCustomCa

class URPiLs(CaMethod):
    """
    Unveil Rules from Positive Labels

    #other names:
    #Constraintine
    #Cnstrnts
    #CoCoFin (Compressing Constraints Finder)
    """

    def __init__(
            self, verbose: bool = False,
            implication_pairs_limit: int|None = None,
            downsample_itemset_majority_class: bool = False,
            crossover_found_itemsets: bool = True,
            planning_dataset: bool = False,
            random_seed: int|None = None,
            max_filter_conjunction_length: int = 3,
            max_nr_of_target_zeros: int = -1,
            singleton_positive_support_threshold: float = 0,
            nr_of_sampled_clauses_for_error: int = 0):
        if planning_dataset:
            if nr_of_sampled_clauses_for_error != 0:
                raise NotImplementedError('nr_of_sampled_clauses_for_error != 0 not supported for planning dataset')
            if implication_pairs_limit is None:
                implication_pairs_limit =  0
            self.__custom_ca = PlanningCustomCa(
                verbose=verbose,
                max_nr_of_unobserved_transactions_per_example=implication_pairs_limit
            )
        else:
            self.__custom_ca = HomogenousCustomCa(
                sat_model_counter=MC2(
                    use_graph_lower_bound=True,
                    use_regular_graph_lower_bound=True
                ),
                assume_equal_modelcount_for_all_single_target_constraint_candidates=True,
                itemset_miner = ItemsetMiner(
                    max_pattern_length=max_filter_conjunction_length,
                    downsample_itemset_majority_class=downsample_itemset_majority_class,
                    crossover_found_itemsets=crossover_found_itemsets,
                    singleton_positive_support_threshold=singleton_positive_support_threshold,
                    random_seed=random_seed,
                    verbose=verbose
                ),
                verbose=verbose,
                implication_pairs_limit=implication_pairs_limit,
                max_nr_of_target_zeros=max_nr_of_target_zeros,
                nr_of_sampled_clauses_for_error=nr_of_sampled_clauses_for_error,
                random_seed=random_seed
            )

    def acquire_constraints(self, dataset: CaDataset, target: CaTarget) -> list[CaConstraint]:
        return self.__custom_ca.acquire_constraints(dataset, target)

    def __repr__(self):
        return 'URPiLs'