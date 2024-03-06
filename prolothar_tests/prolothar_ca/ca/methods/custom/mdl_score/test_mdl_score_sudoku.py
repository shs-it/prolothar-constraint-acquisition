import unittest

from prolothar_common.mdl_utils import L_N
from prolothar_ca.ca.methods.custom.model.cross_product_filter import NullCrossProductFilter, NumericFeature, NumericFilter
from prolothar_ca.ca.methods.custom.model.cross_product_filter import AndCrossProductFilter, IntegerQuotient, IntegerConstant
from prolothar_ca.ca.methods.custom.model.custom_constraint import CustomConstraint
from prolothar_ca.ca.methods.custom.model.custom_constraint import DataGraph
from prolothar_ca.ca.methods.custom.model.custom_constraint import JoinTargetConstraint, SingleTargetConstraint
from prolothar_ca.ca.methods.custom.sat_encoding import create_homgenous_sat_encoded_dataset

from prolothar_ca.ca.methods.custom.mdl_score import compute_encoded_data_length
from prolothar_ca.ca.methods.custom.model.for_all_join_n import ForAllJoinN
from prolothar_ca.ca.methods.custom.model.custom_constraint import Count
from prolothar_ca.ca.methods.custom.model.custom_constraint import PartitionByTargetParameterFeaturesAreTrue
from prolothar_ca.ca.dataset_generator.sudoku import SudokuCaDatasetGenerator
from prolothar_ca.ca.dataset_generator.sudoku import CELL_TYPE_NAME
from prolothar_ca.ca.dataset_generator.sudoku import CELL_VALUE_TYPE_NAME
from prolothar_ca.model.sat.cnf import CnfFormula
from prolothar_ca.model.sat.term_factory import TermFactory
from prolothar_ca.model.ca.relation import CaRelation
from prolothar_ca.solver.sat.modelcount.mc2 import MC2

class TestMdlScoreSudoku(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dataset_generator = SudokuCaDatasetGenerator(size=4)
        cls.ca_dataset = cls.dataset_generator.generate(100, 0, random_seed=171022)
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
            ignore_non_solution_dpll_branch=True)

    @staticmethod
    def compute_model_cost(model: list[CustomConstraint]):
        return L_N(len(model) + 1) + sum(constraint.encoded_model_length for constraint in model)

    @staticmethod
    def compute_data_cost(model: CnfFormula):
        return compute_encoded_data_length(
            model, TestMdlScoreSudoku.sat_dataset, TestMdlScoreSudoku.sat_variables,
            TestMdlScoreSudoku.model_counter)

    def test_compute_mdl_score(self):
        empty_model = CnfFormula()
        model_cost_empty_model = TestMdlScoreSudoku.compute_model_cost([])
        self.assertTrue(empty_model.value())
        data_cost_of_empty_model = TestMdlScoreSudoku.compute_data_cost(empty_model)
        self.assertGreaterEqual(data_cost_of_empty_model, len(TestMdlScoreSudoku.sat_dataset) * len(TestMdlScoreSudoku.sat_variables))

        one_value_per_cell_constraint = ForAllJoinN(
            1, 1, NullCrossProductFilter(),
            JoinTargetConstraint([(0, 1)], (0, 2), False, (16, 4)), 3)

        model_one_value_per_cell_constraint = CnfFormula(one_value_per_cell_constraint.compute_cnf_clauses(
            TestMdlScoreSudoku.datagraph, TermFactory()))
        model_count_one_value_per_cell_constraint = TestMdlScoreSudoku.model_counter.count(model_one_value_per_cell_constraint)
        model_cost_one_value_per_cell_constraint = TestMdlScoreSudoku.compute_model_cost([one_value_per_cell_constraint])
        self.assertGreater(model_cost_one_value_per_cell_constraint, model_cost_empty_model)
        data_cost_one_value_per_cell_constraint = TestMdlScoreSudoku.compute_data_cost(model_one_value_per_cell_constraint)
        self.assertLess(data_cost_one_value_per_cell_constraint, data_cost_of_empty_model)

        row_constraint = ForAllJoinN(
            0, 1, NumericFilter(NumericFeature('x', 0, 3, 2), NumericFilter.EQ, NumericFeature('x', 2, 3, 2)),
            JoinTargetConstraint([(0, 1)], (2, 1), False, (16, 4)), 3)
        model_row_constraint = CnfFormula(row_constraint.compute_cnf_clauses(
            TestMdlScoreSudoku.datagraph, TermFactory()))
        model_cost_row_constraint = TestMdlScoreSudoku.compute_model_cost([row_constraint])
        self.assertGreater(model_cost_row_constraint, model_cost_empty_model)
        data_cost_row_constraint = TestMdlScoreSudoku.compute_data_cost(model_row_constraint)
        self.assertLess(data_cost_row_constraint, data_cost_of_empty_model)

        model_combined = model_row_constraint.extend(model_one_value_per_cell_constraint)
        self.assertNotEqual(model_combined, model_row_constraint)
        self.assertGreater(model_combined.get_nr_of_clauses(), model_row_constraint.get_nr_of_clauses())
        model_cost_combined = TestMdlScoreSudoku.compute_model_cost([row_constraint, one_value_per_cell_constraint])
        self.assertTrue(row_constraint.to_ca_model(TestMdlScoreSudoku.datagraph).holds(TestMdlScoreSudoku.first_example, {}))
        self.assertTrue(one_value_per_cell_constraint.to_ca_model(TestMdlScoreSudoku.datagraph).holds(TestMdlScoreSudoku.first_example, {}))
        for variable, value in TestMdlScoreSudoku.sat_dataset[0].items():
            variable.value = value
        self.assertTrue(model_combined.value())
        self.assertEqual(2, min(len(clause) for clause in model_combined.iter_clauses()))
        self.assertEqual(2, max(len(clause) for clause in model_combined.iter_clauses()))
        data_cost_combined = TestMdlScoreSudoku.compute_data_cost(model_combined)
        self.assertGreater(model_cost_combined, model_cost_row_constraint)
        self.assertLess(data_cost_combined, data_cost_of_empty_model)
        model_count_combined = TestMdlScoreSudoku.model_counter.count(model_combined)
        self.assertLess(model_count_combined, model_count_one_value_per_cell_constraint)
        self.assertLess(data_cost_combined, data_cost_one_value_per_cell_constraint)
        self.assertLess(data_cost_combined, data_cost_row_constraint)
        self.assertGreater(data_cost_combined, 0)
        self.assertLess(
            data_cost_combined + model_cost_combined,
            data_cost_row_constraint + model_cost_row_constraint
        )

        column_constraint = ForAllJoinN(
            0, 1, NumericFilter(NumericFeature('y', 0, 3, 2), NumericFilter.EQ, NumericFeature('y', 2, 3, 2)),
            JoinTargetConstraint([(0, 1)], (2, 1), False, (16, 4)), 3)
        model_combined_plus = model_combined.extend(
            CnfFormula(column_constraint.compute_cnf_clauses(
                TestMdlScoreSudoku.datagraph, TermFactory())))
        self.assertGreater(model_combined_plus.get_nr_of_clauses(), model_combined.get_nr_of_clauses())
        model_cost_combined_plus = TestMdlScoreSudoku.compute_model_cost([
            row_constraint, column_constraint, one_value_per_cell_constraint])
        data_cost_combined_plus = TestMdlScoreSudoku.compute_data_cost(model_combined_plus)
        self.assertGreater(model_cost_combined_plus, model_cost_combined)
        self.assertLess(data_cost_combined_plus, data_cost_combined)
        self.assertGreater(data_cost_combined_plus, 0)
        self.assertLess(
            data_cost_combined_plus + model_cost_combined_plus,
            data_cost_combined + model_cost_combined
        )

        single_block_constraint = SingleTargetConstraint(
            [TestMdlScoreSudoku.datagraph.get_target_variable(
                CaRelation(
                    TestMdlScoreSudoku.target_relation.name,
                    (
                        TestMdlScoreSudoku.first_example.get_object_by_type_and_id(
                            CELL_TYPE_NAME, 'cell_0_0'
                        ),
                        TestMdlScoreSudoku.first_example.get_object_by_type_and_id(
                            CELL_VALUE_TYPE_NAME, '1'
                        ),
                    ),
                    True
                )
            ).nr],
            TestMdlScoreSudoku.datagraph.get_target_variable(
                CaRelation(
                    TestMdlScoreSudoku.target_relation.name,
                    (
                        TestMdlScoreSudoku.first_example.get_object_by_type_and_id(
                            CELL_TYPE_NAME, 'cell_1_1'
                        ),
                        TestMdlScoreSudoku.first_example.get_object_by_type_and_id(
                            CELL_VALUE_TYPE_NAME, '1'
                        ),
                    ),
                    True
                )
            ).nr,
            False, TestMdlScoreSudoku.datagraph.get_nr_of_target_variables()
        )
        model_combined_plus_plus = model_combined_plus.extend(
            CnfFormula(single_block_constraint.compute_cnf_clauses(
                TestMdlScoreSudoku.datagraph, TermFactory())))
        self.assertGreater(model_combined_plus_plus.get_nr_of_clauses(), model_combined_plus.get_nr_of_clauses())
        model_cost_combined_plus_plus = TestMdlScoreSudoku.compute_model_cost([
            single_block_constraint, row_constraint, column_constraint, one_value_per_cell_constraint])
        data_cost_combined_plus_plus = TestMdlScoreSudoku.compute_data_cost(model_combined_plus_plus)
        self.assertGreater(model_cost_combined_plus_plus, model_cost_combined_plus)
        self.assertGreater(data_cost_combined_plus_plus, 0)

        block_constraint = ForAllJoinN(
            0, 1,
            AndCrossProductFilter([
                NumericFilter(
                    IntegerQuotient(NumericFeature('x', 0, 3, 2), IntegerConstant(2)),
                    NumericFilter.EQ,
                    IntegerQuotient(NumericFeature('x', 2, 3, 2), IntegerConstant(2))
                ),
                NumericFilter(
                    IntegerQuotient(NumericFeature('y', 0, 3, 2), IntegerConstant(2)),
                    NumericFilter.EQ,
                    IntegerQuotient(NumericFeature('y', 2, 3, 2), IntegerConstant(2))
                )
            ]),
            JoinTargetConstraint([(0, 1)], (2, 1), False, (16, 4)), 3
        )
        model_complete = model_combined_plus.extend(
            CnfFormula(block_constraint.compute_cnf_clauses(
                TestMdlScoreSudoku.datagraph, TermFactory())))
        self.assertGreater(model_complete.get_nr_of_clauses(), model_combined_plus_plus.get_nr_of_clauses())
        model_cost_complete = TestMdlScoreSudoku.compute_model_cost([
            block_constraint.merge(row_constraint.merge(column_constraint)), one_value_per_cell_constraint])
        print(block_constraint.merge(row_constraint.merge(column_constraint)))
        data_cost_complete = TestMdlScoreSudoku.compute_data_cost(model_complete)
        self.assertGreater(model_cost_complete, model_cost_combined_plus)
        self.assertLess(data_cost_complete, data_cost_combined_plus)
        self.assertGreater(data_cost_complete, 0)
        self.assertLess(
            data_cost_complete + model_cost_complete,
            data_cost_combined_plus + model_cost_combined_plus
        )

        model_with_redundant_constraint = model_complete.extend(
            CnfFormula(block_constraint.compute_cnf_clauses(
                TestMdlScoreSudoku.datagraph, TermFactory()))
        )
        self.assertEqual(model_complete.get_nr_of_clauses(), model_with_redundant_constraint.get_nr_of_clauses())

    def test_compute_mdl_score_false_single_constraint(self):
        empty_model = CnfFormula()
        model_cost_empty_model = TestMdlScoreSudoku.compute_model_cost([])
        data_cost_of_empty_model = TestMdlScoreSudoku.compute_data_cost(empty_model)
        total_cost_of_empty_model = model_cost_empty_model + data_cost_of_empty_model

        false_constraint = SingleTargetConstraint(
            [TestMdlScoreSudoku.datagraph.get_target_variable(
                CaRelation(
                    TestMdlScoreSudoku.target_relation.name,
                    (
                        TestMdlScoreSudoku.first_example.get_object_by_type_and_id(
                            CELL_TYPE_NAME, 'cell_0_0'
                        ),
                        TestMdlScoreSudoku.first_example.get_object_by_type_and_id(
                            CELL_VALUE_TYPE_NAME, '1'
                        ),
                    ),
                    True
                )
            ).nr],
            TestMdlScoreSudoku.datagraph.get_target_variable(
                CaRelation(
                    TestMdlScoreSudoku.target_relation.name,
                    (
                        TestMdlScoreSudoku.first_example.get_object_by_type_and_id(
                            CELL_TYPE_NAME, 'cell_0_0'
                        ),
                        TestMdlScoreSudoku.first_example.get_object_by_type_and_id(
                            CELL_VALUE_TYPE_NAME, '2'
                        ),
                    ),
                    True
                )
            ).nr,
            True, TestMdlScoreSudoku.datagraph.get_nr_of_target_variables()
        )
        false_constraint_model = CnfFormula(false_constraint.compute_cnf_clauses(
            TestMdlScoreSudoku.datagraph, TermFactory()))
        model_cost_false_model = TestMdlScoreSudoku.compute_model_cost([false_constraint])
        data_cost_of_false_model = TestMdlScoreSudoku.compute_data_cost(false_constraint_model)
        total_cost_of_false_model = model_cost_false_model + data_cost_of_false_model
        self.assertGreater(model_cost_false_model, model_cost_empty_model)
        self.assertGreaterEqual(total_cost_of_false_model, total_cost_of_empty_model)

        true_constraint = SingleTargetConstraint(
            [TestMdlScoreSudoku.datagraph.get_target_variable(
                CaRelation(
                    TestMdlScoreSudoku.target_relation.name,
                    (
                        TestMdlScoreSudoku.first_example.get_object_by_type_and_id(
                            CELL_TYPE_NAME, 'cell_0_0'
                        ),
                        TestMdlScoreSudoku.first_example.get_object_by_type_and_id(
                            CELL_VALUE_TYPE_NAME, '1'
                        ),
                    ),
                    True
                )
            ).nr],
            TestMdlScoreSudoku.datagraph.get_target_variable(
                CaRelation(
                    TestMdlScoreSudoku.target_relation.name,
                    (
                        TestMdlScoreSudoku.first_example.get_object_by_type_and_id(
                            CELL_TYPE_NAME, 'cell_0_0'
                        ),
                        TestMdlScoreSudoku.first_example.get_object_by_type_and_id(
                            CELL_VALUE_TYPE_NAME, '2'
                        ),
                    ),
                    True
                )
            ).nr,
            False, TestMdlScoreSudoku.datagraph.get_nr_of_target_variables()
        )
        true_constraint_model = CnfFormula(true_constraint.compute_cnf_clauses(
            TestMdlScoreSudoku.datagraph, TermFactory()))
        model_cost_true_model = TestMdlScoreSudoku.compute_model_cost([true_constraint])
        data_cost_of_true_model = TestMdlScoreSudoku.compute_data_cost(true_constraint_model)
        self.assertGreater(model_cost_true_model, model_cost_empty_model)
        self.assertLess(data_cost_of_true_model, data_cost_of_empty_model)

        false_constraint = SingleTargetConstraint(
            [TestMdlScoreSudoku.datagraph.get_target_variable(
                CaRelation(
                    TestMdlScoreSudoku.target_relation.name,
                    (
                        TestMdlScoreSudoku.first_example.get_object_by_type_and_id(
                            CELL_TYPE_NAME, 'cell_0_0'
                        ),
                        TestMdlScoreSudoku.first_example.get_object_by_type_and_id(
                            CELL_VALUE_TYPE_NAME, '1'
                        ),
                    ),
                    True
                )
            ).nr],
            TestMdlScoreSudoku.datagraph.get_target_variable(
                CaRelation(
                    TestMdlScoreSudoku.target_relation.name,
                    (
                        TestMdlScoreSudoku.first_example.get_object_by_type_and_id(
                            CELL_TYPE_NAME, 'cell_3_3'
                        ),
                        TestMdlScoreSudoku.first_example.get_object_by_type_and_id(
                            CELL_VALUE_TYPE_NAME, '2'
                        ),
                    ),
                    True
                )
            ).nr,
            True, TestMdlScoreSudoku.datagraph.get_nr_of_target_variables()
        )
        false_constraint_model = CnfFormula(false_constraint.compute_cnf_clauses(
            TestMdlScoreSudoku.datagraph, TermFactory()))
        model_cost_false_model = TestMdlScoreSudoku.compute_model_cost([false_constraint])
        data_cost_of_false_model = TestMdlScoreSudoku.compute_data_cost(false_constraint_model)
        total_cost_of_false_model = model_cost_false_model + data_cost_of_false_model
        self.assertGreater(model_cost_false_model, model_cost_empty_model)
        self.assertGreaterEqual(data_cost_of_false_model, data_cost_of_empty_model)
        self.assertGreaterEqual(total_cost_of_false_model, total_cost_of_empty_model)

    def test_compute_mdl_score_count_constraint(self):
        empty_model = CnfFormula()
        model_cost_empty_model = TestMdlScoreSudoku.compute_model_cost([])
        data_cost_of_empty_model = TestMdlScoreSudoku.compute_data_cost(empty_model)
        total_cost_of_empty_model = model_cost_empty_model + data_cost_of_empty_model

        false_constraint = Count(
            PartitionByTargetParameterFeaturesAreTrue(1, 2, [], 1),
            14, 16, TestMdlScoreSudoku.datagraph.get_nr_of_target_variables(), {}
        )
        false_constraint_model = CnfFormula(false_constraint.compute_cnf_clauses(
            TestMdlScoreSudoku.datagraph, TermFactory()))
        model_cost_false_model = TestMdlScoreSudoku.compute_model_cost([false_constraint])
        data_cost_of_false_model = TestMdlScoreSudoku.compute_data_cost(false_constraint_model)
        total_cost_of_false_model = model_cost_false_model + data_cost_of_false_model
        self.assertFalse(false_constraint.to_ca_model(TestMdlScoreSudoku.datagraph).holds(TestMdlScoreSudoku.first_example, {}))
        self.assertGreater(false_constraint_model.get_nr_of_untrue_clauses(), 0)
        self.assertGreater(len(list(false_constraint_model.iter_clauses())), 0)
        self.assertGreater(model_cost_false_model, model_cost_empty_model)
        self.assertGreaterEqual(total_cost_of_false_model, total_cost_of_empty_model)

        true_constraint = Count(
            PartitionByTargetParameterFeaturesAreTrue(1, 2, [], 1),
            4, 4, TestMdlScoreSudoku.datagraph.get_nr_of_target_variables(), {}
        )
        true_constraint_model = CnfFormula(true_constraint.compute_cnf_clauses(
            TestMdlScoreSudoku.datagraph, TermFactory()))
        model_cost_true_model = TestMdlScoreSudoku.compute_model_cost([true_constraint])
        self.assertEqual(true_constraint_model.get_nr_of_untrue_clauses(), 0)
        data_cost_of_true_model = TestMdlScoreSudoku.compute_data_cost(true_constraint_model)
        total_cost_of_true_model = model_cost_true_model + data_cost_of_true_model
        self.assertTrue(true_constraint.to_ca_model(TestMdlScoreSudoku.datagraph).holds(TestMdlScoreSudoku.first_example, {}))
        self.assertGreater(len(list(true_constraint_model.iter_clauses())), 0)
        self.assertGreater(model_cost_true_model, model_cost_empty_model)
        self.assertLess(total_cost_of_true_model, total_cost_of_empty_model)

if __name__ == '__main__':
    unittest.main()