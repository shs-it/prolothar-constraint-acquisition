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

from prolothar_ca.model.ca.constraints.constraint import CaConstraint
from prolothar_ca.model.ca.example import CaExample
from prolothar_ca.model.ca.obj import CaObject

class Query:

    def evaluate(self, example: CaExample, variables: dict[str, CaObject]) -> list: ...
    def count_nr_of_terms(self) -> int: ...

class AllOfType(Query):
    type_name: str
    variable_name: str

    def __init__(self, type_name: str, variable_name: str): ...

class AllOfTypeOrderBy(Query):
    type_name: str
    variable_name: str
    by: str|list[str]

class Product(Query):
    subquery_list: list[Query]

    def __init__(self, subquery_list: list[Query]): ...

class Filter(Query):
    query: Query
    constraint: CaConstraint

    def __init__(self, query: Query, constraint: CaConstraint): ...
