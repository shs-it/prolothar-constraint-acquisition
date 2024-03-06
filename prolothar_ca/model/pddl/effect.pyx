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

from prolothar_ca.model.pddl.numeric_expression import NumericExpression
from prolothar_ca.model.pddl.utils import check_parameter_names


cdef class Effect:
    def to_pddl(self) -> str:
        """
        creates a pddl representation of this effect
        """
        raise NotImplementedError()

    cpdef modify_state(self, dict parameter_assignment, state):
        """
        executes the effect by modifying the given state
        """
        raise NotImplementedError()

cdef class SetPredicateTrue(Effect):

    def __init__(self, predicate, list parameter_names):
        check_parameter_names(predicate, parameter_names)
        self.__predicate = predicate
        self.__parameter_names = parameter_names

    def to_pddl(self) -> str:
        return f'({self.__predicate.name} {" ".join("?" + p for p in self.__parameter_names)})'

    cpdef modify_state(self, dict parameter_assignment, state):
        state.set_predicate_true(self.__predicate, tuple(map(parameter_assignment.get, self.__parameter_names)))

    def get_parameter_names(self) -> list:
        return self.__parameter_names

    def __eq__(self, other):
        return (
            isinstance(other, SetPredicateTrue) and
            self.__predicate == (<SetPredicateTrue>other).__predicate and
            self.__parameter_names == (<SetPredicateTrue>other).__parameter_names
        )

cdef class SetPredicateFalse(Effect):

    def __init__(self, predicate, list parameter_names):
        check_parameter_names(predicate, parameter_names)
        self.__predicate = predicate
        self.__parameter_names = parameter_names

    def to_pddl(self) -> str:
        return f'(not ({self.__predicate.name} {" ".join("?" + p for p in self.__parameter_names)}))'

    cpdef modify_state(self, dict parameter_assignment, state):
        state.set_predicate_false(
            self.__predicate,
            tuple(map(parameter_assignment.get, self.__parameter_names)))

    def get_parameter_names(self) -> list:
        return self.__parameter_names

    def __eq__(self, other):
        return (
            isinstance(other, SetPredicateFalse) and
            self.__predicate == (<SetPredicateFalse>other).__predicate and
            self.__parameter_names == (<SetPredicateFalse>other).__parameter_names
        )

cdef class DecreaseEffect(Effect):

    def __init__(self, numeric_fluent, list parameter_names, value):
        check_parameter_names(numeric_fluent, parameter_names)
        self.__numeric_fluent = numeric_fluent
        self.__parameter_names = parameter_names
        self.__value = NumericExpression.int_to_constant(value)

    def to_pddl(self) -> str:
        return f'(decrease ({self.__numeric_fluent.name} {" ".join("?" + p for p in self.__parameter_names)}) {self.__value.to_pddl()})'

    cpdef modify_state(self, dict parameter_assignment, state):
        object_tuple = tuple(map(parameter_assignment.get, self.__parameter_names))
        state.set_numeric_fluent_value(
            self.__numeric_fluent, object_tuple,
            state.get_numeric_fluent_value(self.__numeric_fluent, object_tuple) -
            self.__value.evaluate(parameter_assignment, state)
        )

    def __eq__(self, other):
        return (
            isinstance(other, DecreaseEffect) and
            self.__numeric_fluent == (<DecreaseEffect>other).__numeric_fluent and
            self.__parameter_names == (<DecreaseEffect>other).__parameter_names and
            self.__value == (<DecreaseEffect>other).__value
        )

cdef class IncreaseEffect(Effect):

    def __init__(self, numeric_fluent, list parameter_names, value):
        check_parameter_names(numeric_fluent, parameter_names)
        self.__numeric_fluent = numeric_fluent
        self.__parameter_names = parameter_names
        self.__value = NumericExpression.int_to_constant(value)

    def to_pddl(self) -> str:
        return f'(increase ({self.__numeric_fluent.name} {" ".join("?" + p for p in self.__parameter_names)}) {self.__value.to_pddl()})'

    cpdef modify_state(self, dict parameter_assignment, state):
        object_tuple = tuple(map(parameter_assignment.get, self.__parameter_names))
        state.set_numeric_fluent_value(
            self.__numeric_fluent, object_tuple,
            state.get_numeric_fluent_value(self.__numeric_fluent, object_tuple) +
            self.__value.evaluate(parameter_assignment, state)
        )

    def __eq__(self, other):
        return (
            isinstance(other, IncreaseEffect) and
            self.__numeric_fluent == (<IncreaseEffect>other).__numeric_fluent and
            self.__parameter_names == (<IncreaseEffect>other).__parameter_names and
            self.__value == (<IncreaseEffect>other).__value
        )

cdef class SetNumericFluent(Effect):

    def __init__(self, numeric_fluent, list parameter_names, value):
        check_parameter_names(numeric_fluent, parameter_names)
        self.__numeric_fluent = numeric_fluent
        self.__parameter_names = parameter_names
        self.__value = NumericExpression.int_to_constant(value)

    def to_pddl(self) -> str:
        return f'(assign ({self.__numeric_fluent.name} {" ".join("?" + p for p in self.__parameter_names)}) {self.__value.to_pddl()})'

    cpdef modify_state(self, dict parameter_assignment, state):
        state.set_numeric_fluent_value(
            self.__numeric_fluent,
            tuple(map(parameter_assignment.__getitem__, self.__parameter_names)),
            self.__value.evaluate(parameter_assignment, state)
        )

    def __eq__(self, other):
        return (
            isinstance(other, SetNumericFluent) and
            self.__numeric_fluent == (<SetNumericFluent>other).__numeric_fluent and
            self.__parameter_names == (<SetNumericFluent>other).__parameter_names and
            self.__value == (<SetNumericFluent>other).__value
        )

cdef class ForAllEffect(Effect):

    def __init__(self, str parameter_name, ObjectType parameter_type, Effect effect):
        self.__parameter_name = parameter_name
        self.__parameter_type = parameter_type
        self.__effect = effect

    def to_pddl(self) -> str:
        return f'(forall (?{self.__parameter_name} - {self.__parameter_type.name}) {self.__effect.to_pddl()})'

    cpdef modify_state(self, dict parameter_assignment, state):
        cdef dict extended_parameter_assignment = dict(parameter_assignment)
        for an_object in state.problem.get_objects_of_type(self.__parameter_type):
            extended_parameter_assignment[self.__parameter_name] = an_object
            self.__effect.modify_state(extended_parameter_assignment, state)

    def __eq__(self, other):
        return (
            isinstance(other, ForAllEffect) and
            self.__parameter_name == (<ForAllEffect>other).__parameter_name and
            self.__parameter_type == (<ForAllEffect>other).__parameter_type and
            self.__condition == (<ForAllEffect>other).__condition
        )

cdef class When(Effect):

    def __init__(self, Condition condition, Effect effect):
        self.__condition = condition
        self.__effect = effect

    def to_pddl(self) -> str:
        return f'(when {self.__condition.to_pddl()} {self.__effect.to_pddl()})'

    cpdef modify_state(self, dict parameter_assignment, state):
        if self.__condition.holds(parameter_assignment, state, state.problem):
            self.__effect.modify_state(parameter_assignment, state)

    def __eq__(self, other):
        return (
            isinstance(other, When) and
            self.__condition == (<When>other).__condition and
            self.__effect == (<When>other).__effect
        )

cdef class AndEffect(Effect):

    def __init__(self, list effect_list):
        self.__effect_list = effect_list

    def to_pddl(self) -> str:
        return f'(and {" ".join(e.to_pddl() for e in self.__effect_list)})'

    cpdef modify_state(self, dict parameter_assignment, state):
        cdef Effect effect
        for effect in self.__effect_list:
            effect.modify_state(parameter_assignment, state)

    def __eq__(self, other):
        return (
            isinstance(other, AndEffect) and
            self.__effect_list == (<AndEffect>other).__effect_list
        )