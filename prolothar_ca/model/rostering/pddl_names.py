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


day_type: str = 'day'
employee_type: str = 'employee'

def assign_required_shift(shift_id: str) -> str:
    return f'assign_required_shift_{shift_id}'
def assign_optional_shift(shift_id: str) -> str:
    return f'assign_optional_shift_{shift_id}'
def block_optional_shift(shift_id: str) -> str:
    return f'block_optional_shift_{shift_id}'
assign_day_off: str = 'assign_day_off'
start_next_day: str = 'start_next_day'

day_action_parameter: str = 'day'
shift_action_parameter: str = 'shift'
employee_action_parameter: str = 'employee'

is_today: str = 'is_today'
def works_at_shift(shift_id: str) -> str:
    return f'works_at_shift_{shift_id}'

total_workload_variable: str = 'total_workload'
consecutive_days_off_variable: str = 'consecutive_days_off'
last_shift_end_variable: str = 'last_shift_end'
number_of_not_assigned_shifts_variable: str = 'number_of_not_assigned_shifts'
def required_employees_variable(shift_id: str) -> str:
    return f'required_employees_{shift_id}'
def optional_employees_variable(shift_id: str) -> str:
    return f'optional_employees_{shift_id}'
def shift_duration_variable(shift_id: str) -> str:
    return f'shift_duration_{shift_id}'
def shift_start_variable(shift_id: str) -> str:
    return f'shift_start_{shift_id}'
def shift_end_variable(shift_id: str) -> str:
    return f'shift_end_{shift_id}'
def consecutive_shifts_variable(shift_id: str|list[str]|tuple[str]) -> str:
    if not isinstance(shift_id, str):
        shift_id = '_'.join(sorted(shift_id))
    return f'consecutive_shifts_{shift_id}'

def day_object_name(date: date) -> str:
    return 'day_' + date.strftime('%Y_%m_%d')
def employee_object_name(employee_id: str) -> str:
    return f'employee_{employee_id}'
