import unittest
from copy import deepcopy

from prolothar_ca.ca.dataset_generator.random import RandomCaDatasetGenerator
from prolothar_ca.ca.noise_generator.noisy_examples_adder import NoisyExamplesAdder
from prolothar_ca.ca.noise_generator.boolean_relation_flipper import BooleanRelationFlipper

class TestNoisyExamplesAdder(unittest.TestCase):

    def test_generate(self):
        dataset_generator = RandomCaDatasetGenerator(
            dimensions=2, nr_of_objects=10, boolean_features=1, numeric_features=1, numeric_values=3)
        original_ca_dataset = dataset_generator.generate(10, 0, random_seed=21092022)
        target_relation_name = dataset_generator.get_target().relation_name

        self.__test_noise_level(original_ca_dataset, target_relation_name, 0)
        self.__test_noise_level(original_ca_dataset, target_relation_name, 0.3)
        self.__test_noise_level(original_ca_dataset, target_relation_name, 0.5)
        self.__test_noise_level(original_ca_dataset, target_relation_name, 1)

    def __test_noise_level(self, original_ca_dataset, target_relation_name, noise_level: float):
        expected_nr_of_noisy_examples = len(original_ca_dataset) * noise_level
        noise_generator = NoisyExamplesAdder(noise_level, BooleanRelationFlipper(
            0.1, target_relation_name, random_seed=322023), random_seed=322023)
        noisy_dataset = deepcopy(original_ca_dataset)
        noise_generator.apply(original_ca_dataset)
        nr_of_noisy_examples = 0
        for left_example, right_example in zip(original_ca_dataset, noisy_dataset):
            if left_example.relations != right_example.relations:
                nr_of_noisy_examples += 1
        self.assertEqual(expected_nr_of_noisy_examples, nr_of_noisy_examples)

if __name__ == '__main__':
    unittest.main()