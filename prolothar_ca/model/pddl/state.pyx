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

cdef class State:
    def __init__(self, problem, set true_predicates, dict numeric_fluents):
        self.problem = problem
        self.__true_predicates = true_predicates
        self.__numeric_values = numeric_fluents

    cpdef bint is_predicate_true(self, object predicate, tuple object_tuple):
        return (predicate, object_tuple) in self.__true_predicates

    cpdef set_predicate_true(self, object predicate, tuple object_tuple):
        self.__true_predicates.add((predicate, object_tuple))

    def iter_true_predicates(self):
        return iter(self.__true_predicates)

    cpdef set_predicate_false(self, object predicate, tuple object_tuple):
        self.__true_predicates.discard((predicate, object_tuple))

    cpdef long get_numeric_fluent_value(self, object numeric_fluent, tuple object_tuple):
        return <long>(self.__numeric_values.get((numeric_fluent, object_tuple), 0))

    cpdef set_numeric_fluent_value(self, object numeric_fluent, tuple object_tuple, long value):
        for o in object_tuple:
            if o is None:
                raise ValueError(f'object tuple must not contain None: {object_tuple}')
        self.__numeric_values[(numeric_fluent, object_tuple)] = value

    cpdef size_t get_nr_of_true_predicates(self):
        return len(self.__true_predicates)

    cpdef State flat_copy(self):
        return State(
            self.problem,
            set(self.__true_predicates),
            dict(self.__numeric_values)
        )

    def to_pddl(self, ignore_zeros: bool = False) -> str:
        def o_list_to_str(o_list):
            return ' '.join(o.name for o in o_list)
        predicates_str = ' '.join(f'({p.name} {o_list_to_str(o_list)})' for p,o_list in self.__true_predicates)
        numeric_fluents_str = ' '.join(
            f'(({k[0].name} {o_list_to_str(k[1])}) {v})'
            for k,v in self.__numeric_values.items()
            if not ignore_zeros or v != 0
        )
        return f'(:state {predicates_str}{" " if self.__numeric_values else ""}{numeric_fluents_str})'

    def __str__(self):
        true_predicates_str = '\n'.join(sorted(
            f'    {predicate.name}({" ,".join(o.name for o in objects)})'
            for predicate, objects in self.__true_predicates
        ))
        numeric_fluents_str = '\n'.join(sorted(
            f'    {numeric_value_key[0].name}({" ,".join(o.name for o in numeric_value_key[1])}) = {value}'
            for numeric_value_key, value in self.__numeric_values.items()
        ))
        return f'True Predicates:\n{true_predicates_str}\nNumeric Fluents:\n{numeric_fluents_str}'