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

from libc.math cimport log2, powl
from more_itertools import first
from libcpp.unordered_set cimport unordered_set

from graycode import gen_gray_codes

from prolothar_ca.model.sat.cnf cimport CnfFormula, CnfDisjunction
from prolothar_ca.model.sat.variable cimport Variable, Value
from prolothar_ca.model.sat.term cimport Term
from prolothar_ca.solver.sat.modelcount.model_counter import ModelCounter

cpdef nr_of_models compute_graph_lower_bound(ConstraintGraph constraint_graph):
    cdef nr_of_models lower_bound = 1
    cdef int node_degree
    for _,node_degree in constraint_graph.degree_per_node():
        # lower_bound *= (node_degree + 2)**(1 / (node_degree + 1))
        lower_bound *= powl(node_degree + 2, 1 / (node_degree + 1))
    return lower_bound

cdef class MC2:
    """
    exact 2-sat model counter with worst-case complexity O(1.1892**m)
    with being the number of clauses
    https://www.cs.huji.ac.il/~jeff/aaai10/02/AAAI10-046.pdf

    we extend the approach with bounds / approximations, which can be
    turned on via the constructor
    """
    cdef bint use_regular_graph_upper_bound
    cdef bint use_regular_graph_lower_bound
    cdef bint use_graph_lower_bound
    cdef bint ignore_non_solution_dpll_branch
    cdef fast_fallback_model_counter
    cdef counter_for_non_solution_dpll_branch

    def __init__(
        self, bint use_regular_graph_upper_bound = False,
        bint use_regular_graph_lower_bound = False,
        bint use_graph_lower_bound = False,
        bint ignore_non_solution_dpll_branch = False,
        counter_for_non_solution_dpll_branch: ModelCounter|None = None,
        fast_fallback_model_counter: ModelCounter|None = None):
        """
        configures

        Parameters
        ----------
        use_regular_graph_upper_bound : bool, optional
            if True (by default False), we use an upper bound if the constraint graph
            in the counting process is a regular graph.
            The number of satisyfing models is equivalent to the number of
            independent sets in the constraint graph
            (see the paper "Counting models for 2SAT and 3SAT formulae"
            by Dahllöf et al.,
            https://reader.elsevier.com/reader/sd/pii/S0304397504007297).
            A regular graph is graph where all nodes have the same degree.
            The number of indepedent sets in a regular graph has an upper bound:
            http://web.mit.edu/yufeiz/www/papers/indep_reg.pdf
        use_regular_graph_lower_bound : bool, optional
            if True (by default False), we use a lower bound if the constraint graph
            in the counting process is a regular graph.
            https://www.sciencedirect.com/science/article/abs/pii/S0095895619300085
        ignore_non_solution_dpll_branch : bool, optional
            if True (by default False), we reduce exponential growth of the
            search space during DPLL split by only discovering the branch
            of a known existing solution. in this case, the variables of the
            CNF must be initialized to a solution before calling the count
            method
        """
        self.use_regular_graph_upper_bound = use_regular_graph_upper_bound
        self.use_regular_graph_lower_bound = use_regular_graph_lower_bound
        self.use_graph_lower_bound = use_graph_lower_bound
        self.fast_fallback_model_counter = fast_fallback_model_counter
        self.counter_for_non_solution_dpll_branch = counter_for_non_solution_dpll_branch
        self.ignore_non_solution_dpll_branch = ignore_non_solution_dpll_branch

    cpdef nr_of_models count(self, CnfFormula cnf, set eliminated_variables = None):
        cdef nr_of_models nr_of_solutions
        if cnf.contains_empty_clause():
            #Case 1 of paper
            nr_of_solutions = 0
        elif cnf.get_nr_of_clauses() == 0:
            #Case 2 of paper
            if eliminated_variables is not None:
                return 2 ** len(eliminated_variables)
            else:
                return 1
        elif len(cnf.get_variable_nr_set()) <= 4:
            #Case 3 of paper
            nr_of_solutions = self.__count_by_enumeration(cnf, self.__create_variable_list(cnf))
        elif cnf.get_nr_of_literal_clauses() > 0:
            return self.count(cnf.fix_literal_clauses())
        else:
            if eliminated_variables is None:
                eliminated_variables = set()
            nr_of_solutions = self.__count_solutions_from_constraint_graph(
                cnf, eliminated_variables)
        if eliminated_variables:
            nr_of_solutions *= (2 ** len(eliminated_variables))
        return nr_of_solutions

    cdef list __create_variable_list(self, CnfFormula cnf):
        cdef unordered_set[int] open_variable_nrs = set(cnf.get_variable_nr_set())
        cdef list variable_list = []
        cdef CnfDisjunction clause
        cdef Term term
        for clause in cnf.iter_clauses():
            for term in clause.get_terms():
                if open_variable_nrs.erase(term.variable.nr) != 0:
                    variable_list.append(term.variable)
                elif open_variable_nrs.empty():
                    return variable_list
        return variable_list

    cdef nr_of_models __count_by_enumeration(self, CnfFormula cnf, list variable_list):
        cdef nr_of_models nr_of_solutions = 0
        cdef Variable variable
        for variable in variable_list:
            variable.value = Value.FALSE
        if cnf.value() == Value.TRUE:
            nr_of_solutions += 1
            last_cnf_value = Value.TRUE
        else:
            last_cnf_value = Value.FALSE
        last_gray_code = 0
        #skip all 0 assignment, which already is handled
        for gray_code in gen_gray_codes(len(variable_list))[1:]:
            changed_variable_index_code = last_gray_code ^ gray_code
            variable = variable_list[(changed_variable_index_code&-changed_variable_index_code).bit_length()-1]
            if variable.value == Value.FALSE:
                variable.value = Value.TRUE
            else:
                variable.value = Value.FALSE
            if cnf.value_after_variable_changed(last_cnf_value, variable) == Value.TRUE:
                nr_of_solutions += 1
                last_cnf_value = Value.TRUE
            else:
                last_cnf_value = Value.FALSE
            last_gray_code = gray_code
        return nr_of_solutions

    cdef nr_of_models __count_solutions_from_constraint_graph(self, CnfFormula cnf, set eliminated_variables):
        constraint_graph = cnf.to_constraint_graph()
        components = constraint_graph.connected_components()
        if len(components) > 1:
            # Case 4 of the paper
            return self.__count_solutions_from_disjoint_components(cnf, components, eliminated_variables)
        elif components:
            return self.__count_solutions_from_connected_graph(cnf, constraint_graph, eliminated_variables)
        else:
            #graph consists of single, unconnected nodes => 1 solution
            return 1

    cdef nr_of_models __count_solutions_from_connected_graph(
            self, CnfFormula cnf, ConstraintGraph constraint_graph, set eliminated_variables):
        cdef int min_degree, max_degree
        min_degree, max_degree, max_degree_variable = self.__compute_min_max_degree(constraint_graph)
        if max_degree == 2:
            # Case 5 of the paper
            if min_degree == 2:
                # constraint_graph is a cycle => fix any variable
                return self.__count_solutions_by_dpll(cnf, max_degree_variable, eliminated_variables)
            else:
                # constraint_graph is a chain => fix variable in the middle
                return self.__count_solutions_from_chain(cnf, constraint_graph, eliminated_variables)
        elif max_degree == 3:
            # Case 6 of the paper
            y, z, w, sum_of_degrees_y_z_w = self.__find_y_z_w(constraint_graph, max_degree_variable)
            lfx, ux = self.__compute_lfx(constraint_graph, max_degree_variable)
            if lfx == 1:
                return self.__count_solutions_by_dpll(cnf, ux, eliminated_variables)
            elif lfx == 2 and sum_of_degrees_y_z_w == 5:
                raise NotImplementedError()
            else:
                return self.__count_solutions_by_dpll(cnf, max_degree_variable, eliminated_variables)
        elif self.use_regular_graph_upper_bound and min_degree == max_degree:
            return powl(powl(2, (min_degree+1)) - 1, (constraint_graph.number_of_nodes()/min_degree/2))
        elif self.use_regular_graph_lower_bound and min_degree == max_degree:
            return powl(min_degree + 2, constraint_graph.number_of_nodes() / (min_degree + 1))
        elif self.use_graph_lower_bound:
            return compute_graph_lower_bound(constraint_graph)
        elif self.fast_fallback_model_counter is not None:
            return self.fast_fallback_model_counter.count(cnf)
        elif self.ignore_non_solution_dpll_branch:
            return self.__count_solutions_by_half_dpll(cnf, max_degree_variable, eliminated_variables)
        elif self.counter_for_non_solution_dpll_branch is not None:
            return self.__count_solutions_by_half_dpll_plus_fallback(cnf, max_degree_variable, eliminated_variables)
        else:
            return self.__count_solutions_by_dpll(cnf, max_degree_variable, eliminated_variables)

    def __find_y_z_w(
            self, constraint_graph,
            max_degree_variable: Variable) -> tuple:
        y, z, w = constraint_graph.get_neighbors(max_degree_variable)
        degree_y = constraint_graph.get_degree(y)
        degree_z = constraint_graph.get_degree(z)
        degree_w = constraint_graph.get_degree(w)
        if degree_z < degree_w:
            z, w = w, z
        if degree_y < degree_z:
            y, z = z, y
        return y, z, w, degree_y + degree_z + degree_w

    cdef nr_of_models __count_solutions_from_chain(
            self, CnfFormula cnf, ConstraintGraph constraint_graph,
            set eliminated_variables):
        split_variable = first(node for node, d in constraint_graph.degree_per_node() if d == 1)
        for _ in range(constraint_graph.number_of_nodes() // 2):
            split_variable = first(constraint_graph.get_neighbors(split_variable))
        return self.__count_solutions_by_dpll(cnf, split_variable, eliminated_variables)

    def __compute_lfx(self, constraint_graph, max_degree_variable) -> tuple:
        neighbors_of_x = constraint_graph.get_neighbors(max_degree_variable)
        ux = [
            neighbor for neighbor in neighbors_of_x
            if constraint_graph.get_neighbors(neighbor).difference(neighbors_of_x)
        ]
        lfx = len(ux)
        ux = ux[0] if lfx == 1 else None
        return lfx, ux

    cdef nr_of_models __count_solutions_from_disjoint_components(
            self, CnfFormula cnf, list components, set eliminated_variables):
        cdef nr_of_models nr_of_solutions = 1
        cdef set component
        for component in components:
            nr_of_solutions *= self.count(
                cnf.clauses_must_contain_one_of(component),
                eliminated_variables=eliminated_variables
            )
        return nr_of_solutions

    cdef tuple __compute_min_max_degree(self, ConstraintGraph constraint_graph):
        cdef int min_degree, max_degree, node_degree
        node_degree_iterator = iter(constraint_graph.degree_per_node())
        max_degree_node, min_degree = next(node_degree_iterator)
        max_degree = min_degree
        for node, node_degree in node_degree_iterator:
            if node_degree < min_degree:
                min_degree = node_degree
            elif node_degree > max_degree:
                max_degree = node_degree
                max_degree_node = node
        return min_degree, max_degree, max_degree_node

    cdef nr_of_models __count_solutions_by_dpll(
            self, CnfFormula cnf, Variable variable,
            set eliminated_variables):
        cnf_variable_true = cnf.fix_variable(variable, True)
        eliminated_variables_true = eliminated_variables.union(
            cnf.get_variable_nr_set().difference(cnf_variable_true.get_variable_nr_set())
        )
        eliminated_variables_true.remove(variable.nr)
        cnf_variable_false = cnf.fix_variable(variable, False)
        eliminated_variables_false = eliminated_variables.union(
            cnf.get_variable_nr_set().difference(cnf_variable_false.get_variable_nr_set())
        )
        eliminated_variables_false.remove(variable.nr)
        return self.count(
            cnf_variable_true,
            eliminated_variables=eliminated_variables_true
        ) + self.count(
            cnf_variable_false,
            eliminated_variables=eliminated_variables_false
        )

    cdef nr_of_models __count_solutions_by_half_dpll(
            self, CnfFormula cnf, Variable variable,
            set eliminated_variables):
        cnf_with_fixed_variable = cnf.fix_variable(variable, variable.value == Value.TRUE)
        eliminated_variables = eliminated_variables.union(
            cnf.get_variable_nr_set().difference(cnf_with_fixed_variable.get_variable_nr_set())
        )
        eliminated_variables.remove(variable.nr)
        return self.count(cnf_with_fixed_variable, eliminated_variables=eliminated_variables)

    cdef nr_of_models  __count_solutions_by_half_dpll_plus_fallback(
            self, CnfFormula cnf, Variable variable,
            set eliminated_variables):
        cnf_variable_true = cnf.fix_variable(variable, True)
        cnf_variable_false = cnf.fix_variable(variable, False)
        if variable.value == Value.TRUE:
            solution_cnf = cnf_variable_true
            non_solution_cnf = cnf_variable_false
            solution_eliminated_variables = eliminated_variables.union(
                cnf.get_variable_nr_set().difference(cnf_variable_true.get_variable_nr_set())
            )
        else:
            solution_cnf = cnf_variable_false
            non_solution_cnf = cnf_variable_true
            solution_eliminated_variables = eliminated_variables.union(
                cnf.get_variable_nr_set().difference(cnf_variable_false.get_variable_nr_set())
            )
        solution_eliminated_variables.remove(variable.nr)
        return self.count(
            solution_cnf,
            eliminated_variables=solution_eliminated_variables
        ) + self.counter_for_non_solution_dpll_branch.count(non_solution_cnf)

    cpdef double countlog2(self, CnfFormula cnf):
        cdef nr_of_models count = self.count(cnf)
        if count != 0:
            return log2(count)
        return 0
