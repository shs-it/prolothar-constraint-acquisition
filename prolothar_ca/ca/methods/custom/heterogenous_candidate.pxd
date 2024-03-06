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

from prolothar_ca.ca.methods.custom.model.custom_constraint cimport CustomConstraint

cdef class Candidate:

    cdef public list model_cnf_list
    cdef public CustomConstraint constraint
    cdef public CustomConstraint replaced_constraint
    cdef public replaced_constraint_index
    cdef public double model_cost
    cdef public double data_cost
    cdef public double total_cost
    cdef public double gain
    cdef public int iteration

    cpdef update_gain(
            self, int iteration, list model, double model_cost,
            list model_cnf_list, list sat_encoded_dataset,
            double total_cost, sat_model_counter)
