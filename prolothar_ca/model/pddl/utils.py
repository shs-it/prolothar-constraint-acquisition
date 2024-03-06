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

NEWLINE = '\n'
CLEAN_TRANSLATION_TABLE = str.maketrans({
    unallowed_char: '_'
    for unallowed_char in ['-', ' ', '.', '/', '\\']
})

def check_parameter_names(definition, parameter_names: list[str]):
    if len(definition.parameter_types) != len(parameter_names):
        raise ValueError(
            f'{definition.name} requires '
            f'{len(definition.parameter_types)} but was given '
            f'{len(parameter_names)} parameters')

def clean_pddl_name(unclean_name: str) -> str:
    clean_name = unclean_name.translate(CLEAN_TRANSLATION_TABLE)
    if clean_name[0].isdigit():
        clean_name = 'x' + clean_name
    return clean_name
