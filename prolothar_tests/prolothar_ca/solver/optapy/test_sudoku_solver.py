import unittest

from prolothar_ca.model.sudoku import Sudoku
from prolothar_ca.solver.optapy.sudoku.solver import SudokuSolver

class TestSudokuSolver(unittest.TestCase):

    def test_solve(self):
        sudoku = Sudoku(4)
        sudoku[0,0] = 3
        sudoku[0,3] = 1
        solver = SudokuSolver()
        sudoku = solver.solve(sudoku)
        self.assertEqual(sudoku[0,0], 3)
        self.assertEqual(sudoku[0,3], 1)
        self.assertTrue(sudoku.is_solved())
        print(sudoku)

    def test_solve_infeasible(self):
        sudoku = Sudoku(4)
        sudoku[0,0] = 3
        sudoku[0,1] = 3
        solver = SudokuSolver()
        sudoku = solver.solve(sudoku, termination_spent_limit_in_s=5)
        self.assertEqual(sudoku[0,0], 3)
        self.assertEqual(sudoku[0,1], 3)
        self.assertFalse(sudoku.is_solved())

if __name__ == '__main__':
    unittest.main()