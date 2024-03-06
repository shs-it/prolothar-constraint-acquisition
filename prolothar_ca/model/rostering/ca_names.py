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

"""
constants for Constraint Acquisition formulations of the rostering problem and solutions
"""

"""
Types
"""

employee = 'employee'
shift = 'shift'

"""
Object IDs
"""

def employee_id(base_employee_id: str) -> str:
    return f'employee_{base_employee_id}'

def shift_id(base_shift_id: str) -> str:
    return f'shift_{base_shift_id}'

"""
Features
"""

relative_start_time_in_hours: str = 'relative_start_time_in_hours'
relative_end_time_in_hours: str = 'relative_end_time_in_hours'
duration_in_hours: str = 'duration_in_hours'
is_optional: str = 'is_optional'

def has_contract(contract_id: str) -> str:
    return f'has_contract_{contract_id}'

def is_shift_type(shift_type: str) -> str:
    return f'is_shift_type{shift_type}'

"""
Relations
"""

works_at_shift: str = 'works_at_shift'
distance_in_hours: str = 'distance_in_hours'
shifts_are_within_one_day: str = 'shifts_are_within_one_day'
