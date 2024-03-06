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

from optapy import problem_fact

@problem_fact
class OptapyShift:
    def __init__(self, shift_id, shift_type, start_time, end_time, is_optional):
        self.shift_id = shift_id
        self.shift_type = shift_type
        self.start_time = start_time
        self.end_time = end_time
        self.is_optional = is_optional
        if self.start_time > self.end_time:
            raise NotImplementedError(self.end_time - self.start_time)
        else:
            self.duration_in_hours = (self.end_time - self.start_time).total_seconds() / 3600

    def __str__(self):
        return f'Shift({self.shift_type}, {self.start_time}, {self.end_time}, {self.is_optional})'

@problem_fact
class OptapyEmployee:
    def __init__(self, employee_id, contract_ids):
        self.employee_id = employee_id
        self.contract_ids = contract_ids

    def __str__(self):
        return f'Employee({self.employee_id}, {self.contract_ids})'
