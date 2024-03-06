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

from prolothar_ca.model.pddl.utils import check_parameter_names

cdef class NumericExpression():
    def to_pddl(self) -> str:
        """
        creates a pddl representation of this numeric expression
        """
        raise NotImplementedError()

    cpdef long evaluate(self, dict parameter_assignment, object state):
        """
        returns the current value (dependent on parameter assignment and state) of
        this numeric fluent
        """
        raise NotImplementedError()

    @staticmethod
    def int_to_constant(expression) -> 'NumericExpression':
        if isinstance(expression, int):
            return ConstantExpression(expression)
        else:
            return expression

cdef class ConstantExpression(NumericExpression):
    def __init__(self, long constant_value):
        self.__constant_value = constant_value

    def to_pddl(self) -> str:
        return str(self.__constant_value)

    cpdef long evaluate(self, dict parameter_assignment, object state):
        return self.__constant_value

    def __eq__(self, other):
        return (
            isinstance(other, ConstantExpression) and
            self.__constant_value == (<ConstantExpression>other).__constant_value
        )

cdef class NumericFluentExpression(NumericExpression):
    def __init__(self, numeric_fluent, list parameter_names):
        check_parameter_names(numeric_fluent, parameter_names)
        self.__numeric_fluent = numeric_fluent
        self.__parameter_names = parameter_names

    def to_pddl(self) -> str:
        if self.__parameter_names:
            return f'({self.__numeric_fluent.name} {" ".join("?" + p for p in self.__parameter_names)})'
        else:
            return f'({self.__numeric_fluent.name})'

    cpdef long evaluate(self, dict parameter_assignment, object state):
        return state.get_numeric_fluent_value(
            self.__numeric_fluent,
            tuple(map(parameter_assignment.get, self.__parameter_names)))

    def __eq__(self, other):
        return (
            isinstance(other, NumericFluentExpression) and
            self.__numeric_fluent == (<NumericFluentExpression>other).__numeric_fluent and
            self.__parameter_names == (<NumericFluentExpression>other).__parameter_names
        )

cdef class Add(NumericExpression):
    def __init__(self, NumericExpression summand_a, NumericExpression summand_b):
        self.__summand_a = summand_a
        self.__summand_b = summand_b

    def to_pddl(self) -> str:
        return f'(+ {self.__summand_a.to_pddl()} {self.__summand_b.to_pddl()})'

    def __eq__(self, other):
        return (
            isinstance(other, Add) and
            self.__summand_a == (<Add>other).__summand_a and
            self.__summand_b == (<Add>other).__summand_b
        )

    cpdef long evaluate(self, dict parameter_assignment, object state):
        return (
            self.__summand_a.evaluate(parameter_assignment, state) +
            self.__summand_b.evaluate(parameter_assignment, state)
        )

cdef class Subtract(NumericExpression):
    def __init__(self, NumericExpression summand_a, NumericExpression summand_b):
        self.__summand_a = summand_a
        self.__summand_b = summand_b

    def to_pddl(self) -> str:
        return f'(- {self.__summand_a.to_pddl()} {self.__summand_b.to_pddl()})'

    cpdef long evaluate(self, dict parameter_assignment, object state):
        return (
            self.__summand_a.evaluate(parameter_assignment, state) -
            self.__summand_b.evaluate(parameter_assignment, state)
        )

    def __eq__(self, other):
        return (
            isinstance(other, Subtract) and
            self.__summand_a == (<Subtract>other).__summand_a and
            self.__summand_b == (<Subtract>other).__summand_b
        )

cdef class Divide(NumericExpression):
    def __init__(self, NumericExpression summand_a, NumericExpression summand_b):
        self.__summand_a = summand_a
        self.__summand_b = summand_b

    def to_pddl(self) -> str:
        return f'(/ {self.__summand_a.to_pddl()} {self.__summand_b.to_pddl()})'

    cpdef long evaluate(self, dict parameter_assignment, object state):
        return <long>(
            self.__summand_a.evaluate(parameter_assignment, state) /
            self.__summand_b.evaluate(parameter_assignment, state)
        )

    def __eq__(self, other):
        return (
            isinstance(other, Divide) and
            self.__summand_a == (<Divide>other).__summand_a and
            self.__summand_b == (<Divide>other).__summand_b
        )

cdef class Multiply(NumericExpression):
    def __init__(self, NumericExpression summand_a, NumericExpression summand_b):
        self.__summand_a = summand_a
        self.__summand_b = summand_b

    def to_pddl(self) -> str:
        return f'(* {self.__summand_a.to_pddl()} {self.__summand_b.to_pddl()})'

    cpdef long evaluate(self, dict parameter_assignment, object state):
        return (
            self.__summand_a.evaluate(parameter_assignment, state) *
            self.__summand_b.evaluate(parameter_assignment, state)
        )

    def __eq__(self, other):
        return (
            isinstance(other, Multiply) and
            self.__summand_a == (<Multiply>other).__summand_a and
            self.__summand_b == (<Multiply>other).__summand_b
        )
