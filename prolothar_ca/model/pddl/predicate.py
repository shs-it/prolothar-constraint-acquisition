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
from prolothar_ca.model.pddl.condition import Condition, Not, PredicateIsTrueCondition
from prolothar_ca.model.pddl.effect import SetPredicateFalse, SetPredicateTrue

from prolothar_ca.model.pddl.object_type import ObjectType

@dataclass(unsafe_hash=True)
class Predicate:
    """
    a PDDL predicate

    https://planning.wiki/ref/pddl/domain#predicates
    """

    name: str = field(hash=True)
    parameter_types: list[ObjectType] = field(hash=False)

    def is_true(self, parameter_names: list[str]) -> Condition:
        return PredicateIsTrueCondition(self, parameter_names)

    def is_false(self, parameter_names: list[str]) -> Condition:
        return Not(PredicateIsTrueCondition(self, parameter_names))

    def set_true(self, parameter_names: list[str]) -> Condition:
        return SetPredicateTrue(self, parameter_names)

    def set_false(self, parameter_names: list[str]) -> Condition:
        return SetPredicateFalse(self, parameter_names)

    def to_pddl(self) -> str:
        parameter_definitions = [
            f'?x{i+1} - {t.name}' for i,t in enumerate(self.parameter_types)
        ]
        return f'({self.name} {" ".join(parameter_definitions)})'
