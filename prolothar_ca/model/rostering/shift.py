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

from dataclasses import dataclass


from datetime import time

from prolothar_common import validate

@dataclass(frozen=True)
class Shift:
    shift_id: str
    shift_name: str
    start_time: time
    end_time: time

    def __post_init__(self):
        validate.is_not_none(self.shift_id)
        validate.is_not_none(self.shift_name)

    @property
    def duration_in_hours(self) -> float:
        if self.start_time < self.end_time:
            return self.end_time.hour - self.start_time.hour
        else:
            return self.end_time.hour + 24 - self.start_time.hour