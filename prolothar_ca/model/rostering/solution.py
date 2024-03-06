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

from collections import defaultdict
from itertools import product
import os
from datetime import datetime, timedelta
import sys
from random import Random

from calendar_view.calendar import Calendar, CalendarConfig
from prolothar_ca.model.ca.dataset import CaDataset
from prolothar_ca.model.ca.example import CaExample
from prolothar_ca.model.ca.obj import CaObject
from prolothar_ca.model.ca.relation import CaRelation

from prolothar_ca.model.pddl.domain import Domain
from prolothar_ca.model.pddl.problem import Problem
from prolothar_ca.model.pddl.state import State
from prolothar_ca.model.rostering import pddl_names, ca_names
from prolothar_ca.model.rostering.assignment import DateAssignment, DayAssignment
from prolothar_ca.model.pddl.plan import Plan
from prolothar_ca.model.rostering.scheduling_period import SchedulingPeriod


class Solution:
    def __init__(self, assignment_list: list[DateAssignment|DayAssignment], scheduling_period: SchedulingPeriod):
        self.assignment_list = assignment_list
        self.scheduling_period = scheduling_period

    def permutate_employees_with_same_contract(self, random_generator: Random|None = None) -> 'Solution':
        if random_generator is None:
            random_generator = Random()
        contract_to_employees = defaultdict(list)
        for employee in self.scheduling_period.employees.values():
            contract_to_employees[tuple(sorted(employee.contract_ids))].append(employee.employee_id)
        employee_mapping = {}
        for original_employee_order in contract_to_employees.values():
            new_employee_order = list(original_employee_order)
            random_generator.shuffle(new_employee_order)
            for employee_pre, employee_post in zip(original_employee_order, new_employee_order):
                employee_mapping[employee_pre] = employee_post
        new_assignment_list = []
        for old_assignment in self.assignment_list:
            new_assignment = old_assignment.to_date_assignment(self.scheduling_period.start_date)
            new_assignment.employee_id = employee_mapping[new_assignment.employee_id]
            new_assignment_list.append(new_assignment)
        return Solution(new_assignment_list, self.scheduling_period)

    def holds_all_constraints(self) -> bool:
        for cover_requirement in self.scheduling_period.cover_requirements:
            if not cover_requirement.holds(self.assignment_list, self.scheduling_period):
                return False
        return self.holds_all_contract_constraints()

    def holds_all_contract_constraints(self) -> bool:
        for contract in self.scheduling_period.contracts.values():
            for constraint in contract.shift_constraints:
                if not constraint.holds(self.assignment_list, self.scheduling_period):
                    return False
        return True

    @staticmethod
    def from_xml(xml: str, scheduling_period: SchedulingPeriod) -> 'Solution':
        from prolothar_ca.model.rostering.xml_parsing import parse_solution
        return parse_solution(xml, scheduling_period)

    def to_pddl(self, domain: Domain, problem: Problem) -> Plan:
        action_list = []
        state = problem.get_intitial_state().to_state()

        start_next_day_action = domain.get_action_by_name(pddl_names.start_next_day)

        for assignment in sorted(self.assignment_list, key=lambda a: a.time_key_for_sorting()):
            assignment = assignment.to_date_assignment(self.scheduling_period.start_date)
            while True:
                state, could_assign_shift = self.__try_assign_shift(
                    assignment, domain, problem, state, action_list)
                if could_assign_shift:
                    break
                else:
                    state = self.__assign_days_off(domain, problem, state, last_date)
                    state = self.__block_remaining_optional_shifts(domain, problem, state, last_date)
                    action_parameter = {
                        'current_day': problem.get_object_by_name(
                            pddl_names.day_object_name(last_date)),
                        'next_day': problem.get_object_by_name(
                            pddl_names.day_object_name(assignment.date))
                    }
                    if not start_next_day_action.is_applicable(action_parameter, state, problem):
                        print(state)
                        raise NotImplementedError(assignment)
                    else:
                        state = start_next_day_action.apply(action_parameter, state)
            last_date = assignment.date
        plan_cost = state.get_numeric_fluent_value(domain.get_numeric_fluent_by_name(
            pddl_names.number_of_not_assigned_shifts_variable), tuple())
        return Plan(action_list, plan_cost)

    def __block_remaining_optional_shifts(self, domain: Domain, problem: Problem, state: State, last_date) -> State:
        for shift_id in self.scheduling_period.shifts:
            block_optional_shift_action = domain.get_action_by_name(
                pddl_names.block_optional_shift(shift_id))
            action_parameters = {
                pddl_names.day_action_parameter: problem.get_object_by_name(
                    pddl_names.day_object_name(last_date))
            }
            while block_optional_shift_action.is_applicable(action_parameters, state, problem):
                state = block_optional_shift_action.apply(action_parameters, state)
        return state

    def __assign_days_off(self, domain, problem, state, last_date) -> State:
        assign_day_off_action = domain.get_action_by_name(pddl_names.assign_day_off)
        for employee in problem.get_objects_of_type(domain.get_type_by_name(pddl_names.employee_type)):
            action_parameter = {
                            pddl_names.employee_action_parameter: employee,
                            pddl_names.day_action_parameter: problem.get_object_by_name(
                                pddl_names.day_object_name(last_date))
                        }
            if assign_day_off_action.is_applicable(action_parameter, state, problem):
                state = assign_day_off_action.apply(action_parameter, state)
        return state

    def __try_assign_shift(
            self, assignment: DateAssignment, domain: Domain, problem: Problem,
            state: State, action_list) -> tuple[State, bool]:
        assign_required_shift_action = domain.get_action_by_name(
            pddl_names.assign_required_shift(assignment.shift_id))
        assign_optional_shift_action = domain.get_action_by_name(
            pddl_names.assign_optional_shift(assignment.shift_id))

        action_parameter = {
            pddl_names.day_action_parameter: problem.get_object_by_name(
                pddl_names.day_object_name(assignment.date)),
            pddl_names.employee_action_parameter: problem.get_object_by_name(
                pddl_names.employee_object_name(assignment.employee_id))
        }
        if assign_required_shift_action.is_applicable(action_parameter, state, problem):
            action_list.append((assign_required_shift_action, action_parameter))
            state = assign_required_shift_action.apply(action_parameter, state)
            return state, True
        elif assign_optional_shift_action.is_applicable(action_parameter, state, problem):
            action_list.append((assign_optional_shift_action, action_parameter))
            state = assign_optional_shift_action.apply(action_parameter, state)
            return state, True
        return state, False

    def create_ca_example(self, ca_dataset: CaDataset, with_helpful_relations: bool = False, is_valid: bool = True):
        employee_objects = {
            ca_names.employee_id(employee.employee_id): CaObject(
                ca_names.employee_id(employee.employee_id),
                ca_names.employee,
                {
                    ca_names.has_contract(contract_id): contract_id in employee.contract_ids
                    for contract_id in self.scheduling_period.contracts
                }
                if len(self.scheduling_period.contracts) > 1 else {}
            )
            for employee in self.scheduling_period.employees.values()
        }
        start_datetime = datetime(
            self.scheduling_period.start_date.year,
            self.scheduling_period.start_date.month,
            self.scheduling_period.start_date.day,
            0, 0, 0
        )
        shift_objects = {
            ca_names.shift_id(shift.shift_id): CaObject(
                ca_names.shift_id(shift.shift_id),
                ca_names.shift,
                {
                    ca_names.relative_start_time_in_hours: (
                        shift.start_time - start_datetime
                    ).total_seconds() / 3600,
                    ca_names.relative_end_time_in_hours: (
                        shift.end_time - start_datetime
                    ).total_seconds() / 3600,
                    ca_names.duration_in_hours: shift.duration_in_hours,
                    ca_names.is_optional: shift.is_optional
                } | {
                    ca_names.is_shift_type(shift_id): shift.shift_type == shift_id
                    for shift_id in self.scheduling_period.shifts
                }
            )
            for cover_requirement in self.scheduling_period.cover_requirements
            for shift in cover_requirement.to_optapy_shift_list(self.scheduling_period)
        }
        shift_ids = defaultdict(lambda: iter(range(1, sys.maxsize)))
        works_at_shift_set = set(
            (
                ca_names.employee_id(assignment.employee_id),
                ca_names.shift_id(f'{assignment.date.strftime("%Y_%m_%d")}_{assignment.shift_id}_{next(shift_ids[(assignment.date, assignment.shift_id)])}')
            )
            for assignment in [
                a.to_date_assignment(self.scheduling_period.start_date)
                for a in self.assignment_list
            ]
        )
        if with_helpful_relations:
            helpful_relations = {
                ca_names.distance_in_hours: set(CaRelation(
                    ca_names.distance_in_hours,
                    (shift_a, shift_b),
                    (
                        shift_a.features[ca_names.relative_end_time_in_hours] -
                        shift_b.features[ca_names.relative_start_time_in_hours]
                    )
                ) for shift_a, shift_b in product(shift_objects.values(), shift_objects.values())),
                ca_names.shifts_are_within_one_day: set(CaRelation(
                    ca_names.shifts_are_within_one_day,
                    (shift_a, shift_b),
                    abs(
                        shift_a.features[ca_names.relative_end_time_in_hours] -
                        shift_b.features[ca_names.relative_start_time_in_hours]
                    ) <= 24
                ) for shift_a, shift_b in product(shift_objects.values(), shift_objects.values()))
            }
        else:
            helpful_relations = {}
        return CaExample(
            {
                ca_names.employee: set(employee_objects.values()),
                ca_names.shift: set(shift_objects.values())
            },
            {
                ca_names.works_at_shift: set(
                    CaRelation(
                        ca_names.works_at_shift,
                        (employee, shift),
                        (employee.object_id, shift.object_id) in works_at_shift_set
                    )
                    for employee, shift in product(employee_objects.values(), shift_objects.values())
                )
            } | helpful_relations,
            is_valid
        )

    def add_to_ca_dataset(self, ca_dataset: CaDataset, with_helpful_relations: bool = False, is_valid: bool = True):
        ca_dataset.add_example(self.create_ca_example(
            ca_dataset, with_helpful_relations=with_helpful_relations, is_valid=is_valid))

    def save_as_calendar_png_images(self, image_directory_path: str):
        if self.scheduling_period.start_date.weekday() != 0:
            raise NotImplementedError('scheduling period is expected to start with a monday')
        start_date = self.scheduling_period.start_date
        # Calendar can only show 14 days
        two_weeks_later_date = start_date + timedelta(weeks=2)
        assignments_grouped_by_date_and_shift_id = defaultdict(lambda: defaultdict(list))
        for assignment in self.assignment_list:
            assignment = assignment.to_date_assignment(self.scheduling_period.start_date)
            assignments_grouped_by_date_and_shift_id[assignment.date][assignment.shift_id].append(assignment)

        while start_date < self.scheduling_period.end_date:
            dates_str = (
                f'{start_date.strftime("%Y-%m-%d")} - '
                f'{(two_weeks_later_date - timedelta(days=1)).strftime("%Y-%m-%d")}'
            )
            calendar = Calendar.build(CalendarConfig(
                title=dates_str,
                dates=dates_str
            ))
            current_date = start_date
            while current_date < two_weeks_later_date:
                for shift_id, assignment_list in assignments_grouped_by_date_and_shift_id[current_date].items():
                    shift = self.scheduling_period.shifts[shift_id]
                    calendar.add_event(
                        title=', '.join(sorted(a.employee_id for a in assignment_list)),
                        day=current_date.strftime("%Y-%m-%d"),
                        start=shift.start_time.strftime('%H:%M'),
                        end=shift.end_time.strftime('%H:%M'),
                    )
                current_date += timedelta(days=1)
            calendar.save(os.path.join(
                image_directory_path,
                f'roster_{start_date.strftime("%Y-%m-%d")}_{(two_weeks_later_date - timedelta(days=1)).strftime("%Y-%m-%d")}.png'
            ))
            start_date = two_weeks_later_date
            two_weeks_later_date = start_date + timedelta(weeks=2)
