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

from prolothar_ca.model.sat.cnf import CnfFormula
from prolothar_ca.model.sat.variable import Variable, Value
from prolothar_ca.solver.sat.modelcount.model_counter import ModelCounter

class QuadraticVariableElimination(ModelCounter):
    """
    gives a lower bound: in each iteration, we fix the value of one variable
    in the CNF with a known solution => it is the caller's responsibility to ensure
    that the current values of the variables satisfy the CNF.
    we select the variable that eliminates most of the other variables.
    we return 2**|eliminated variables|
    """

    def count(self, cnf: CnfFormula) -> int:
        return 2**self.countlog2(cnf)

    def countlog2(self, cnf: CnfFormula) -> float:
        variables = cnf.compute_variables_dict()
        nr_of_variables = len(variables)
        nr_of_eliminated_variables = 0
        while variables:
            best_cnf = None
            for variable in variables.values():
                cnf_candidate = cnf.fix_variable(variable, variable.value == Value.TRUE)
                candidate_nr_of_eliminated_variables = nr_of_variables - len(cnf_candidate.get_variable_nr_set()) - 1
                if candidate_nr_of_eliminated_variables > nr_of_eliminated_variables:
                    nr_of_eliminated_variables = candidate_nr_of_eliminated_variables
                    best_cnf = cnf_candidate
            if best_cnf is None:
                best_cnf = cnf_candidate
            cnf = best_cnf
            variables = {
                variable_nr: variable for variable_nr, variable in variables.items()
                if variable_nr in cnf.get_variable_nr_set()
            }
            nr_of_variables = len(variables)
        return max(1, nr_of_eliminated_variables)