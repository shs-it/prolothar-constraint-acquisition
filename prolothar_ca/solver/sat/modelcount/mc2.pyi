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

from prolothar_ca.model.sat.cnf import CnfFormula
from prolothar_ca.solver.sat.modelcount.model_counter import ModelCounter

def compute_graph_lower_bound(constraint_graph) -> int: ...

class MC2(ModelCounter):
    """
    exact 2-sat model counter with worst-case complexity O(1.1892**m)
    with being the number of clauses
    https://www.cs.huji.ac.il/~jeff/aaai10/02/AAAI10-046.pdf

    we extend the approach with bounds / approximations, which can be
    turned on via the constructor
    """

    def __init__(
        self, use_regular_graph_upper_bound: bool = False,
        use_regular_graph_lower_bound: bool = False,
        use_graph_lower_bound: bool = False,
        ignore_non_solution_dpll_branch: bool = False,
        counter_for_non_solution_dpll_branch: ModelCounter|None = None,
        fast_fallback_model_counter: ModelCounter|None = None):
        """
        configures

        Parameters
        ----------
        use_regular_graph_upper_bound : bool, optional
            if True (by default False), we use an upper bound if the constraint graph
            in the counting process is a regular graph.
            The number of satisyfing models is equivalent to the number of
            independent sets in the constraint graph
            (see the paper "Counting models for 2SAT and 3SAT formulae"
            by Dahllöf et al.,
            https://reader.elsevier.com/reader/sd/pii/S0304397504007297).
            A regular graph is graph where all nodes have the same degree.
            The number of indepedent sets in a regular graph has an upper bound:
            http://web.mit.edu/yufeiz/www/papers/indep_reg.pdf
        use_regular_graph_lower_bound : bool, optional
            if True (by default False), we use a lower bound if the constraint graph
            in the counting process is a regular graph.
            https://www.sciencedirect.com/science/article/abs/pii/S0095895619300085
        ignore_non_solution_dpll_branch : bool, optional
            if True (by default False), we reduce exponential growth of the
            search space during DPLL split by only discovering the branch
            of a known existing solution. in this case, the variables of the
            CNF must be initialized to a solution before calling the count
            method
        """
        ...

    def count(self, cnf: CnfFormula, eliminated_variables: set[int]|None = None) -> int: ...
    def countlog2(self, cnf: CnfFormula) -> float: ...
