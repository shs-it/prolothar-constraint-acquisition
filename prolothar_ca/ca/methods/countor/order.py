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
from dataclasses import dataclass

from prolothar_ca.model.ca.obj import CaObject, CaObjectType


class ObjectOrder(ABC):
    @abstractmethod
    def sort_objects(self, object_set: set[CaObject]) -> list[CaObject]:
        """
        sorts the given objects depending on the concrete subclass implementation
        """

class OrderByObjectId:
    def sort_objects(self, object_set: set[CaObject]) -> list[CaObject]:
        return sorted(object_set, key=lambda o: o.object_id)

@dataclass
class OrderByFeature:
    type_name: str
    feature_name: str

    def sort_objects(self, object_set: set[CaObject]) -> list[CaObject]:
        if not object_set:
            return []
        if next(iter(object_set)).type_name == self.type_name:
            return sorted(object_set, key=lambda o: o.features[self.feature_name])
        else:
            return OrderByObjectId().sort_objects(object_set)