from prolothar_common.mdl_utils import L_N
from prolothar_ca.ca.methods.custom.model.cross_product_filter import OrCrossProductFilter
from prolothar_ca.ca.methods.custom.model.cross_product_filter import BooleanFeature
from prolothar_ca.ca.methods.custom.model.cross_product_filter import NotCrossProductFilter
from prolothar_ca.ca.methods.custom.model.cross_product_filter import BooleanRelation
import unittest
import sys
from more_itertools import first
sys.setrecursionlimit(15000)

from prolothar_ca.ca.methods.custom.model.custom_constraint import CustomConstraint
from prolothar_ca.ca.methods.custom.model.custom_constraint import DataGraph
from prolothar_ca.ca.methods.custom.model.for_all_no_join import ForAll
from prolothar_ca.ca.methods.custom.model.custom_constraint import JoinTargetConstraint
from prolothar_ca.ca.methods.custom.sat_encoding import create_homgenous_sat_encoded_dataset

from prolothar_ca.ca.methods.custom.mdl_score import compute_encoded_data_length_from_known_solution
from prolothar_ca.ca.methods.custom.mdl_score import compute_encoded_data_length
from prolothar_ca.ca.dataset_generator.metaplanning import MetaplanningCaDatasetGenerator
from prolothar_ca.model.sat.cnf import CnfFormula
from prolothar_ca.model.sat.term_factory import TermFactory
from prolothar_ca.solver.sat.modelcount.mc2 import MC2

class TestMdlScoreHanoi(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dataset_generator = MetaplanningCaDatasetGenerator('prolothar_tests/resources/meta_planning/hanoi')
        cls.ca_dataset = cls.dataset_generator.generate(50, 0, random_seed=171022)
        cls.first_example = next(iter(cls.ca_dataset))
        cls.target_relation = cls.ca_dataset.get_relation_type(
            cls.dataset_generator.get_target().relation_name)
        cls.datagraph = DataGraph(cls.first_example, cls.ca_dataset, cls.target_relation)
        cls.sat_dataset = create_homgenous_sat_encoded_dataset(
            cls.ca_dataset,
            cls.target_relation,
            cls.datagraph)
        cls.sat_variables = cls.datagraph.get_target_variables()
        cls.model_counter = MC2(
            use_regular_graph_lower_bound=True,
            use_graph_lower_bound=True
        )

    @staticmethod
    def compute_model_cost(model: list[CustomConstraint]):
        return L_N(len(model) + 1) + sum(constraint.encoded_model_length for constraint in model)

    @staticmethod
    def compute_data_cost(model: CnfFormula):
        return compute_encoded_data_length_from_known_solution(
            model, TestMdlScoreHanoi.sat_dataset, TestMdlScoreHanoi.sat_variables,
            TestMdlScoreHanoi.model_counter, TestMdlScoreHanoi.sat_dataset[0])

    def test_ground_truth_should_produce_gain(self):
        empty_model = CnfFormula()
        model_cost_empty_model = TestMdlScoreHanoi.compute_model_cost([])
        self.assertTrue(empty_model.value)
        data_cost_of_empty_model = len(TestMdlScoreHanoi.sat_dataset) * len(TestMdlScoreHanoi.sat_variables)

        nr_of_objects = len(first(TestMdlScoreHanoi.first_example.all_objects_per_type.values()))
        smaller_relation = TestMdlScoreHanoi.ca_dataset.get_relation_type('smaller')
        ison_relation = TestMdlScoreHanoi.ca_dataset.get_relation_type('ison')

        ground_truth_constraint_incomplete = ForAll(
            OrCrossProductFilter([
                NotCrossProductFilter(BooleanFeature('clear', 2, 3, 2)),
                NotCrossProductFilter(BooleanRelation(ison_relation, (0, 1), 3, 2)),
                NotCrossProductFilter(BooleanRelation(smaller_relation, (2, 0), 3, 2))
            ]),
            JoinTargetConstraint(
                [], (0,1,2), False, (nr_of_objects, nr_of_objects, nr_of_objects)
            )
        )
        ca_ground_truth_constraint_incomplete = ground_truth_constraint_incomplete.to_ca_model(TestMdlScoreHanoi.datagraph)
        self.assertTrue(ca_ground_truth_constraint_incomplete.holds(TestMdlScoreHanoi.first_example, {}))
        self.assertEqual(1, ca_ground_truth_constraint_incomplete.compute_probability_that_constraint_holds(
                TestMdlScoreHanoi.ca_dataset))
        ground_truth_constraint_model_incomplete = CnfFormula(ground_truth_constraint_incomplete.compute_cnf_clauses(
            TestMdlScoreHanoi.datagraph, TermFactory()))
        model_cost_incomplete = TestMdlScoreHanoi.compute_model_cost([ground_truth_constraint_incomplete])
        data_cost_incomplete = TestMdlScoreHanoi.compute_data_cost(ground_truth_constraint_model_incomplete)
        self.assertGreater(model_cost_incomplete, model_cost_empty_model)
        self.assertLess(data_cost_incomplete, data_cost_of_empty_model)
        self.assertLess(
            model_cost_incomplete + data_cost_incomplete,
            model_cost_empty_model + data_cost_of_empty_model
        )

        ground_truth_constraint = ForAll(
            OrCrossProductFilter([
                NotCrossProductFilter(BooleanFeature('clear', 0, 3, 2)),
                NotCrossProductFilter(BooleanFeature('clear', 2, 3, 2)),
                NotCrossProductFilter(BooleanRelation(ison_relation, (0, 1), 3, 2)),
                NotCrossProductFilter(BooleanRelation(smaller_relation, (2, 0), 3, 2))
            ]),
            JoinTargetConstraint(
                [], (0,1,2), False, (nr_of_objects, nr_of_objects, nr_of_objects)
            )
        )
        ca_ground_truth_constraint = ground_truth_constraint.to_ca_model(TestMdlScoreHanoi.datagraph)
        self.assertTrue(ca_ground_truth_constraint.holds(TestMdlScoreHanoi.first_example, {}))
        self.assertEqual(1, ca_ground_truth_constraint.compute_probability_that_constraint_holds(
                TestMdlScoreHanoi.ca_dataset))
        ground_truth_constraint_model = CnfFormula(ground_truth_constraint.compute_cnf_clauses(
            TestMdlScoreHanoi.datagraph, TermFactory()))
        model_cost = TestMdlScoreHanoi.compute_model_cost([ground_truth_constraint])
        data_cost = TestMdlScoreHanoi.compute_data_cost(ground_truth_constraint_model)
        self.assertGreater(model_cost, model_cost_empty_model)
        self.assertLess(data_cost, data_cost_of_empty_model)
        self.assertGreater(model_cost, model_cost_incomplete)
        self.assertLess(data_cost, data_cost_incomplete)
        self.assertLess(
            model_cost + data_cost,
            model_cost_empty_model + data_cost_of_empty_model
        )
        self.assertLess(
            model_cost + data_cost,
            model_cost_incomplete + data_cost_incomplete
        )

if __name__ == '__main__':
    unittest.main()