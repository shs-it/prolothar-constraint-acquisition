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

from typing import Iterator

from prolothar_ca.model.pddl.numeric_fluent import NumericFluent
from prolothar_ca.model.pddl.pddl_object import Object

from prolothar_ca.model.pddl.predicate import Predicate


class State:
    def __init__(
            self, problem, true_predicates: set[tuple[Predicate, tuple[Object]]],
            numeric_fluents: dict[tuple[NumericFluent, tuple[Object]], int]): ...

    def is_predicate_true(self, predicate: Predicate, object_tuple: tuple[Object]) -> bool: ...

    def set_predicate_true(self, predicate: Predicate, object_tuple: tuple[Object]): ...

    def iter_true_predicates(self) -> Iterator[tuple[Predicate, tuple[Object]]]: ...

    def set_predicate_false(self, predicate: Predicate, object_tuple: tuple[Object]): ...

    def get_numeric_fluent_value(self, numeric_fluent: NumericFluent, object_tuple: tuple[Object]) -> int: ...

    def set_numeric_fluent_value(self, numeric_fluent: NumericFluent, object_tuple: tuple[Object], value: int): ...

    def get_nr_of_true_predicates(self) -> int: ...

    def flat_copy(self) -> 'State': ...

    def to_pddl(self) -> str: ...