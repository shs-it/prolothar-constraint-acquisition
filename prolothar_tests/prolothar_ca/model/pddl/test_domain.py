import unittest

from prolothar_ca.model.pddl import Domain

class TestDomain(unittest.TestCase):

    def test_build_domain(self):
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

        reconstructed_domain = Domain.from_pddl(domain.to_pddl())
        self.assertEqual(domain, reconstructed_domain)

    def test_build_domain_with_durative_action(self):
        #https://planning.wiki/ref/pddl21/domain
        domain = Domain('rover-domain')

        rover_type = domain.add_type('rover')
        waypoint_type = domain.add_type('waypoint')

        at_predicate = domain.add_predicate('at', [rover_type, waypoint_type])
        is_blocked_predicate = domain.add_predicate('is_blocked', [waypoint_type])

        battery_level = domain.add_numeric_fluent('battery-level', [rover_type])
        move_duration = domain.add_numeric_fluent('move_duration', [rover_type])

        domain.add_durative_action(
            'move',
            {'r': rover_type, 'from': waypoint_type, 'to': waypoint_type},
            move_duration.get_value(['r']),
            [at_predicate.is_true(['r', 'from']), battery_level.greater(['r'], 0)],
            [is_blocked_predicate.is_false(['to'])],
            [is_blocked_predicate.set_false(['from'])],
            [battery_level.decrease(['r'], 1), is_blocked_predicate.set_true(['to'])]
        )

        reconstructed_domain = Domain.from_pddl(domain.to_pddl())
        self.assertEqual(domain, reconstructed_domain)

if __name__ == '__main__':
    unittest.main()