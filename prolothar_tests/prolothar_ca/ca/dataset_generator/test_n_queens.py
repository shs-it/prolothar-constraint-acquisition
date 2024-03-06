import unittest

from prolothar_ca.ca.dataset_generator.n_queens import NQueensCaDatasetGenerator

class TestNQueensCaDatasetGenerator(unittest.TestCase):

    def test_generate(self):
        dataset_generator = NQueensCaDatasetGenerator(5)
        positive_ca_dataset = dataset_generator.generate(10, 0, random_seed=17082022)
        negative_ca_dataset = dataset_generator.generate(0, 10, random_seed=17082022)

        for constraint in dataset_generator.get_ground_truth_constraints():
            print(constraint)
            for example in positive_ca_dataset:
                constraint.holds(example, {})

        for example in negative_ca_dataset:
            self.assertTrue(any(
                not constraint.holds(example, {})
                for constraint in dataset_generator.get_ground_truth_constraints()
            ))

if __name__ == '__main__':
    unittest.main()