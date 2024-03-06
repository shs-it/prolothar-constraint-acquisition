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

from prolothar_common import validate

from prolothar_ca.model.pddl.numeric_expression import NumericExpression

class Metric(ABC):

    def __init__(self, numeric_expression: NumericExpression):
        validate.is_not_none(numeric_expression)
        self.numeric_expression = numeric_expression

    def to_pddl(self, indent: str = '') -> str:
        return f'{indent}(:metric {self.get_objective_operator()} {self.numeric_expression.to_pddl()})'

    @abstractmethod
    def get_objective_operator(self) -> str:
        pass

    def __eq__(self, other):
        return (
            isinstance(other, Metric) and
            self.numeric_expression == other.numeric_expression and
            self.get_objective_operator() == other.get_objective_operator()
        )

class MaximizeMetric(Metric):
    def get_objective_operator(self) -> str:
        return 'maximize'

class MinimizeMetric(Metric):
    def get_objective_operator(self) -> str:
        return 'minimize'