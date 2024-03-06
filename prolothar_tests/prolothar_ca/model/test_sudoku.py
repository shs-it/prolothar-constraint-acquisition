import unittest
import numpy as np

from prolothar_ca.model.sudoku import Sudoku

class TestSudoku(unittest.TestCase):

    def test_to_pddl(self):
        domain, problem = Sudoku().to_pddl()
        self.assertIsNotNone(domain)
        self.assertIsNotNone(problem)

    def test_from_and_to_numpy(self):
        array = np.array([
            [2, 4, 3, 8, 6, 5, 7, 1, 9],
            [6, 9, 7, 3, 1, 4, 5, 2, 8],
            [1, 5, 8, 9, 7, 2, 6, 3, 4],
            [4, 5, 1, 6, 2, 3, 8, 9, 7],
            [3, 7, 9, 5, 4, 8, 1, 2, 6],
            [8, 6, 2, 9, 7, 1, 4, 5, 3],
            [4, 8, 7, 2, 5, 6, 3, 6, 1],
            [9, 3, 2, 1, 8, 7, 9, 4, 5],
            [5, 1, 6, 4, 3, 9, 8, 7, 2]
        ])
        sudoku = Sudoku.from_numpy(array)
        self.assertTrue(np.array_equal(array, sudoku.to_numpy()))
        self.assertFalse(sudoku.is_solved())

if __name__ == '__main__':
    unittest.main()