'''
    This file is part of Prolothar-Constraint-Acquisition (More Info: https://github.com/shs-it/prolothar-constraint-acquisition).

    Prolothar-Constraint-Acquisition is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Prolothar-Constraint-Acquisition is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Prolothar-Constraint-Acquisition. If not, see <https://www.gnu.org/licenses/>.
'''

from abc import ABC, abstractmethod
from math import log2
from typing import Callable, Generator
from prolothar_common.mdl_utils import L_N, L_R, log2binom
from prolothar_ca.model.ca.constraints.conjunction import And, Or

from prolothar_ca.model.ca.constraints.constraint import CaConstraint
from prolothar_ca.model.ca.constraints.objects import ObjectsEqual, ObjectsNotEqual
from prolothar_ca.model.ca.constraints.boolean import BooleanFeatureIsTrue
from prolothar_ca.model.ca.constraints.boolean import BooleanFeatureIsFalse
from prolothar_ca.model.ca.constraints.boolean import RelationIsTrue
from prolothar_ca.model.ca.constraints.boolean import Not as CaNot
from prolothar_ca.model.ca.constraints.numeric import Equal, Greater, LessOrEqual, NumericExpression, Less
from prolothar_ca.model.ca.constraints.numeric import NumericFeature as CaNumericFeature
from prolothar_ca.model.ca.constraints.numeric import Difference as CaDifference
from prolothar_ca.model.ca.constraints.numeric import Sum as CaSum
from prolothar_ca.model.ca.constraints.numeric import Division as CaDivision
from prolothar_ca.model.ca.constraints.numeric import Constant as CaConstant
from prolothar_ca.model.ca.constraints.numeric import IntegerDivision as CaIntegerDivision
from prolothar_ca.model.ca.constraints.numeric import Absolute as CaAbsolute
from prolothar_ca.model.ca.relation import CaRelationType

from prolothar_ca.ca.methods.custom.model.datagraph_sql_constants import COLUMN_OBJECT_ID

class CrossProductFilter(ABC):

    def __init__(self, encoded_model_length: float):
        self.encoded_model_length = encoded_model_length + log2(3)

    @abstractmethod
    def yield_sql_where_clauses(self, variable_index_to_name: Callable[[int], str]) -> Generator[str, None, None]:
        """
        yields filter clauses in a sql query
        """

    @abstractmethod
    def yield_relation_join_sql_statements(self, variable_index_to_name: Callable[[int], str]) -> Generator[str, None, None]:
        """
        yields additional join clauses in a sql query
        """

    @abstractmethod
    def to_ca_model(
        self, target_relation: CaRelationType, additional_joins: tuple[int],
        variable_names: list[str], is_child: bool = False) -> CaConstraint:
        """
        converts this CrossProductFilter into an equivalent CaConstraint
        from the prolothar_ca.model.ca.constraint package

        Parameters
        ----------
        target_relation : CaRelationType
            the target concept of the constraint acquisition task for which
            this CrossProductFilter was created
        additional_joins : tuple[int]
            this tuple together with the target_relation defines the cross product on which
            this filter is applied. the tuple contains the indices of the parameter types
            of the target relation which are additionally joined with the parameter types of
            the target relation. example: let "(A,B,C)" be the types of the parameters
            of the target relation and additional_joins is "(0,2,2)". in this case,
            the cross product is "A x B x C x A x C x C"
        variable_names : list[str]
            assigns a variable name for each object set in the cross product

        Returns
        -------
        CaConstraint
            the equivalent CaConstraint
        """

    def _create_objects_not_equal_ca_terms(
            self, target_relation: CaRelationType, additional_joins: tuple[int],
            variable_names: list[str]) -> list[ObjectsNotEqual]:
        return [
            ObjectsNotEqual(
                variable_names[left_index],
                variable_names[right_index + len(target_relation.parameter_types)])
            for right_index, left_index in enumerate(additional_joins)
        ]

    def __eq__(self, other):
        return repr(self) == repr(other)

    def __hash__(self):
        return hash(repr(self))

class AndCrossProductFilter(CrossProductFilter):

    def __init__(self, terms: list[CrossProductFilter]):
        super().__init__(L_N(len(terms) - 1) + sum(t.encoded_model_length for t in terms))
        self.terms = terms

    def yield_sql_where_clauses(self, variable_index_to_name: Callable[[int], str]) -> Generator[str, None, None]:
        for term in self.terms:
            yield from term.yield_sql_where_clauses(variable_index_to_name)

    def yield_relation_join_sql_statements(self, variable_index_to_name: Callable[[int], str]) -> Generator[str, None, None]:
        for term in self.terms:
            yield from term.yield_relation_join_sql_statements(variable_index_to_name)

    def to_ca_model(
            self, target_relation: CaRelationType, additional_joins: tuple[int], variable_names: list[str],
            is_child: bool = False) -> CaConstraint:
        and_terms = [
            term.to_ca_model(target_relation, additional_joins, variable_names, is_child=True)
            for term in self.terms
        ]
        if not is_child:
            and_terms = self._create_objects_not_equal_ca_terms(
                target_relation, additional_joins, variable_names) + and_terms
            return And(and_terms)
        else:
            return And(and_terms)

    def __or__(self, other: CrossProductFilter) -> 'OrCrossProductFilter':
        if isinstance(other, OrCrossProductFilter):
            return OrCrossProductFilter(other.terms + [self])
        else:
            return OrCrossProductFilter([other, self])

    def __repr__(self):
        return f'({" & ".join(map(repr,self.terms))})'

class OrCrossProductFilter(CrossProductFilter):

    def __init__(self, terms: list[CrossProductFilter]):
        super().__init__(L_N(len(terms) - 1) + sum(t.encoded_model_length for t in terms))
        self.terms = terms

    def yield_sql_where_clauses(self, variable_index_to_name: Callable[[int], str]) -> Generator[str, None, None]:
        yield ''.join((
            '(',
            ' OR '.join(
                '(' + ' AND '.join(term.yield_sql_where_clauses(variable_index_to_name)) + ')'
                for term in self.terms
            ),
            ')'
        ))

    def yield_relation_join_sql_statements(self, variable_index_to_name: Callable[[int], str]) -> Generator[str, None, None]:
        for term in self.terms:
            yield from term.yield_relation_join_sql_statements(variable_index_to_name)

    def to_ca_model(
            self, target_relation: CaRelationType, additional_joins: tuple[int], variable_names: list[str],
            is_child: bool = False) -> CaConstraint:
        or_term = Or([
            term.to_ca_model(target_relation, additional_joins, variable_names, is_child=True)
            for term in self.terms
        ])
        if not is_child:
            condition_terms = self._create_objects_not_equal_ca_terms(
                target_relation, additional_joins, variable_names)
            condition_terms.append(or_term)
            return And(condition_terms)
        else:
            return or_term

    def __or__(self, other: CrossProductFilter) -> CrossProductFilter:
        if isinstance(other, OrCrossProductFilter):
            merged_terms = set(self.terms)
            merged_terms.update(other.terms)
            return OrCrossProductFilter(list(merged_terms))
        else:
            return OrCrossProductFilter(self.terms + [other])

    def __repr__(self):
        return f'({" | ".join(map(repr,self.terms))})'

class NotCrossProductFilter(CrossProductFilter):

    def __init__(self, term: CrossProductFilter):
        super().__init__(1 + term.encoded_model_length)
        self.term = term

    def yield_sql_where_clauses(self, variable_index_to_name: Callable[[int], str]) -> Generator[str, None, None]:
        yield f'NOT ({" AND ".join(self.term.yield_sql_where_clauses(variable_index_to_name))})'

    def yield_relation_join_sql_statements(self, variable_index_to_name: Callable[[int], str]) -> Generator[str, None, None]:
        yield from self.term.yield_relation_join_sql_statements(variable_index_to_name)

    def to_ca_model(
            self, target_relation: CaRelationType, additional_joins: tuple[int], variable_names: list[str],
            is_child: bool = False) -> CaConstraint:
        return CaNot(self.term.to_ca_model(target_relation, additional_joins, variable_names, is_child))

    def __and__(self, other: CrossProductFilter) -> AndCrossProductFilter:
        if isinstance(other, AndCrossProductFilter):
            return AndCrossProductFilter(other.terms + [self])
        else:
            return AndCrossProductFilter([self, other])

    def __or__(self, other: CrossProductFilter) -> CrossProductFilter:
        if isinstance(other, OrCrossProductFilter):
            return OrCrossProductFilter(other.terms + [self])
        elif self.term == other:
            return other
        else:
            return OrCrossProductFilter([self, other])

    def __repr__(self):
        return f'!{self.term}'

class NullCrossProductFilter(CrossProductFilter):

    def __init__(self):
        super().__init__(0)

    def to_ca_model(self, target_relation: CaRelationType, additional_joins: tuple[int], variable_names: list[str], is_child: bool=False) -> CaConstraint:
        condition_terms = self._create_objects_not_equal_ca_terms(target_relation, additional_joins, variable_names)
        if len(condition_terms) == 1:
            return condition_terms[0]
        else:
            return And(condition_terms)

    def yield_sql_where_clauses(self, variable_index_to_name: Callable[[int], str]) -> Generator[str, None, None]:
        yield from ()

    def yield_relation_join_sql_statements(self, variable_index_to_name: Callable[[int], str]) -> Generator[str, None, None]:
        yield from ()

    def __repr__(self):
        return 'NullFilter'

class ObjectEquality(CrossProductFilter):

    def __init__(self, first_parameter_index: int, second_parameter_index: int, nr_of_parameters: int):
        super().__init__(log2binom(nr_of_parameters, 2))
        self.first_parameter_index = first_parameter_index
        self.second_parameter_index = second_parameter_index

    def to_ca_model(
            self, target_relation: CaRelationType, additional_joins: tuple[int],
            variable_names: list[str], is_child: bool=False) -> CaConstraint:
        return ObjectsEqual(variable_names[self.first_parameter_index], variable_names[self.second_parameter_index])

    def yield_sql_where_clauses(self, variable_index_to_name: Callable[[int], str]) -> Generator[str, None, None]:
        yield (
            f'{variable_index_to_name(self.first_parameter_index)}.{COLUMN_OBJECT_ID} = '
            f'{variable_index_to_name(self.second_parameter_index)}.{COLUMN_OBJECT_ID}'
        )

    def yield_relation_join_sql_statements(self, variable_index_to_name: Callable[[int], str]) -> Generator[str, None, None]:
        yield from ()

    def __repr__(self):
        return f'{self.first_parameter_index} = {self.second_parameter_index}'

class NumericValue:

    def __init__(self, encoded_model_length: float):
        #constant or relation/feature
        self.encoded_model_length = encoded_model_length + 1

class RealConstant(NumericValue):

    def __init__(self, value: float):
        super().__init__(L_R(value))
        self.value = value

    def __repr__(self):
        return str(self.value)

    def to_sql(self, variable_index_to_name: Callable[[int], str]) -> str:
        return str(self.value)

    def to_ca_model(self, target_relation: CaRelationType, additional_joins: tuple[int], variable_names: list[str]) -> NumericExpression:
        return CaConstant(self.value)

class IntegerConstant(NumericValue):

    def __init__(self, value: int):
        super().__init__(L_N(value+1))
        self.value = value

    def __repr__(self):
        return str(self.value)

    def to_sql(self, variable_index_to_name: Callable[[int], str]) -> str:
        return str(self.value)

    def to_ca_model(self, target_relation: CaRelationType, additional_joins: tuple[int], variable_names: list[str]) -> NumericExpression:
        return CaConstant(self.value)

class Absolute(NumericValue):

    def __init__(self, value: NumericValue):
        super().__init__(value.encoded_model_length)
        self.value = value

    def __repr__(self):
        return f'|{self.value}|'

    def to_sql(self, variable_index_to_name: Callable[[int], str]) -> str:
        return f'abs({self.value.to_sql(variable_index_to_name)})'

    def to_ca_model(self, target_relation: CaRelationType, additional_joins: tuple[int], variable_names: list[str]) -> NumericExpression:
        return CaAbsolute(self.value.to_ca_model(target_relation, additional_joins, variable_names))

class NumericFeature(NumericValue):

    def __init__(self, feature_name: str, variable_index: int, cross_product_cardinality: int, nr_of_numeric_features: int):
        super().__init__(log2(cross_product_cardinality) + log2(nr_of_numeric_features))
        self.feature_name = feature_name
        self.variable_index = variable_index

    def __repr__(self):
        return f'{self.variable_index}.{self.feature_name}'

    def to_sql(self, variable_index_to_name: Callable[[int], str]) -> str:
        return f'{variable_index_to_name(self.variable_index)}.{self.feature_name}'

    def to_ca_model(self, target_relation: CaRelationType, additional_joins: tuple[int], variable_names: list[str]) -> NumericExpression:
        try:
            object_type = target_relation.parameter_types[self.variable_index]
        except IndexError:
            object_type = target_relation.parameter_types[additional_joins[self.variable_index - len(target_relation.parameter_types)]]
        return CaNumericFeature(object_type, variable_names[self.variable_index], self.feature_name)

class NumericOperation(NumericValue):

    def __init__(self, left_term: NumericValue, right_term: NumericValue, operator: str, ca_model_type):
        super().__init__(left_term.encoded_model_length + right_term.encoded_model_length)
        self.left_term = left_term
        self.right_term = right_term
        self.operator = operator
        self.ca_model_type = ca_model_type

    def __repr__(self):
        return f'{self.left_term} {self.operator} {self.right_term}'

    def to_sql(self, variable_index_to_name: Callable[[int], str]) -> str:
        return f'{self.left_term.to_sql(variable_index_to_name)} {self.operator} {self.right_term.to_sql(variable_index_to_name)}'

    def to_ca_model(self, target_relation: CaRelationType, additional_joins: tuple[int], variable_names: list[str]) -> NumericExpression:
        return self.ca_model_type(
            self.left_term.to_ca_model(target_relation, additional_joins, variable_names),
            self.right_term.to_ca_model(target_relation, additional_joins, variable_names)
        )

class Difference(NumericOperation):

    def __init__(self, left_term: NumericValue, right_term: NumericValue):
        super().__init__(left_term, right_term, '-', CaDifference)

class Sum(NumericOperation):

    def __init__(self, left_term: NumericValue, right_term: NumericValue):
        super().__init__(left_term, right_term, '+', CaSum)

class Quotient(NumericOperation):

    def __init__(self, left_term: NumericValue, right_term: NumericValue):
        super().__init__(left_term, right_term, '/', CaDivision)

class IntegerQuotient(NumericOperation):

    def __init__(self, left_term: NumericValue, right_term: NumericValue):
        super().__init__(left_term, right_term, '//', CaIntegerDivision)

    def to_sql(self, variable_index_to_name: Callable[[int], str]) -> str:
        return f'FLOOR({self.left_term.to_sql(variable_index_to_name)} / {self.right_term.to_sql(variable_index_to_name)})'


class NumericComparator:
    def __init__(self, sql_operator_char: str, ca_constructor):
        self.sql_operator_char = sql_operator_char
        self.ca_constructor = ca_constructor

    def __repr__(self):
        return self.sql_operator_char

class NumericFilter(CrossProductFilter):
    EQ = NumericComparator('=', Equal)
    LE = NumericComparator('<=', LessOrEqual)
    GT = NumericComparator('>', Greater)
    LT = NumericComparator('<', Less)

    def __init__(self, left_value: NumericValue, comperator: NumericComparator, right_value: NumericValue):
        super().__init__(left_value.encoded_model_length + log2(3) + right_value.encoded_model_length)
        self.left_value = left_value
        self.right_value = right_value
        self.comperator = comperator

    def __and__(self, other: CrossProductFilter) -> AndCrossProductFilter:
        if isinstance(other, AndCrossProductFilter):
            return AndCrossProductFilter(other.terms + [self])
        else:
            return AndCrossProductFilter([self, other])

    def __or__(self, other: CrossProductFilter) -> AndCrossProductFilter:
        if isinstance(other, OrCrossProductFilter):
            return OrCrossProductFilter(other.terms + [self])
        else:
            return OrCrossProductFilter([self, other])

    def __repr__(self):
        return f'{self.left_value} {self.comperator} {self.right_value}'

    def yield_sql_where_clauses(self, variable_index_to_name: Callable[[int], str]) -> Generator[str, None, None]:
        yield f'{self.left_value.to_sql(variable_index_to_name)} {self.comperator.sql_operator_char} {self.right_value.to_sql(variable_index_to_name)}'

    def yield_relation_join_sql_statements(self, variable_index_to_name: Callable[[int], str]) -> Generator[str, None, None]:
        yield from ()

    def to_ca_model(
            self, target_relation: CaRelationType, additional_joins: tuple[int],
            variable_names: list[str], is_child: bool = False) -> CaConstraint:
        ca_term = self.comperator.ca_constructor(
            self.left_value.to_ca_model(target_relation, additional_joins, variable_names),
            self.right_value.to_ca_model(target_relation, additional_joins, variable_names)
        )
        if is_child:
            return ca_term
        else:
            condition_terms = self._create_objects_not_equal_ca_terms(
                target_relation, additional_joins, variable_names)
            condition_terms.append(ca_term)
            return And(condition_terms)

class BooleanFeature(CrossProductFilter):

    def __init__(self, feature_name: str, variable_index: int, cross_product_cardinality: int, nr_of_boolean_features: int):
        super().__init__(log2(cross_product_cardinality) + log2(nr_of_boolean_features))
        self.feature_name = feature_name
        self.variable_index = variable_index

    def __repr__(self):
        return f'{self.variable_index}.{self.feature_name}'

    def yield_sql_where_clauses(self, variable_index_to_name: Callable[[int], str]) -> Generator[str, None, None]:
        yield f'{variable_index_to_name(self.variable_index)}.{self.feature_name} = 1'

    def yield_relation_join_sql_statements(self, variable_index_to_name: Callable[[int], str]) -> Generator[str, None, None]:
        yield from ()

    def __or__(self, other: CrossProductFilter) -> AndCrossProductFilter:
        if isinstance(other, OrCrossProductFilter):
            return OrCrossProductFilter(other.terms + [self])
        else:
            return OrCrossProductFilter([self, other])

    def to_ca_model(
            self, target_relation: CaRelationType, additional_joins: tuple[int],
            variable_names: list[str], is_child: bool = False) -> NumericExpression:
        try:
            object_type = target_relation.parameter_types[self.variable_index]
        except IndexError:
            object_type = target_relation.parameter_types[additional_joins[self.variable_index - len(target_relation.parameter_types)]]
        return BooleanFeatureIsTrue(object_type, variable_names[self.variable_index], self.feature_name)

class BooleanFeaturesNotEqual(CrossProductFilter):

    def __init__(
            self, first_feature_name: str, first_variable_index: int,
            second_feature_name: str, second_variable_index: int,
            cross_product_cardinality: int, nr_of_boolean_features: int):
        super().__init__(log2(cross_product_cardinality) + log2(nr_of_boolean_features))
        self.first_feature_name = first_feature_name
        self.first_variable_index = first_variable_index
        self.second_feature_name = second_feature_name
        self.second_variable_index = second_variable_index

    def __repr__(self):
        return f'{self.first_variable_index}.{self.first_feature_name} != {self.second_variable_index}.{self.second_feature_name}'

    def yield_sql_where_clauses(self, variable_index_to_name: Callable[[int], str]) -> Generator[str, None, None]:
        yield f'{variable_index_to_name(self.first_variable_index)}.{self.first_feature_name} != {variable_index_to_name(self.second_variable_index)}.{self.second_feature_name}'

    def yield_relation_join_sql_statements(self, variable_index_to_name: Callable[[int], str]) -> Generator[str, None, None]:
        yield from ()

    def __or__(self, other: CrossProductFilter) -> AndCrossProductFilter:
        if isinstance(other, OrCrossProductFilter):
            return OrCrossProductFilter(other.terms + [self])
        else:
            return OrCrossProductFilter([self, other])

    def to_ca_model(
            self, target_relation: CaRelationType, additional_joins: tuple[int],
            variable_names: list[str], is_child: bool = False) -> NumericExpression:
        try:
            object_type = target_relation.parameter_types[self.variable_index]
        except IndexError:
            object_type = target_relation.parameter_types[additional_joins[self.variable_index - len(target_relation.parameter_types)]]
        return Or([
            And([
                BooleanFeatureIsTrue(object_type, variable_names[self.first_variable_index], self.first_feature_name),
                BooleanFeatureIsFalse(object_type, variable_names[self.second_variable_index], self.second_feature_name)
            ]),
            And([
                BooleanFeatureIsFalse(object_type, variable_names[self.first_variable_index], self.first_feature_name),
                BooleanFeatureIsTrue(object_type, variable_names[self.second_variable_index], self.second_feature_name)
            ])
        ])

class BooleanRelation(CrossProductFilter):
    def __init__(self, relation_type: CaRelationType, variable_indices: tuple[int], cross_product_cardinality: int, nr_of_boolean_relations: int):
        super().__init__(
            log2(nr_of_boolean_relations) +
            log2binom(cross_product_cardinality, len(variable_indices))
        )
        self.relation_type = relation_type
        self.variable_indices = variable_indices
        self.__sql_table_alias = f'{self.relation_type.name}_' + '_'.join(str(i) for i in self.variable_indices)

    def __and__(self, other: CrossProductFilter) -> AndCrossProductFilter:
        if isinstance(other, AndCrossProductFilter):
            return AndCrossProductFilter(other.terms + [self])
        else:
            return AndCrossProductFilter([self, other])

    def __or__(self, other: CrossProductFilter) -> AndCrossProductFilter:
        if isinstance(other, OrCrossProductFilter):
            return OrCrossProductFilter(other.terms + [self])
        elif isinstance(other, NotCrossProductFilter) and self == other.term:
            return other
        else:
            return OrCrossProductFilter([self, other])

    def __repr__(self):
        return f'{self.relation_type.name}({self.variable_indices})'

    def yield_sql_where_clauses(self, variable_index_to_name: Callable[[int], str]) -> Generator[str, None, None]:
        yield f'{self.__sql_table_alias}.value = 1'

    def yield_relation_join_sql_statements(self, variable_index_to_name: Callable[[int], str]) -> Generator[str, None, None]:
        if self.variable_indices:
            join_criterion = ' AND '.join(
                f'{variable_index_to_name(j)}.object_id = {self.__sql_table_alias}.p{i}'
                for i,j in enumerate(self.variable_indices)
            )
            yield f'INNER JOIN {self.relation_type.name} AS {self.__sql_table_alias} ON {join_criterion}'
        else:
            yield f'INNER JOIN {self.relation_type.name} AS {self.__sql_table_alias}'

    def to_ca_model(
            self, target_relation: CaRelationType, additional_joins: tuple[int],
            variable_names: list[str], is_child: bool = False) -> CaConstraint:
        return RelationIsTrue(self.relation_type, tuple(variable_names[i] for i in self.variable_indices))
