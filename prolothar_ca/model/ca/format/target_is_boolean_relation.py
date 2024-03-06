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

from prolothar_common import validate

from prolothar_ca.model.ca.dataset import CaDataset
from prolothar_ca.model.ca.targets import CaTarget, RelationTarget
from prolothar_ca.model.ca.format.invalid_ca_format_error import InvalidCaFormatError
from prolothar_ca.model.ca.format.format import CaFormat
from prolothar_ca.model.ca.variable_type import CaBoolean

class TargetIsBooleanRelation(CaFormat):
    """
    validates that the target is boolean relation target
    """

    def _validate(self, dataset: CaDataset, target: CaTarget):
        validate.is_instance(target, RelationTarget)
        validate.is_instance(
            dataset.get_relation_type(target.relation_name).value_type, CaBoolean
        )
