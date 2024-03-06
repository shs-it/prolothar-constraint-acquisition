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


from prolothar_ca.model.pddl.utils import NEWLINE
from prolothar_ca.model.pddl.condition cimport Condition
from prolothar_ca.model.pddl.effect cimport Effect

cdef class Action:

    def __init__(self, str action_name, dict parameters, list preconditions, list effects):
        self.action_name = action_name
        self.parameters = parameters
        self.preconditions = preconditions
        self.effects = effects

    def to_pddl(self, indent: str = '') -> str:
        parameter_definitions = [
            f'?{name} - {t.name}' for name, t in self.parameters.items()
        ]
        preconditions = [
            f'{indent}            {c.to_pddl()}' for c in self.preconditions
        ]
        effects = [
            f'{indent}            {e.to_pddl()}' for e in self.effects
        ]
        return (
            f'{indent}(:action {self.action_name}{NEWLINE}'
            f'{indent}    :parameters({" ".join(parameter_definitions)}){NEWLINE}'
            f'{indent}    :precondition{NEWLINE}'
            f'{indent}        (and{NEWLINE}'
            f'{NEWLINE.join(preconditions)}{NEWLINE}'
            f'{indent}        ){NEWLINE}'
            f'{indent}    :effect{NEWLINE}'
            f'{indent}        (and{NEWLINE}'
            f'{NEWLINE.join(effects)}{NEWLINE}'
            f'{indent}        ){NEWLINE}'
            f'{indent})'
        )

    cpdef bint is_applicable(self, dict parameter_assignment, State state, problem):
        cdef Condition condition
        for condition in self.preconditions:
            if not condition.holds(parameter_assignment, state, problem):
                condition.holds(parameter_assignment, state, problem)
                return False
        return True

    cpdef State apply(self, dict parameter_assignment, State state):
        new_state = state.flat_copy()
        cdef Effect effect
        for effect in self.effects:
            effect.modify_state(parameter_assignment, new_state)
        return new_state

    def __eq__(self, other: 'Action'):
        return self.action_name == other.action_name \
        and self.parameters == other.parameters \
        and self.preconditions == other.preconditions \
        and self.effects == other.effects

    def __hash__(self) -> int:
        return hash(self.action_name)

    def __repr__(self):
        return f'Action({self.action_name})'