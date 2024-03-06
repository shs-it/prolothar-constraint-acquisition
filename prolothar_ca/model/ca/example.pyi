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

from prolothar_ca.model.ca.obj import CaObject
from prolothar_ca.model.ca.relation import CaRelation

class CaExample:
    all_objects_per_type: dict[str, set[CaObject]]
    relations: dict[str, set[CaRelation]]
    is_valid_solution: bool

    def __init__(
            self, parameters: dict[str, CaObject], all_objects_per_type: dict[str, set[CaObject]],
            relations: dict[str, set[CaRelation]], is_valid_solution: bool, validate: bool = True):
        ...

    def get_object_by_type_and_id(self, type_name, object_id) -> CaObject:
        ...
    def get_relation_value(self, relation_type_name: str, parameters: tuple[CaObject]) -> bool|float|int:
        ...
    def add_relation(self, relation: CaRelation, validate: bool = True):
        ...
    def remove_all_objects_not_in_set(self, objects_to_keep: set[CaObject]):
        ...

