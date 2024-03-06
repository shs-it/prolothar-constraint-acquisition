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

from itertools import product
from more_itertools import ilen
from typing import Iterator
import pickle
from prolothar_common import validate as validate_utils

from prolothar_ca.model.ca.example import CaExample
from prolothar_ca.model.ca.obj import CaObjectType, CaObject
from prolothar_ca.model.ca.relation import CaRelationType
from prolothar_ca.model.ca.variable_type import CaNumber, CaBoolean

class CaDataset:

    def __init__(
            self, types_definition: dict[str, CaObjectType],
            relations_definition: dict[str, CaRelationType]):
        for type_name, object_type in types_definition.items():
            validate_utils.equals(type_name, object_type.name)
        for type_name, relation_type in types_definition.items():
            validate_utils.equals(type_name, relation_type.name)
        self.__types_definition = types_definition
        self.__relations_definition = relations_definition
        self.__examples = []

    def empty_copy(self) -> 'CaDataset':
        """
        creates a new empty dataset (i.e. without examples) with the same definition as this dataset
        """
        return CaDataset(self.__types_definition, self.__relations_definition)

    def add_example(self, example: CaExample, validate: bool = True):
        if validate:
            validate_utils.collection.is_subset(example.all_objects_per_type.keys(), self.__types_definition.keys())
            validate_utils.collection.is_subset(example.relations.keys(), self.__relations_definition.keys())
            # check that relations is defined for all possible parameter assignments
            for relation_name, relation_set in example.relations.items():
                validate_utils.equals(
                    ilen(product(*[
                        example.all_objects_per_type[type_name]
                        for type_name in self.__relations_definition[relation_name].parameter_types])),
                    len(relation_set)
                )
            for object_set in example.all_objects_per_type.values():
                for an_object in object_set:
                    self.__types_definition[an_object.type_name].validate_object(an_object)
        self.__examples.append(example)

    def get_max_size_of_object_set(self) -> int:
        max_size = 0
        for example in self.__examples:
            for object_set in example.all_objects_per_type.values():
                if len(object_set) > max_size:
                    max_size = len(object_set)
        return max_size

    def get_object_type(self, type_name: str) -> CaObjectType:
        return self.__types_definition[type_name]

    def has_object_type(self, type_name: str) -> bool:
        return type_name in self.__types_definition

    def get_object_types(self) -> list[CaObjectType]:
        return list(self.__types_definition.values())

    def get_relation_type(self, type_name: str) -> CaRelationType:
        return self.__relations_definition[type_name]

    def get_relation_types(self) -> list[CaRelationType]:
        return list(self.__relations_definition.values())

    def get_nr_of_numeric_features(self, object_type: str) -> int:
        nr_of_numeric_features = 0
        for feature_type in self.__types_definition[object_type].feature_definition.values():
            if isinstance(feature_type, CaNumber):
                nr_of_numeric_features += 1
        return nr_of_numeric_features

    def get_nr_of_boolean_features(self, object_type: str) -> int:
        nr_of_numeric_features = 0
        for feature_type in self.__types_definition[object_type].feature_definition.values():
            if isinstance(feature_type, CaBoolean):
                nr_of_numeric_features += 1
        return nr_of_numeric_features

    def compute_minimum_feature_value(self, object_type: CaObjectType, feature_name: str) -> float:
        return min(
            o.features[feature_name]
            for example in self
            for o in example.all_objects_per_type[object_type.name]
        )

    def compute_maximum_feature_value(self, object_type: CaObjectType, feature_name: str) -> float:
        return max(
            o.features[feature_name]
            for example in self
            for o in example.all_objects_per_type[object_type.name]
        )

    def get_total_nr_of_boolean_functions(self) -> int:
        """
        returns the total number of all boolean features and relations
        """
        result = 0
        for object_type in self.get_object_types():
            result += self.get_nr_of_boolean_features(object_type.name)
        for relation_type in self.get_relation_types():
            if isinstance(relation_type.value_type, CaBoolean):
                result += 1
        return result

    def get_total_nr_of_numeric_functions(self) -> int:
        """
        returns the total number of all numeric features and relations
        """
        result = 0
        for object_type in self.get_object_types():
            result += self.get_nr_of_numeric_features(object_type.name)
        for relation_type in self.get_relation_types():
            if isinstance(relation_type.value_type, CaNumber):
                result += 1
        return result

    def is_relation_true_for_any_example(self, relation_type_name: str, parameters: tuple[CaObject]) -> bool:
        for example in self:
            if example.get_relation_value(relation_type_name, parameters):
                return True
        return False

    def __len__(self):
        """
        returns the number of examples in this dataset
        """
        return len(self.__examples)

    def __iter__(self) -> Iterator[CaExample]:
        return iter(self.__examples)

    def fast_deepcopy(self) -> 'CaDataset':
        return pickle.loads(pickle.dumps(self))
