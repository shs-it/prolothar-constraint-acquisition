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

from datetime import date
from prolothar_common.collections.list_utils import deep_flatten

from optapy import solver_factory_create, score_manager_create
from optapy.types import SolverConfig, TerminationConfig, Duration

from prolothar_ca.model.rostering.assignment import DateAssignment

from prolothar_ca.model.rostering.solution import Solution
from prolothar_ca.model.rostering.scheduling_period import SchedulingPeriod

from prolothar_ca.solver.optapy.rostering.facts import OptapyEmployee, OptapyShift
from prolothar_ca.solver.optapy.rostering.constraints import create_constraints
from prolothar_ca.solver.optapy.rostering.constraints import employee_cannot_work_at_parallel_shifts_constraint
from prolothar_ca.solver.optapy.rostering.constraints import mandatory_shift_must_be_assigned_constraint
from prolothar_ca.solver.optapy.rostering.constraints import optional_shift_should_be_assigned_constraint
from prolothar_ca.solver.optapy.rostering.entities import OptapyShiftAssignment
from prolothar_ca.solver.optapy.rostering.solution import Roster

class RosteringSolver:

    def solve_and_explain(
            self, scheduling_period: SchedulingPeriod,
            termination_spent_limit_in_s: int|None = 300,
            no_improvement_limit_in_s: int = None) -> tuple[Solution, any]:
        constraint_list = [
            mandatory_shift_must_be_assigned_constraint,
            optional_shift_should_be_assigned_constraint,
            employee_cannot_work_at_parallel_shifts_constraint
        ] + deep_flatten([
            contract.to_optapy_constraint_list(scheduling_period)
            for contract in scheduling_period.contracts.values()
        ])
        termination_config = TerminationConfig()
        if termination_spent_limit_in_s is not None:
            termination_config = termination_config.withSpentLimit(
                Duration.ofSeconds(termination_spent_limit_in_s))
        if no_improvement_limit_in_s is not None:
            termination_config = termination_config.withUnimprovedSpentLimit(
                Duration.ofSeconds(no_improvement_limit_in_s))
        solver_config = SolverConfig()\
            .withEntityClasses(OptapyShiftAssignment)\
            .withSolutionClass(Roster)\
            .withConstraintProviderClass(create_constraints(constraint_list))\
            .withTerminationConfig(termination_config)

        solver = solver_factory_create(solver_config).buildSolver()
        optapy_solution = solver.solve(self.__generate_problem(scheduling_period))
        return (
            self.__map_optapy_solution(optapy_solution, scheduling_period),
            score_manager_create(solver_factory_create(solver_config)).explainScore(optapy_solution)
        )

    def __map_optapy_solution(self, optapy_solution: Roster, scheduling_period: SchedulingPeriod) -> Solution:
        return Solution([
            DateAssignment(
                assignment.employee.employee_id, assignment.shift.shift_type,
                date(
                    assignment.shift.start_time.year,
                    assignment.shift.start_time.month,
                    assignment.shift.start_time.day
                )
            )
            for assignment in optapy_solution.assignment_list
            if assignment.employee is not None
        ], scheduling_period)

    def __generate_problem(self, scheduling_period: SchedulingPeriod):
        shift_list = self.__generate_shift_list(scheduling_period)
        return Roster(
            shift_list,
            self.__generate_employee_list(scheduling_period),
            self.__generate_initial_assignment_list(shift_list)
        )

    def __generate_shift_list(self, scheduling_period: SchedulingPeriod):
        shift_list = []
        for cover_requirement in scheduling_period.cover_requirements:
            shift_list.extend(cover_requirement.to_optapy_shift_list(scheduling_period))
        return shift_list

    def __generate_employee_list(self, scheduling_period: SchedulingPeriod):
        return [
            OptapyEmployee(employee.employee_id, employee.contract_ids)
            for employee in scheduling_period.employees.values()
        ]

    def __generate_initial_assignment_list(self, shift_list: list[OptapyShift]) -> list[OptapyShiftAssignment]:
        return [
            OptapyShiftAssignment(i, shift) for i, shift in enumerate(shift_list)
        ]
