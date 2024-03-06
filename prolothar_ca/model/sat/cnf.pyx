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

from typing import Iterable, Iterator, Tuple, Generator
from itertools import chain
cimport cython
from cython.operator import dereference
from cpython.tuple cimport PyTuple_GET_ITEM, PyTuple_GET_SIZE

from prolothar_ca.model.sat.term import Term
from prolothar_ca.model.sat.variable import Variable

cdef class CnfDisjunction:

    def __init__(self, tuple terms):
        self.__term_ids = frozenset(terms)
        self.__terms = terms
        self.__hash = hash(self.__term_ids)

    def __iter__(self):
        return iter(self.__terms)

    def iter_term_pairs(self) -> Generator[Tuple[Term, Term], None, None]:
        for i, term in enumerate(self.__terms):
            for other_term in self.__terms[i+1:]:
                yield term, other_term

    cpdef bint contains_variable(self, Variable variable):
        for term in self.__terms:
            if (<Term>term).variable.nr == variable.nr:
                return True
        return False

    cpdef bint contains_one_of(self, set variable_set):
        for term in self.__terms:
            if (<Term>term).variable in variable_set:
                return True
        return False

    cpdef Value value(self):
        cdef Value default_value = Value.FALSE
        cdef Value term_value
        cdef size_t i
        # for term in self.__terms:
        for i in range(PyTuple_GET_SIZE(self.__terms)):
            term_value = (<Term>PyTuple_GET_ITEM(self.__terms, i)).value()
            if term_value == Value.TRUE:
                return Value.TRUE
            if term_value == Value.UNKNOWN:
                default_value = Value.UNKNOWN
        return default_value

    cpdef Term get_first_term(self):
        return <Term>(self.__terms[0])

    cpdef CnfDisjunction without_term(self, Term term):
        cdef list term_list = []
        for own_term in self.__terms:
            if not (<Term>own_term).equals_term(term):
                term_list.append(own_term)
        return CnfDisjunction(tuple(term_list))

    cdef bint is_informative_implication(self):
        cdef Term first_term = <Term>(self.__terms[0])
        return first_term.is_negated() and first_term.variable.value == Value.TRUE

    cpdef tuple get_terms(self):
        return self.__terms

    cpdef size_t get_nr_of_terms(self):
        return PyTuple_GET_SIZE(self.__terms)

    def __len__(self):
        return PyTuple_GET_SIZE(self.__terms)

    def __hash__(self):
        return self.__hash

    def __eq__(self, other: 'CnfDisjunction'):
        return self.__term_ids == other.__term_ids

    def __str__(self):
        return '|'.join(str((<Term>term).to_int_encoding()) for term in self.__terms)

cdef CnfDisjunction EMPTY_CLAUSE = CnfDisjunction(tuple())

cdef class CnfFormula:
    """
    model of a boolean formula in conjunctive normal form
    """

    def __init__(
            self, set disjunctions = None,
            dict nr_of_untrue_clauses_per_example = None,
            set new_disjunctions = None,
            set variable_nr_set = None,
            ConstraintGraph constraint_graph = None):
        self.__disjunctions = disjunctions if disjunctions is not None else set()
        if nr_of_untrue_clauses_per_example is not None:
            self.__nr_of_untrue_clauses_per_example = nr_of_untrue_clauses_per_example
        self.__new_disjunctions = new_disjunctions if new_disjunctions is not None else set()
        if variable_nr_set is not None:
            self.__variable_nr_set = variable_nr_set
        else:
            self.__variable_nr_set = set()
            for disjunction in self.__disjunctions:
                for term in (<CnfDisjunction>disjunction).get_terms():
                    self.__variable_nr_set.add((<Term>term).variable.nr)
        self.__constraint_graph = constraint_graph

    cpdef set get_variable_nr_set(self):
        #returns Set[int]
        return self.__variable_nr_set

    cpdef CnfFormula extend(self, CnfFormula other):
        disjunctions = self.__disjunctions.union(self.__new_disjunctions)
        return CnfFormula(
            disjunctions = disjunctions,
            nr_of_untrue_clauses_per_example = self.__nr_of_untrue_clauses_per_example,
            new_disjunctions = other.__disjunctions.union(other.__new_disjunctions).difference(disjunctions),
            variable_nr_set = self.__variable_nr_set.union(other.get_variable_nr_set()),
            constraint_graph = None
        )

    cpdef CnfFormula resolve_new_clauses(self):
        return CnfFormula(
            disjunctions = self.__disjunctions.union(self.__new_disjunctions),
            nr_of_untrue_clauses_per_example = self.__nr_of_untrue_clauses_per_example,
            variable_nr_set = self.__variable_nr_set,
            constraint_graph = self.__constraint_graph
        )

    cpdef CnfFormula fix_variable(self, Variable variable, bint value):
        cdef set new_clauses = set()
        cdef Term term
        cdef CnfDisjunction clause
        cdef set clause_set
        for clause_set in (self.__disjunctions, self.__new_disjunctions):
            for clause in clause_set:
                if clause.get_nr_of_terms() == 1:
                    term = clause.get_first_term()
                    if term.variable.nr == variable.nr:
                        if value == term.is_negated():
                            new_clauses.add(EMPTY_CLAUSE)
                    else:
                        new_clauses.add(clause)
                else:
                    for term in clause.get_terms():
                        if term.variable.nr == variable.nr:
                            if value == term.is_negated():
                                new_clauses.add(clause.without_term(term))
                            break
                    else:
                        new_clauses.add(clause)
        cdef set new_variable_nr_set = set()
        for clause in new_clauses:
            for term in clause.get_terms():
                new_variable_nr_set.add(term.variable.nr)
        cdef ConstraintGraph new_constraint_graph = None
        if self.__constraint_graph is not None:
            new_constraint_graph = self.__constraint_graph.copy()
            for variable_nr in self.__variable_nr_set.difference(new_variable_nr_set):
                new_constraint_graph.remove_node_with_variable_nr(variable_nr)
        return CnfFormula(
            new_clauses, variable_nr_set=new_variable_nr_set,
            constraint_graph=new_constraint_graph)

    cpdef CnfFormula without_uninformative_implications(self):
        cdef set filtered_clauses = set()
        cdef CnfDisjunction clause
        for clause in self.__disjunctions:
            if clause.is_informative_implication():
                filtered_clauses.add(clause)
        for clause in self.__new_disjunctions:
            if clause.is_informative_implication():
                filtered_clauses.add(clause)
        return CnfFormula(filtered_clauses)

    cpdef tuple get_untrue_clauses(self):
        """
        returns (List[CnfDisjunction], List[CnfDisjunction])
        """
        cdef list untrue_clauses = []
        cdef list untrue_new_clauses = []
        cdef CnfDisjunction clause
        for clause in self.__disjunctions:
            if clause.value() != Value.TRUE:
                untrue_clauses.append(clause)
        for clause in self.__new_disjunctions:
            if clause.value() != Value.TRUE:
                untrue_new_clauses.append(clause)
        return untrue_clauses, untrue_new_clauses

    cpdef bint contains_empty_clause(self):
        return EMPTY_CLAUSE in self.__disjunctions or EMPTY_CLAUSE in self.__new_disjunctions

    cpdef int get_nr_of_untrue_clauses(self):
        cdef int nr_of_untrue_clauses = 0
        cdef CnfDisjunction clause
        for clause in self.__disjunctions:
            if clause.value() != Value.TRUE:
                nr_of_untrue_clauses += 1
        for clause in self.__new_disjunctions:
            if clause.value() != Value.TRUE:
                nr_of_untrue_clauses += 1
        return nr_of_untrue_clauses

    cpdef int get_nr_of_untrue_clauses_for_example(self, int example_id):
        cdef int nr_of_untrue_clauses = 0
        cdef unordered_map[int,int].iterator nr_of_untrue_clauses_iterator = self.__nr_of_untrue_clauses_per_example.find(example_id)
        if nr_of_untrue_clauses_iterator != self.__nr_of_untrue_clauses_per_example.end():
            nr_of_untrue_clauses = dereference(nr_of_untrue_clauses_iterator).second
            if self.__examples_with_updated_nr_of_untrue_clauses.find(example_id) == self.__examples_with_updated_nr_of_untrue_clauses.end():
                for clause in self.__new_disjunctions:
                    if (<CnfDisjunction>clause).value() != Value.TRUE:
                        nr_of_untrue_clauses += 1
                self.__examples_with_updated_nr_of_untrue_clauses.insert(example_id)
                self.__nr_of_untrue_clauses_per_example[example_id] = nr_of_untrue_clauses
        else:
            for clause in self.__disjunctions:
                if (<CnfDisjunction>clause).value() != Value.TRUE:
                    nr_of_untrue_clauses += 1
            for clause in self.__new_disjunctions:
                if (<CnfDisjunction>clause).value() != Value.TRUE:
                    nr_of_untrue_clauses += 1
            self.__examples_with_updated_nr_of_untrue_clauses.insert(example_id)
            self.__nr_of_untrue_clauses_per_example[example_id] = nr_of_untrue_clauses
        return nr_of_untrue_clauses

    cpdef int estimate_nr_of_untrue_clauses_for_example(self, int example_id, int nr_of_sampled_clauses):
        cdef int nr_of_untrue_clauses = 0
        cdef int nr_of_new_untrue_clauses = 0
        cdef unordered_map[int,int].iterator nr_of_untrue_clauses_iterator = self.__nr_of_untrue_clauses_per_example.find(example_id)
        cdef int i = 0
        if nr_of_untrue_clauses_iterator != self.__nr_of_untrue_clauses_per_example.end():
            nr_of_untrue_clauses = dereference(nr_of_untrue_clauses_iterator).second
            if self.__examples_with_updated_nr_of_untrue_clauses.find(example_id) == self.__examples_with_updated_nr_of_untrue_clauses.end():
                for clause in self.__new_disjunctions:
                    if (<CnfDisjunction>clause).value() != Value.TRUE:
                        nr_of_new_untrue_clauses += 1
                    i += 1
                    if i == nr_of_sampled_clauses:
                        nr_of_new_untrue_clauses = <int>(nr_of_new_untrue_clauses / (<float>i / len(self.__new_disjunctions)))
                        break
                self.__examples_with_updated_nr_of_untrue_clauses.insert(example_id)
                nr_of_untrue_clauses += nr_of_new_untrue_clauses
                self.__nr_of_untrue_clauses_per_example[example_id] = nr_of_untrue_clauses
        else:
            for clause in self.__disjunctions:
                if (<CnfDisjunction>clause).value() != Value.TRUE:
                    nr_of_untrue_clauses += 1
                i += 1
                if i == nr_of_sampled_clauses:
                    nr_of_untrue_clauses = <int>(nr_of_untrue_clauses / (<float>i / len(self.__disjunctions)))
                    break
            i = 0
            for clause in self.__new_disjunctions:
                if (<CnfDisjunction>clause).value() != Value.TRUE:
                    nr_of_new_untrue_clauses += 1
                i += 1
                if i == nr_of_sampled_clauses:
                    nr_of_new_untrue_clauses = <int>(nr_of_new_untrue_clauses / (<float>i / len(self.__new_disjunctions)))
                    break
            self.__examples_with_updated_nr_of_untrue_clauses.insert(example_id)
            nr_of_untrue_clauses += nr_of_new_untrue_clauses
            self.__nr_of_untrue_clauses_per_example[example_id] = nr_of_untrue_clauses
        return nr_of_untrue_clauses

    cpdef size_t get_nr_of_clauses(self):
        return len(self.__disjunctions) + len(self.__new_disjunctions)

    cpdef CnfFormula fix_literal_clauses(self):
        cdef CnfDisjunction clause
        cdef list literal_list = []
        for clause in self.iter_clauses():
            if clause.get_nr_of_terms() == 1:
                literal_list.append(clause.get_first_term())
        if not literal_list:
            return self
        cdef CnfFormula fixed_cnf = self
        cdef Term literal
        for literal in literal_list:
            fixed_cnf = fixed_cnf.fix_variable(literal.variable, literal.is_negated())
        return fixed_cnf.fix_literal_clauses()

    cpdef int get_nr_of_literal_clauses(self):
        cdef int nr_of_literal_clauses = 0
        cdef CnfDisjunction clause
        for clause in self.iter_clauses():
            if clause.get_nr_of_terms() == 1:
                nr_of_literal_clauses += 1
        return nr_of_literal_clauses

    def remove_clauses(self, clauses: Iterable[CnfDisjunction]):
        self.__constraint_graph = None
        self.__disjunctions.difference_update(clauses)

    def add_clauses(self, clauses: Iterable[CnfDisjunction]):
        self.__disjunctions.update(clauses)

    def remove_new_clauses(self, clauses: Iterable[CnfDisjunction]):
        self.__new_disjunctions.difference_update(clauses)

    def add_new_clauses(self, clauses: Iterable[CnfDisjunction]):
        self.__new_disjunctions.update(clauses)

    def to_dimacs(self) -> str:
        """
        creates a string DIMACS CNF representation of this formula.
        see https://jix.github.io/varisat/manual/0.2.0/formats/dimacs.html
        """
        return f'p cnf {max(self.__variable_nr_set)} {self.get_nr_of_clauses()}\n' + '\n'.join(
            ' '.join(str(term.to_int_encoding()) for term in disjunction) + ' 0'
            for disjunction in self.iter_clauses()
        )

    def iter_clauses(self) -> Iterator[CnfDisjunction]:
        return chain(self.__disjunctions, self.__new_disjunctions)

    cpdef Value value(self):
        cdef Value default_value = Value.TRUE
        cdef CnfDisjunction clause
        cdef Value clause_value
        for clause in self.iter_clauses():
            clause_value = clause.value()
            if clause_value == Value.UNKNOWN:
                default_value = Value.UNKNOWN
            elif clause_value == Value.FALSE:
                return Value.FALSE
        return default_value

    cpdef Value value_after_variable_changed(
            self, Value cnf_value_before_change,
            Variable variable):
        cdef CnfDisjunction clause
        cdef Value clause_value
        if cnf_value_before_change == Value.TRUE:
            for clause in self.iter_clauses():
                if clause.contains_variable(variable):
                    clause_value = clause.value()
                    if clause_value != Value.TRUE:
                        return clause_value
            return cnf_value_before_change
        else:
            return self.value()

    cpdef ConstraintGraph to_constraint_graph(self):
        """
        converts this formula into a constraint graph,
        i.e. variables are nodes and two variables are connected by an
        undirected edge if they occur together in a clause
        """
        if self.__constraint_graph is None:
            self.__constraint_graph = ConstraintGraph()
            self.__add_disjunctions_to_constraint_graph(self.__disjunctions)
            self.__add_disjunctions_to_constraint_graph(self.__new_disjunctions)
        else:
            self.__add_disjunctions_to_constraint_graph(self.__new_disjunctions)
        return self.__constraint_graph

    @cython.boundscheck(False)
    cpdef ImplicationGraph to_implication_graph(self):
        """
        converts this formula into an implication graph,
        i.e. variables and their negation are nodes and two variables are connected by an
        undirected edge if they occur together in a clause.
        """
        cdef ImplicationGraph implication_graph = ImplicationGraph(max(self.__variable_nr_set))
        cdef CnfDisjunction clause
        cdef set clause_set
        cdef tuple terms
        cdef size_t clause_length
        cdef int term_i_encoding, term_j_encoding
        cdef size_t i
        cdef size_t j
        for clause_set in (self.__disjunctions, self.__new_disjunctions):
            for clause in clause_set:
                terms = clause.get_terms()
                clause_length = len(terms)
                if clause_length == 1:
                    term_i_encoding = (<Term>terms[0]).to_int_encoding()
                    implication_graph.add_edge(-term_i_encoding, term_i_encoding)
                else:
                    for i in range(clause_length):
                        term_i_encoding = (<Term>terms[i]).to_int_encoding()
                        for j in range(i+1,clause_length):
                            term_j_encoding = (<Term>terms[j]).to_int_encoding()
                            implication_graph.add_edge(-term_i_encoding, term_j_encoding)
                            implication_graph.add_edge(-term_j_encoding, term_i_encoding)
        return implication_graph

    cdef __add_disjunctions_to_constraint_graph(self, set disjunctions):
        cdef tuple terms
        cdef size_t clause_length
        cdef int i
        cdef int j
        for clause in disjunctions:
            clause_length = (<CnfDisjunction>clause).get_nr_of_terms()
            if clause_length == 1:
                self.__constraint_graph.add_node_if_not_existing((<CnfDisjunction>clause).get_first_term().variable)
            else:
                terms = (<CnfDisjunction>clause).get_terms()
                for i in range(clause_length):
                    for j in range(i+1,clause_length):
                        self.__constraint_graph.add_edge(
                            (<Term>PyTuple_GET_ITEM(terms, i)).variable,
                            (<Term>PyTuple_GET_ITEM(terms, j)).variable
                        )
        return self.__constraint_graph

    cpdef CnfFormula clauses_must_contain_one_of(self, set variable_set):
        cdef set filtered_clauses = set()
        cdef Term term
        for clause in self.__disjunctions:
            if (<CnfDisjunction>clause).contains_one_of(variable_set):
                filtered_clauses.add(clause)
        for clause in self.__new_disjunctions:
            if (<CnfDisjunction>clause).contains_one_of(variable_set):
                filtered_clauses.add(clause)
        return CnfFormula(filtered_clauses)

    cpdef dict compute_variables_dict(self):
        """
        returns Dict[int, Variable], variable_nr => Variable
        """
        cdef set open_variable_nrs = set(self.get_variable_nr_set())
        cdef dict variables = {}
        cdef Term term
        for clause in self.iter_clauses():
            for term in <CnfDisjunction>clause:
                try:
                    open_variable_nrs.remove(term.variable.nr)
                    variables[term.variable.nr] = term.variable
                except KeyError:
                    if not open_variable_nrs:
                        return variables
        return variables

    cpdef bint has_overlap(self, CnfFormula other):
        for clause in self.__disjunctions:
            if other.contains_clause(clause):
                return True
        for clause in self.__new_disjunctions:
            if other.contains_clause(clause):
                return True
        return False

    cpdef bint contains_clause(self, CnfDisjunction clause):
        return clause in self.__disjunctions or clause in self.__new_disjunctions

    def __repr__(self):
        return ' & '.join(f'({clause})' for clause in self.iter_clauses())

    def __eq__(self, other):
        return (
            isinstance(other, CnfFormula) and
            self.__disjunctions == (<CnfFormula>other).__disjunctions and
            self.__new_disjunctions == (<CnfFormula>other).__new_disjunctions
        )