import unittest
import sys
sys.setrecursionlimit(15000)
from prolothar_common.mdl_utils import L_N
from prolothar_ca.ca.methods.custom.model.cross_product_filter import NullCrossProductFilter, NumericFeature, NumericFilter, Difference

from prolothar_ca.ca.methods.custom.model.custom_constraint import CustomConstraint
from prolothar_ca.ca.methods.custom.model.custom_constraint import DataGraph
from prolothar_ca.ca.methods.custom.model.for_all_join_n import ForAllJoinN
from prolothar_ca.ca.methods.custom.model.for_all_join_all import ForAllJoinAll
from prolothar_ca.ca.methods.custom.model.custom_constraint import JoinTargetConstraint
from prolothar_ca.ca.methods.custom.sat_encoding import create_homgenous_sat_encoded_dataset

from prolothar_ca.ca.methods.custom.mdl_score import compute_encoded_data_length_from_known_solution
from prolothar_ca.ca.dataset_generator.n_queens import NQueensCaDatasetGenerator
from prolothar_ca.model.sat.cnf import CnfFormula
from prolothar_ca.model.sat.term_factory import TermFactory
from prolothar_ca.solver.sat.modelcount.mc2 import MC2
from prolothar_ca.solver.sat.modelcount.two_sat_first_moment_bound import TwoSatFirstMomentBound

class TestMdlScoreNQueens(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('A')
        cls.dataset_generator = NQueensCaDatasetGenerator(8)
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
            ignore_non_solution_dpll_branch=True,
            use_graph_lower_bound=True,
            counter_for_non_solution_dpll_branch=TwoSatFirstMomentBound())

    @staticmethod
    def compute_model_cost(model: list[CustomConstraint]):
        return L_N(len(model) + 1) + sum(constraint.encoded_model_length for constraint in model)

    @staticmethod
    def compute_data_cost(model: CnfFormula):
        return compute_encoded_data_length_from_known_solution(
            model, TestMdlScoreNQueens.sat_dataset, TestMdlScoreNQueens.sat_variables,
            TestMdlScoreNQueens.model_counter, TestMdlScoreNQueens.sat_dataset[0])

    def test_compute_mdl_score(self):
        empty_model = CnfFormula()
        model_cost_empty_model = TestMdlScoreNQueens.compute_model_cost([])
        self.assertTrue(empty_model.value)
        data_cost_of_empty_model = len(TestMdlScoreNQueens.sat_dataset) * len(TestMdlScoreNQueens.sat_variables)

        queen_on_one_square_constraint = ForAllJoinN(
            1, 1, NullCrossProductFilter(),
            JoinTargetConstraint([(0,1)], (0,2), False, (8, 64)), 2
        )
        self.assertEqual(1, queen_on_one_square_constraint.to_ca_model(
            TestMdlScoreNQueens.datagraph).compute_probability_that_constraint_holds(
                TestMdlScoreNQueens.ca_dataset))
        queen_on_one_square_model = CnfFormula(queen_on_one_square_constraint.compute_cnf_clauses(
            TestMdlScoreNQueens.datagraph, TermFactory()))
        data_cost_queen_on_one_square_model = TestMdlScoreNQueens.compute_data_cost(queen_on_one_square_model)
        self.assertLess(data_cost_queen_on_one_square_model, data_cost_of_empty_model)

        row_constraint = ForAllJoinAll(
            NumericFilter(NumericFeature('x', 1, 4, 2), NumericFilter.EQ, NumericFeature('x', 3, 4, 2)),
            JoinTargetConstraint([(0,1)],(2,3), False, (8, 64)), 2
        )
        print(row_constraint.to_ca_model(TestMdlScoreNQueens.datagraph))
        model_row_constraint = CnfFormula(row_constraint.compute_cnf_clauses(
            TestMdlScoreNQueens.datagraph, TermFactory()))
        model_cost_row_constraint = TestMdlScoreNQueens.compute_model_cost([row_constraint])
        self.assertGreater(model_cost_row_constraint, model_cost_empty_model)
        data_cost_row_constraint = TestMdlScoreNQueens.compute_data_cost(model_row_constraint)
        self.assertLess(data_cost_row_constraint, data_cost_of_empty_model)

        column_constraint = ForAllJoinAll(
            NumericFilter(NumericFeature('y', 1, 4, 2), NumericFilter.EQ, NumericFeature('y', 3, 4, 2)),
            JoinTargetConstraint([(0,1)],(2,3), False, (8, 64)), 2
        )
        model_column_constraint = CnfFormula(column_constraint.compute_cnf_clauses(
            TestMdlScoreNQueens.datagraph, TermFactory()))
        model_cost_column_constraint = TestMdlScoreNQueens.compute_model_cost([column_constraint])
        self.assertEqual(model_cost_row_constraint, model_cost_column_constraint)
        data_cost_column_constraint = TestMdlScoreNQueens.compute_data_cost(model_column_constraint)
        self.assertLess(data_cost_column_constraint, data_cost_of_empty_model)

        model_row_and_column_constraint = model_row_constraint.extend(model_column_constraint)
        model_cost_row_and_column_constraint = TestMdlScoreNQueens.compute_model_cost([row_constraint, column_constraint])
        data_cost_row_and_column_constraint = TestMdlScoreNQueens.compute_data_cost(model_row_and_column_constraint)
        model_count_row_and_column_constraint = TestMdlScoreNQueens.model_counter.count(model_row_and_column_constraint)
        self.assertGreater(model_cost_row_and_column_constraint, model_cost_row_constraint)
        self.assertLess(data_cost_row_and_column_constraint, data_cost_of_empty_model)
        self.assertLess(data_cost_row_and_column_constraint, data_cost_column_constraint)
        self.assertLess(data_cost_row_and_column_constraint, data_cost_row_constraint)
        self.assertLess(
            data_cost_row_and_column_constraint + model_cost_row_and_column_constraint,
            data_cost_row_constraint + model_cost_row_constraint
        )

        half_diagonal_constraint = ForAllJoinAll(
            NumericFilter(
                Difference(
                    NumericFeature('x', 1, 4, 2),
                    NumericFeature('y', 1, 4, 2),
                ),
                NumericFilter.EQ,
                Difference(
                    NumericFeature('x', 3, 4, 2),
                    NumericFeature('y', 3, 4, 2)
                )
            ),
            JoinTargetConstraint([(0,1)],(2,3), False, (8, 64)), 2
        )
        model_half_diagonal_constraint = CnfFormula(half_diagonal_constraint.compute_cnf_clauses(
            TestMdlScoreNQueens.datagraph, TermFactory()))
        model_with_half_diagonal_constraint = model_row_and_column_constraint.extend(model_half_diagonal_constraint)
        model_count_with_half_diagonal_constraint = TestMdlScoreNQueens.model_counter.count(model_with_half_diagonal_constraint)
        model_cost_with_half_diagonal_constraint = TestMdlScoreNQueens.compute_model_cost([row_constraint, column_constraint, half_diagonal_constraint])
        data_cost_with_half_diagonal_constraint = TestMdlScoreNQueens.compute_data_cost(model_with_half_diagonal_constraint)
        self.assertGreater(model_cost_with_half_diagonal_constraint, model_cost_row_and_column_constraint)
        self.assertLess(model_count_with_half_diagonal_constraint, model_count_row_and_column_constraint)
        self.assertLess(data_cost_with_half_diagonal_constraint, data_cost_of_empty_model)
        self.assertLess(data_cost_with_half_diagonal_constraint, data_cost_column_constraint)
        self.assertLess(data_cost_with_half_diagonal_constraint, data_cost_row_and_column_constraint)
        self.assertLess(
            data_cost_with_half_diagonal_constraint + model_cost_with_half_diagonal_constraint,
            data_cost_row_and_column_constraint + model_cost_row_and_column_constraint
        )

if __name__ == '__main__':
    unittest.main()