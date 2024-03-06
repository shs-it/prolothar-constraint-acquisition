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

from optapy import planning_entity, planning_id, planning_variable

from prolothar_ca.solver.optapy.rostering.facts import OptapyEmployee, OptapyShift

@planning_entity
class OptapyShiftAssignment:

    def __init__(self, assignment_id, shift, employee=None):
        self.assignment_id = assignment_id
        self.shift = shift
        self.employee = employee

    @planning_id
    def get_id(self):
        return self.assignment_id

    @planning_variable(OptapyShift, value_range_provider_refs=['shiftRange'])
    def get_shift(self):
        return self.shift

    def set_shift(self, shift):
        self.shift = shift

    @planning_variable(OptapyEmployee, value_range_provider_refs=['employeeRange'], nullable=True)
    def get_employee(self):
        return self.employee

    def set_employee(self, employee):
        self.employee = employee

    def __repr__(self) -> str:
        return f'ShiftAssignment({self.shift}, {self.employee})'

