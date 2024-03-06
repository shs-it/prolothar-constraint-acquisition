import unittest
from copy import deepcopy

from prolothar_ca.ca.dataset_generator.random import RandomCaDatasetGenerator
from prolothar_ca.ca.noise_generator.boolean_relation_flipper import BooleanRelationFlipper

class TestBooleanTargetFlipper(unittest.TestCase):

    def test_generate(self):
        dataset_generator = RandomCaDatasetGenerator(
            dimensions=2, nr_of_objects=10, boolean_features=1, numeric_features=1, numeric_values=3)
        original_ca_dataset = dataset_generator.generate(10, 0, random_seed=21092022)
        target_relation_name = dataset_generator.get_target().relation_name

        self.__assert_nr_of_flips_equals(original_ca_dataset, 0.0, target_relation_name, 0)
        self.__assert_nr_of_flips_equals(original_ca_dataset, 0.01, target_relation_name, 10)
        self.__assert_nr_of_flips_equals(original_ca_dataset, 1.0, target_relation_name, 1000)

    def __assert_nr_of_flips_equals(self, original_ca_dataset, noise_proportion, target_relation_name, expected_nr_of_flips):
        noise_generator = BooleanRelationFlipper(noise_proportion, target_relation_name)
        noisy_ca_dataset = deepcopy(original_ca_dataset)
        noise_generator.apply(noisy_ca_dataset)
        self.assertEqual(expected_nr_of_flips, self.__compute_nr_of_flips(original_ca_dataset, noisy_ca_dataset, target_relation_name))

    def __compute_nr_of_flips(self, original_ca_dataset, noisy_ca_dataset, target_relation_name):
        nr_of_flips = 0
        for original_example, noisy_example in zip(original_ca_dataset, noisy_ca_dataset):
            for original_relation, noisy_relation in zip(
                    sorted(original_example.relations[target_relation_name], key=lambda r: tuple(o.object_id for o in r.objects)),
                    sorted(noisy_example.relations[target_relation_name], key=lambda r: tuple(o.object_id for o in r.objects))):
                if original_relation.value != noisy_relation.value:
                    nr_of_flips += 1
        return nr_of_flips

if __name__ == '__main__':
    unittest.main()