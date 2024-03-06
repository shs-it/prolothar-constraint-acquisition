import unittest

from prolothar_ca.ca.dataset_generator.sudoku import SudokuCaDatasetGenerator, CELL_TYPE_NAME

class TestSudokuCaDatasetGenerator(unittest.TestCase):

    def test_generate(self):
        dataset_generator = SudokuCaDatasetGenerator(4)
        positive_ca_dataset = dataset_generator.generate(1, 0, random_seed=17082022)
        negative_ca_dataset = dataset_generator.generate(0, 1, random_seed=17082022)

        for constraint in dataset_generator.get_ground_truth_constraints():
            print(constraint)
            for example in positive_ca_dataset:
                constraint.holds(example, {})

        for example in negative_ca_dataset:
            self.assertTrue(any(
                not constraint.holds(example, {})
                for constraint in dataset_generator.get_ground_truth_constraints()
            ))

    def test_generate_with_block_feature(self):
        dataset_generator = SudokuCaDatasetGenerator(4, include_block_feature=True)
        positive_ca_dataset = dataset_generator.generate(1, 0, random_seed=17082022)
        negative_ca_dataset = dataset_generator.generate(0, 1, random_seed=17082022)
        self.assertEqual(3, len(positive_ca_dataset.get_object_type(CELL_TYPE_NAME).feature_definition))

        for constraint in dataset_generator.get_ground_truth_constraints():
            for example in positive_ca_dataset:
                constraint.holds(example, {})

        for example in negative_ca_dataset:
            self.assertTrue(any(
                not constraint.holds(example, {})
                for constraint in dataset_generator.get_ground_truth_constraints()
            ))

if __name__ == '__main__':
    unittest.main()