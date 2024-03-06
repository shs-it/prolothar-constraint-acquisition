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

from prolothar_ca.model.ca.constraints.query import Query
from prolothar_ca.model.ca.constraints.constraint import CaConstraint
from prolothar_ca.model.ca.example import CaExample
from prolothar_ca.model.ca.obj import CaObject
from prolothar_ca.model.ca.relation import CaRelationType


class NumericExpression:
    def evaluate(self, example: CaExample, variables: dict[str, CaObject]) -> float:
        """
        evaluates and returns the value of this numeric expression
        """
        ...

    def __lt__(self, other: 'NumericExpression'):
        """
        returns True if this numeric expression is always smaller than another numeric expression
        """
        ...

    def __gt__(self, other: 'NumericExpression'):
        """
        returns True if this numeric expression is always greater than another numeric expression
        """
        ...

    def count_nr_of_terms(self) -> int:
        """
        counts the number of terms in this numeric expression. the more terms,
        the more complex the expression is supposed to be
        """
        ...

class Constant(NumericExpression):
    value: int

    def __init__(self, value: int):
        self.value = value

class NumericVariable(NumericExpression):
    variable_name: str

    def __init__(self, variable_name: str): ...

class Modulo(NumericExpression):
    a: NumericExpression
    b: NumericExpression

    def __init__(self, a: NumericExpression, b: NumericExpression): ...

class IntegerDivision(NumericExpression):
    a: NumericExpression
    b: NumericExpression

    def __init__(self, a: NumericExpression, b: NumericExpression): ...

class Division(NumericExpression):
    a: NumericExpression
    b: NumericExpression

    def __init__(self, a: NumericExpression, b: NumericExpression): ...

class NumericFeature(NumericExpression):
    object_type: str
    object_id: str
    feature_name: str

    def __init__(self, object_type: str, object_id: str, feature_name: str): ...

class NumericRelation(NumericExpression):
    relation_type: CaRelationType
    object_id_list: list[str]

    def __init__(self, relation_type: CaRelationType, object_id_list: list[str]): ...

class Count(NumericExpression):
    query: Query

    def __init__(self, query: Query): ...

class AggregateSum(NumericExpression):
    expression: NumericExpression
    query: Query

    def __init__(self, expression: NumericExpression, query: Query): ...

class Absolute(NumericExpression):
    expression: NumericExpression

    def __init__(self, expression: NumericExpression): ...

class Difference(NumericExpression):
    left_expression: NumericExpression
    right_expression: NumericExpression

    def __init__(self, left_expression: NumericExpression, right_expression: NumericExpression): ...

class Sum(NumericExpression):
    left_expression: NumericExpression
    right_expression: NumericExpression

    def __init__(self, left_expression: NumericExpression, right_expression: NumericExpression): ...

class Between(CaConstraint):
    lower: NumericExpression
    x: NumericExpression
    upper: NumericExpression

    def __init__(self, lower: NumericExpression, x: NumericExpression, upper: NumericExpression): ...

class BinaryNumericCaConstraint(CaConstraint):
    a: NumericExpression
    b: NumericExpression

    def __init__(self, a: NumericExpression, b: NumericExpression): ...

class Equal(BinaryNumericCaConstraint): ...

class NotEqual(BinaryNumericCaConstraint): ...

class Greater(BinaryNumericCaConstraint): ...

class GreaterOrEqual(BinaryNumericCaConstraint): ...

class LessOrEqual(BinaryNumericCaConstraint): ...

class Less(BinaryNumericCaConstraint): ...
