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

from libc.math cimport ceil, log2
cimport cython
from prolothar_common.mdl_utils cimport log2binom, L_N, prequential_coding_length
from prolothar_ca.ca.methods.custom.sat_encoding import SatEncodedExample

from prolothar_ca.model.sat.variable cimport Variable, Value
from prolothar_ca.solver.sat.modelcount.model_counter import ModelCounter

@cython.cdivision(True)
cpdef double compute_error_score(CnfFormula candidate_cnf, dict example, int example_id):
    for variable, variable_value in example.items():
        (<Variable>variable).value = <Value>variable_value
    cdef int nr_of_variables = <int>len(example)
    cdef int nr_of_errors = min(
        nr_of_variables // 2,
        <int>(ceil(nr_of_variables - nr_of_variables * (1 - 1 / (<double>nr_of_variables))**candidate_cnf.get_nr_of_untrue_clauses_for_example(example_id)))
    )
    return L_N(nr_of_errors+1) + log2binom(nr_of_variables, nr_of_errors)

@cython.cdivision(True)
cpdef double estimate_error_score(CnfFormula candidate_cnf, dict example, int example_id, int nr_of_sampled_clauses):
    for variable, variable_value in example.items():
        (<Variable>variable).value = <Value>variable_value
    cdef int nr_of_variables = <int>len(example)
    cdef int nr_of_errors = min(
        nr_of_variables // 2,
        <int>(ceil(nr_of_variables - nr_of_variables * (1 - 1 / (<double>nr_of_variables))**candidate_cnf.estimate_nr_of_untrue_clauses_for_example(example_id, nr_of_sampled_clauses)))
    )
    return L_N(nr_of_errors+1) + log2binom(nr_of_variables, nr_of_errors)

cpdef double compute_encoded_data_length_from_known_solution(
        CnfFormula candidate_cnf, list sat_encoded_dataset,
        dict variables, sat_model_counter: ModelCounter,
        dict solution):
    for variable, variable_value in (<dict>solution).items():
        (<Variable>variable).value = <Value>variable_value
    cdef double encoded_length = len(sat_encoded_dataset) * sat_model_counter.countlog2(candidate_cnf)
    #one bit to encode true or false for each variable not in the model
    encoded_length += len(sat_encoded_dataset) * (len(variables) - len(candidate_cnf.get_variable_nr_set()))
    for i,example in enumerate(sat_encoded_dataset):
        encoded_length += compute_error_score(candidate_cnf, <dict>example, <int>i)
    return encoded_length

cpdef double compute_encoded_data_length_from_known_solution_with_upperbound(
        CnfFormula candidate_cnf, list sat_encoded_dataset,
        dict variables, sat_model_counter: ModelCounter,
        dict solution, double upperbound):
    for variable, variable_value in (<dict>solution).items():
        (<Variable>variable).value = <Value>variable_value
    cdef double encoded_length = len(sat_encoded_dataset) * sat_model_counter.countlog2(candidate_cnf)
    #one bit to encode true or false for each variable not in the model
    encoded_length += len(sat_encoded_dataset) * (len(variables) - len(candidate_cnf.get_variable_nr_set()))
    for i,example in enumerate(sat_encoded_dataset):
        encoded_length += compute_error_score(candidate_cnf, <dict>example, <int>i)
        if encoded_length > upperbound:
            return encoded_length
    return encoded_length

cpdef double compute_encoded_planning_data_length_with_upperbound(
        list candidate_cnf_list, list sat_encoded_dataset, double upperbound):
    cdef double encoded_length = 0
    cdef int nr_of_positive_examples = 0
    cdef int nr_of_negative_examples = 0
    cdef int i
    for i,candidate_cnf in enumerate(candidate_cnf_list):
        if candidate_cnf.get_nr_of_untrue_clauses_for_example(i) == 0:
            nr_of_positive_examples += 1
            encoded_length += log2(len(<list>(sat_encoded_dataset[i])) - len(candidate_cnf.get_variable_nr_set()))
        else:
            encoded_length += log2(len(candidate_cnf.get_variable_nr_set()))
            nr_of_negative_examples += 1
        if encoded_length > upperbound:
            return encoded_length
    if nr_of_negative_examples > nr_of_positive_examples:
        #we prevent selection of a constraint that most of the time is wrong (and thus has low entropy)
        return float('inf')
    encoded_length += prequential_coding_length({0: nr_of_positive_examples, 1: nr_of_negative_examples})
    return encoded_length

def compute_encoded_data_length(
        candidate_cnf: CnfFormula, sat_encoded_dataset: list[SatEncodedExample],
        variables: dict[int, Variable], sat_model_counter: ModelCounter) -> float:
    encoded_length = 0
    for example in sat_encoded_dataset:
        encoded_length += computed_encoded_length_of_example(
            candidate_cnf, example, variables, sat_model_counter)
    return encoded_length

def computed_encoded_length_of_example(
        candidate_cnf: CnfFormula, example: SatEncodedExample,
        variables: dict[int, Variable],
        sat_model_counter: ModelCounter) -> float:
    for variable, variable_value in example.items():
        variable.value = variable_value

    false_clauses, false_new_clauses = candidate_cnf.get_untrue_clauses()
    nr_of_variables = len(variables)
    nr_of_errors = min(
        nr_of_variables // 2,
        int(ceil(nr_of_variables - nr_of_variables * (1 - 1 / nr_of_variables)**(0.5 * (len(false_clauses) + len(false_new_clauses)))))
    )
    encoded_length = L_N(nr_of_errors+1) + log2binom(nr_of_variables, nr_of_errors)

    candidate_cnf.remove_clauses(false_clauses)
    candidate_cnf.remove_new_clauses(false_new_clauses)
    if candidate_cnf.get_nr_of_clauses() > 0:
        encoded_length += sat_model_counter.countlog2(candidate_cnf)
        #one bit to encode true or false for each variable not in the model
        encoded_length += len(variables) - len(candidate_cnf.get_variable_nr_set())
    else:
        encoded_length += len(variables)
    candidate_cnf.add_clauses(false_clauses)
    candidate_cnf.add_new_clauses(false_new_clauses)

    return encoded_length
