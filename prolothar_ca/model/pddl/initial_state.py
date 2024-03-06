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
from prolothar_ca.model.pddl.state import State

from prolothar_ca.model.pddl.utils import NEWLINE
from prolothar_ca.model.pddl.numeric_fluent import NumericFluent
from prolothar_ca.model.pddl.predicate import Predicate
from prolothar_ca.model.pddl.pddl_object import Object

@dataclass
class InitialState:
    problem: object
    true_predicates: set[tuple[Predicate, tuple[Object]]] = field(default_factory=set)
    numeric_fluents: set[tuple[NumericFluent, tuple[Object], int|float]] = field(default_factory=set)

    def __post_init__(self):
        for predicate, object_list in self.true_predicates:
            validate.equals(predicate.parameter_types, [o.object_type for o in object_list])
        for numeric_fluent, object_list, _ in self.numeric_fluents:
            validate.equals(numeric_fluent.parameter_types, [o.object_type for o in object_list])

    def to_pddl(self, indent: str = '') -> str:
        predicates_pddl = ''
        for predicate, object_list in self.true_predicates:
            predicates_pddl += f'{indent}    ({predicate.name} {" ".join(o.name for o in object_list)}){NEWLINE}'
        predicates_pddl = NEWLINE.join(sorted(predicates_pddl.split(NEWLINE)))

        numeric_fluents_pddl = ''
        for numeric_fluent, object_list, value in self.numeric_fluents:
            numeric_fluents_pddl += f'{indent}    (= ({numeric_fluent.name} {" ".join(o.name for o in object_list)}) {value}){NEWLINE}'
        numeric_fluents_pddl = NEWLINE.join(sorted(numeric_fluents_pddl.split(NEWLINE)))

        return (
            f'{indent}(:init'
            f'{predicates_pddl}'
            f'{numeric_fluents_pddl}{NEWLINE}'
            f'{indent}){NEWLINE}'
        )

    def to_state(self) -> State:
        return State(
            self.problem,
            self.true_predicates,
            {
                numeric_fluent_tuple[:-1]: numeric_fluent_tuple[-1]
                for numeric_fluent_tuple in self.numeric_fluents
            }
        )
