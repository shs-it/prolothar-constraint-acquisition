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

from prolothar_ca.model.pddl.pddl_object import Object

class NumericExpression(ABC):
    @abstractmethod
    def to_pddl(self) -> str: ...
    """
    creates a pddl representation of this numeric expression
    """

    @abstractmethod
    def evaluate(self, parameter_assignment: dict[str, Object], state) -> int|float: ...
    """
    returns the current value (dependent on parameter assignment and state) of
    this numeric fluent
    """

    @staticmethod
    def int_to_constant(expression) -> 'ConstantExpression': ...

class ConstantExpression(NumericExpression):
    def __init__(self, constant_value: int): ...

    def to_pddl(self) -> str: ...

    def evaluate(self, parameter_assignment: dict[str, Object], state) -> int|float: ...

class NumericFluentExpression(NumericExpression):
    def __init__(self, numeric_fluent, parameter_names: list[str]): ...

    def to_pddl(self) -> str: ...

    def evaluate(self, parameter_assignment: dict[str, Object], state) -> int|float: ...

class Add(NumericExpression):
    def __init__(self, summand_a: NumericExpression, summand_b: NumericExpression): ...

    def to_pddl(self) -> str: ...

    def evaluate(self, parameter_assignment: dict[str, Object], state) -> int|float: ...

class Subtract(NumericExpression):
    def __init__(self, summand_a: NumericExpression, summand_b: NumericExpression): ...

    def to_pddl(self) -> str: ...

    def evaluate(self, parameter_assignment: dict[str, Object], state) -> int|float: ...

class Divide(NumericExpression):
    def __init__(self, summand_a: NumericExpression, summand_b: NumericExpression): ...

    def to_pddl(self) -> str: ...

    def evaluate(self, parameter_assignment: dict[str, Object], state) -> int|float: ...

class Multiply(NumericExpression):
    def __init__(self, summand_a: NumericExpression, summand_b: NumericExpression): ...

    def to_pddl(self) -> str: ...

    def evaluate(self, parameter_assignment: dict[str, Object], state) -> int|float: ...
