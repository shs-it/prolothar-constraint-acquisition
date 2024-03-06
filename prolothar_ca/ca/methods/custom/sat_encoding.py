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

from prolothar_ca.model.ca.example import CaExample
from prolothar_ca.model.ca import CaDataset
from prolothar_ca.model.ca.relation import CaRelationType
from prolothar_ca.model.sat.variable import Value

from prolothar_ca.model.sat.variable import Variable

SatEncodedExample = dict[Variable, Value]

def create_homgenous_sat_encoded_dataset(
        dataset: CaDataset, target_relation: CaRelationType,
        datagraph) -> list[SatEncodedExample]:
    return [
        create_sat_encoded_example(example, target_relation, datagraph)
        for example in dataset
    ]

def create_heterogenous_sat_encoded_dataset(
        dataset: CaDataset, target_relation: CaRelationType,
        datagraph_list: list) -> list[SatEncodedExample]:
    return [
        create_sat_encoded_example(example, target_relation, datagraph)
        for example, datagraph in zip(dataset, datagraph_list)
    ]

def create_sat_encoded_example(
        example: CaExample, target_relation: CaRelationType,
        datagraph) -> SatEncodedExample:
    encoded_example = {}
    for relation in example.relations[target_relation.name]:
        try:
            encoded_example[datagraph.get_target_variable(relation)] = Value.TRUE if relation.value else Value.FALSE
        except KeyError as e:
            # if we downsampled the number of 0s in the target variables,
            # there might not exists a mapping for this relation.
            # otherwise this is an unplanned exception!
            if relation.value:
                raise e
    return encoded_example