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

from prolothar_common.mdl_utils cimport L_N, log2binom
from prolothar_common.experiments.statistics cimport Statistics

from prolothar_ca.ca.methods.custom.mdl_score cimport compute_encoded_data_length_from_known_solution_with_upperbound
from prolothar_ca.ca.methods.custom.mdl_score cimport compute_error_score
from prolothar_ca.ca.methods.custom.mdl_score cimport estimate_error_score
from prolothar_ca.ca.methods.custom.model.custom_constraint cimport Count
from prolothar_ca.ca.methods.custom.model.custom_constraint cimport DataGraph
from libc.math cimport log2, ceil

from prolothar_ca.solver.sat.solver.solver import SatSolver
from prolothar_ca.solver.sat.solver.twosat_solver import TwoSatSolver
from prolothar_ca.model.sat.term_factory cimport TermFactory
from prolothar_ca.model.sat.variable cimport Variable, Value


cdef class Candidate:

    def __init__(
            self, CustomConstraint constraint,
            DataGraph datagraph,
            list dataset,
            TermFactory term_factory,
            sat_solver: SatSolver = TwoSatSolver(),
            int nr_of_sampled_clauses_for_error = 0):
        self.constraint = constraint
        self.replaced_constraint = None
        self.replaced_constraint_index = None
        self.model_cnf = CnfFormula(self.constraint.compute_cnf_clauses(datagraph, term_factory))
        self.model_cost = 0
        self.data_cost = 0
        self.total_cost = 0
        self.gain = (
            self.constraint.encoded_model_length -
            len(dataset) * len(self.model_cnf.get_variable_nr_set())
        )
        cdef bint at_least_one_example_satisfied = False
        cdef int i
        if self.model_cnf.get_nr_of_clauses() == 0:
            self.gain = float('inf')
        else:
            self.gain += len(dataset)
            for i,example in enumerate(dataset):
                if nr_of_sampled_clauses_for_error <= 0:
                    self.gain += compute_error_score(self.model_cnf, <dict>example, i)
                else:
                    self.gain += estimate_error_score(
                        self.model_cnf, <dict>example, i, nr_of_sampled_clauses_for_error)
                if self.model_cnf.get_nr_of_untrue_clauses_for_example(i) == 0:
                    at_least_one_example_satisfied = True
                if self.gain > 0:
                    break
            if not at_least_one_example_satisfied:
                self.gain = float('inf')
        self.iteration = 0
        self.__sat_solver = sat_solver

    cpdef update_gain(
            self, int iteration, list model, double model_cost,
            CnfFormula model_cnf, list sat_encoded_dataset,
            double total_cost, dict variables,
            sat_model_counter):
        # model is empty in iteration 1 => we can use the model created in __init__
        if iteration > 1:
            self.model_cnf = model_cnf.extend(self.model_cnf)
            if self.model_cnf.get_nr_of_clauses() == model_cnf.get_nr_of_clauses():
                #all constraints are redundant
                self.gain = self.constraint.encoded_model_length
                return
        cdef dict solution = self.__find_solution_from_dataset(sat_encoded_dataset)
        if solution is None:
            solution = self.__sat_solver.solve_cnf(self.model_cnf)
        if solution is None:
            #we do not want unsatisfiable models that result from contradictory constraints!
            self.gain = self.constraint.encoded_model_length
            return
        cdef CustomConstraint constraint, merged_constraint
        if self.replaced_constraint_index is not None:
            constraint = model[self.replaced_constraint_index]
            if self.replaced_constraint is not constraint:
                self.replaced_constraint = constraint
                self.constraint = (<CustomConstraint>model[self.replaced_constraint_index]).merge(self.constraint)
                self.model_cost = model_cost - constraint.encoded_model_length + self.constraint.encoded_model_length
        else:
            for i, constraint in enumerate(model):
                merged_constraint = constraint.merge(self.constraint)
                if merged_constraint is not None:
                    self.replaced_constraint = constraint
                    self.replaced_constraint_index = i
                    self.constraint = merged_constraint
                    self.model_cost = model_cost - constraint.encoded_model_length + merged_constraint.encoded_model_length
                    break
            else:
                self.model_cost = (
                    model_cost - L_N(len(model) + 1) + L_N(len(model) + 2) +
                    self.constraint.encoded_model_length
                )
        try:
            self.data_cost = compute_encoded_data_length_from_known_solution_with_upperbound(
                self.model_cnf, sat_encoded_dataset, variables, sat_model_counter,
                solution, total_cost)
        except OverflowError:
            #we have a very high number of possible solutions for the boolean formula model
            self.data_cost = float('inf')
        self.iteration = iteration
        self.total_cost = self.model_cost + self.data_cost
        self.gain = self.total_cost - total_cost

    cdef dict __find_solution_from_dataset(self, list sat_encoded_dataset):
        for example in sat_encoded_dataset:
            for variable, value in (<dict>example).items():
                (<Variable>variable).value = <Value>value
            if self.model_cnf.value() == Value.TRUE:
                return <dict>example
        return None

    def __lt__(self, other: 'Candidate') -> bool:
        return self.gain < other.gain

cdef class CountCandidate:

    def __init__(
            self, Count count_constraint,
            CnfFormula model_cnf,
            list dataset,
            DataGraph datagraph):
        self.count_constraint = count_constraint
        self.replaced_constraint = None
        self.replaced_constraint_index = None
        self.model_cnf = model_cnf
        self.model_cost = 0
        self.data_cost = 0
        self.total_cost = 0
        self.gain = (
            self.count_constraint.encoded_model_length -
            len(dataset) * count_constraint.get_nr_of_target_variables()
        )
        cdef int nr_of_variables = <int>len(dataset[0])
        cdef int nr_of_untrue_clauses
        self.gain += len(dataset)
        for i,example in enumerate(dataset):
            for variable, value in example.items():
                variable.value = value
            nr_of_untrue_clauses = count_constraint.get_nr_of_untrue_clauses_for_example(datagraph, i)
            self.gain += log2binom(
                nr_of_variables, min(nr_of_variables // 2, nr_of_untrue_clauses))
        self.iteration = 0

    cpdef update_gain(
            self, int iteration, int total_nr_of_constraints_in_model,
            list other_count_constraints, double model_cost,
            list sat_encoded_dataset, DataGraph datagraph, double total_cost,
            list model_count_list):
        cdef Count constraint, merged_constraint
        if self.replaced_constraint_index is not None:
            constraint = other_count_constraints[self.replaced_constraint_index]
            if self.replaced_constraint is not constraint:
                self.replaced_constraint = constraint
                self.count_constraint = (<CustomConstraint>other_count_constraints[self.replaced_constraint_index]).merge(self.count_constraint)
                self.model_cost = model_cost - constraint.encoded_model_length + self.count_constraint.encoded_model_length
        else:
            for i, constraint in enumerate(other_count_constraints):
                merged_constraint = constraint.merge(self.count_constraint)
                if merged_constraint is not None:
                    self.replaced_constraint = constraint
                    self.replaced_constraint_index = i
                    self.count_constraint = merged_constraint
                    self.model_cost = model_cost - constraint.encoded_model_length + merged_constraint.encoded_model_length
                    break
            else:
                self.model_cost = (
                    model_cost - L_N(total_nr_of_constraints_in_model + 1) +
                    L_N(total_nr_of_constraints_in_model + 2) +
                    self.count_constraint.encoded_model_length
                )
        self.model_count = self.count_constraint.count_nr_of_solutions(datagraph)
        cdef Statistics model_count_statistics = Statistics()
        model_count_statistics.push(self.model_count)
        for i,other_model_count in enumerate(model_count_list):
            if self.replaced_constraint_index != i - 1:
                model_count_statistics.push(<double>other_model_count)
        self.data_cost = len(sat_encoded_dataset) * max(0,log2(model_count_statistics.mean() / len(model_count_statistics)))
        cdef int nr_of_errors
        cdef int j
        cdef int nr_of_variables = self.count_constraint.get_nr_of_target_variables()
        cdef Count other_count_constraint
        for j,example in enumerate(sat_encoded_dataset):
            for variable, variable_value in (<dict>example).items():
                (<Variable>variable).value = <Value>variable_value
            nr_of_errors = self.model_cnf.get_nr_of_untrue_clauses_for_example(j)
            nr_of_errors += self.count_constraint.get_nr_of_untrue_clauses_for_example(datagraph, j)
            for other_count_constraint in other_count_constraints:
                if other_count_constraint is not self.replaced_constraint:
                    nr_of_errors += (<Count>other_count_constraint).get_nr_of_untrue_clauses_for_example(datagraph, j)
            nr_of_errors = min(
                nr_of_variables // 2,
                <int>(ceil(nr_of_variables - nr_of_variables * (1 - 1 / nr_of_variables)**(nr_of_errors)))
            )
            self.data_cost += log2binom(nr_of_variables, nr_of_errors)
        self.iteration = iteration
        self.total_cost = self.model_cost + self.data_cost
        self.gain = self.total_cost - total_cost

    def __lt__(self, other: 'CountCandidate') -> bool:
        return self.gain < other.gain