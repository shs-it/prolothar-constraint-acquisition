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
from prolothar_ca.model.pddl.numeric_expression import NumericExpression
from prolothar_ca.model.pddl.utils import check_parameter_names


cdef class Condition:
    cpdef bint holds(self, dict parameter_assignment, state, problem):
        raise NotImplementedError()

cdef class PredicateIsTrueCondition(Condition):

    def __init__(self, predicate, list parameter_names):
        check_parameter_names(predicate, parameter_names)
        self.__predicate = predicate
        self.__parameter_names = parameter_names

    def get_predicate(self):
        return self.__predicate

    def get_parameter_names(self) -> list[str]:
        return self.__parameter_names

    def to_pddl(self) -> str:
        return f'({self.__predicate.name} {" ".join("?" + p for p in self.__parameter_names)})'

    cpdef bint holds(self, dict parameter_assignment, state, problem):
        return state.is_predicate_true(self.__predicate, tuple(map(parameter_assignment.get, self.__parameter_names)))

    def __eq__(self, other):
        return (
            isinstance(other, PredicateIsTrueCondition) and
            self.__predicate == (<PredicateIsTrueCondition>other).__predicate and
            self.__parameter_names == (<PredicateIsTrueCondition>other).__parameter_names
        )

cdef class Greater(Condition):

    def __init__(self, expression_a, expression_b):
        self.__expression_a = NumericExpression.int_to_constant(expression_a)
        self.__expression_b = NumericExpression.int_to_constant(expression_b)

    def to_pddl(self) -> str:
        return f'(> {self.__expression_a.to_pddl()} {self.__expression_b.to_pddl()})'

    cpdef bint holds(self, dict parameter_assignment, state, problem):
        return (
            self.__expression_a.evaluate(parameter_assignment, state) >
            self.__expression_b.evaluate(parameter_assignment, state)
        )

    def __eq__(self, other):
        return (
            isinstance(other, Greater) and
            self.__expression_a == (<Greater>other).__expression_a and
            self.__expression_b == (<Greater>other).__expression_b
        )

cdef class GreaterOrEqual(Condition):

    def __init__(self, expression_a, expression_b):
        self.__expression_a = NumericExpression.int_to_constant(expression_a)
        self.__expression_b = NumericExpression.int_to_constant(expression_b)

    def to_pddl(self) -> str:
        return f'(>= {self.__expression_a.to_pddl()} {self.__expression_b.to_pddl()})'

    cpdef bint holds(self, dict parameter_assignment, state, problem):
        return (
            self.__expression_a.evaluate(parameter_assignment, state) >=
            self.__expression_b.evaluate(parameter_assignment, state)
        )

    def __eq__(self, other):
        return (
            isinstance(other, GreaterOrEqual) and
            self.__expression_a == (<GreaterOrEqual>other).__expression_a and
            self.__expression_b == (<GreaterOrEqual>other).__expression_b
        )

cdef class Less(Condition):

    def __init__(self, expression_a, expression_b):
        self.__expression_a = NumericExpression.int_to_constant(expression_a)
        self.__expression_b = NumericExpression.int_to_constant(expression_b)

    def to_pddl(self) -> str:
        return f'(< {self.__expression_a.to_pddl()} {self.__expression_b.to_pddl()})'

    cpdef bint holds(self, dict parameter_assignment, state, problem):
        return (
            self.__expression_a.evaluate(parameter_assignment, state) <
            self.__expression_b.evaluate(parameter_assignment, state)
        )

    def __eq__(self, other):
        return (
            isinstance(other, Less) and
            self.__expression_a == (<Less>other).__expression_a and
            self.__expression_b == (<Less>other).__expression_b
        )

cdef class LessOrEqual(Condition):

    def __init__(self, expression_a, expression_b):
        self.__expression_a = NumericExpression.int_to_constant(expression_a)
        self.__expression_b = NumericExpression.int_to_constant(expression_b)

    def to_pddl(self) -> str:
        return f'(<= {self.__expression_a.to_pddl()} {self.__expression_b.to_pddl()})'

    cpdef bint holds(self, dict parameter_assignment, state, problem):
        return (
            self.__expression_a.evaluate(parameter_assignment, state) <=
            self.__expression_b.evaluate(parameter_assignment, state)
        )

    def __eq__(self, other):
        return (
            isinstance(other, LessOrEqual) and
            self.__expression_a == (<LessOrEqual>other).__expression_a and
            self.__expression_b == (<LessOrEqual>other).__expression_b
        )

cdef class Equals(Condition):

    def __init__(self, expression_a, expression_b):
        self.__expression_a = NumericExpression.int_to_constant(expression_a)
        self.__expression_b = NumericExpression.int_to_constant(expression_b)

    def to_pddl(self) -> str:
        return f'(= {self.__expression_a.to_pddl()} {self.__expression_b.to_pddl()})'

    cpdef bint holds(self, dict parameter_assignment, state, problem):
        return (
            self.__expression_a.evaluate(parameter_assignment, state) ==
            self.__expression_b.evaluate(parameter_assignment, state)
        )

    def __eq__(self, other):
        return (
            isinstance(other, Equals) and
            self.__expression_a == (<Equals>other).__expression_a and
            self.__expression_b == (<Equals>other).__expression_b
        )

cdef class Not(Condition):

    def __init__(self, Condition condition):
        self.__condition = condition

    def to_pddl(self) -> str:
        return f'(not {self.__condition.to_pddl()})'

    cpdef bint holds(self, dict parameter_assignment, state, problem):
        return not self.__condition.holds(parameter_assignment, state, problem)

    def __eq__(self, other):
        return (
            isinstance(other, Not) and
            self.__condition == (<Not>other).__condition
        )

cdef class Or(Condition):

    def __init__(self, list condition_list):
        validate.is_not_none(condition_list)
        self.__condition_list = condition_list

    def to_pddl(self) -> str:
        return f'(or {" ".join(c.to_pddl() for c in self.__condition_list)})'

    cpdef bint holds(self, dict parameter_assignment, state, problem):
        for condition in self.__condition_list:
            if condition.holds(parameter_assignment, state, problem):
                return True
        return False

    def __eq__(self, other):
        return (
            isinstance(other, Or) and
            self.__condition_list == other.__condition_list
        )

cdef class And(Condition):

    def __init__(self, list condition_list):
        validate.is_not_none(condition_list)
        self.__condition_list = condition_list

    def to_pddl(self) -> str:
        return f'(and {" ".join(c.to_pddl() for c in self.__condition_list)})'

    cpdef bint holds(self, dict parameter_assignment, state, problem):
        for condition in self.__condition_list:
            if not condition.holds(parameter_assignment, state, problem):
                return False
        return True

    def __eq__(self, other):
        return (
            isinstance(other, And) and
            self.__condition_list == (<And>other).__condition_list
        )

cdef class Exists(Condition):

    def __init__(self, str parameter_name, ObjectType parameter_type, Condition condition):
        self.__parameter_name = parameter_name
        self.__parameter_type = parameter_type
        self.__condition = condition

    def to_pddl(self) -> str:
        return f'(exists (?{self.__parameter_name} - {self.__parameter_type.name}) {self.__condition.to_pddl()})'

    cpdef bint holds(self, dict parameter_assignment, state, problem):
        for o in problem.get_objects_of_type(self.__parameter_type):
            parameter_assignment[self.__parameter_name] = o
            try:
                if self.__condition.holds(parameter_assignment, state, problem):
                    return True
            finally:
                parameter_assignment.pop(self.__parameter_name)
        return False

    def __eq__(self, other):
        return (
            isinstance(other, Exists) and
            self.__parameter_name == (<Exists>other).__parameter_name and
            self.__parameter_type == (<Exists>other).__parameter_type and
            self.__condition == (<Exists>other).__condition
        )

cdef class ForAll(Condition):

    def __init__(self, str parameter_name, ObjectType parameter_type, Condition condition):
        self.__parameter_name = parameter_name
        self.__parameter_type = parameter_type
        self.__condition = condition

    def to_pddl(self) -> str:
        return f'(forall (?{self.__parameter_name} - {self.__parameter_type.name}) {self.__condition.to_pddl()})'

    cpdef bint holds(self, dict parameter_assignment, state, problem):
        for o in problem.get_objects_of_type(self.__parameter_type):
            parameter_assignment[self.__parameter_name] = o
            try:
                if not self.__condition.holds(parameter_assignment, state, problem):
                    return False
            finally:
                parameter_assignment.pop(self.__parameter_name)
        return True

    def __eq__(self, other):
        return (
            isinstance(other, ForAll) and
            self.__parameter_name == (<ForAll>other).__parameter_name and
            self.__parameter_type == (<ForAll>other).__parameter_type and
            self.__condition == (<ForAll>other).__condition
        )
