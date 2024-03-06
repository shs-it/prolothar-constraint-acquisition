import unittest

from prolothar_ca.ca.dataset_generator.double_round_robin import DoubleRoundRobinCaDatasetGenerator

class TestDoubleRoundRobinCaDatasetGenerator(unittest.TestCase):

    def test_generate(self):
        dataset_generator = DoubleRoundRobinCaDatasetGenerator(4)
        ca_dataset = dataset_generator.generate(6, 6, random_seed=21092022)
        self.assertEqual(12, len(ca_dataset))
        for example in ca_dataset:
            if example.is_valid_solution:
                for constraint in dataset_generator.get_ground_truth_constraints():
                    self.assertTrue(constraint.holds(example, {}), msg=f'"{constraint}" does not hold')
            else:
                self.assertFalse(all(
                    constraint.holds(example, {}) for constraint
                    in dataset_generator.get_ground_truth_constraints()
                ))

if __name__ == '__main__':
    unittest.main()