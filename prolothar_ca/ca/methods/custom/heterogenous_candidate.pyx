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

from libc.math cimport log2
from prolothar_common.mdl_utils cimport L_N
from prolothar_ca.ca.methods.custom.mdl_score cimport compute_encoded_planning_data_length_with_upperbound
from prolothar_ca.ca.methods.custom.model.custom_constraint cimport CustomConstraint

from prolothar_ca.model.sat.term_factory cimport TermFactory
from prolothar_ca.model.sat.variable cimport Variable, Value
from prolothar_ca.model.sat.cnf cimport CnfFormula


cdef class Candidate:

    def __init__(
            self, CustomConstraint constraint,
            list datagraph_list,
            list dataset,
            TermFactory term_factory,
            object replaced_constraint_index=None):
        self.constraint = constraint
        self.replaced_constraint = None
        self.replaced_constraint_index = replaced_constraint_index
        self.model_cnf_list = [
            CnfFormula(self.constraint.compute_cnf_clauses(datagraph, term_factory))
            for datagraph in datagraph_list
        ]
        self.model_cost = 0
        self.data_cost = 0
        self.total_cost = 0
        self.gain = self.constraint.encoded_model_length
        cdef bint at_least_one_nonempty_model = False
        for model_cnf in self.model_cnf_list:
            if (<CnfFormula>model_cnf).get_nr_of_clauses() > 0:
                at_least_one_nonempty_model = True
                break
        cdef int i
        if at_least_one_nonempty_model:
            for i,model_cnf in enumerate(self.model_cnf_list):
                self.gain -= log2(len(<list>(dataset[i])))
            self.gain += compute_encoded_planning_data_length_with_upperbound(
                self.model_cnf_list, dataset, float('inf'))
        else:
            self.gain = float('inf')
        self.iteration = 0

    cpdef update_gain(
            self, int iteration, list model, double model_cost,
            list model_cnf_list, list sat_encoded_dataset,
            double total_cost,
            sat_model_counter):
        # model is empty in iteration 1 => we can use the model created in __init__
        if iteration > 1:
            self.model_cnf_list = [a.extend(b) for a,b in zip(model_cnf_list, self.model_cnf_list)]
            for a,b in zip(model_cnf_list, self.model_cnf_list):
                if a.get_nr_of_clauses() != b.get_nr_of_clauses():
                    break
            else:
                #all constraints are redundant
                self.gain = self.constraint.encoded_model_length
                return
        #we do not want unsatisfiable models that result from contradictory constraints!
        cdef bint at_least_one_example_satisfies_model = False
        for i,example in enumerate(sat_encoded_dataset):
            for variable, value in (<dict>example).items():
                (<Variable>variable).value = <Value>value
            model_cnf = self.model_cnf_list[i]
            if model_cnf.value() == Value.TRUE:
                at_least_one_example_satisfies_model = True
        if not at_least_one_example_satisfies_model:
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
            self.data_cost = compute_encoded_planning_data_length_with_upperbound(
                self.model_cnf_list, sat_encoded_dataset, total_cost)
        except OverflowError:
            #we have a very high number of possible solutions for the boolean formula model
            self.data_cost = float('inf')
        self.iteration = iteration
        self.total_cost = self.model_cost + self.data_cost
        self.gain = self.total_cost - total_cost

    def __lt__(self, other: 'Candidate') -> bool:
        return self.gain < other.gain