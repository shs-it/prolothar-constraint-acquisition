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

from prolothar_ca.model.pddl.utils import check_parameter_names

cdef class NumericExpression():
    cpdef long evaluate(self, dict parameter_assignment, object state)

cdef class ConstantExpression(NumericExpression):
    cdef long __constant_value

cdef class NumericFluentExpression(NumericExpression):
    cdef object __numeric_fluent
    cdef list __parameter_names

cdef class Add(NumericExpression):
    cdef NumericExpression __summand_a
    cdef NumericExpression __summand_b

cdef class Subtract(NumericExpression):
    cdef NumericExpression __summand_a
    cdef NumericExpression __summand_b

cdef class Divide(NumericExpression):
    cdef NumericExpression __summand_a
    cdef NumericExpression __summand_b

cdef class Multiply(NumericExpression):
    cdef NumericExpression __summand_a
    cdef NumericExpression __summand_b
