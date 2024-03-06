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

from typing import Iterable
from cpython.set cimport PySet_Add

from prolothar_common import validate as validate_utils

from prolothar_ca.model.ca.relation import CaRelation
from prolothar_ca.model.ca.obj cimport CaObject

cdef class CaExample:

    def __init__(self, dict all_objects_per_type, dict relations, bint is_valid_solution, bint validate = True):
        self.all_objects_per_type = all_objects_per_type
        self.relations = relations
        self.is_valid_solution = is_valid_solution
        if validate:
            self.__validate_state()
        self.__reinit()

    cdef __reinit(self):
        self.__relation_value_per_type_and_objects = {
            relation_type_name: {
                relation.objects: relation.value
                for relation in relation_set
            }
            for relation_type_name, relation_set in self.relations.items()
        }

        self.__objects_per_type_and_id = {
            type_name: { o.object_id: o for o in object_set }
            for type_name, object_set in self.all_objects_per_type.items()
        }

    def __validate_state(self):
        for type_name, object_set in self.all_objects_per_type.items():
            for an_object in object_set:
                validate_utils.equals(type_name, an_object.type_name)
        for relation_name, relation_set in self.relations.items():
            for relation in relation_set:
                validate_utils.equals(relation.name, relation_name)
                for o in relation.objects:
                    validate_utils.is_in(o, self.all_objects_per_type[o.type_name])

    def get_relation_value(self, relation_type_name: str, parameters: tuple) -> bool|int|float:
        return self.__relation_value_per_type_and_objects[relation_type_name][parameters]

    cdef bint get_boolean_relation_value(self, relation_type_name, parameters):
        return <bint>(<dict>self.__relation_value_per_type_and_objects[relation_type_name]).get(parameters, False)

    cpdef CaObject get_object_by_type_and_id(self, type_name, object_id):
        return <CaObject>(self.__objects_per_type_and_id[type_name][object_id])

    def iter_objects(self) -> Iterable[CaObject]:
        for object_set in self.all_objects_per_type.values():
            for o in object_set:
                yield o

    def iter_relations(self) -> Iterable[CaRelation]:
        for relation_set in self.relations.values():
            for relation in relation_set:
                yield relation

    cpdef add_relation(self, CaRelation relation, bint validate = True):
        if validate:
            for o in relation.objects:
                validate_utils.is_in(o, self.all_objects_per_type[o.type_name])
        try:
            PySet_Add(<set>self.relations[relation.name], relation)
            (<dict>self.__relation_value_per_type_and_objects[relation.name])[relation.objects] = relation.value
        except KeyError:
            self.relations[relation.name] = {relation}
            self.__relation_value_per_type_and_objects[relation.name] = {
                relation.objects: relation.value
            }

    def set_relation_value(self, CaRelation relation, new_value):
        relation.value = new_value
        self.__relation_value_per_type_and_objects[relation.name][relation.objects] = new_value

    cpdef remove_all_objects_not_in_set(self, set objects_to_keep):
        for object_set in self.all_objects_per_type.values():
            (<set>object_set).intersection_update(objects_to_keep)
        cdef set filtered_relations
        for relation_name, relation_set in self.relations.items():
            filtered_relations = set()
            for relation in (<set>relation_set):
                for o in (<CaRelation>relation).objects:
                    if o not in objects_to_keep:
                        break
                else:
                    filtered_relations.add(relation)
            self.relations[relation_name] = filtered_relations
        self.__reinit()
