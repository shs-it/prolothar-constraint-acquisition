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

"""
Pseudo method that returns a fixed list of constraints
"""

from prolothar_common import validate

from prolothar_ca.model.ca import CaDataset
from prolothar_ca.model.ca.targets import CaTarget
from prolothar_ca.model.ca.constraints.constraint import CaConstraint

from prolothar_ca.ca.methods.method import CaMethod

class OracleCaMethod(CaMethod):
    """
    Pseudo method that returns a fixed list of constraints
    """

    def __init__(self, constraint_list: list[CaConstraint], method_name: str = 'Oracle'):
        validate.is_not_none(constraint_list)
        self.__constraint_list = constraint_list
        self.__method_name = method_name

    def acquire_constraints(self, dataset: CaDataset, target: CaTarget) -> list[CaConstraint]:
        return self.__constraint_list

    def __repr__(self):
        return self.__method_name
