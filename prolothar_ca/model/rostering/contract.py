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

from dataclasses import dataclass
from prolothar_common import validate

from optapy.types import HardSoftScore
from prolothar_ca.solver.optapy.rostering.entities import OptapyShiftAssignment

from prolothar_ca.model.rostering.shift_constraints import ShiftConstraint

@dataclass
class Contract:
    contract_id: str
    shift_constraints: list[ShiftConstraint]

    def __post_init__(self):
        validate.is_not_none(self.contract_id)
        validate.is_not_none(self.shift_constraints)
        for constraint in self.shift_constraints:
            if constraint is None:
                raise ValueError(f'shift constraints contains None: {self.shift_constraints}')
            validate.equals(constraint.contract_id, self.contract_id)

    def __hash__(self):
        return hash(self.contract_id)

    def to_optapy_constraint_list(self, scheduling_period):
        constraint_list = []
        for shift_constraint in self.shift_constraints:
            def constraint(constraint_factory, shift_constraint=shift_constraint):
                return shift_constraint.add_optapy_stream_filter(
                    constraint_factory\
                        .for_each(OptapyShiftAssignment)\
                        .filter(lambda assignment: self.contract_id in assignment.employee.contract_ids),
                    scheduling_period
                ).penalize(f'Contract {self.contract_id} -> {shift_constraint}', HardSoftScore.ONE_HARD)
            constraint_list.append(constraint)
        return constraint_list

    def rename_contract(self, new_contract_id: str):
        self.contract_id = new_contract_id
        for constraint in self.shift_constraints:
            constraint.rename_contract(new_contract_id)
