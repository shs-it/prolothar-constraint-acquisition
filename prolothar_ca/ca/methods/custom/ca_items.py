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

from typing import List, Tuple

from prolothar_ca.ca.methods.custom.model.cross_product_filter import CrossProductFilter
from prolothar_ca.ca.methods.custom.model.cross_product_filter import AndCrossProductFilter
from prolothar_ca.ca.methods.custom.model.cross_product_filter import NumericFeature
from prolothar_ca.ca.methods.custom.model.cross_product_filter import BooleanFeature
from prolothar_ca.ca.methods.custom.model.cross_product_filter import IntegerConstant
from prolothar_ca.ca.methods.custom.model.cross_product_filter import Absolute
from prolothar_ca.ca.methods.custom.model.cross_product_filter import ObjectEquality
from prolothar_ca.ca.methods.custom.model.cross_product_filter import NumericFilter
from prolothar_ca.ca.methods.custom.model.cross_product_filter import Difference
from prolothar_ca.ca.methods.custom.model.cross_product_filter import Sum
from prolothar_ca.ca.methods.custom.model.cross_product_filter import Quotient
from prolothar_ca.ca.methods.custom.model.cross_product_filter import IntegerQuotient

NUMERIC_OPERATOR_MAP = {
    '<': NumericFilter.LT,
    '<=': NumericFilter.LE,
    '=': NumericFilter.EQ,
    '>': NumericFilter.GT,
}

NUMERIC_FILTER_ARITHMETIC_OPERATORS = [
    ('-', Difference),
    ('+', Sum),
    ('//', IntegerQuotient),
    ('/', Quotient)
]

def pattern_to_cross_product_filter(
        pattern: List[str], cross_product_cardinality: int,
        nr_of_numeric_features_per_parameter: Tuple[int],
        nr_of_boolean_features_per_parameter: Tuple[int]) -> CrossProductFilter:
    if len(pattern) == 1:
        return __parse_item_to_cross_product_filter(
            pattern[0], cross_product_cardinality,
            nr_of_numeric_features_per_parameter,
            nr_of_boolean_features_per_parameter)
    else:
        return AndCrossProductFilter([
            __parse_item_to_cross_product_filter(
                item, cross_product_cardinality,
                nr_of_numeric_features_per_parameter,
                nr_of_boolean_features_per_parameter)
            for item in pattern
        ])

def __parse_item_to_cross_product_filter(
        item: str, cross_product_cardinality: int,
        nr_of_numeric_features_per_parameter: Tuple[int],
        nr_of_boolean_features_per_parameter: Tuple[int]) -> CrossProductFilter:
    if ' ' not in item:
        return __parse_boolean_filter_value(item, cross_product_cardinality, nr_of_boolean_features_per_parameter)
    left, op, right = item.split(' ')
    if '=' == op and '.' not in left and '.' not in right:
        return ObjectEquality(int(left), int(right), len(nr_of_boolean_features_per_parameter))
    if '&' == op:
        return AndCrossProductFilter([
            __parse_boolean_filter_value(
                left, cross_product_cardinality, nr_of_boolean_features_per_parameter),
            __parse_boolean_filter_value(
                right, cross_product_cardinality, nr_of_boolean_features_per_parameter)
        ])
    else:
        try:
            return NumericFilter(
                __parse_numeric_filter_value(
                    left, cross_product_cardinality, nr_of_numeric_features_per_parameter
                ),
                NUMERIC_OPERATOR_MAP[op],
                __parse_numeric_filter_value(
                    right, cross_product_cardinality, nr_of_numeric_features_per_parameter
                )
            )
        except KeyError:
            raise NotImplementedError(item)

def __parse_numeric_filter_value(
        pattern: str, cross_product_cardinality: int,
        nr_of_numeric_features_per_parameter: Tuple[int]):
    if pattern.startswith('|') and pattern.endswith('|'):
        return Absolute(__parse_numeric_filter_value(
            pattern[1:-1], cross_product_cardinality, nr_of_numeric_features_per_parameter))
    for operator, constructor in NUMERIC_FILTER_ARITHMETIC_OPERATORS:
        if operator in pattern:
            left, right = pattern.split(operator)
            return constructor(
                __parse_numeric_filter_value(
                    left, cross_product_cardinality,
                    nr_of_numeric_features_per_parameter
                ),
                __parse_numeric_filter_value(
                    right, cross_product_cardinality,
                    nr_of_numeric_features_per_parameter
                )
            )
    if '.' in pattern:
        parameter_index, feature_name = pattern.split('.')
        parameter_index = int(parameter_index)
        return NumericFeature(
            feature_name, parameter_index,
            cross_product_cardinality,
            nr_of_numeric_features_per_parameter[parameter_index]
        )
    else:
        return IntegerConstant(int(pattern))

def __parse_boolean_filter_value(
        pattern: str, cross_product_cardinality: int,
        nr_of_boolean_features_per_parameter: Tuple[int]):
    if '.' in pattern:
        parameter_index, feature_name = pattern.split('.')
        parameter_index = int(parameter_index)
        return BooleanFeature(
            feature_name, parameter_index,
            cross_product_cardinality,
            nr_of_boolean_features_per_parameter[parameter_index]
        )
    else:
        raise NotImplementedError(pattern)