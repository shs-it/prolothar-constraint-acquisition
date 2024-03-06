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

from optapy import solver_factory_create
from optapy.types import SolverConfig, TerminationConfig, Duration
import optapy.config

from prolothar_ca.model.sudoku import Sudoku

from prolothar_ca.solver.optapy.sudoku.constraints import create_constraint_provider
from prolothar_ca.solver.optapy.sudoku.solution import SudokuSolution
from prolothar_ca.solver.optapy.sudoku.entities import Cell
from prolothar_ca.solver.optapy.sudoku.facts import CellValue

class SudokuSolver:

    def __init__(
        self, row_constraint_active: bool = True,
        column_constraint_active: bool = True,
        block_constraint_active: bool = True):
        """
        creates a new solver instance. the parameters can be used to switch off
        certain constraints, which is useful in generating invalid example
        solutions that are not completely random.

        Parameters
        ----------
        row_constraint_active : bool, optional
            decides whether the constraint that all values in a row must be different
            should be active, by default True
        column_constraint_active : bool, optional
            decides whether the constraint that all values in a column must be different
            should be active, by default True
        block_constraint_active : bool, optional
            decides whether the constraint that all values in a block must be different
            should be active, by default True
        """
        self.__row_constraint_active = row_constraint_active
        self.__column_constraint_active = column_constraint_active
        self.__block_constraint_active = block_constraint_active

    def solve(
        self, sudoku: Sudoku,
        termination_spent_limit_in_s: int|None = 300) -> Sudoku:
        """
        solves the given instance of sudoku if there is a feasible solution

        returns the solved Sudoku instance. depending on the instance and the
        termination_spent_limit_in_s it might be that the instance is not solved.
        check result.is_solved() to verify whether the solution is solved
        """
        termination_config = TerminationConfig()\
            .withBestScoreFeasible(True)\
            .withTerminationCompositionStyle(optapy.config.solver.termination.TerminationCompositionStyle.OR)
        if termination_spent_limit_in_s is not None:
            termination_config = termination_config.withSpentLimit(
                Duration.ofSeconds(termination_spent_limit_in_s))
        solver_config = SolverConfig()\
            .withEntityClasses(Cell)\
            .withSolutionClass(SudokuSolution)\
            .withConstraintProviderClass(create_constraint_provider(
                sudoku.get_block_size(),
                row_constraint_active = self.__row_constraint_active,
                column_constraint_active = self.__column_constraint_active,
                block_constraint_active = self.__block_constraint_active
            ))\
            .withTerminationConfig(termination_config)

        solver = solver_factory_create(solver_config).buildSolver()
        optapy_solution = solver.solve(self.__generate_problem(sudoku))
        return self.__map_optapy_solution(optapy_solution, sudoku.get_max_value())

    def __generate_problem(self, sudoku: Sudoku) -> SudokuSolution:
        return SudokuSolution(
            [
                CellValue(i) for i in range(1, sudoku.get_max_value() + 1)
            ],
            [
                Cell(
                    x,
                    y,
                    value = CellValue(value) if value is not None else None,
                    pinned = value is not None
                ) for x,y,value in sudoku
            ]
        )

    def __map_optapy_solution(self, solution: SudokuSolution, max_value: int) -> Sudoku:
        sudoku = Sudoku(max_value)
        for cell in solution.cell_list:
            if cell is None:
                raise NotImplementedError(solution.cell_list)
            sudoku[cell.x_coordinate, cell.y_coordinate] = cell.value.number
        return sudoku

