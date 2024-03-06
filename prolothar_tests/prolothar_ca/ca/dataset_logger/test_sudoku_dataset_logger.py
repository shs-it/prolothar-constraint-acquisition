import os
import unittest
from tempfile import TemporaryDirectory

from prolothar_ca.ca.dataset_generator.sudoku import SudokuCaDatasetGenerator
from prolothar_ca.ca.dataset_logger.sudoku_dataset_logger import SudokuDatasetLogger

class TestSudokuDatasetLogger(unittest.TestCase):

    def test_log_dataset(self):
        dataset = SudokuCaDatasetGenerator(4).generate(3, 2, random_seed=17082022)
        with TemporaryDirectory() as tempdir:
            dataset_logger = SudokuDatasetLogger(tempdir)
            dataset_logger.log_dataset(dataset, 'testdataset')
            self.assertEqual(3, len(os.listdir(dataset_logger.get_positive_examples_directory('testdataset'))))
            self.assertEqual(2, len(os.listdir(dataset_logger.get_negative_examples_directory('testdataset'))))

if __name__ == '__main__':
    unittest.main()