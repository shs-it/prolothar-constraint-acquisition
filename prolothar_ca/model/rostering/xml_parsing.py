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

from datetime import date, time, timedelta
from typing import Generator

import xmltodict
from prolothar_ca.model.rostering.assignment import DateAssignment, DayAssignment
from prolothar_ca.model.rostering.contract import Contract
from prolothar_ca.model.rostering.cover_requirement import Cover, CoverRequirement
from prolothar_ca.model.rostering.cover_requirement import DayOfWeekCover, ShiftCover, TimePeriodCover
from prolothar_ca.model.rostering.cover_requirement import DateSpecificCover
from prolothar_ca.model.rostering.day_on_request import DayOnRequest
from prolothar_ca.model.rostering.employee import Employee
from prolothar_ca.model.rostering.scheduling_period import SchedulingPeriod
from prolothar_ca.model.rostering.shift import Shift
from prolothar_ca.model.rostering.shift_constraints import (
    AndShiftConstraint, MaxConsecutiveShiftsOfTypeConstraint, MaxShiftsOfType,
    MinConsecutiveShiftsOfTypeConstraint, MinHoursRestTimeAfterAnyShift,
    MinHoursRestTimeAfterShift, MinMaxWorkloadConstraint, MinShiftsOfType, PatternShiftConstraint,
    ShiftConstraint, ValidShifts)
from prolothar_ca.model.rostering.shift_off_request import ShiftOffRequest
from prolothar_ca.model.rostering.shift_on_request import ShiftOnRequest
from prolothar_ca.model.rostering.solution import Solution
from prolothar_ca.model.rostering.week_day import WeekDay


def parse_scheduling_period(xml: str) -> SchedulingPeriod:
    shift_groups = {}
    fixed_assignments = []
    day_on_requests = []
    shift_off_requests = []
    shift_on_requests = []
    for tag, content in xmltodict.parse(xml)['SchedulingPeriod'].items():
        if tag == 'StartDate':
            start_date = date.fromisoformat(content)
        elif tag == 'EndDate':
            end_date = date.fromisoformat(content)
        elif tag == 'ShiftTypes':
            shifts = parse_shifts(content['Shift'])
        elif tag == 'ShiftGroups':
            shift_groups = parse_shift_groups(content['ShiftGroup'])
        elif tag == 'Employees':
            employees = parse_employees(content['Employee'])
        elif tag == 'Contracts':
            contracts = parse_contracts(content['Contract'])
        elif tag == 'CoverRequirements':
            cover_requirements = parse_cover_requirements(content, start_date)
        elif tag == 'FixedAssignments':
            if content is not None:
                fixed_assignments = parse_fixed_assignments(content)
        elif tag == 'DayOnRequests':
            if content is not None:
                day_on_requests = parse_day_on_requests(content)
        elif tag == 'ShiftOffRequests':
            if content is not None:
                shift_off_requests = parse_shift_off_requests(content, start_date)
        elif tag == 'ShiftOnRequests':
            if content is not None:
                shift_on_requests = parse_shift_on_requests(content, start_date)
        elif tag not in ['@xmlns:xsi', '@xsi:noNamespaceSchemaLocation'] and content is not None:
            raise NotImplementedError(f'unknown tag "{tag}" with content "{content}"')
    return SchedulingPeriod(
        start_date,
        end_date,
        {s.shift_id: s for s in shifts},
        shift_groups,
        {e.employee_id: e for e in employees},
        {c.contract_id: c for c in contracts},
        cover_requirements,
        fixed_assignments,
        day_on_requests,
        shift_off_requests,
        shift_on_requests
    )

def parse_shifts(shifts: list[dict]|dict) -> list[Shift]:
    def parse_shift_time(s: str) -> time:
        try:
            return time.fromisoformat(s)
        except ValueError:
            hours, minutes = s.split(':')
            if len(hours) == 1:
                hours = '0' + hours
            if len(minutes) == 1:
                if minutes != '0':
                    raise NotImplementedError(s)
                minutes = '00'
            return time.fromisoformat(f'{hours}:{minutes}')
    def parse_shift_end_time(shift: dict) -> time:
        try:
            return parse_shift_time(shift['EndTime'])
        except KeyError:
            start_time = parse_shift_time(shift['StartTime'])
            duration_in_minutes = int(shift['Duration'])
            end_time_in_minutes = start_time.hour * 60 + start_time.minute + duration_in_minutes
            if end_time_in_minutes >= 24 * 60:
                end_time_in_minutes -= 24 * 60
            return time(end_time_in_minutes // 60, end_time_in_minutes % 60)
    def parse_shift(shift: dict):
        return Shift(
            shift['@ID'],
            shift.get('Name', shift['@ID']),
            parse_shift_time(shift['StartTime']),
            parse_shift_end_time(shift)
        )
    if isinstance(shifts, dict):
        return [parse_shift(shifts)]
    else:
        return list(map(parse_shift, shifts))

def parse_shift_groups(shift_groups: list[dict]) -> dict[str, list[str]]:
    parsed_shift_groups = {}
    if isinstance(shift_groups, dict):
        shift_groups = [shift_groups]
    for shift_group in shift_groups:
        shifts = shift_group['Shift']
        if isinstance(shifts, str):
            shifts = [shifts]
        parsed_shift_groups[shift_group['@ID']] = shifts
    return parsed_shift_groups

def parse_employees(employees: list[dict]) -> list[Employee]:
    return [
        Employee(
            e['@ID'],
            e['ContractID'] if isinstance(e['ContractID'], list) else [e['ContractID']]
        )
        for e in employees
    ]

def parse_contracts(contracts: list[dict]) -> list[Contract]:
    if isinstance(contracts, dict):
        contracts = [contracts]
    parsed_contracts = []
    for contract in contracts:
        shift_constraints = []
        for key, content in contract.items():
            if key == '@ID':
                contract_id = contract[key]
            elif key != 'Label':
                if isinstance(content, dict):
                    content = [content]
                for shift_constraint in content:
                    parsed_constraint = parse_shift_constraint(contract_id, key, shift_constraint)
                    if parsed_constraint is not None:
                        shift_constraints.append(parsed_constraint)
        parsed_contracts.append(Contract(
            contract_id,
            shift_constraints
        ))
    return parsed_contracts

def parse_shift_constraint(contract_id: str, key: str, content: dict) -> ShiftConstraint:
    def ensure_hours(timevalue: int):
        if timevalue > 1000:
            timevalue = timevalue / 60
        return timevalue
    if key == 'MinSeq':
        return MinConsecutiveShiftsOfTypeConstraint(
            contract_id,
            content['@shift'].split(','),
            int(content['@value'])
        )
    elif key == 'MaxSeq':
        return MaxConsecutiveShiftsOfTypeConstraint(
            contract_id,
            content['@shift'].split(','),
            int(content['@value'])
        )
    elif key == 'Workload':
        time_units = content['TimeUnits']
        if isinstance(time_units, dict):
            return MinMaxWorkloadConstraint(
                contract_id,
                ensure_hours(int(time_units['Min']['Count'])) if 'Min' in time_units else None,
                ensure_hours(int(time_units['Max']['Count'])) if 'Max' in time_units else None,
                int(time_units['RegionStart']) if 'RegionStart' in time_units else None,
                int(time_units['RegionEnd']) if 'RegionEnd' in time_units else None,
            )
        else:
            return AndShiftConstraint(contract_id, [
                MinMaxWorkloadConstraint(
                    contract_id,
                    ensure_hours(int(sub_time_unit['Min']['Count'])) if 'Min' in sub_time_unit else None,
                    ensure_hours(int(sub_time_unit['Max']['Count'])) if 'Max' in sub_time_unit else None,
                    int(sub_time_unit['RegionStart']) if 'RegionStart' in sub_time_unit else None,
                    int(sub_time_unit['RegionEnd']) if 'RegionEnd' in sub_time_unit else None
                )
                for sub_time_unit in time_units
            ])
    elif key == 'MinRestTime':
        if '@shift' not in content:
            return MinHoursRestTimeAfterAnyShift(
                contract_id, int(content['#text']) // 60,
            )
        else:
            return MinHoursRestTimeAfterShift(
                contract_id, int(content['#text']) // 60,
                content['@shift']
            )
    elif key == 'MinTot':
        return MinShiftsOfType(contract_id,content['@shift'].split(','), int(content['@value']))
    elif key == 'MaxTot':
        return MaxShiftsOfType(contract_id,content['@shift'].split(','), int(content['@value']))
    elif key == 'Patterns':
        return parse_patterns(contract_id,content['Match'])
    elif key == 'ValidShifts':
        return ValidShifts(contract_id,content['@shift'].split(','))
    elif key != 'MultipleShiftsPerDay':
        raise NotImplementedError(f'unknown shift constraint key "{key}" with content "{content}"')

def parse_cover_requirements(cover_requirements: dict, start_date: date) -> list[CoverRequirement]:
    parsed_requirements = []
    for type_key, requirement_list in cover_requirements.items():
        if isinstance(requirement_list, dict):
            requirement_list = []
        for requirement in requirement_list:
            if type_key == 'DayOfWeekCover':
                parsed_requirements.append(
                    DayOfWeekCover(
                        WeekDay.from_string(requirement['Day']),
                        parse_cover_list(requirement['Cover'])
                    )
                )
            elif type_key == 'DateSpecificCover':
                parsed_requirements.append(
                    DateSpecificCover(
                        start_date + timedelta(days=int(requirement['Day'])),
                        parse_cover_list(requirement['Cover'])
                    )
                )
            else:
                raise NotImplementedError(type_key, requirement)
    return parsed_requirements

def parse_cover_list(cover_list: list[dict]) -> list[Cover]:
    if isinstance(cover_list, dict):
        cover_list = [cover_list]
    parsed_cover_list = []
    for cover in cover_list:
        try:
            min_shifts = int(cover['Min']['#text']) if isinstance(cover['Min'], dict) else int(cover['Min'][0]['#text'])
        except KeyError:
            min_shifts = 0
        try:
            max_shifts = int(cover['Max']['#text']) if isinstance(cover['Max'], dict) else int(cover['Max'][0]['#text'])
        except KeyError:
            max_shifts = None
        if 'Shift' in cover:
            parsed_cover_list.append(ShiftCover(
                min_shifts,
                max_shifts,
                cover['Shift']
            ))
        else:
            parsed_cover_list.append(TimePeriodCover(
                min_shifts,
                max_shifts,
                time.fromisoformat(cover['TimePeriod']['Start']),
                time.fromisoformat(cover['TimePeriod']['End'])
            ))
    return parsed_cover_list

def parse_fixed_assignments(content: dict) -> list[DateAssignment]:
    parsed_fixed_assignments = []
    if len(content.keys()) != 1:
        raise NotImplementedError(content)
    employee_list = content['Employee']
    if isinstance(employee_list, dict):
        employee_list = [employee_list]
    for employee in employee_list:
        assign_list = employee['Assign']
        if isinstance(assign_list, dict):
            assign_list = [assign_list]
        for assign in assign_list:
            if 'Date' in assign:
                parsed_fixed_assignments.append(DateAssignment(
                    employee['EmployeeID'],
                    assign['Shift'],
                    date.fromisoformat(assign['Date'])
                ))
            else:
                parsed_fixed_assignments.append(DayAssignment(
                    employee['EmployeeID'],
                    assign['Shift'],
                    int(assign['Day'])
                ))
    return parsed_fixed_assignments

def parse_patterns(contract_id: str, pattern_list: list[dict]) -> AndShiftConstraint|ShiftConstraint:
    if isinstance(pattern_list, dict):
        pattern_list = [pattern_list]
    parsed_pattern_constraints = [
        parse_pattern_constraint(contract_id, pattern_constraint)
        for pattern_constraint in pattern_list
    ]
    if len(parsed_pattern_constraints) > 1:
        return AndShiftConstraint(contract_id, parsed_pattern_constraints)
    else:
        return parsed_pattern_constraints[0]

def parse_pattern_constraint(contract_id: str, pattern_constraint) -> PatternShiftConstraint:
    if 'Min' in pattern_constraint:
        min_count = int(pattern_constraint['Min']['Count'])
    else:
        min_count = None
    if 'Max' in pattern_constraint:
        max_count = int(pattern_constraint['Max']['Count'])
    else:
        max_count = None
    if 'RegionStart' in pattern_constraint:
        region_start = int(pattern_constraint['RegionStart'])
    else:
        region_start = None
    if 'RegionEnd' in pattern_constraint:
        region_end = int(pattern_constraint['RegionStart'])
    else:
        region_end = None

    pattern_part = pattern_constraint.get('Pattern', [])
    if isinstance(pattern_part, dict):
        pattern_part = [pattern_part]
    shifts_list = []
    startday = None
    for pattern in pattern_part:
        for key, values in pattern.items():
            if key == 'Shift':
                shifts_list.append(values)
            elif key == 'ShiftGroup':
                if isinstance(values, str):
                    shifts_list.append([values])
                else:
                    shifts_list.extend([v] for v in values)
            elif key == 'StartDay':
                startday = WeekDay.from_string(values)
            else:
                raise NotImplementedError(key, values)

    return PatternShiftConstraint(
        contract_id, min_count, max_count, region_start, region_end,
        startday, shifts_list
    )

def parse_day_on_requests(content: dict) -> list[DayOnRequest]:
    if len(content.keys()) != 1:
        raise NotImplementedError(content)
    raw_day_on_requests = content['DayOn']
    if isinstance(raw_day_on_requests, dict):
        raw_day_on_requests = [raw_day_on_requests]
    return [
        DayOnRequest(raw_day_on_request['EmployeeID'], date.fromisoformat(raw_day_on_request['Date']))
        for raw_day_on_request in raw_day_on_requests
    ]

def parse_shift_off_requests(content: dict, start_date: date) -> list[ShiftOffRequest]:
    if len(content.keys()) != 1:
        raise NotImplementedError(content)
    raw_shift_off_requests = content['ShiftOff']
    if isinstance(raw_shift_off_requests, dict):
        raw_shift_off_requests = [raw_shift_off_requests]
    def parse_shift_off_request(shift_off_request: dict):
        return ShiftOffRequest(
            shift_off_request['EmployeeID'],
            shift_off_request['Shift'],
            (
                date.fromisoformat(shift_off_request['Date'])
                if 'Date' in shift_off_request
                else start_date + timedelta(days=int(shift_off_request['Day']))
            )
        )
    return list(map(parse_shift_off_request, raw_shift_off_requests))

def parse_shift_on_requests(content: dict, start_date: date) -> list[ShiftOnRequest]:
    if len(content.keys()) != 1:
        raise NotImplementedError(content)
    raw_shift_on_requests = content['ShiftOn']
    if isinstance(raw_shift_on_requests, dict):
        raw_shift_on_requests = [raw_shift_on_requests]
    def parse_requested_date(shift_on_request):
        try:
            return date.fromisoformat(shift_on_request['Date'])
        except KeyError:
            return start_date + timedelta(days=int(shift_on_request['Day']))
    return [
        ShiftOnRequest(
            shift_on_request['EmployeeID'],
            [shift_on_request['Shift']],
            parse_requested_date(shift_on_request)
        ) if 'Shift' in shift_on_request else ShiftOnRequest(
            shift_on_request['EmployeeID'],
            shift_on_request['ShiftGroup']['Shift'],
            parse_requested_date(shift_on_request)
        )
        for shift_on_request in raw_shift_on_requests
    ]

def parse_solution(xml: str, scheduling_period: SchedulingPeriod) -> Solution:
    assignment_list = []
    for tag, content in xmltodict.parse(xml)['Roster'].items():
        if tag == 'Employee':
            for assignment in content:
                assignment_list.extend(parse_solution_assignments(assignment))
        elif tag not in [
                '@xmlns:xsi',
                '@xsi:noNamespaceSchemaLocation',
                'SchedulingPeriodFile',
                'Penalty'] and content is not None:
            raise NotImplementedError(f'unknown tag "{tag}" with content "{content}"')
    return Solution(assignment_list, scheduling_period)

def parse_solution_assignments(employee_assignment: dict) -> Generator[DayAssignment|DateAssignment,None,None]:
    for assign in employee_assignment.get('Assign', []):
        if 'Date' in assign:
            yield DateAssignment(
                employee_assignment['@ID'],
                assign['Shift'],
                date.fromisoformat(assign['Date'])
            )
        else:
            yield DayAssignment(
                employee_assignment['@ID'],
                assign['Shift'],
                int(assign['Day'])
            )
