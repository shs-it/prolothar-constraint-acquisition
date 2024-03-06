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

cdef class Object:

    def __init__(self, str name, ObjectType object_type):
        self.name = name
        self.object_type = object_type

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other: 'Object'):
        return (
            isinstance(other, Object) and
            self.name == (<Object>other).name and
            self.object_type.name == (<Object>other).object_type.name
        )

