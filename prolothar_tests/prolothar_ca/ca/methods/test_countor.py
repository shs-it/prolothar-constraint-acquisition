import unittest
from prolothar_ca.model.ca.targets import RelationTarget

from prolothar_ca.model.rostering import SchedulingPeriod, Solution, ca_names
from prolothar_ca.model.sudoku import Sudoku

from prolothar_ca.ca.methods.countor.countor import CountOr
from prolothar_ca.ca.dataset_generator.sudoku import CELL_VALUE_RELATION, SudokuCaDatasetGenerator
from prolothar_ca.ca.dataset_generator.n_queens import NQueensCaDatasetGenerator

class TestCountOr(unittest.TestCase):

    def test_acquire_constraints_sudoku(self):
        sudoku_dataset_generator = SudokuCaDatasetGenerator(4)
        ca_dataset = sudoku_dataset_generator.generate(2, 0, random_seed=10082022)

        count_or = CountOr()
        constraints = count_or.acquire_constraints(ca_dataset, RelationTarget(CELL_VALUE_RELATION))
        self.assertIsNotNone(constraints)
        for constraint in constraints:
            print(constraint)
            for example in ca_dataset:
                self.assertTrue(constraint.holds(example, {}))

        #validate that CountOr misses to detect a specific negative example
        #that violates the block constraint in sudoku, but follows all the
        #row and column constraints
        block_constraint_violating_sudoku = Sudoku(4)
        for i in range(4):
            for j in range(4):
                block_constraint_violating_sudoku[i,j] = (i + j) % 4 + 1
        self.assertFalse(block_constraint_violating_sudoku.is_solved())
        block_constraint_violating_example = sudoku_dataset_generator.sudoku_to_example(
            block_constraint_violating_sudoku, False)
        self.assertTrue(all(c.holds(block_constraint_violating_example, {}) for c in constraints))

    def test_acquire_constraints_nqueens(self):
        dataset_generator = NQueensCaDatasetGenerator(4)
        ca_dataset = dataset_generator.generate(10, 0, random_seed=22082022)

        count_or = CountOr()
        constraints = count_or.acquire_constraints(ca_dataset, dataset_generator.get_target())
        self.assertIsNotNone(constraints)
        self.assertGreater(len(constraints), 0)
        for constraint in constraints:
            print(constraint)
            for example in ca_dataset:
                self.assertTrue(constraint.holds(example, {}))

if __name__ == '__main__':
    unittest.main()