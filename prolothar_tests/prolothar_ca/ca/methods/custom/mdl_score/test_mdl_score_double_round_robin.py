from prolothar_common.mdl_utils import L_N
from prolothar_ca.ca.methods.custom.model.cross_product_filter import AndCrossProductFilter, NumericFeature
from prolothar_ca.ca.methods.custom.model.cross_product_filter import NumericFilter, ObjectEquality, IntegerConstant
from prolothar_ca.ca.methods.custom.model.cross_product_filter import Absolute, Difference
import unittest
import sys
sys.setrecursionlimit(15000)

from prolothar_ca.ca.methods.custom.model.custom_constraint import CustomConstraint
from prolothar_ca.ca.methods.custom.model.custom_constraint import DataGraph
from prolothar_ca.ca.methods.custom.model.for_all_join_n import ForAllJoinN
from prolothar_ca.ca.methods.custom.model.for_all_join_all import ForAllJoinAll
from prolothar_ca.ca.methods.custom.model.custom_constraint import JoinTargetConstraint
from prolothar_ca.ca.methods.custom.sat_encoding import create_homgenous_sat_encoded_dataset

from prolothar_ca.ca.methods.custom.mdl_score import compute_encoded_data_length_from_known_solution
from prolothar_ca.ca.dataset_generator.double_round_robin import DoubleRoundRobinCaDatasetGenerator
from prolothar_ca.model.sat.cnf import CnfFormula
from prolothar_ca.model.sat.term_factory import TermFactory
from prolothar_ca.solver.sat.modelcount.mc2 import MC2
from prolothar_ca.solver.sat.modelcount.two_sat_first_moment_bound import TwoSatFirstMomentBound

class TestMdlScoreDoubleRoundRobin(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dataset_generator = DoubleRoundRobinCaDatasetGenerator(4)
        cls.ca_dataset = cls.dataset_generator.generate(10, 0, random_seed=171022)
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
            use_graph_lower_bound=True,
            counter_for_non_solution_dpll_branch=TwoSatFirstMomentBound())

    @staticmethod
    def compute_model_cost(model: list[CustomConstraint]):
        return L_N(len(model) + 1) + sum(constraint.encoded_model_length for constraint in model)

    @staticmethod
    def compute_data_cost(model: CnfFormula):
        return compute_encoded_data_length_from_known_solution(
            model, TestMdlScoreDoubleRoundRobin.sat_dataset, TestMdlScoreDoubleRoundRobin.sat_variables,
            TestMdlScoreDoubleRoundRobin.model_counter, TestMdlScoreDoubleRoundRobin.sat_dataset[0])

    def test_symmetry_constraint_should_produce_gain(self):
        empty_model = CnfFormula()
        model_cost_empty_model = TestMdlScoreDoubleRoundRobin.compute_model_cost([])
        self.assertTrue(empty_model.value)
        data_cost_of_empty_model = len(TestMdlScoreDoubleRoundRobin.sat_dataset) * len(TestMdlScoreDoubleRoundRobin.sat_variables)

        symmetry_constraint = ForAllJoinAll(
            AndCrossProductFilter([
                NumericFilter(
                    Absolute(Difference(
                        NumericFeature('nr', 0, 6, 1),
                        NumericFeature('nr', 3, 6, 1),
                    )),
                    NumericFilter.EQ,
                    IntegerConstant(3)
                ),
                ObjectEquality(1, 5, 6),
                ObjectEquality(2, 4, 6),
            ]),
            JoinTargetConstraint(
                [(0,1,2)], (3,4,5), True, (6, 4, 4)
            ),
            3
        )
        ca_symmtry_constraint = symmetry_constraint.to_ca_model(TestMdlScoreDoubleRoundRobin.datagraph)
        self.assertTrue(ca_symmtry_constraint.holds(TestMdlScoreDoubleRoundRobin.first_example, {}))
        self.assertEqual(1, ca_symmtry_constraint.compute_probability_that_constraint_holds(
                TestMdlScoreDoubleRoundRobin.ca_dataset))
        symmetry_constraint_model = CnfFormula(symmetry_constraint.compute_cnf_clauses(
            TestMdlScoreDoubleRoundRobin.datagraph, TermFactory()))
        model_cost_symmetry_constraint = TestMdlScoreDoubleRoundRobin.compute_model_cost([symmetry_constraint])
        data_cost_symmetry_constraint = TestMdlScoreDoubleRoundRobin.compute_data_cost(symmetry_constraint_model)
        self.assertGreater(model_cost_symmetry_constraint, model_cost_empty_model)
        self.assertLess(data_cost_symmetry_constraint, data_cost_of_empty_model)

if __name__ == '__main__':
    unittest.main()