import unittest

from prolothar_ca.ca.methods.custom.model.cross_product_filter import NumericFeature, NumericFilter
from prolothar_ca.ca.methods.custom.model.cross_product_filter import BooleanRelation
from prolothar_ca.ca.methods.custom.model.cross_product_filter import NotCrossProductFilter
from prolothar_ca.ca.methods.custom.model.custom_constraint import DataGraph
from prolothar_ca.ca.dataset_generator.metaplanning import MetaplanningCaDatasetGenerator
from prolothar_ca.ca.dataset_generator.n_queens import NQueensCaDatasetGenerator
from prolothar_ca.ca.methods.custom.model.custom_constraint import JoinTargetConstraint
from prolothar_ca.ca.methods.custom.model.for_all_no_join import ForAll
from prolothar_ca.ca.methods.custom.sat_encoding import create_sat_encoded_example
from prolothar_ca.ca.methods.custom.sat_encoding import create_heterogenous_sat_encoded_dataset
from prolothar_ca.model.sat.cnf import CnfFormula
from prolothar_ca.model.sat.term_factory import TermFactory
from prolothar_ca.model.sat.variable import Value

class TestCustomConstraint(unittest.TestCase):

    def test_query_variables_nqueens(self):
        dataset_generator = NQueensCaDatasetGenerator(8, include_queen_permutations=False)
        ca_dataset = dataset_generator.generate(1, 0, random_seed=22082022)
        target_relation = ca_dataset.get_relation_type(dataset_generator.get_target().relation_name)
        first_example = next(iter(ca_dataset))

        datagraph = DataGraph(first_example, ca_dataset, target_relation)
        clauses = datagraph.compute_cnf_clauses(
            JoinTargetConstraint([(0, 1)], (2, 3), False, (64, 8)), (0, 1),
            NumericFilter(
                NumericFeature('x', 1, 3, 2),
                NumericFilter.EQ,
                NumericFeature('x', 3, 3, 2)
            )
        )
        sat_encoded_example = create_sat_encoded_example(first_example, target_relation, datagraph)
        model = CnfFormula(clauses)
        for variable, value in sat_encoded_example.items():
            variable.value = value
        self.assertEqual(0, model.get_nr_of_untrue_clauses())
        self.assertEqual(0, model.get_nr_of_untrue_clauses_for_example(0))
        self.assertEqual(0, model.get_nr_of_untrue_clauses_for_example(0))
        self.assertEqual(([],[]), model.get_untrue_clauses())

    def test_constraint_in_hanoi(self):
        dataset_generator = MetaplanningCaDatasetGenerator(
            'prolothar_tests/resources/meta_planning/hanoi',
            filter_actions_with_duplicate_parameter=True
        )
        term_factory = TermFactory()
        ca_dataset = dataset_generator.generate(20, 0, random_seed=17082022)
        target_relation = ca_dataset.get_relation_type(dataset_generator.get_target().relation_name)
        ison_relation = ca_dataset.get_relation_type('ison')
        datagraph_list = [DataGraph(example, ca_dataset, target_relation) for example in ca_dataset]
        sat_encoded_dataset = create_heterogenous_sat_encoded_dataset(ca_dataset, target_relation, datagraph_list)
        ison_01_constraint = ForAll(
            NotCrossProductFilter(BooleanRelation(ison_relation, (0, 1), 3, 2)),
            JoinTargetConstraint([], (0,1,2), False, (8,8,8))
        )
        ison_01_cnf_list = [
            CnfFormula(ison_01_constraint.compute_cnf_clauses(datagraph, term_factory))
            for datagraph in datagraph_list
        ]
        ison_21_constraint = ForAll(
            NotCrossProductFilter(BooleanRelation(ison_relation, (2, 1), 3, 2)),
            JoinTargetConstraint([], (0,1,2), False, (8,8,8))
        )
        ison_21_cnf_list = [
            CnfFormula(ison_21_constraint.compute_cnf_clauses(datagraph, term_factory))
            for datagraph in datagraph_list
        ]
        for i,ison_01_cnf in enumerate(ison_01_cnf_list):
            for variable, value in sat_encoded_dataset[i].items():
                variable.value = value
            self.assertEqual(ison_01_cnf.value(), Value.TRUE)
        for i,ison_21_cnf in enumerate(ison_21_cnf_list):
            for variable, value in sat_encoded_dataset[i].items():
                variable.value = value
            self.assertEqual(ison_21_cnf.value(), Value.FALSE)
        i = 0
        for ison_01_cnf,ison_21_cnf in zip(ison_01_cnf_list, ison_21_cnf_list):
            for variable, value in sat_encoded_dataset[i].items():
                variable.value = value
            common_cnf = ison_01_cnf.extend(ison_21_cnf)
            self.assertEqual(common_cnf.value(), Value.FALSE)
            i += 1

if __name__ == '__main__':
    unittest.main()