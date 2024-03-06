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
from prolothar_ca.model.ca.constraints.boolean import RelationIsTrue
from prolothar_ca.model.ca.constraints.boolean import RelationIsFalse
from prolothar_ca.model.ca.constraints.conjunction import And
from prolothar_ca.model.ca.constraints.conjunction import Or
from prolothar_ca.model.ca.constraints.numeric import Absolute
from prolothar_ca.model.ca.constraints.numeric import Difference
from prolothar_ca.model.ca.constraints.numeric import Modulo
from prolothar_ca.model.ca.constraints.numeric import IntegerDivision
from prolothar_ca.model.ca.constraints.numeric import Equal
from prolothar_ca.model.ca.constraints.numeric import LessOrEqual
from prolothar_ca.model.ca.constraints.numeric import GreaterOrEqual
from prolothar_ca.model.ca.constraints.numeric import NumericFeature
from prolothar_ca.model.ca.constraints.numeric import NumericRelation
from prolothar_ca.model.ca.constraints.numeric import AggregateSum
from prolothar_ca.model.ca.constraints.numeric import CountConsecutive
from prolothar_ca.model.ca.constraints.query import AllOfTypeOrderBy
from prolothar_ca.model.ca.constraints.query import AllOfType
from prolothar_ca.model.ca.constraints.query import Product
from prolothar_ca.model.ca.constraints.query import Filter
from prolothar_ca.model.ca.constraints.quantifier import ForAll
from prolothar_ca.model.ca.constraints.objects import ObjectsEqual
from prolothar_ca.model.ca.constraints.objects import ObjectsNotEqual