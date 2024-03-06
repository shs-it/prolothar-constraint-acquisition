import unittest

from prolothar_ca.ca.dataset_generator.multiple_knapsack import MultipleKnapsackCaDatasetGenerator

class TestMultipleKnapsackCaDatasetGenerator(unittest.TestCase):

    def test_generate(self):
        dataset_generator = MultipleKnapsackCaDatasetGenerator(
            nr_of_items=10, nr_of_knapsacks = 3, min_knapsack_size = 1, max_knapsack_size = 10,
            min_weight=1, max_weight=10, min_value=1, max_value=10, random_seed=14062023
        )
        ca_dataset = dataset_generator.generate(10, 9, random_seed=21092022)
        self.assertEqual(19, len(ca_dataset))
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