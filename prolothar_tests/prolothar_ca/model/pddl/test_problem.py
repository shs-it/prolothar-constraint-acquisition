import unittest

from prolothar_ca.model.pddl import Domain
from prolothar_ca.model.pddl import Problem
from prolothar_ca.model.pddl.condition import Less, PredicateIsTrueCondition
from prolothar_ca.model.pddl.initial_state import InitialState
from prolothar_ca.model.pddl.metric import MaximizeMetric
from prolothar_ca.model.pddl.numeric_expression import NumericFluentExpression

class TestProblem(unittest.TestCase):

    def test_build_problem(self):
        domain = Domain('rover-domain')

        rover_type = domain.add_type('rover')
        waypoint_type = domain.add_type('waypoint')

        at_predicate = domain.add_predicate('at', [rover_type, waypoint_type])
        is_blocked_predicate = domain.add_predicate('is_blocked', [waypoint_type])

        battery_level = domain.add_numeric_fluent('battery-level', [rover_type])

        domain.add_action(
            'move',
            {'r': rover_type, 'from': waypoint_type, 'to': waypoint_type},
            [
                at_predicate.is_true(['r', 'from']),
                is_blocked_predicate.is_false(['to']),
                battery_level.greater(['r'], 0)
            ],
            [
                is_blocked_predicate.set_false(['from']),
                battery_level.decrease(['r'], 1),
                is_blocked_predicate.set_true(['to'])
            ]
        )

        problem = Problem('mars-discovery', domain)
        rover = problem.add_object('rover', rover_type)
        waypoint_a = problem.add_object('A', waypoint_type)
        waypoint_b = problem.add_object('B', waypoint_type)

        problem.set_initial_state(InitialState(
            problem,
            true_predicates=set([
                (at_predicate, (rover, waypoint_a)),
                (is_blocked_predicate, (waypoint_a,))
            ]),
            numeric_fluents=set([
                (battery_level, (rover,), 100)
            ])
        ))

        problem.set_goal([
            PredicateIsTrueCondition(at_predicate, [rover.name, waypoint_b.name]),
            Less(NumericFluentExpression(battery_level, [rover.name]), 50)
        ])

        problem.set_metric(MaximizeMetric(NumericFluentExpression(battery_level, [rover.name])))

        reconstructed_problem = Problem.from_pddl(problem.to_pddl(), domain)
        self.assertEqual(problem, reconstructed_problem)

if __name__ == '__main__':
    unittest.main()