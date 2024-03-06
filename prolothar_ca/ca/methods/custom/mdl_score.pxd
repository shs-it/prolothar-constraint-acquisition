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

from prolothar_ca.model.sat.cnf cimport CnfFormula

cpdef double compute_encoded_data_length_from_known_solution(
        CnfFormula candidate_cnf, list sat_encoded_dataset,
        dict variables, sat_model_counter: ModelCounter,
        dict solution)

cpdef double compute_encoded_data_length_from_known_solution_with_upperbound(
        CnfFormula candidate_cnf, list sat_encoded_dataset,
        dict variables, sat_model_counter: ModelCounter,
        dict solution, double upperbound)

cpdef double compute_encoded_planning_data_length_with_upperbound(
        list candidate_cnf_list, list sat_encoded_dataset, double upperbound)

cpdef double compute_error_score(CnfFormula candidate_cnf, dict example, int example_id)

cpdef double estimate_error_score(CnfFormula candidate_cnf, dict example, int example_id, int nr_of_sampled_clauses)
