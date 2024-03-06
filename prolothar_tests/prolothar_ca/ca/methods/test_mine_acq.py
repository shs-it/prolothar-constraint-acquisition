import unittest

from prolothar_ca.ca.methods import MineAcq
from prolothar_ca.ca.dataset_generator.n_queens import NQueensCaDatasetGenerator

class TestMineAcq(unittest.TestCase):

    def test_acquire_constraints_nqueens(self):
        dataset_generator = NQueensCaDatasetGenerator(4, include_queen_permutations=False)
        ca_dataset = dataset_generator.generate(2, 0, random_seed=22082022)

        mine_acq = MineAcq()
        constraints = mine_acq.acquire_constraints(ca_dataset, dataset_generator.get_target())
        self.assertIsNotNone(constraints)
        self.assertGreater(len(constraints), 0)

if __name__ == '__main__':
    unittest.main()