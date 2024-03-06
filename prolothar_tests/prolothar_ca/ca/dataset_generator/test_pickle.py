import unittest

import os
import pickle
from tempfile import TemporaryDirectory

from prolothar_ca.ca.dataset_generator.n_queens import NQueensCaDatasetGenerator
from prolothar_ca.ca.dataset_generator.pickle import PickleCaDatasetGenerator

class TestPickleCaDatasetGenerator(unittest.TestCase):

    def test_generate(self):
        with TemporaryDirectory() as temp_dir:
            temp_file = os.path.join(temp_dir, 'dataset.pickle')
            queens_dataset_generator = NQueensCaDatasetGenerator(5)
            with open(temp_file, 'wb') as f:
                pickle.dump(queens_dataset_generator.generate(10, 5, random_seed=17082022), f)
            dataset_generator = PickleCaDatasetGenerator(
                temp_file, queens_dataset_generator.get_target().relation_name)
            self.assertEqual(15, len(dataset_generator.generate(10, 5)))

if __name__ == '__main__':
    unittest.main()