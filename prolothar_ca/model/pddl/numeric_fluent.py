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

from dataclasses import dataclass, field
from prolothar_common import validate
from prolothar_ca.model.pddl.condition import Condition, Greater
from prolothar_ca.model.pddl.effect import DecreaseEffect, Effect
from prolothar_ca.model.pddl.numeric_expression import NumericExpression, NumericFluentExpression


from prolothar_ca.model.pddl.object_type import ObjectType

@dataclass(unsafe_hash=True)
class NumericFluent:
    """
    https://planning.wiki/ref/pddl21/domain#numeric-fluents
    """
    name: str = field(hash=True)
    parameter_types: list[ObjectType] = field(hash=False)

    def get_value(self, parameter_names: list[str]) -> NumericExpression:
        return NumericFluentExpression(self, parameter_names)

    def greater(self, parameter_names: list[str], other: NumericExpression|int) -> Condition:
        return Greater(self.get_value(parameter_names), other)

    def decrease(self, parameter_names: list[str], value: NumericExpression|int) -> Effect:
        return DecreaseEffect(self, parameter_names, value)

    def to_pddl(self) -> str:
        if self.parameter_types:
            parameters = [
                f'?x{i+1} - {t.name}' for i, t in enumerate(self.parameter_types)
            ]
            return f'({self.name} {" ".join(parameters)})'
        else:
            return f'({self.name})'

    def __post_init__(self):
        validate.is_not_none(self.name)
        validate.is_not_none(self.parameter_types)
