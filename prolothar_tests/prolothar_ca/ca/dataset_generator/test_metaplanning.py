import unittest

from prolothar_ca.ca.dataset_generator.metaplanning import MetaplanningCaDatasetGenerator

PATH_TO_HANOI_DATASET = 'prolothar_tests/resources/meta_planning/hanoi'

class TestMetaplanningCaDatasetGenerator(unittest.TestCase):

    def test_generate(self):
        dataset_generator = MetaplanningCaDatasetGenerator(PATH_TO_HANOI_DATASET)
        ca_dataset = dataset_generator.generate(5, 3, random_seed=17082022)
        self.assertEqual(8, len(ca_dataset))
        for i,example in enumerate(ca_dataset):
            if example.is_valid_solution:
                for constraint in dataset_generator.get_ground_truth_constraints():
                    self.assertTrue(
                        constraint.holds(example, {}),
                        msg=f'{constraint} violates {i}-th example'
                    )

    def test_get_ground_truth_constraints(self):
        dataset_generator = MetaplanningCaDatasetGenerator(PATH_TO_HANOI_DATASET)
        self.assertEqual(1, len(dataset_generator.get_ground_truth_constraints()))

    def test_generate_more_positive_examples_than_planned(self):
        self.assertRaises(ValueError, lambda: MetaplanningCaDatasetGenerator(
            PATH_TO_HANOI_DATASET,
            search_new_valid_actions=False).generate(101, 0))

        dataset_generator = MetaplanningCaDatasetGenerator(
            PATH_TO_HANOI_DATASET,
            search_new_valid_actions=True)
        ca_dataset = dataset_generator.generate(101, 0, random_seed=17082022)
        self.assertEqual(101, len(ca_dataset))
        for i,example in enumerate(ca_dataset):
            for constraint in dataset_generator.get_ground_truth_constraints():
                self.assertTrue(
                    constraint.holds(example, {}),
                    msg=f'{constraint} violates {i}-th example'
                )

if __name__ == '__main__':
    unittest.main()