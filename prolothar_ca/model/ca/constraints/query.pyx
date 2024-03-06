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

from typing import Dict, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from itertools import product

cdef class Query:
    cpdef list evaluate(self, CaExample example, dict variables):
        """
        evaluates the query and returns all entities that match this query.
        returns a list of QueryResultElement
        """
        raise NotImplementedError()

    cpdef int count_nr_of_terms(self):
        """
        counts the number of terms in the query. the more terms the more complex
        the query.
        """
        raise NotImplementedError()

cdef class EvaluateOnceQueryWrapper(Query):
    """
    wraps a query. at first evaluation, the wrapped query is evaluated and the
    result list is cached. every subsequent call of evaluate with the same example
     leads to the same cached result. this can give
    a tremendous speed up if the same query (e.g. a cross product) can be
    reused multiple time.
    only use this class if you know what you are doing!
    """
    cdef public Query query
    cdef list result_list
    cdef evaluated_example
    cdef str __str

    def __init__(self, Query query):
        self.query = query
        self.__str = str(query)

    cpdef list evaluate(self, example: CaExample, dict variables: Dict[str, CaObject]):
        if self.result_list is None:
            self.result_list = self.query.evaluate(example, variables)
            self.evaluated_example = example
            return self.result_list
        elif self.evaluated_example is not example:
            return self.query.evaluate(example, variables)
        else:
            return self.result_list

    def __str__(self):
        return self.__str

    def __eq__(self, other):
        return (
            isinstance(other, EvaluateOnceQueryWrapper) and self.query == other.query
        ) or self.query == other

    cpdef int count_nr_of_terms(self):
        return self.query.count_nr_of_terms()

cdef class AllOfType(Query):
    cdef str type_name
    cdef str variable_name

    def __init__(self, str type_name, str variable_name):
        self.type_name = type_name
        self.variable_name = variable_name

    cpdef list evaluate(self, CaExample example, dict variables: Dict[str, CaObject]):
        return [{self.variable_name: o} for o in example.all_objects_per_type[self.type_name]]

    def __str__(self):
        return f'{self.variable_name} in {self.type_name}'

    cpdef int count_nr_of_terms(self):
        return 2

cdef class DistinctValuesOfFeatureQuery(Query):
    cdef str object_type
    cdef str feature_name
    cdef str variable_name

    def __init__(self, str object_type, str feature_name, str variable_name):
        self.object_type = object_type
        self.feature_name = feature_name
        self.variable_name = variable_name

    cpdef list evaluate(self, example: CaExample, dict variables: Dict[str, CaObject]):
        cdef set distinct_feature_values = set()
        for o in example.all_objects_per_type[self.object_type]:
            distinct_feature_values.add(o.features[self.feature_name])
        return [
            {self.variable_name: feature_value} for feature_value in distinct_feature_values
        ]

    def __str__(self) -> str:
        return f'{self.variable_name} in distinct({self.object_type}.{self.feature_name})'

    cpdef int count_nr_of_terms(self):
        return 2

cdef class AllOfTypeOrderBy(Query):

    def __init__(self, str type_name, str variable_name, by):
        self.type_name = type_name
        self.variable_name = variable_name
        self.by = by
        if isinstance(self.by, str):
            self.__sort_function = self.__sort_by_str
        else:
            self.__sort_function = self.__sort_by_list

    def __sort_by_str(self, result):
        return result[self.variable_name].features[self.by]

    def __sort_by_list(self, result):
        return tuple(result[self.variable_name].features[b] for b in self.by)

    cpdef list evaluate(self, CaExample example, dict variables):
        result_list = AllOfType(self.type_name, self.variable_name).evaluate(example, variables)
        result_list.sort(key=self.__sort_function)
        return result_list

    def __hash__(self):
        return hash(str(self))

    def __str__(self) -> str:
        return f'{self.variable_name} in {self.type_name} order by {self.by}'

    cpdef int count_nr_of_terms(self):
        if isinstance(self.by, str):
            return 3
        else:
            return len(self.by) + 2

cdef class Product(Query):
    # subquery_list: list[Query]
    cdef public list subquery_list

    def __init__(self, list subquery_list):
        self.subquery_list = subquery_list

    cpdef list evaluate(self, example: CaExample, dict variables: Dict[str, CaObject]):
        cdef list result_list = []
        cdef tuple product_element
        cdef dict result
        for product_element in product(*[
            subquery.evaluate(example, variables)
            for subquery in self.subquery_list
        ]):
            result = dict(product_element[0])
            for subresult in product_element[1:]:
                result.update(subresult)
            result_list.append(result)
        return result_list

    def __hash__(self):
        return hash(str(self))

    def __str__(self) -> str:
        return ' x '.join(f'({sq})' for sq in self.subquery_list)

    cpdef int count_nr_of_terms(self):
        cdef int nr_of_terms = 0
        cdef Query subquery
        for subquery in self.subquery_list:
            nr_of_terms += subquery.count_nr_of_terms()
        return nr_of_terms

    def __eq__(self, other):
        return isinstance(other, Product) and self.subquery_list == other.subquery_list

cdef class Filter(Query):
    """
    This query consists of a subquery that is filtered by a CaConstraint
    """
    cdef public Query query
    cdef public CaConstraint constraint

    def __init__(self, Query query, CaConstraint constraint):
        self.query = query
        self.constraint = constraint

    cpdef list evaluate(self, example: CaExample, dict variables):
        #variables is of type Dict[str, CaObject]
        cdef list result_list = []
        cdef dict result_with_variables
        for result in self.query.evaluate(example, variables):
            result_with_variables = dict(<dict>result)
            result_with_variables.update(variables)
            if self.constraint.holds(example, result_with_variables):
                result_list.append(result)
        return result_list

    def __str__(self) -> str:
        return f'{self.query} | {self.constraint}'

    cpdef int count_nr_of_terms(self):
        return self.query.count_nr_of_terms() + self.constraint.count_nr_of_terms()

    def count_nr_of_preconditions(self) -> int:
        return self.constraint.count_nr_of_preconditions()
