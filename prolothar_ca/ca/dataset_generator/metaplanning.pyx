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

from random import Random
import os
from prolothar_common import validate
from pyparsing import nested_expr
from tqdm import tqdm
import bz2
from multiprocessing.pool import ThreadPool
from threading import Lock
from typing import Set, List, Tuple
import pickle
import gc

from prolothar_ca.ca.dataset_generator.dataset_generator import CaDatasetGenerator
from prolothar_ca.ca.dataset_generator.pddl import PddlCaDatasetGenerator
from prolothar_ca.model.ca.constraints.constraint import CaConstraint

from prolothar_ca.model.ca.dataset import CaDataset
from prolothar_ca.model.ca.example import CaExample
from prolothar_ca.model.ca.targets import RelationTarget

from prolothar_ca.model.pddl.domain import Domain
from prolothar_ca.model.pddl.problem import Problem
from prolothar_ca.model.pddl.plan import Plan
from prolothar_ca.model.pddl.condition import PredicateIsTrueCondition

class MetaplanningCaDatasetGenerator(CaDatasetGenerator):

    def __init__(
            self, directory: str, action_name_of_interest: str|None = None,
            search_new_valid_actions: bool = False,
            filter_actions_with_duplicate_parameter: bool = False,
            relations_to_ignore: Set[str]|None = None,
            nr_of_target_relation_samples: int|None = None,
            nr_of_feature_relation_samples: int|None = None,
            nr_of_threads: int = 1,
            max_trajectory_files: int = -1,
            cache_parsed_trajectories: bool = False,
            disable_gc_during_parsing: bool = False,
            ignore_parameters: list[str]|None = None,
            remove_unused_objects: bool = False):
        if disable_gc_during_parsing:
            gc.disable()
        try:
            domain_file = os.path.join(directory, 'reference')
            if os.path.exists(domain_file):
                with open(domain_file) as f:
                    domain = Domain.from_pddl(f.read())
                    domain.add_type('object')
            else:
                validate.is_true(not search_new_valid_actions)
                with open(os.path.join(directory, 'domain.pddl')) as f:
                    domain = Domain.from_pddl(f.read())
            problem_list, plan_list = self.__parse_problem_and_plan_list(
                directory, nr_of_threads, domain, max_trajectory_files, cache_parsed_trajectories)
            if action_name_of_interest is None:
                action_of_interest = plan_list[0].action_list[0][0]
            else:
                action_of_interest = domain.get_action_by_name(action_name_of_interest)
            self.pddl_ca_dataset_generator = PddlCaDatasetGenerator(
                domain, problem_list, plan_list, action_of_interest,
                search_new_valid_actions=search_new_valid_actions,
                filter_actions_with_duplicate_parameter=filter_actions_with_duplicate_parameter,
                relations_to_ignore=relations_to_ignore,
                nr_of_target_relation_samples=nr_of_target_relation_samples,
                nr_of_feature_relation_samples=nr_of_feature_relation_samples,
                ignore_parameters=ignore_parameters,
                remove_unused_objects=remove_unused_objects
            )
        finally:
            gc.enable()

    def __parse_problem_and_plan_list(
            self, directory: str, nr_of_threads: int, domain: Domain, max_trajectory_files: int,
            cache_parsed_trajectories: bool):
        cdef list problem_list = []
        cdef list plan_list = []
        trajectory_file_list = [
            os.path.join(directory, trajectory_file)
            for trajectory_file in os.listdir(directory)
            if trajectory_file.startswith('trajectory-') and not trajectory_file.endswith('.cache')
        ]
        if max_trajectory_files > 0:
            trajectory_file_list = trajectory_file_list[:max_trajectory_files]
        if nr_of_threads == 1:
            for trajectory_file in tqdm(trajectory_file_list, desc='parse trajectory files'):
                problem, plan = parse_trajectory_file(trajectory_file, domain, cache_parsed_trajectories)
                problem_list.append(problem)
                plan_list.append(plan)
        else:
            lock = Lock()
            def parse_trajectory_file_fixed_domain(trajectory_file: str) -> Tuple[Problem, Plan]:
                result = parse_trajectory_file(trajectory_file, domain, cache_parsed_trajectories)
                with lock:
                    progressbar.update()
                return result
            with tqdm(total=len(trajectory_file_list), desc='parse trajectory_files') as progressbar:
                pool = ThreadPool(nr_of_threads)
                for result in pool.map(parse_trajectory_file_fixed_domain, trajectory_file_list):
                    problem_list.append(result[0])
                    plan_list.append(result[1])
        return problem_list,plan_list

    def _create_empty_dataset(self) -> CaDataset:
        return self.pddl_ca_dataset_generator._create_empty_dataset()

    def generate(
            self, nr_of_positive_examples: int,
            nr_of_negative_examples: int,
            random_seed: int|None = None) -> CaDataset:
        return self.pddl_ca_dataset_generator.generate(
            nr_of_positive_examples, nr_of_negative_examples,
            random_seed=random_seed)

    def _generate_positive_example(self, random_generator: Random) -> CaExample:
        return self.pddl_ca_dataset_generator._generate_positive_example(random_generator)

    def _generate_negative_example(self, random_generator: Random) -> CaExample:
        return self.pddl_ca_dataset_generator._generate_negative_example(random_generator)

    def get_ground_truth_constraints(self) -> List[CaConstraint]:
        return self.pddl_ca_dataset_generator.get_ground_truth_constraints()

    def get_target(self) -> RelationTarget:
        return self.pddl_ca_dataset_generator.get_target()

def parse_trajectory_file(
        trajectory_file: str, domain: Domain,
        cache_parsed_trajectories: bool) -> Tuple[Problem, Plan]:
    if cache_parsed_trajectories:
        cache_file = trajectory_file + '.cache'
        if os.path.exists(cache_file):
            with open(cache_file, mode='rb') as f:
                return pickle.load(f)
    problem = Problem(trajectory_file, domain)
    if trajectory_file.endswith('bz2'):
        with bz2.open(trajectory_file, 'rt') as f:
            plan = parse_plan_with_custom_parsing(f.read(), domain, problem)
    else:
        with open(trajectory_file) as f:
            plan = parse_plan_with_nested_expression(f.read(), domain, problem)
    if cache_parsed_trajectories:
        with open(cache_file, mode='wb') as f:
            pickle.dump((problem, plan), f, protocol=pickle.HIGHEST_PROTOCOL)
    return problem, plan

def load_pickled_trajectory_file(trajectory_file: str) -> Tuple[Problem, Plan]:
    cache_file = trajectory_file + '.cache'
    if os.path.exists(cache_file):
        with open(cache_file, mode='rb') as f:
            return pickle.load(f)
    else:
        raise NotImplementedError(f'multiprocessing requires pickled trajectory, but {cache_file} does not exist')

def parse_plan_with_nested_expression(trajectory: str, domain: Domain, problem: Problem) -> Plan:
    parsed_trajectory = nested_expr().parse_string(trajectory)[0]
    validate.equals(parsed_trajectory[0], 'trajectory')
    action_list = []
    for pddl_section in tqdm(parsed_trajectory[1:], desc='sections'):
        section_name = pddl_section[0]
        section_content = pddl_section[1:]
        if section_name == ':objects':
            problem.add_objects_from_parsed_pddl(section_content)
        elif section_name == ':init':
            problem.set_initial_state_from_parsed_pddl(section_content)
        elif section_name == ':action':
            action = domain.get_action_by_name(section_content[0][0])
            action_list.append((action, {
                parameter_name: problem.get_object_by_name(object_name)
                for parameter_name, object_name in zip(sorted(action.parameters.keys()), section_content[0][1:])
            }))
        elif section_name == ':state':
            problem.set_goal([
                PredicateIsTrueCondition(
                    domain.get_predicate_by_name(raw_condition[0]),
                    raw_condition[1:]
                )
                for raw_condition in section_content
                if isinstance(raw_condition[0], str)
            ])
        else:
            raise NotImplementedError(f'unsupported section "{section_name}" with content "{section_content}"')
    return Plan(action_list, len(action_list))

def parse_plan_with_custom_parsing(trajectory: str, domain: Domain, problem: Problem) -> Plan:
    cdef list action_list = []
    cdef str line
    cdef list init_state_list
    cdef str predicate
    for line in trajectory.splitlines():
        line = ' '.join(line.split())
        if line.startswith('(:objects '):
            problem.add_objects_from_parsed_pddl(line[len('(:objects '):-1].split())
        elif line.startswith('(:init ('):
            init_state_list = []
            for predicate in line[len('(:init ('):-2].split(') ('):
                if predicate.startswith('= ('):
                    init_state_list.append(['=', predicate[len('= ('):predicate.index(')')].split(), predicate.split()[-1]])
                else:
                    init_state_list.append(predicate.split())
            problem.set_initial_state_from_parsed_pddl(init_state_list)
        elif line.startswith('(:action ('):
            action_parts = line[len('(:action ('):-2].split()
            action = domain.get_action_by_name(action_parts[0])
            action_list.append((action, {
                parameter_name: problem.get_object_by_name(object_name)
                for parameter_name, object_name in zip(sorted(action.parameters.keys()), action_parts[1:])
            }))
        elif line and line != ')' and line != '(trajectory' and not line.startswith('(:state'):
            raise NotImplementedError(line[:50])
    return Plan(action_list, len(action_list))