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

from prolothar_ca.model.ca.dataset import CaDataset
from prolothar_ca.model.ca.example import CaExample
from prolothar_ca.model.ca.obj import CaObject, CaObjectType
from prolothar_ca.model.ca.relation import CaRelation, CaRelationType
from prolothar_ca.model.ca.variable_type import CaBoolean, CaNumber

class CaTarget(ABC):
    @abstractmethod
    def transform_to_boolean_relations(self, dataset: CaDataset) -> tuple[CaDataset, list[str]]:
        """
        transforms the dataset such that the target concept is available as a list
        of boolean valued relations.

        returns a tuple (transformed dataset, list of boolean target relations)
        """

@dataclass
class RelationTarget(CaTarget):
    relation_name: str

    def transform_to_boolean_relations(self, dataset: CaDataset) -> tuple[CaDataset, list[str]]:
        if isinstance(dataset.get_relation_type(self.relation_name).value_type, CaBoolean):
            return dataset, [self.relation_name]
        elif isinstance(dataset.get_relation_type(self.relation_name).value_type, CaNumber):
            value_to_relation_name = {
                relation.value: f'{self.relation_name}_{relation.value}'
                for example in dataset
                for relation in example.relations[self.relation_name]
            }
            transformed_dataset = CaDataset(
                {
                    object_type.name: object_type
                    for object_type in dataset.get_object_types()
                },
                {
                    relation.name: relation
                    for relation in dataset.get_relation_types()
                    if relation.name != self.relation_name
                } | {
                    new_relation_name: CaRelationType(
                        new_relation_name,
                        dataset.get_relation_type(self.relation_name).parameter_types,
                        CaBoolean()
                    )
                    for new_relation_name in value_to_relation_name.values()
                }
            )
            for example in dataset:
                transformed_dataset.add_example(CaExample(
                    example.all_objects_per_type,
                    {
                        relation_name: relation_set
                        for relation_name, relation_set in example.relations.items()
                        if relation_name != self.relation_name
                    } | {
                        new_relation_name: set(CaRelation(
                            new_relation_name,
                            relation.objects,
                            relation.value == value
                        ) for relation in example.relations[self.relation_name])
                        for value, new_relation_name in value_to_relation_name.items()
                    },
                    example.is_valid_solution
                ))
            return transformed_dataset, list(value_to_relation_name.values())
        else:
            raise NotImplementedError()

@dataclass
class BooleanRelationListTarget(CaTarget):
    relation_name_list: list[str]

    def transform_to_boolean_relations(self, dataset: CaDataset) -> tuple[CaDataset, list[str]]:
        return dataset, self.relation_name_list

@dataclass
class FeatureValueTarget(CaTarget):
    type_name: str
    feature_name: str

    def transform_to_boolean_relations(self, dataset: CaDataset) -> tuple[CaDataset, list[str]]:
        """
        we remove the feature from the given object type definition and
        from all individual objects and replace it with a relation that
        has a single object as its parameter
        """
        new_relation_name = f'{self.type_name}_{self.feature_name}'
        transformed_dataset = CaDataset(
            {
                object_type.name: object_type
                for object_type in dataset.get_object_types()
                if object_type.name != self.type_name
            } | {
                self.type_name: CaObjectType(self.type_name, {
                    feature_name: feature_type
                    for feature_name, feature_type
                    in dataset.get_object_type(self.type_name).feature_definition.items()
                    if feature_name != self.feature_name
                })
            },
            {
                relation.name: relation
                for relation in dataset.get_relation_types()
            } | {
                new_relation_name: CaRelationType(
                    new_relation_name,
                    [self.type_name],
                    dataset.get_object_type(self.type_name).feature_definition[self.feature_name]
                )
            }
        )
        for example in dataset:
            object_id_to_new_object = {
                an_object.object_id: CaObject(
                    an_object.object_id,
                    an_object.type_name,
                    {
                        feature_name: feature_value
                        for feature_name, feature_value in an_object.features.items()
                        if feature_name != self.feature_name
                    }
                )
                for an_object in example.all_objects_per_type[self.type_name]
            }
            transformed_dataset.add_example(CaExample(
                {
                    object_type: object_set
                    for object_type, object_set in example.all_objects_per_type.items()
                    if object_type != self.type_name
                } | {
                    self.type_name: set(
                        object_id_to_new_object[an_object.object_id]
                        for an_object in example.all_objects_per_type[self.type_name]
                    )
                },
                {
                    relation_name: set(CaRelation(
                        relation_name,
                        tuple(object_id_to_new_object.get(o.object_id, o) for o in relation.objects),
                        relation.value
                    ) for relation in relation_set)
                    for relation_name, relation_set in example.relations
                } | {
                    new_relation_name: set(
                        CaRelation(
                            new_relation_name,
                            (object_id_to_new_object[an_object.object_id],),
                            an_object.features[self.feature_name]
                        )
                        for an_object in example.all_objects_per_type[self.type_name]
                    )
                },
                example.is_valid_solution
            ))
        return RelationTarget(new_relation_name).transform_to_boolean_relations(transformed_dataset)