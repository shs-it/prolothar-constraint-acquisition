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

from dataclasses import dataclass
from datetime import date, timedelta
from collections import defaultdict
from prolothar_ca.model.ca.dataset import CaDataset
from prolothar_ca.model.ca.relation import CaRelationType

from prolothar_ca.model.pddl.metric import MinimizeMetric
from prolothar_common import validate

from prolothar_ca.model.pddl import Domain, Problem
from prolothar_ca.model.pddl.effect import DecreaseEffect, IncreaseEffect, SetNumericFluent, SetPredicateFalse, SetPredicateTrue
from prolothar_ca.model.pddl.numeric_expression import NumericFluentExpression
from prolothar_ca.model.pddl.condition import And, Equals, ForAll, Greater, Less, Not, Or, PredicateIsTrueCondition

from prolothar_ca.model.ca import CaDataset, CaObjectType, CaBoolean, CaNumber

from prolothar_ca.model.rostering.assignment import DateAssignment
from prolothar_ca.model.rostering.contract import Contract
from prolothar_ca.model.rostering.cover_requirement import CoverRequirement
from prolothar_ca.model.rostering.day_on_request import DayOnRequest
from prolothar_ca.model.rostering.employee import Employee

from prolothar_ca.model.rostering.shift import Shift
from prolothar_ca.model.rostering.shift_off_request import ShiftOffRequest
from prolothar_ca.model.rostering.shift_on_request import ShiftOnRequest
import prolothar_ca.model.rostering.pddl_names as pddl_names
import prolothar_ca.model.rostering.ca_names as ca_names

ONE_DAY_IN_SECONDS = 24 * 3600

@dataclass(frozen=True)
class SchedulingPeriod:
    start_date: date
    end_date: date
    shifts: dict[str, Shift]
    shift_groups: dict[str, list[str]]
    employees: dict[str, Employee]
    contracts : dict[str, Contract]
    cover_requirements: list[CoverRequirement]
    fixed_assignments: list[DateAssignment]
    day_on_requests: list[DayOnRequest]
    shift_off_requests: list[ShiftOffRequest]
    shift_on_requests: list[ShiftOnRequest]

    def __post_init__(self):
        validate.is_not_none(self.start_date)
        validate.is_not_none(self.end_date)
        validate.less_or_equal(self.start_date, self.end_date)
        for employee in self.employees.values():
            validate.collection.is_subset(employee.contract_ids, self.contracts)
        for shift_group in self.shift_groups.values():
            validate.collection.is_subset(shift_group, self.shifts)
        validate.is_not_none(self.day_on_requests)
        for day_on_request in self.day_on_requests:
            validate.is_in(day_on_request.employee_id, self.employees)
            validate.greater_or_equal(day_on_request.requested_date, self.start_date)
            validate.less_or_equal(day_on_request.requested_date, self.end_date)
        validate.is_not_none(self.shift_off_requests)
        for shift_off_request in self.shift_off_requests:
            validate.is_in(shift_off_request.employee_id, self.employees)
            validate.is_in(shift_off_request.shift_id, self.shifts)
            validate.greater_or_equal(shift_off_request.requested_date, self.start_date)
            validate.less_or_equal(shift_off_request.requested_date, self.end_date)
        for shift_on_request in self.shift_on_requests:
            validate.is_in(shift_on_request.employee_id, self.employees)
            validate.collection.is_subset(shift_on_request.shift_ids, self.shifts)
            validate.greater_or_equal(shift_on_request.requested_date, self.start_date)
            validate.less_or_equal(shift_on_request.requested_date, self.end_date)

    def to_pddl(
            self, domain_name: str = 'rostering',
            problem_name: str = 'rostering-problem') -> tuple[Domain, Problem]:
        domain = Domain(domain_name)

        day_type = domain.add_type(pddl_names.day_type)
        employee_type = domain.add_type(pddl_names.employee_type)

        is_today = domain.add_predicate(pddl_names.is_today, [day_type])
        is_next_day = domain.add_predicate('is_next_day', [day_type, day_type])
        has_day_assigned = domain.add_predicate('has_day_assigned', [employee_type, day_type])
        has_day_off = domain.add_predicate('has_day_off', [employee_type, day_type])
        works_at_shift = {
            shift_id: domain.add_predicate(pddl_names.works_at_shift(shift_id), [employee_type, day_type])
            for shift_id in self.shifts
        }
        has_contract_predicates = {
            contract: domain.add_predicate(f'has_contract_{contract.contract_id}', [employee_type])
            for contract in self.contracts.values()
        }

        required_employees_variable = {
            shift_id: domain.add_numeric_fluent(
                pddl_names.required_employees_variable(shift_id), [day_type])
            for shift_id in self.shifts
        }
        optional_employees_variable = {
            shift_id: domain.add_numeric_fluent(
                pddl_names.optional_employees_variable(shift_id), [day_type])
            for shift_id in self.shifts
        }
        number_of_not_assigned_shifts_variable = domain.add_numeric_fluent(
            pddl_names.number_of_not_assigned_shifts_variable, [])
        shift_start_variable = {
            shift_id: domain.add_numeric_fluent(pddl_names.shift_start_variable(shift_id), [])
            for shift_id in self.shifts
        }
        shift_end_variable = {
            shift_id: domain.add_numeric_fluent(pddl_names.shift_end_variable(shift_id), [])
            for shift_id in self.shifts
        }
        shift_duration_variable = {
            shift_id: domain.add_numeric_fluent(pddl_names.shift_duration_variable(shift_id), [])
            for shift_id in self.shifts
        }
        total_workload_variable = domain.add_numeric_fluent(pddl_names.total_workload_variable, [employee_type])
        consecutive_shifts_variable = {
            shift_id: domain.add_numeric_fluent(
                pddl_names.consecutive_shifts_variable(shift_id),
                [employee_type]
            )
            for shift_id in self.shifts
        } | {
            (shift_id_a, shift_id_b): domain.add_numeric_fluent(
                pddl_names.consecutive_shifts_variable((shift_id_a,shift_id_b)),
                [employee_type]
            )
            for shift_id_a in self.shifts
            for shift_id_b in self.shifts
            if shift_id_a < shift_id_b
        }
        consecutive_days_off_variable = domain.add_numeric_fluent(
            pddl_names.consecutive_days_off_variable, [employee_type]
        )
        last_shift_end_variable = domain.add_numeric_fluent(
            pddl_names.last_shift_end_variable, [employee_type]
        )

        def general_assign_shift_constraints(shift_id: str):
            return [
                PredicateIsTrueCondition(is_today, [pddl_names.day_action_parameter]),
                Not(PredicateIsTrueCondition(
                    has_day_off,
                    [pddl_names.employee_action_parameter, pddl_names.day_action_parameter]
                ))
            ] + [
                Not(And([
                    PredicateIsTrueCondition(
                        works_at_shift[parallel_shift_id],
                        [
                            pddl_names.employee_action_parameter,
                            pddl_names.day_action_parameter,
                        ]
                    ),
                    Less(
                        NumericFluentExpression(shift_start_variable[parallel_shift_id], []),
                        NumericFluentExpression(shift_end_variable[shift_id], []),
                    ),
                    Greater(
                        NumericFluentExpression(shift_end_variable[parallel_shift_id], []),
                        NumericFluentExpression(shift_start_variable[shift_id], []),
                    )
                ]))
                for parallel_shift_id in self.shifts
            ]

        def general_assign_shift_effects(shift_id: str):
            return  [
                SetPredicateTrue(
                    has_day_assigned,
                    [
                        pddl_names.employee_action_parameter,
                        pddl_names.day_action_parameter
                    ]
                ),
                SetPredicateTrue(
                    works_at_shift[shift_id],
                    [
                        pddl_names.employee_action_parameter,
                        pddl_names.day_action_parameter,
                    ]
                ),
                SetNumericFluent(
                    last_shift_end_variable,
                    [pddl_names.employee_action_parameter],
                    NumericFluentExpression(shift_end_variable[shift_id], [])
                ),
                SetNumericFluent(
                    consecutive_days_off_variable,
                    [pddl_names.employee_action_parameter], 0
                ),
                IncreaseEffect(
                    total_workload_variable, [pddl_names.employee_action_parameter],
                    NumericFluentExpression(shift_duration_variable[shift_id], [])
                ),
                IncreaseEffect(
                    consecutive_shifts_variable[shift_id],
                    [
                        pddl_names.employee_action_parameter,
                    ],
                    1
                )
            ] + [
                SetNumericFluent(
                    consecutive_shifts_variable[other_shift_id],
                    [pddl_names.employee_action_parameter], 0
                ) for other_shift_id in self.shifts
                if other_shift_id != shift_id
            ] + [
                IncreaseEffect(
                    domain.get_numeric_fluent_by_name(
                        pddl_names.consecutive_shifts_variable((shift_id, other_shift_id))),
                    [pddl_names.employee_action_parameter], 1
                ) for other_shift_id in self.shifts
                if other_shift_id != shift_id
            ]

        contract_constraints_for_shifts = {}
        for shift_id in self.shifts:
            contract_constraints = []
            for contract, has_contract in has_contract_predicates.items():
                shift_contraints = [x for x in [
                    shift_constraint.to_pddl_for_assign_shift_actions(domain, shift_id, self.shift_groups)
                    for shift_constraint in contract.shift_constraints
                ] if x is not None]
                if len(shift_contraints) == 1:
                    contract_constraints.append(Or([
                        Not(PredicateIsTrueCondition(has_contract, [pddl_names.employee_action_parameter])),
                        shift_contraints[0]
                    ]))
                elif len(shift_contraints) > 1:
                    contract_constraints.append(Or([
                        Not(PredicateIsTrueCondition(has_contract, [pddl_names.employee_action_parameter])),
                        And(shift_contraints)
                    ]))
            contract_constraints_for_shifts[shift_id] = contract_constraints

        for shift_id in self.shifts:
            domain.add_action(
                pddl_names.assign_required_shift(shift_id),
                {
                    pddl_names.day_action_parameter: day_type,
                    pddl_names.employee_action_parameter: employee_type
                },
                general_assign_shift_constraints(shift_id) + [
                    Greater(
                        NumericFluentExpression(
                            required_employees_variable[shift_id],
                            [pddl_names.day_action_parameter]
                        ), 0
                    ),
                ] + contract_constraints_for_shifts[shift_id],
                general_assign_shift_effects(shift_id) + [
                    DecreaseEffect(
                        required_employees_variable[shift_id],
                        [
                            pddl_names.day_action_parameter
                        ], 1
                    )
                ]
            )

            domain.add_action(
                pddl_names.assign_optional_shift(shift_id),
                {
                    pddl_names.day_action_parameter: day_type,
                    pddl_names.employee_action_parameter: employee_type
                },
                general_assign_shift_constraints(shift_id) + [
                    Greater(
                        NumericFluentExpression(
                            optional_employees_variable[shift_id],
                            [pddl_names.day_action_parameter]
                        ), 0
                    ),
                ] + contract_constraints_for_shifts[shift_id],
                general_assign_shift_effects(shift_id) + [
                    DecreaseEffect(
                        optional_employees_variable[shift_id],
                        [
                            pddl_names.day_action_parameter
                        ], 1
                    )
                ]
            )

        domain.add_action(
            pddl_names.assign_day_off,
            {
                pddl_names.day_action_parameter: day_type,
                pddl_names.employee_action_parameter: employee_type
            },
            [
                PredicateIsTrueCondition(is_today, [pddl_names.day_action_parameter]),
                Not(PredicateIsTrueCondition(
                    has_day_assigned,
                    [pddl_names.employee_action_parameter, pddl_names.day_action_parameter]
                )),
            ],
            [
                SetPredicateTrue(
                    has_day_assigned,
                    [
                        pddl_names.employee_action_parameter,
                        pddl_names.day_action_parameter
                    ]
                ),
                SetPredicateTrue(
                    has_day_off,
                    [
                        pddl_names.employee_action_parameter,
                        pddl_names.day_action_parameter
                    ]
                ),
                IncreaseEffect(
                    consecutive_days_off_variable,
                    [pddl_names.employee_action_parameter], 1
                )
            ] + [
                SetNumericFluent(variable, [pddl_names.employee_action_parameter], 0)
                for variable in consecutive_shifts_variable.values()
            ]
        )

        domain.add_action(
            pddl_names.start_next_day,
            {
                'current_day': day_type,
                'next_day': day_type
            },
            [
                PredicateIsTrueCondition(is_today, ['current_day']),
                PredicateIsTrueCondition(is_next_day, ['current_day', 'next_day']),
                ForAll('employee', employee_type, PredicateIsTrueCondition(
                    has_day_assigned, ['employee', 'current_day']
                ))
            ] + [
                Equals(
                    NumericFluentExpression(required_employees_variable[shift_id], ['current_day']), 0
                ) for shift_id in self.shifts
            ] + [
                Equals(
                    NumericFluentExpression(optional_employees_variable[shift_id], ['current_day']), 0
                ) for shift_id in self.shifts
            ],
            [
                SetPredicateFalse(is_today, ['current_day']),
                SetPredicateTrue(is_today, ['next_day'])
            ] + [
                IncreaseEffect(shift_start_variable[shift_id], [], 24)
                for shift_id in self.shifts
            ] + [
                IncreaseEffect(shift_end_variable[shift_id], [], 24)
                for shift_id in self.shifts
            ]
        )

        for shift_id in self.shifts:
            domain.add_action(
                pddl_names.block_optional_shift(shift_id),
                {
                    'day': day_type
                },
                [
                    PredicateIsTrueCondition(is_today, ['day']),
                    Greater(
                        NumericFluentExpression(optional_employees_variable[shift_id], ['day']), 0
                    )
                ],
                [
                    IncreaseEffect(number_of_not_assigned_shifts_variable, [], 1),
                    DecreaseEffect(optional_employees_variable[shift_id], ['day'], 1)
                ]
            )

        problem = Problem(problem_name, domain)
        current_date = self.start_date
        previous_day_object = None
        while current_date <= self.end_date + timedelta(days=1):
            current_day_object = problem.add_object(pddl_names.day_object_name(current_date), day_type)
            if previous_day_object is not None:
                problem.get_intitial_state().true_predicates.add((
                    is_next_day, tuple([previous_day_object, current_day_object])
                ))
            current_date += timedelta(days=1)
            previous_day_object = current_day_object
        problem.get_intitial_state().true_predicates.add((
            is_today, tuple([problem.get_object_by_name(pddl_names.day_object_name(self.start_date))])
        ))
        for employee in self.employees.values():
            #ensure that pddl object id for employees do not start with a number
            employee_object = problem.add_object(
                pddl_names.employee_object_name(employee.employee_id), employee_type)
            for contract_id in employee.contract_ids:
                problem.get_intitial_state().true_predicates.add((
                    has_contract_predicates[self.contracts[contract_id]],
                    tuple([employee_object])
                ))
            problem.get_intitial_state().numeric_fluents.add((
                total_workload_variable,
                tuple([employee_object]),
                0
            ))
            problem.get_intitial_state().numeric_fluents.add((
                consecutive_days_off_variable,
                tuple([employee_object]),
                0
            ))
            problem.get_intitial_state().numeric_fluents.add((
                last_shift_end_variable,
                tuple([employee_object]),
                -1000
            ))
            for variable in consecutive_shifts_variable.values():
                problem.get_intitial_state().numeric_fluents.add((
                    variable,
                    tuple([employee_object]),
                    0
                ))
        for shift in self.shifts.values():
            if shift.end_time < shift.start_time:
                raise NotImplementedError()
            problem.get_intitial_state().numeric_fluents.add((
                shift_start_variable[shift.shift_id], tuple(), shift.start_time.hour
            ))
            problem.get_intitial_state().numeric_fluents.add((
                shift_end_variable[shift.shift_id], tuple(), shift.end_time.hour
            ))
            problem.get_intitial_state().numeric_fluents.add((
                shift_duration_variable[shift.shift_id], tuple(),
                shift.end_time.hour - shift.start_time.hour
            ))

        for cover_requirement in self.cover_requirements:
            cover_requirement.to_pddl(problem, domain, self)

        problem.get_intitial_state().numeric_fluents.add((
            number_of_not_assigned_shifts_variable, tuple(), 0
        ))

        problem.add_goal(
            PredicateIsTrueCondition(is_today, [pddl_names.day_object_name(self.end_date + timedelta(days=1))])
        )

        problem.set_metric(MinimizeMetric(NumericFluentExpression(number_of_not_assigned_shifts_variable, [])))

        return domain, problem

    def conflate_equivalent_contracts(self):
        """
        merges contracts that have equivalent shift constraints
        """
        contracts_grouped_by_constraints = defaultdict(list)
        for contract in self.contracts.values():
            contracts_grouped_by_constraints[frozenset(contract.shift_constraints)].append(contract)
        def merge_contract_ids(constract_group: list[Contract]) -> str:
            return 'Contract_' + '_'.join(contract.contract_id for contract in constract_group)
        contract_id_mapping = {
            contract.contract_id: merge_contract_ids(contract_group)
            for contract_group in contracts_grouped_by_constraints.values()
            for contract in contract_group
        }
        for contract_group in contracts_grouped_by_constraints.values():
            self.contracts[contract_group[0].contract_id].rename_contract(contract_id_mapping[contract_group[0].contract_id])
        for employee in self.employees.values():
            employee.contract_ids = list(set(map(contract_id_mapping.get, employee.contract_ids)))

    @staticmethod
    def from_xml(xml: str) -> 'SchedulingPeriod':
        from prolothar_ca.model.rostering.xml_parsing import parse_scheduling_period
        return parse_scheduling_period(xml)

    def to_ca_dataset(self, with_helpful_relations: bool = False) -> CaDataset:
        if with_helpful_relations:
            helpful_relations = {
                ca_names.distance_in_hours: CaRelationType(
                    ca_names.distance_in_hours,
                    (ca_names.shift, ca_names.shift),
                    CaNumber()
                ),
                ca_names.shifts_are_within_one_day: CaRelationType(
                    ca_names.shifts_are_within_one_day,
                    (ca_names.shift, ca_names.shift),
                    CaBoolean()
                )
            }
        else:
            helpful_relations = {}
        return CaDataset(
            {
                ca_names.employee: CaObjectType(
                    ca_names.employee,
                    {
                        ca_names.has_contract(contract_id): CaBoolean()
                        for contract_id in self.contracts
                    }
                    if len(self.contracts) > 1 else {}
                ),
                ca_names.shift: CaObjectType(
                    ca_names.shift,
                    {
                        ca_names.is_shift_type(shift_id): CaBoolean()
                        for shift_id in self.shifts
                    } | {
                        ca_names.relative_start_time_in_hours: CaNumber(),
                        ca_names.relative_end_time_in_hours: CaNumber(),
                        ca_names.duration_in_hours: CaNumber(),
                        ca_names.is_optional: CaBoolean()
                    }
                )
            },
            {
                ca_names.works_at_shift: CaRelationType(
                    ca_names.works_at_shift,
                    (ca_names.employee, ca_names.shift),
                    CaBoolean()
                )
            } | helpful_relations
        )
