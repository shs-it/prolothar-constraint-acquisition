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

from typing import Dict
from prolothar_ca.solver.sat.solver.solver import SatSolver
from prolothar_ca.model.sat.cnf import CnfFormula
from prolothar_ca.model.sat.implication_graph import ImplicationGraph
from prolothar_ca.model.sat.implication_graph cimport ImplicationGraph
from prolothar_ca.model.sat.variable import Variable, Value
from prolothar_ca.model.sat.variable cimport Value as CValue

class TwoSatSolver(SatSolver):
    """
    implementation inspired by
    https://github.com/mikolalysenko/2-sat
    """

    def solve_cnf(self, cnf: CnfFormula) -> Dict[Variable, Value]|None:
        return self.solve_implication_graph(cnf.to_implication_graph(), cnf.compute_variables_dict())

    def solve_implication_graph(self, implication_graph: ImplicationGraph, variables: Dict[int, Variable]) -> Dict[Variable, Value]|None:
        raw_solution = self.__find_raw_solution_from_implication_graph(implication_graph)
        if raw_solution is None:
            return None
        return self.__map_raw_solution(raw_solution, variables)

    def __find_raw_solution_from_implication_graph(self, ImplicationGraph implication_graph) -> Dict[int, Value]|None:
        cdef list connected_components = implication_graph.find_strongly_connected_components()
        cdef dict solution = self.__initialize_solution_to_all_false(connected_components)
        cdef CValue color = CValue.UNKNOWN
        cdef list neighbors
        for component in connected_components:
            (<list>component).sort()
            #visit all nodes in queue
            for variable_nr in (<list>component):
                if variable_nr > 0 and -variable_nr in (<list>component):
                    return None
                if (<CValue>solution[variable_nr]) == CValue.TRUE:
                    color = CValue.TRUE
            #update solution in component
            for variable_nr in (<list>component):
                solution[variable_nr] = color
                if color == CValue.TRUE:
                    solution[-variable_nr] = CValue.FALSE
                    neighbors = implication_graph.get_ancestors(variable_nr)
                else:
                    solution[-variable_nr] = CValue.TRUE
                    neighbors = implication_graph.get_ancestors(-variable_nr)
                for neighbor in neighbors:
                    solution[neighbor] = CValue.TRUE
        return solution

    def __map_raw_solution(self, raw_solution: Dict[int, Value], variables: Dict[int, Variable]) -> Dict[Variable, Value]:
        cdef dict solution = {}
        for variable_nr, variable in variables.items():
            solution[variable] = raw_solution[variable_nr]
        return solution

    def __initialize_solution_to_all_false(self, list connected_components) -> Dict[int, Value]:
        cdef dict solution = {}
        for component in connected_components:
            for variable_nr in <list>component:
                solution[variable_nr] = Value.FALSE
                solution[-variable_nr] = Value.FALSE
        return solution

    def is_cnf_satisfiable(self, cnf: CnfFormula) -> bool:
        implication_graph = cnf.to_implication_graph()
        connected_components = implication_graph.find_strongly_connected_components()
        for component in connected_components:
            if len(set(map(abs, component))) < len(component):
                return False
        return True