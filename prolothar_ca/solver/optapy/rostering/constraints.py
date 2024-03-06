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

from optapy import constraint_provider
from optapy.types import Joiners, HardSoftScore

from prolothar_ca.solver.optapy.rostering.entities import OptapyShiftAssignment

def create_constraints(constraint_list):
    @constraint_provider
    def define_constraints(constraint_factory):
        return [
            constraint(constraint_factory)
            for constraint in constraint_list
        ]
    return define_constraints

def mandatory_shift_must_be_assigned_constraint(constraint_factory):
    return constraint_factory.for_each_including_null_vars(OptapyShiftAssignment
    ).filter(
        lambda assignment: not assignment.shift.is_optional and assignment.employee is None
    ).penalize("Mandatory shift not assigned", HardSoftScore.ONE_HARD)

def optional_shift_should_be_assigned_constraint(constraint_factory):
    return constraint_factory.for_each_including_null_vars(OptapyShiftAssignment
    ).filter(
        lambda assignment: not assignment.shift.is_optional and assignment.employee is None
    ).penalize("Optional shift not assigned", HardSoftScore.ONE_SOFT)

def employee_cannot_work_at_parallel_shifts_constraint(constraint_factory):
    return constraint_factory.for_each_unique_pair(OptapyShiftAssignment,
        Joiners.equal(
            lambda assignment: assignment.employee.employee_id,
        ),
        Joiners.overlapping(
            lambda assignment: assignment.shift.start_time,
            lambda assignment: assignment.shift.end_time
        )
    ).penalize("Parallel shift conflict", HardSoftScore.ONE_HARD)

