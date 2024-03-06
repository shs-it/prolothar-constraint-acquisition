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

from prolothar_common import validate

cdef class CaObject:
    def __init__(self, str object_id, str type_name, dict features):
        self.object_id = object_id
        self.type_name = type_name
        self.features = features
        self.__hash = hash(self.object_id)

    def __hash__(self):
        return self.__hash

    def __eq__(self, other: 'CaObject'):
        return self.object_id == other.object_id and self.type_name == other.type_name

    def __repr__(self):
        return f'CaObject({self.object_id}, {self.type_name}, {self.features})'

cdef class CaObjectType:
    """
    defines a class of objects with the same type.
    all objects of the same type share a common
    features definition.
    """

    def __init__(self, str name, dict feature_definition):
        self.name = name
        self.feature_definition = feature_definition

    cpdef validate_object(self, CaObject an_object):
        """
        throws an error if the given object does not conform to this
        object type definition
        """
        validate.equals(self.name, an_object.type_name)
        validate.equals(self.feature_definition.keys(), an_object.features.keys())