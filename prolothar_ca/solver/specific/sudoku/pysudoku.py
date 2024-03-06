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

import numpy as np
from sudoku import Sudoku as PySudoku

from prolothar_ca.model.sudoku import Sudoku

class SudokuSolver:

    def solve(
        self, sudoku: Sudoku) -> Sudoku:
        """
        solves the given instance of sudoku if there is a feasible solution

        returns the solved Sudoku instance. depending on the instance and the
        termination_spent_limit_in_s it might be that the instance is not solved.
        check result.is_solved() to verify whether the solution is solved
        """
        return Sudoku.from_numpy(np.array(
            PySudoku(sudoku.get_block_size(), board=list(sudoku.iter_rows())).solve().board
        ))


