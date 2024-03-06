import unittest

from prolothar_ca.ca.dataset_generator.random import RandomCaDatasetGenerator

class TestRandomCaDatasetGenerator(unittest.TestCase):

    def test_generate(self):
        dataset_generator = RandomCaDatasetGenerator(
            dimensions=2, boolean_features=2, numeric_features=2, numeric_values=5)
        ca_dataset = dataset_generator.generate(10, 0, random_seed=21092022)
        self.assertEqual(10, len(ca_dataset))

if __name__ == '__main__':
    unittest.main()