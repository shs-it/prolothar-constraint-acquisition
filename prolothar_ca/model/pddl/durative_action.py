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

from dataclasses import dataclass
import os
from prolothar_ca.model.pddl.condition import Condition

from prolothar_ca.model.pddl.utils import NEWLINE
from prolothar_ca.model.pddl.effect import Effect
from prolothar_ca.model.pddl.numeric_expression import NumericExpression
from prolothar_ca.model.pddl.object_type import ObjectType


@dataclass()
class DurativeAction:
    action_name: str
    parameters: dict[str, ObjectType]
    duration: int|NumericExpression
    start_conditions: list[Condition]
    overall_conditions: list[Condition]
    start_effects: list[Effect]
    end_effects: list[Effect]

    def to_pddl(self, indent: str = '') -> str:
        parameter_definitions = [
            f'?{name} - {t.name}' for name, t in self.parameters.items()
        ]
        start_conditions = [
            f'{indent}            (at start {c.to_pddl()})' for c in self.start_conditions
        ]
        overall_conditions = [
            f'{indent}            (over all {c.to_pddl()})' for c in self.overall_conditions
        ]
        start_effects = [
            f'{indent}            (at start {e.to_pddl()})' for e in self.start_effects
        ]
        end_effects = [
            f'{indent}            (at end {e.to_pddl()})' for e in self.end_effects
        ]
        return (
            f'{indent}(:durative-action {self.action_name}{NEWLINE}'
            f'{indent}    :parameters({" ".join(parameter_definitions)}){NEWLINE}'
            f'{indent}    :duration(= ?duration {NumericExpression.int_to_constant(self.duration).to_pddl()}){NEWLINE}'
            f'{indent}    :condition{NEWLINE}'
            f'{indent}        (and{NEWLINE}'
            f'{NEWLINE.join(start_conditions)}{NEWLINE}'
            f'{NEWLINE.join(overall_conditions)}{NEWLINE}'
            f'{indent}        ){NEWLINE}'
            f'{indent}    :effect{NEWLINE}'
            f'{indent}        (and{NEWLINE}'
            f'{NEWLINE.join(start_effects)}{NEWLINE}'
            f'{NEWLINE.join(end_effects)}{NEWLINE}'
            f'{indent}        ){NEWLINE}'
            f'{indent})'
        )