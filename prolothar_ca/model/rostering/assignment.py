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
from dataclasses import dataclass
from datetime import date, timedelta

from prolothar_common import validate

@dataclass
class DateAssignment:
    employee_id: str
    shift_id: str
    date: date

    def __post_init__(self):
        validate.is_not_none(self.employee_id)
        validate.is_not_none(self.shift_id)
        validate.is_not_none(self.date)

    def time_key_for_sorting(self):
        return self.date

    def to_date_assignment(self, start_date: date) -> 'DateAssignment':
        return self

    def to_day_assignment(self, start_date: date) -> 'DayAssignment':
        return DayAssignment(self.employee_id, self.shift_id, (start_date - self.date).days)

@dataclass
class DayAssignment:
    employee_id: str
    shift_id: str
    day: int

    def __post_init__(self):
        validate.is_not_none(self.employee_id)
        validate.is_not_none(self.shift_id)
        validate.is_not_none(self.day)

    def time_key_for_sorting(self):
        return self.day

    def to_date_assignment(self, start_date: date) -> 'DateAssignment':
        return DateAssignment(self.employee_id, self.shift_id, start_date + timedelta(days=self.day))

    def to_day_assignment(self, start_date: date) -> 'DateAssignment':
        return self

def group_assignments_by_employee(
        assignment_list: list[DayAssignment|DateAssignment]
        ) -> dict[str, list[DayAssignment|DateAssignment]]:
    """
    returns a dictionary where the keys are employee ids and values are the
    assignments belonging to this employee
    """
    grouped_assignments = defaultdict(list)
    for assignment in assignment_list:
        grouped_assignments[assignment.employee_id].append(assignment)
    return grouped_assignments

