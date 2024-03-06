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

from itertools import product
from math import ceil, log2
import numpy as np
from prolothar_ca.model.sat.cnf import CnfFormula
from prolothar_ca.solver.sat.modelcount.model_counter import ModelCounter

class PolynomialUpperBound(ModelCounter):
    """
    gives a polynomial times upper bound on the number of solutions of a CNF

    https://www.researchgate.net/profile/Bernd-Schuh-2/publication/316985615_Polynomial_time_estimates_for_SAT/links/591f0acbaca272d31bd3cfac/Polynomial-time-estimates-for-SAT.pdf
    """

    def count(self, cnf: CnfFormula) -> int:
        nr_of_variables = max(cnf.get_variable_nr_set())
        return ceil(self.__compute_upper_bound_fraction(cnf, nr_of_variables) * 2**nr_of_variables)

    def countlog2(self, cnf: CnfFormula) -> float:
        nr_of_variables = max(cnf.get_variable_nr_set())
        return log2(self.__compute_upper_bound_fraction(cnf, nr_of_variables)) + nr_of_variables

    def __compute_upper_bound_fraction(self, cnf: CnfFormula, int nr_of_variables) -> float:
        f = []
        for clause in cnf.iter_clauses():
            f_row = [0] * nr_of_variables
            for term in clause:
                f_row[(term.variable.nr - 1)] = -1 if term.is_negated() else 1
            f.append(f_row)
        f = np.array(f, dtype=float)

        two_to_power_of_minus_k = np.power(2, -np.sum(np.abs(f), axis=1))
        lambdas = np.matmul(two_to_power_of_minus_k, f)
        mus = np.einsum('i,ij,ik->jk',two_to_power_of_minus_k,f,f)
        np.fill_diagonal(mus, 0)
        mus[np.tril_indices_from(mus)] = 0
        vs = np.einsum('i,ij,ik,il->jkl', two_to_power_of_minus_k,f,f,f)
        cdef double[:,:,:] vs_view = vs
        cdef int i,j,k
        for i in range(nr_of_variables):
            for j in range(nr_of_variables):
                for k in range(nr_of_variables):
                    if i >= j or i >= k or j >= k:
                        vs_view[i,j,k] = 0
        variance = np.sum(np.square(lambdas)) + np.sum(np.square(mus)) + np.sum(np.square(vs))
        c = np.sum(two_to_power_of_minus_k)
        return variance / (variance + c*c)