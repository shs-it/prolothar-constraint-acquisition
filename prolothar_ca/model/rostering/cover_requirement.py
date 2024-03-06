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

from abc import ABC
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from more_itertools import ilen
from collections import defaultdict
from prolothar_common import validate

from prolothar_ca.model.pddl.domain import Domain
from prolothar_ca.model.pddl.problem import Problem
from prolothar_ca.solver.optapy.rostering.facts import OptapyShift

import prolothar_ca.model.rostering.pddl_names as pddl_names
from prolothar_ca.model.rostering.week_day import WeekDay
from prolothar_ca.model.rostering.assignment import DateAssignment, DayAssignment

@dataclass
class Cover(ABC):
    min_employees: int
    max_employees: int|None

    def __post_init__(self):
        validate.greater_or_equal(self.min_employees, 0)
        if self.max_employees is not None:
            validate.greater_or_equal(self.max_employees, self.min_employees)

@dataclass
class ShiftCover(Cover):
    shift_id: str

    def __post_init__(self):
        super().__post_init__()
        validate.is_not_none(self.shift_id)

    def holds(self, assignment_list: list[DateAssignment|DayAssignment], scheduling_period) -> bool:
        return self.min_employees <= ilen(
            assignment for assignment in assignment_list
            if assignment.shift_id == self.shift_id
        ) <= self.max_employees

    def to_pddl(self, problem: Problem, domain: Domain, shift_date: date, scheduling_period):
        required_employees = domain.get_numeric_fluent_by_name(pddl_names.required_employees_variable(self.shift_id))
        optional_employees = domain.get_numeric_fluent_by_name(pddl_names.optional_employees_variable(self.shift_id))
        day_object = problem.get_object_by_name(pddl_names.day_object_name(shift_date))
        problem.get_intitial_state().numeric_fluents.add((
            required_employees,
            tuple([day_object]),
            self.min_employees
        ))
        if self.max_employees is not None:
            problem.get_intitial_state().numeric_fluents.add((
                optional_employees,
                tuple([day_object]),
                self.max_employees - self.min_employees
            ))
        else:
            problem.get_intitial_state().numeric_fluents.add((
                optional_employees,
                tuple([day_object]),
                0
            ))

    def to_optapy_shift_list(self, shift_date: date, scheduling_period) -> list[OptapyShift]:
        shift = scheduling_period.shifts[self.shift_id]
        if shift.start_time < shift.end_time:
            end_date = shift_date
        else:
            end_date = shift_date + timedelta(days=1)
        shift_list = []
        for i in range(1, self.max_employees + 1):
            shift_list.append(OptapyShift(
                f'{shift_date.strftime("%Y_%m_%d")}_{shift.shift_id}_{i}', shift.shift_id,
                datetime(
                    shift_date.year, shift_date.month, shift_date.day,
                    shift.start_time.hour, shift.start_time.minute
                ),
                datetime(
                    end_date.year, end_date.month, end_date.day,
                    shift.end_time.hour, shift.end_time.minute
                ),
                i > self.min_employees
            ))
        return shift_list

@dataclass
class TimePeriodCover(Cover):
    start: time
    end: time

    def __post_init__(self):
        super().__post_init__()
        validate.is_not_none(self.start)
        validate.is_not_none(self.end)
        validate.not_equals(self.start, self.end)

class CoverRequirement(ABC):
    pass

@dataclass
class DayOfWeekCover(CoverRequirement):
    weekday: WeekDay
    required_covers: list[Cover]

    def __post_init__(self):
        validate.is_not_none(self.weekday)
        validate.is_not_none(self.required_covers)
        validate.collection.not_empty(self.required_covers)

    def to_pddl(self, problem: Problem, domain: Domain, scheduling_period):
        current_date = scheduling_period.start_date
        while current_date <= scheduling_period.end_date:
            if self.weekday == WeekDay.from_date(current_date):
                for cover in self.required_covers:
                    cover.to_pddl(problem, domain, current_date, scheduling_period)
                current_date += timedelta(days=7)
            else:
                current_date += timedelta(days=1)

    def to_optapy_shift_list(self, scheduling_period) -> list[OptapyShift]:
        shift_list = []
        current_date = scheduling_period.start_date
        while current_date <= scheduling_period.end_date:
            if self.weekday == WeekDay.from_date(current_date):
                for cover in self.required_covers:
                    shift_list.extend(cover.to_optapy_shift_list(current_date, scheduling_period))
                current_date += timedelta(days=7)
            else:
                current_date += timedelta(days=1)
        return shift_list

    def holds(self, assignment_list: list[DateAssignment|DayAssignment], scheduling_period) -> bool:
        assignment_list = [
            assignment.to_date_assignment(scheduling_period.start_date)
            for assignment in assignment_list
        ]
        grouped_assignments = defaultdict(list)
        for assignment in assignment_list:
            if WeekDay.from_date(assignment.date) == self.weekday:
                grouped_assignments[assignment.date].append(assignment)
        for cover in self.required_covers:
            for date_assignments in grouped_assignments.values():
                if not cover.holds(date_assignments, scheduling_period):
                    return False
        return True

@dataclass
class DateSpecificCover(CoverRequirement):
    the_date: date
    required_covers: list[Cover]

    def __post_init__(self):
        validate.is_not_none(self.the_date)
        validate.is_not_none(self.required_covers)
        validate.collection.not_empty(self.required_covers)

    def holds(self, assignment_list: list[DateAssignment|DayAssignment], scheduling_period) -> bool:
        assignment_list = [
            assignment.to_date_assignment(scheduling_period.start_date)
            for assignment in assignment_list
        ]
        grouped_assignments = defaultdict(list)
        for assignment in assignment_list:
            if assignment.date == self.the_date:
                grouped_assignments[assignment.date].append(assignment)
        for cover in self.required_covers:
            for date_assignments in grouped_assignments.values():
                if not cover.holds(date_assignments, scheduling_period):
                    return False
        return True

    def to_optapy_shift_list(self, scheduling_period) -> list[OptapyShift]:
        shift_list = []
        current_date = scheduling_period.start_date
        while current_date <= scheduling_period.end_date:
            if self.the_date == current_date:
                for cover in self.required_covers:
                    shift_list.extend(cover.to_optapy_shift_list(current_date, scheduling_period))
            current_date += timedelta(days=1)
        return shift_list