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

from pysat.solvers import Solver
from pysat.formula import CNF

from prolothar_ca.solver.sat.solver.solver import SatSolver
from prolothar_ca.model.sat.cnf import CnfFormula
from prolothar_ca.model.sat.variable import Variable, Value

class PySat(SatSolver):
    """
    interface to the PySAT library
    """

    def solve_cnf(self, cnf: CnfFormula) -> dict[Variable, Value]|None:
        with Solver(bootstrap_with=CNF(from_clauses=[
            [term.to_int_encoding() for term in clause]
            for clause in cnf.iter_clauses()
        ])) as solver:
            if solver.solve():
                variables = cnf.compute_variables_dict()
                assignment = {}
                for i, int_encoding in enumerate(solver.get_model()):
                    try:
                        assignment[variables[i+1]] = Value.TRUE if int_encoding > 0 else Value.FALSE
                    except KeyError:
                        #we ignore variables not implicitly present in the CnfFormula
                        pass
                return assignment
            else:
                return None

    def is_cnf_satisfiable(self, cnf: CnfFormula) -> bool:
        with Solver(bootstrap_with=CNF(from_clauses=[
            [term.to_int_encoding() for term in clause]
            for clause in cnf.iter_clauses()
        ])) as solver:
            return solver.solve()