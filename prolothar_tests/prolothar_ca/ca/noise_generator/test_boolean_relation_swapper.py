import unittest
from copy import deepcopy

from prolothar_ca.model.ca.dataset import CaDataset
from prolothar_ca.ca.dataset_generator.random import RandomCaDatasetGenerator
from prolothar_ca.ca.noise_generator.boolean_relation_swapper import BooleanRelationSwapper

class TestBooleanTargetSwapper(unittest.TestCase):

    def test_generate(self):
        dataset_generator = RandomCaDatasetGenerator(
            dimensions=2, nr_of_objects=10, boolean_features=1, numeric_features=1, numeric_values=3)
        original_ca_dataset = dataset_generator.generate(10, 0, random_seed=21092022)
        target_relation_name = dataset_generator.get_target().relation_name

        self.__assert_noise_level(original_ca_dataset, 0.0, target_relation_name)
        self.__assert_noise_level(original_ca_dataset, 0.01, target_relation_name)
        self.__assert_noise_level(original_ca_dataset, 1.0, target_relation_name)

    def __assert_noise_level(self, original_ca_dataset, noise_proportion, target_relation_name):
        noise_generator = BooleanRelationSwapper(noise_proportion, target_relation_name)
        noisy_ca_dataset = deepcopy(original_ca_dataset)
        noise_generator.apply(noisy_ca_dataset)
        self.assertListEqual(
            self.__count_true_target_relations_per_example(original_ca_dataset, target_relation_name),
            self.__count_true_target_relations_per_example(noisy_ca_dataset, target_relation_name)
        )

    def __count_true_target_relations_per_example(self, ca_dataset: CaDataset, target_relation_name: str) -> list[int]:
        result_list = []
        for example in ca_dataset:
            nr_of_trues = 0
            for relation in example.relations[target_relation_name]:
                if relation.value:
                    nr_of_trues += 1
            result_list.append(nr_of_trues)
        return result_list


if __name__ == '__main__':
    unittest.main()