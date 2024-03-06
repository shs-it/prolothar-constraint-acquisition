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

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from collections import defaultdict
from optapy.types import ConstraintCollectors, Joiners

from prolothar_common import validate
from prolothar_ca.model.pddl.condition import And, Condition, Equals, Greater, Less, Not, Or
from prolothar_ca.model.pddl.domain import Domain
from prolothar_ca.model.pddl.numeric_expression import Add, NumericFluentExpression, Subtract
from prolothar_ca.solver.optapy.rostering.entities import OptapyShiftAssignment

from prolothar_ca.model.rostering.week_day import WeekDay
import prolothar_ca.model.rostering.pddl_names as pddl_names
from prolothar_ca.model.rostering.assignment import DateAssignment, DayAssignment

ONE_DAY_IN_SECONDS = 3600 * 24

def flatten_shift_ids(shift_ids: set[str], shift_groups: dict[str, list[str]]) -> list[str]:
    flattened_shift_ids = []
    for shift_group_id in shift_ids:
        flattened_shift_ids.extend(shift_groups.get(shift_group_id, [shift_group_id]))
    return flattened_shift_ids

def count_consecutive_optapy_shifts(shift_list):
    if not shift_list:
        return []
    shift_list = sorted(shift_list, key=lambda: a.shift.start_time)
    consec = [1]
    for a, b in zip(shift_list, shift_list[1:]):
        if 0 <= (b.shift.start_time - a.shift.end_time).total_seconds() <= ONE_DAY_IN_SECONDS:
            consec[-1] += 1
        else:
            consec.append(1)
    #start and end of scheduling period are not included in constraint
    return consec[1:-1]

def count_consecutive_shifts(assignment_list: list[DateAssignment|DayAssignment]):
    if not assignment_list:
        return []
    assignment_list = sorted(assignment_list, key=lambda a: a.time_key_for_sorting())
    consec = [1]
    for a, b in zip(assignment_list, assignment_list[1:]):
        if (isinstance(a, DayAssignment) and b.day - a.day <= 1 ) \
        or (isinstance(a, DateAssignment) and (a.date - b.date).total_seconds() <= ONE_DAY_IN_SECONDS):
            consec[-1] += 1
        else:
            consec.append(1)
    #start and end of scheduling period are not included in constraint
    return consec[1:-1]

def count_consecutive_days_off(assignment_list: list[DayAssignment]):
    assignment_list = sorted(assignment_list, key=lambda a: a.time_key_for_sorting())
    consec = []
    for a, b in zip(assignment_list, assignment_list[1:]):
        days_off = b.day - a.day - 1
        if days_off > 0:
            consec.append(days_off)
    return consec

class ShiftConstraint(ABC):

    @abstractmethod
    def to_pddl_for_assign_shift_actions(
            self, domain: Domain, shift_id: str,
            shift_groups: dict[str, list[str]]) -> Condition|None:
        """
        converts this shift constraint into a pddl condition of an action.
        might be None if the shift constraint does not apply to assign_shift_*_actions
        """

    @abstractmethod
    def rename_contract(self, new_contract_id: str):
        """
        sets the constract_id for this constraint and all subconstraints
        """

@dataclass
class MinConsecutiveShiftsOfTypeConstraint(ShiftConstraint):
    contract_id: str = field(compare=False)
    shift_ids: set[str]
    value: int

    def __post_init__(self):
        validate.collection.not_empty(self.shift_ids, msg='requires at least one shift_id')
        validate.greater_or_equal(self.value, 2)

    def holds(self, assignment_list: list[DateAssignment|DayAssignment], scheduling_period) -> bool:
        if '-' in self.shift_ids:
            for employee_id in scheduling_period.employees:
                if self.contract_id in scheduling_period.employees[employee_id].contract_ids and min(count_consecutive_days_off([
                    a.to_day_assignment(scheduling_period.start_date) for a in assignment_list
                    if a.employee_id == employee_id
                ])) < self.value:
                    return False
        else:
            flattened_shift_ids = flatten_shift_ids(self.shift_ids, scheduling_period.shift_groups)
            for employee_id in scheduling_period.employees:
                if self.contract_id in scheduling_period.employees[employee_id].contract_ids and min(count_consecutive_shifts([
                    a for a in assignment_list
                    if a.employee_id == employee_id and (a.shift_id in flattened_shift_ids or '$' in self.shift_ids)
                ]), default=self.value) < self.value:
                    return False
        return True

    def to_pddl_for_assign_shift_actions(
            self, domain: Domain, shift_id: str,
            shift_groups: dict[str, list[str]]) -> Condition|None:
        flattened_shift_ids = flatten_shift_ids(self.shift_ids, shift_groups)
        if shift_id in flattened_shift_ids:
            return None
        elif flattened_shift_ids == ['-']:
            consecutive_days_off = NumericFluentExpression(
                domain.get_numeric_fluent_by_name(
                    pddl_names.consecutive_days_off_variable),
                [pddl_names.employee_action_parameter]
            )
            return Or([
                Equals(consecutive_days_off, 0),
                Greater(consecutive_days_off, self.value - 1)
            ])
        else:
            consecutive_shifts = NumericFluentExpression(
                domain.get_numeric_fluent_by_name(
                    pddl_names.consecutive_shifts_variable(flattened_shift_ids)),
                [pddl_names.employee_action_parameter]
            )
            return Or([
                Equals(consecutive_shifts, 0),
                Greater(consecutive_shifts, self.value - 1)
            ])

    def add_optapy_stream_filter(self, constraint_stream, scheduling_period):
        flattened_shift_ids = flatten_shift_ids(self.shift_ids, scheduling_period.shift_groups)
        return constraint_stream\
            .filter(lambda assignment: assignment.shift.shift_id in flattened_shift_ids)\
            .groupBy(lambda assignment: assignment.employee.employee_id, ConstraintCollectors.toList())\
            .map(lambda _, assignments: min(count_consecutive_optapy_shifts(assignments)))\
            .filter(lambda nr_of_consecutive_shifts: nr_of_consecutive_shifts < self.value)

    def rename_contract(self, new_contract_id: str):
        self.contract_id = new_contract_id

    def __hash__(self):
        return hash((self.value, frozenset(self.shift_ids)))

@dataclass
class MaxConsecutiveShiftsOfTypeConstraint(ShiftConstraint):
    contract_id: str = field(compare=False)
    shift_ids: set[str]
    value: int

    def __post_init__(self):
        validate.collection.not_empty(self.shift_ids, msg='requires at least one shift_id')
        validate.greater_or_equal(self.value, 2)

    def holds(self, assignment_list: list[DateAssignment|DayAssignment], scheduling_period) -> bool:
        flattened_shift_ids = flatten_shift_ids(self.shift_ids, scheduling_period.shift_groups)
        for employee_id in scheduling_period.employees:
            if self.contract_id in scheduling_period.employees[employee_id].contract_ids and max(count_consecutive_shifts([
                a for a in assignment_list
                if a.employee_id == employee_id
                and (a.shift_id in flattened_shift_ids or '$' in self.shift_ids)
            ]), default=self.value) > self.value:
                return False
        return True

    def to_pddl_for_assign_shift_actions(
            self, domain: Domain, shift_id: str,
            shift_groups: dict[str, list[str]]) -> Condition|None:
        flattened_shift_ids = flatten_shift_ids(self.shift_ids, shift_groups)
        if shift_id not in flattened_shift_ids:
            return None
        else:
            consecutive_shifts = NumericFluentExpression(
                domain.get_numeric_fluent_by_name(
                    pddl_names.consecutive_shifts_variable(flattened_shift_ids)),
                [pddl_names.employee_action_parameter]
            )
            return Less(consecutive_shifts, self.value)

    def add_optapy_stream_filter(self, constraint_stream, scheduling_period):
        flattened_shift_ids = flatten_shift_ids(self.shift_ids, scheduling_period.shift_groups)
        return constraint_stream\
            .filter(lambda assignment: assignment.shift.shift_id in flattened_shift_ids)\
            .groupBy(lambda assignment: assignment.employee.employee_id, ConstraintCollectors.toList())\
            .map(lambda _, assignments: max(count_consecutive_optapy_shifts(assignments)))\
            .filter(lambda nr_of_consecutive_shifts: nr_of_consecutive_shifts > self.value)

    def rename_contract(self, new_contract_id: str):
        self.contract_id = new_contract_id

    def __hash__(self):
        return hash((self.value, frozenset(self.shift_ids)))

@dataclass(unsafe_hash=True)
class MinMaxWorkloadConstraint(ShiftConstraint):
    contract_id: str = field(compare=False, hash=False)
    min_hours: int|None
    max_hours: int|None
    region_start: int|None
    region_end: int|None

    def __post_init__(self):
        if self.min_hours is None and self.max_hours is None:
            raise ValueError('one of min_hours or max_hours must be set')
        if self.min_hours is not None and self.max_hours is not None and self.min_hours > self.max_hours:
            raise ValueError(f'min_hours {self.min_hours} must not be greater than max_hours {self.max_hours}')
        if self.region_start is not None and self.region_end is not None and self.region_start > self.region_end:
            raise ValueError(f'region_start {self.region_start} must not be greater than region_end {self.region_end}')

    def to_pddl_for_assign_shift_actions(
            self, domain: Domain, shift_id: str,
            shift_groups: dict[str, list[str]]) -> Condition|None:
        if self.region_start is None and self.region_end is None:
            total_workload = domain.get_numeric_fluent_by_name(pddl_names.total_workload_variable)
            shift_duration = domain.get_numeric_fluent_by_name(pddl_names.shift_duration_variable(shift_id))
            if self.min_hours is not None and self.max_hours is not None:
                return Not(
                    Greater(
                        Add(
                            NumericFluentExpression(total_workload, [pddl_names.employee_action_parameter]),
                            NumericFluentExpression(shift_duration, [])
                        ),
                        self.max_hours
                    )
                )
        else:
            raise NotImplementedError()

    def holds(self, assignment_list: list[DateAssignment|DayAssignment], scheduling_period) -> bool:
        workload_per_employee = defaultdict(int)
        for assignment in assignment_list:
            if (self.region_start is None or assignment.day >= self.region_start) \
            and (self.region_end is None or assignment.day <= self.region_end) \
            and self.contract_id in scheduling_period.employees[assignment.employee_id].contract_ids:
                workload_per_employee[assignment.employee_id] += scheduling_period.shifts[assignment.shift_id].duration_in_hours
        for workload in workload_per_employee.values():
            if self.min_hours is not None and self.min_hours > workload:
                return False
            if self.max_hours is not None and self.max_hours < workload:
                return False
        return True

    def add_optapy_stream_filter(self, constraint_stream, scheduling_period):
        if self.region_start is not None or self.region_end is not None:
            raise NotImplementedError()
        return constraint_stream\
            .groupBy(lambda assignment: assignment.employee.employee_id, ConstraintCollectors.sum(lambda a: a.shift.duration_in_hours))\
            .filter(lambda _, total_workload: total_workload > self.max_hours or total_workload < self.min_hours)

    def rename_contract(self, new_contract_id: str):
        self.contract_id = new_contract_id

@dataclass(unsafe_hash=True)
class MinHoursRestTimeAfterAnyShift(ShiftConstraint):
    contract_id: str = field(compare=False, hash=False)
    value: int

    def __post_init__(self):
        validate.greater(self.value, 0)

    def holds(self, assignment_list: list[DateAssignment|DayAssignment], scheduling_period) -> bool:
        last_date_per_employee = defaultdict(lambda: date(1970, 1, 1))
        for assignment in sorted(assignment_list, key=lambda a: a.time_key_for_sorting()):
            if self.contract_id in scheduling_period.employees[assignment.employee_id].contract_ids:
                current_date = assignment.to_date_assignment(scheduling_period.start_date).date
                if ((current_date - last_date_per_employee[assignment.employee_id]).total_seconds() // 3600) < self.value:
                    return False
                last_date_per_employee[assignment.employee_id] = current_date
        return True

    def to_pddl_for_assign_shift_actions(
            self, domain: Domain, shift_id: str,
            shift_groups: dict[str, list[str]]) -> Condition|None:
        return Greater(
            Subtract(
                NumericFluentExpression(
                    domain.get_numeric_fluent_by_name(pddl_names.shift_start_variable(shift_id)),
                    []
                ),
                NumericFluentExpression(
                    domain.get_numeric_fluent_by_name(pddl_names.last_shift_end_variable),
                    [pddl_names.employee_action_parameter]
                )
            ),
            self.value - 1
        )

    def add_optapy_stream_filter(self, constraint_stream, scheduling_period):
        return constraint_stream.join(
            OptapyShiftAssignment,
            Joiners.equal(
                lambda assignment: assignment.employee.employee_id,
                lambda assignment: assignment.employee.employee_id
            ),
            Joiners.less_than(
                lambda assignment: assignment.shift.end_time,
                lambda assignment: assignment.shift.start_time
            )
        ).filter(
            lambda a1,a2: (a2.shift.start_time - a1.shift.end_time).total_seconds() / 3600 < self.value
        )

    def rename_contract(self, new_contract_id: str):
        self.contract_id = new_contract_id

@dataclass(unsafe_hash=True)
class MinHoursRestTimeAfterShift(ShiftConstraint):
    contract_id: str = field(compare=False, hash=False)
    value: int
    shift_id: str

    def __post_init__(self):
        validate.greater(self.value, 0)
        validate.is_not_none(self.shift_id)

    def to_pddl_for_assign_shift_actions(
            self, domain: Domain, shift_id: str,
            shift_groups: dict[str, list[str]]) -> Condition|None:
        raise NotImplementedError()

    def rename_contract(self, new_contract_id: str):
        self.contract_id = new_contract_id

@dataclass
class MinShiftsOfType(ShiftConstraint):
    contract_id: str = field(compare=False)
    shift_ids: set[str]
    value: int

    def __post_init__(self):
        validate.is_not_none(self.shift_ids)
        validate.collection.not_empty(self.shift_ids)
        validate.greater(self.value, 0)

    def to_pddl_for_assign_shift_actions(
            self, domain: Domain, shift_id: str,
            shift_groups: dict[str, list[str]]) -> Condition|None:
        raise NotImplementedError()

    def holds(self, assignment_list: list[DateAssignment|DayAssignment], scheduling_period) -> bool:
        workload_per_employee = defaultdict(int)
        shift_ids = flatten_shift_ids(self.shift_ids, scheduling_period.shift_groups)
        for assignment in assignment_list:
            if self.contract_id in scheduling_period.employees[assignment.employee_id].contract_ids \
            and assignment.shift_id in shift_ids:
                workload_per_employee[assignment.employee_id] += 1
        for value in workload_per_employee.values():
            if value < self.value:
                return False
        return True

    def __hash__(self):
        return hash((frozenset(self.shift_ids), self.value))

    def rename_contract(self, new_contract_id: str):
        self.contract_id = new_contract_id

@dataclass
class MaxShiftsOfType(ShiftConstraint):
    contract_id: str = field(compare=False)
    shift_ids: set[str]
    value: int

    def __post_init__(self):
        validate.is_not_none(self.shift_ids)
        validate.collection.not_empty(self.shift_ids)
        validate.greater_or_equal(self.value, 0)

    def to_pddl_for_assign_shift_actions(
            self, domain: Domain, shift_id: str,
            shift_groups: dict[str, list[str]]) -> Condition|None:
        raise NotImplementedError()

    def holds(self, assignment_list: list[DateAssignment|DayAssignment], scheduling_period) -> bool:
        workload_per_employee = defaultdict(int)
        shift_ids = flatten_shift_ids(self.shift_ids, scheduling_period.shift_groups)
        for assignment in assignment_list:
            if self.contract_id in scheduling_period.employees[assignment.employee_id].contract_ids \
            and assignment.shift_id in shift_ids:
                workload_per_employee[assignment.employee_id] += 1
        for value in workload_per_employee.values():
            if value > self.value:
                return False
        return True

    def __hash__(self):
        return hash((frozenset(self.shift_ids), self.value))

    def rename_contract(self, new_contract_id: str):
        self.contract_id = new_contract_id

@dataclass
class AndShiftConstraint(ShiftConstraint):
    contract_id: str
    constraints: list[ShiftConstraint]

    def __post_init__(self):
        validate.is_not_none(self.constraints)
        validate.collection.not_empty(self.constraints)
        for constraint in self.constraints:
            validate.equals(self.contract_id, constraint.contract_id)

    def holds(self, assignment_list: list[DateAssignment|DayAssignment], scheduling_period) -> bool:
        for constraint in self.constraints:
            if not constraint.holds(assignment_list, scheduling_period):
                return False
        return True

    def to_pddl_for_assign_shift_actions(
            self, domain: Domain, shift_id: str,
            shift_groups: dict[str, list[str]]) -> Condition|None:
        return And([
            c.to_pddl(domain, shift_groups) for c in self.constraints
        ])

    def __hash__(self):
        return hash(frozenset(self.constraints))

    def __eq__(self, other):
        return isinstance(other, AndShiftConstraint) \
        and set(self.constraints) == set(other.constraints)

    def rename_contract(self, new_contract_id: str):
        self.contract_id = new_contract_id
        for constraint in self.constraints:
            constraint.rename_contract(new_contract_id)

@dataclass
class PatternShiftConstraint(ShiftConstraint):
    contract_id: str = field(compare=False)
    min_count: int|None
    max_count: int|None
    region_start: int|None
    region_end: int|None
    startday: WeekDay|None
    shifts_list: list[list[str]]

    def __post_init__(self):
        if self.min_count is None and self.max_count is None:
            raise ValueError('one of min_count or max_count must be set')
        if self.min_count is not None and self.max_count is not None and self.min_count > self.max_count:
            raise ValueError(f'min_count {self.min_count} must not be greater than max_count {self.max_count}')
        if self.region_start is not None and self.region_end is not None and self.region_start > self.region_end:
            raise ValueError(f'region_start {self.region_start} must not be greater than region_end {self.region_end}')
        validate.collection.not_empty(self.shifts_list)

    def to_pddl_for_assign_shift_actions(
            self, domain: Domain, shift_id: str,
            shift_groups: dict[str, list[str]]) -> Condition|None:
        raise NotImplementedError()

    def holds(self, assignment_list: list[DateAssignment|DayAssignment], scheduling_period) -> bool:
        if self.region_start is not None or self.region_end is not None \
        or self.shifts_list != [['$', '-'], ['-', '$'], ['$', '$']] or self.min_count is not None:
            raise NotImplementedError(self)
        assignments_by_employee = defaultdict(list)
        for assignment in assignment_list:
            if self.contract_id in scheduling_period.employees[assignment.employee_id].contract_ids:
                assignments_by_employee[assignment.employee_id].append(assignment.to_date_assignment(scheduling_period.start_date))
        for assignments_of_one_employee in assignments_by_employee.values():
            count = 0
            for assignment in assignments_of_one_employee:
                if WeekDay.from_date(assignment.date) == self.startday:
                    count += 1
            if (self.min_count is not None and count < self.min_count) \
            or (self.max_count is not None and count > self.max_count):
                return False
        return True

    def __hash__(self):
        return hash((
            self.min_count, self.max_count,
            self.region_start, self.region_end, self.startday, str(self.shifts_list)
        ))

    def __eq__(self, other) -> bool:
        return isinstance(other, PatternShiftConstraint) \
        and self.min_count == other.min_count \
        and self.max_count == other.max_count \
        and self.region_start == other.region_start \
        and self.region_end == other.region_end \
        and self.startday == other.startday \
        and str(self.shifts_list) == str(other.shifts_list)

    def rename_contract(self, new_contract_id: str):
        self.contract_id = new_contract_id

@dataclass
class ValidShifts(ShiftConstraint):
    contract_id: str = field(compare=False)
    shift_ids: set[str]

    def __post_init__(self):
        validate.is_not_none(self.shift_ids)
        validate.collection.not_empty(self.shift_ids)

    def to_pddl_for_assign_shift_actions(
            self, domain: Domain, shift_id: str,
            shift_groups: dict[str, list[str]]) -> Condition|None:
        raise NotImplementedError()

    def holds(self, assignment_list: list[DateAssignment|DayAssignment], scheduling_period) -> bool:
        flattened_shift_ids = flatten_shift_ids(self.shift_ids, scheduling_period.shift_groups)
        for assignment in assignment_list:
            if self.contract_id in scheduling_period.employees[assignment.employee_id].contract_ids \
            and assignment.shift_id not in flattened_shift_ids:
                return False
        return True

    def __hash__(self):
        return hash(frozenset(self.shift_ids))

    def rename_contract(self, new_contract_id: str):
        self.contract_id = new_contract_id

