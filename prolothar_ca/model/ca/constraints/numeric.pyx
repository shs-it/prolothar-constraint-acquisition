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

from itertools import pairwise

from prolothar_ca.model.ca.constraints.conjunction import Or
from prolothar_ca.model.ca.constraints.query cimport AllOfTypeOrderBy, Query
from prolothar_ca.model.ca.constraints.constraint cimport CaConstraint
from prolothar_ca.model.ca.example cimport CaExample
from prolothar_ca.model.ca.obj cimport CaObject
from prolothar_ca.model.ca.relation cimport CaRelationType


cdef class NumericExpression:
    cpdef double evaluate(self, CaExample example, dict variables):
        """
        evaluates and returns the value of this numeric expression
        """
        raise NotImplementedError()

    def __lt__(self, other: 'NumericExpression'):
        """
        returns True if this numeric expression is always smaller than another numeric expression
        """
        raise NotImplementedError()

    def __gt__(self, other: 'NumericExpression'):
        """
        returns True if this numeric expression is always greater than another numeric expression
        """
        raise NotImplementedError()

    cpdef int count_nr_of_terms(self):
        """
        counts the number of terms in this numeric expression. the more terms,
        the more complex the expression is supposed to be
        """

cdef class Constant(NumericExpression):
    cdef public int value

    def __init__(self, int value):
        self.value = value

    cpdef double evaluate(self, CaExample example, dict variables):
        return self.value

    def __lt__(self, other: NumericExpression):
        return isinstance(other, Constant) and self.value < other.value

    def __gt__(self, other: NumericExpression):
        return isinstance(other, Constant) and self.value > other.value

    def __str__(self) -> str:
        return str(self.value)

    cpdef int count_nr_of_terms(self):
        return 1

cdef class NumericVariable(NumericExpression):
    cdef public str variable_name

    def __init__(self, str variable_name):
        self.variable_name = variable_name

    cpdef double evaluate(self, CaExample example, dict variables):
        return variables[self.variable_name]

    def __lt__(self, other: NumericExpression):
        return False

    def __gt__(self, other: NumericExpression):
        return False

    def __str__(self) -> str:
        return str(self.variable_name)

    cpdef int count_nr_of_terms(self):
        return 1

cdef class Modulo(NumericExpression):
    cdef public NumericExpression a
    cdef public NumericExpression b

    def __init__(self, NumericExpression a, NumericExpression b):
        self.a = a
        self.b = b

    cpdef double evaluate(self, CaExample example, dict variables):
        return self.a.evaluate(example, variables) % self.b.evaluate(example, variables)

    def __lt__(self, other: NumericExpression):
        return False

    def __gt__(self, other: NumericExpression):
        return False

    def __str__(self) -> str:
        return f'{self.a} % {self.b}'

    cpdef int count_nr_of_terms(self):
        return self.a.count_nr_of_terms() + self.b.count_nr_of_terms()

cdef class IntegerDivision(NumericExpression):
    cdef public NumericExpression a
    cdef public NumericExpression b

    def __init__(self, NumericExpression a, NumericExpression b):
        self.a = a
        self.b = b

    cpdef double evaluate(self, CaExample example, dict variables):
        return self.a.evaluate(example, variables) // self.b.evaluate(example, variables)

    def __lt__(self, other: NumericExpression):
        return False

    def __gt__(self, other: NumericExpression):
        return False

    def __str__(self) -> str:
        return f'{self.a} // {self.b}'

    cpdef int count_nr_of_terms(self):
        return self.a.count_nr_of_terms() + self.b.count_nr_of_terms()

cdef class Division(NumericExpression):
    cdef public NumericExpression a
    cdef public NumericExpression b

    def __init__(self, NumericExpression a, NumericExpression b):
        self.a = a
        self.b = b

    cpdef double evaluate(self, CaExample example, dict variables):
        return self.a.evaluate(example, variables) / self.b.evaluate(example, variables)

    def __lt__(self, other: NumericExpression):
        return False

    def __gt__(self, other: NumericExpression):
        return False

    def __str__(self) -> str:
        return f'{self.a} / {self.b}'

    cpdef int count_nr_of_terms(self):
        return self.a.count_nr_of_terms() + self.b.count_nr_of_terms()

cdef class NumericFeature(NumericExpression):
    cdef public str object_type
    cdef public str object_id
    cdef public str feature_name

    def __init__(self, str object_type, str object_id, str feature_name):
        self.object_type = object_type
        self.object_id = object_id
        self.feature_name = feature_name

    cpdef double evaluate(self, CaExample example, dict variables):
        try:
            the_object = variables[self.object_id]
        except KeyError:
            the_object = example.get_object_by_type_and_id(self.object_type, self.object_id)
        return (<CaObject>the_object).features[self.feature_name]

    def __lt__(self, other: NumericExpression):
        return False

    def __gt__(self, other: NumericExpression):
        return False

    def __str__(self) -> str:
        return f'{self.object_id}.{self.feature_name}'

    cpdef int count_nr_of_terms(self):
        return 1

cdef class NumericRelation(NumericExpression):
    cdef public CaRelationType relation_type
    cdef list object_id_list

    def __init__(self, CaRelationType relation_type, list object_id_list):
        self.relation_type = relation_type
        self.object_id_list = object_id_list

    cpdef double evaluate(self, CaExample example, dict variables):
        cdef list parameters = []
        for type_name, object_id in zip(self.relation_type.parameter_types, self.object_id_list):
            try:
                parameters.append(example.get_object_by_type_and_id(type_name, object_id))
            except KeyError:
                parameters.append(variables[object_id])
        example.get_relation_value(self.relation_type.name, tuple(parameters))

    def __lt__(self, other: NumericExpression):
        return False

    def __gt__(self, other: NumericExpression):
        return False

    def __str__(self) -> str:
        return f'{self.relation_type.name}({",".join(self.object_id_list)})'

    cpdef int count_nr_of_terms(self):
        return 1

cdef class Count(NumericExpression):
    cdef public Query query

    def __init__(self, Query query):
        self.query = query

    cpdef double evaluate(self, CaExample example, dict variables):
        return len(self.query.evaluate(example, variables))

    def __lt__(self, other: NumericExpression):
        return isinstance(other, Count) and self.query.is_more_restrictive(other.query)

    def __gt__(self, other: NumericExpression):
        return isinstance(other, Count) and other.query.is_more_restrictive(self.query)

    def __str__(self) -> str:
        return f'count({self.query})'

    cpdef int count_nr_of_terms(self):
        return self.query.count_nr_of_terms()

cdef class AggregateSum(NumericExpression):
    cdef public NumericExpression expression
    cdef public Query query

    def __init__(self, NumericExpression expression, Query query):
        self.expression = expression
        self.query = query

    cpdef double evaluate(self, CaExample example, dict variables):
        cdef double s = 0
        cdef dict extended_variables
        for element in self.query.evaluate(example, variables):
            extended_variables = dict(variables)
            extended_variables.update(<dict>element)
            s += self.expression.evaluate(example, extended_variables)
        return s

    def __lt__(self, other: NumericExpression):
        return (
            isinstance(other, AggregateSum) and
            (
                (
                    self.expression == other.expression and
                    self.query.is_more_restrictive(other.query)
                )
                or
                (
                    self.query == other.query and
                    self.expression < other.expression
                )
            )
        )

    def __gt__(self, other: NumericExpression):
        return (
            isinstance(other, AggregateSum) and
            (
                (
                    self.expression == other.expression and
                    other.query.is_more_restrictive(self.query)
                )
                or
                (
                    self.query == other.query and
                    self.expression > other.expression
                )
            )
        )

    def __str__(self) -> str:
        return f'sum({self.expression} for {self.query})'

    cpdef int count_nr_of_terms(self):
        return self.query.count_nr_of_terms() + self.expression.count_nr_of_terms()

cdef class Absolute(NumericExpression):
    cdef public NumericExpression expression

    def __init__(self, NumericExpression expression):
        self.expression = expression

    cpdef double evaluate(self, CaExample example, dict variables):
        return abs(self.expression.evaluate(example, variables))

    def __lt__(self, other: NumericExpression):
        return (
            isinstance(self, Constant) and
            isinstance(other, Constant) and
            abs(self.value) < other.value
        )

    def __gt__(self, other: NumericExpression):
        return (
            isinstance(self, Constant) and
            isinstance(other, Constant) and
            abs(self.value) > other.value
        )

    def __str__(self) -> str:
        return f'|{self.expression}|'

    cpdef int count_nr_of_terms(self):
        return self.expression.count_nr_of_terms()

cdef class Difference(NumericExpression):
    cdef public NumericExpression left_expression
    cdef public NumericExpression right_expression

    def __init__(self, NumericExpression left_expression, NumericExpression right_expression):
        self.left_expression = left_expression
        self.right_expression = right_expression

    cpdef double evaluate(self, CaExample example, dict variables):
        return (
            self.left_expression.evaluate(example, variables) -
            self.right_expression.evaluate(example, variables)
        )

    def __lt__(self, other: NumericExpression):
        return self.left_expression < other and self.right_expression > Constant(0)

    def __gt__(self, other: NumericExpression):
        return False

    def __str__(self) -> str:
        return f'{self.left_expression} - {self.right_expression}'

    cpdef int count_nr_of_terms(self):
        return self.left_expression.count_nr_of_terms() + self.right_expression.count_nr_of_terms()

cdef class Sum(NumericExpression):
    cdef public NumericExpression left_expression
    cdef public NumericExpression right_expression

    def __init__(self, NumericExpression left_expression, NumericExpression right_expression):
        self.left_expression = left_expression
        self.right_expression = right_expression

    cpdef double evaluate(self, CaExample example, dict variables):
        return (
            self.left_expression.evaluate(example, variables) +
            self.right_expression.evaluate(example, variables)
        )

    def __lt__(self, other: NumericExpression):
        return False

    def __gt__(self, other: NumericExpression):
        return self.left_expression > other or self.right_expression > other

    def __str__(self) -> str:
        return f'{self.left_expression} + {self.right_expression}'

    cpdef int count_nr_of_terms(self):
        return self.left_expression.count_nr_of_terms() + self.right_expression.count_nr_of_terms()

cdef class NumericQuery():
    def __str__(self) -> str:
        """
        returns a human readable representation of this query
        """
        raise NotImplementedError()

    def evaluate(self, example: CaExample, variables: dict) -> list:
        """
        evaluates this numeric query
        """
        raise NotImplementedError()

    cpdef int count_nr_of_terms(self):
        """
        counts the number of terms in this numeric query. the more terms the more
        complex the numeric query.
        """
        raise NotImplementedError()

cdef class MinimumOfNumericQuery(NumericExpression):
    cdef public NumericQuery query

    def __init__(self, NumericQuery query):
        self.query = query

    cpdef double evaluate(self, CaExample example, dict variables):
        return min(self.query.evaluate(example, variables))

    def __lt__(self, other: NumericExpression):
        return False

    def __gt__(self, other: NumericExpression):
        return False

    def __str__(self) -> str:
        return f'min({self.query})'

    cpdef int count_nr_of_terms(self):
        return self.query.count_nr_of_terms()

cdef class MaximumOfNumericQuery(NumericQuery):
    cdef public NumericQuery query

    def __init__(self, NumericQuery query):
        self.query = query

    cpdef double evaluate(self, CaExample example, dict variables):
        return max(self.query.evaluate(example, variables))

    def __lt__(self, other: NumericExpression):
        return False

    def __gt__(self, other: NumericExpression):
        return False

    def __str__(self) -> str:
        return f'max({self.query})'

    cpdef int count_nr_of_terms(self):
        return self.query.count_nr_of_terms()

cdef class CountConsecutive(NumericQuery):
    cdef public AllOfTypeOrderBy query
    cdef public str first_variable_name
    cdef public str second_variable_name
    cdef public CaConstraint constraint

    def __init__(self, AllOfTypeOrderBy query, str first_variable_name, str second_variable_name, CaConstraint constraint):
        self.query = query
        self.first_variable_name = first_variable_name
        self.second_variable_name = second_variable_name
        self.constraint = constraint

    cpdef list evaluate(self, CaExample example, dict variables):
        result_list = []
        current_consecutive = 1
        for a,b in pairwise(self.query.evaluate(example, variables)):
            if self.constraint.holds(example, variables | {
                self.first_variable_name: next(iter(a.values())),
                self.second_variable_name: next(iter(b.values()))
            }):
                current_consecutive += 1
            elif current_consecutive > 1:
                result_list.append(current_consecutive)
                current_consecutive = 1
        result_list.append(current_consecutive)
        return result_list

    def minimum(self) -> MinimumOfNumericQuery:
        return MinimumOfNumericQuery(self)

    def maximum(self) -> MaximumOfNumericQuery:
        return MaximumOfNumericQuery(self)

    def __str__(self) -> str:
        return f'count_consecutive({self.first_variable_name},{self.second_variable_name} in pairwise({self.query}) | {self.constraint})'

    cpdef int count_nr_of_terms(self):
        return 2 +  self.query.count_nr_of_terms() + self.constraint.count_nr_of_terms()

cdef class Between(CaConstraint):
    cdef public NumericExpression lower
    cdef public NumericExpression x
    cdef public NumericExpression upper

    def __init__(self, NumericExpression lower, NumericExpression x, NumericExpression upper):
        self.lower = lower
        self.x = x
        self.upper = upper

    cpdef int count_nr_of_terms(self):
        return (
            self.lower.count_nr_of_terms() +
            self.x.count_nr_of_terms() +
            self.upper.count_nr_of_terms()
        )

    cpdef bint holds(self, CaExample example, dict variables):
        return (
            self.lower.evaluate(example, variables) <= self.x.evaluate(example, variables)
            <= self.upper.evaluate(example, variables)
        )

    def is_more_restrictive(self, other: CaConstraint) -> bool:
        return (
            (isinstance(other, Between) and self.x == other.x and (
                (self.lower >= other.lower or self.upper <= other.upper) and
                (self.lower != other.lower or self.upper != other.upper)
            )) or
            (isinstance(other, Or) and self in other.term_list)
        )

    def __str__(self) -> str:
        return f'{self.lower} <= {self.x} <= {self.upper}'

cdef class BinaryNumericCaConstraint(CaConstraint):
    cdef public NumericExpression a
    cdef public NumericExpression b

    def __init__(self, NumericExpression a, NumericExpression b):
        self.a = a
        self.b = b

    cpdef int count_nr_of_terms(self):
        return self.a.count_nr_of_terms() + self.b.count_nr_of_terms()

cdef class Equal(BinaryNumericCaConstraint):

    cpdef bint holds(self, CaExample example, dict variables):
        return self.a.evaluate(example, variables) == self.b.evaluate(example, variables)

    def negated(self) -> 'NotEqual':
        return NotEqual(self.a, self.b)

    def is_more_restrictive(self, other: CaConstraint) -> bool:
        return (
            (isinstance(other, NotEqual) and self.a == other.a and self.b == other.b) or
            (isinstance(other, Or) and self in other.term_list)
        )

    def __str__(self) -> str:
        return f'{self.a} = {self.b}'

cdef class NotEqual(BinaryNumericCaConstraint):

    cpdef bint holds(self, CaExample example, dict variables):
        return self.a.evaluate(example, variables) == self.b.evaluate(example, variables)

    def negated(self) -> Equal:
        return Equal(self.a, self.b)

    def is_more_restrictive(self, other: CaConstraint) -> bool:
        return isinstance(other, Or) and self in other.term_list

    def __str__(self) -> str:
        return f'{self.a} != {self.b}'

cdef class Greater(BinaryNumericCaConstraint):

    cpdef bint holds(self, CaExample example, dict variables):
        return self.a.evaluate(example, variables) > self.b.evaluate(example, variables)

    def is_more_restrictive(self, other: CaConstraint) -> bool:
        return (
            isinstance(other, Greater) and
            other.a == self.a and
            self.b > other.b
        ) or (isinstance(other, Or) and self in other.term_list)

    def __str__(self) -> str:
        return f'{self.a} > {self.b}'

cdef class GreaterOrEqual(BinaryNumericCaConstraint):

    cpdef bint holds(self, CaExample example, dict variables):
        return self.a.evaluate(example, variables) >= self.b.evaluate(example, variables)

    def is_more_restrictive(self, other: CaConstraint) -> bool:
        return (
            isinstance(other, GreaterOrEqual) and
            other.a == self.a and
            self.b > other.b
        ) or (isinstance(other, Or) and self in other.term_list)

    def __str__(self) -> str:
        return f'{self.a} >= {self.b}'

cdef class LessOrEqual(BinaryNumericCaConstraint):

    cpdef bint holds(self, CaExample example, dict variables):
        return self.a.evaluate(example, variables) <= self.b.evaluate(example, variables)

    def is_more_restrictive(self, other: CaConstraint) -> bool:
        return (
            isinstance(other, LessOrEqual)
            and other.a == self.a
            and self.b < other.b
        ) or (isinstance(other, Or) and self in other.term_list)

    def __str__(self) -> str:
        return f'{self.a} <= {self.b}'

cdef class Less(BinaryNumericCaConstraint):

    cpdef bint holds(self, CaExample example, dict variables):
        return self.a.evaluate(example, variables) < self.b.evaluate(example, variables)

    def is_more_restrictive(self, other: CaConstraint) -> bool:
        return (
            isinstance(other, Less)
            and other.a == self.a
            and self.b < other.b
        ) or (isinstance(other, Or) and self in other.term_list)

    def __str__(self) -> str:
        return f'{self.a} < {self.b}'

