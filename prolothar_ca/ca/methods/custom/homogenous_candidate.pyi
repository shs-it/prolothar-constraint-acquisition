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

from _typeshed import Incomplete
from prolothar_ca.ca.methods.custom.mdl_score import compute_encoded_data_length_from_known_solution as compute_encoded_data_length_from_known_solution
from prolothar_ca.ca.methods.custom.model.custom_constraint import CustomConstraint as CustomConstraint
from prolothar_ca.ca.methods.custom.model.custom_constraint import DataGraph as DataGraph
from prolothar_ca.ca.methods.custom.sat_encoding import SatEncodedExample as SatEncodedExample
from prolothar_ca.model.sat.cnf import CnfFormula as CnfFormula
from prolothar_ca.model.sat.variable import Value as Value, Variable as Variable
from prolothar_ca.solver.sat.modelcount.model_counter import ModelCounter as ModelCounter
from prolothar_ca.solver.sat.solver.solver import SatSolver as SatSolver
from prolothar_ca.solver.sat.solver.twosat_solver import TwoSatSolver as TwoSatSolver

class Candidate:
    constraint: Incomplete
    replaced_constraint: Incomplete
    replaced_constraint_index: Incomplete
    model_cnf: Incomplete
    model_cost: int
    data_cost: int
    total_cost: int
    gain: Incomplete
    iteration: int
    def __init__(self, constraint: CustomConstraint, datagraph: DataGraph, dataset: list[SatEncodedExample], sat_solver: SatSolver = ..., nr_of_sampled_clauses_for_error: int = 0) -> None: ...
    def update_gain(
            self, iteration: int, model: list[CustomConstraint], model_cost: float,
            model_cnf: CnfFormula, sat_encoded_dataset: list[SatEncodedExample],
            total_cost: float, variables: dict[int, Variable], sat_model_counter: ModelCounter): ...
    def __lt__(self, other: Candidate) -> bool: ...
