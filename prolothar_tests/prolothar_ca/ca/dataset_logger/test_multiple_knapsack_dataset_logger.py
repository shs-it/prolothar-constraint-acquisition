import os
import unittest
from tempfile import TemporaryDirectory

from prolothar_ca.ca.dataset_generator.multiple_knapsack import MultipleKnapsackCaDatasetGenerator
from prolothar_ca.ca.dataset_logger.multiple_knacksack_dataset_logger import MultipleKnapsackDatasetLogger

class TestMultipleKnapsackDatasetLogger(unittest.TestCase):

    def test_log_dataset(self):
        dataset = MultipleKnapsackCaDatasetGenerator().generate(3, 2, random_seed=17082022)
        with TemporaryDirectory() as tempdir:
            dataset_logger = MultipleKnapsackDatasetLogger(tempdir)
            dataset_logger.log_dataset(dataset, 'testdataset')
            self.assertEqual(3, len(os.listdir(dataset_logger.get_positive_examples_directory('testdataset'))))
            self.assertEqual(2, len(os.listdir(dataset_logger.get_negative_examples_directory('testdataset'))))

if __name__ == '__main__':
    unittest.main()