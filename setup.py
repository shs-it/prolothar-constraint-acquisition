# -*- coding: utf-8 -*-

#import order is important!
import pathlib
from setuptools import setup
from distutils.extension import Extension
from Cython.Build import cythonize
from Cython.Compiler.Options import get_directive_defaults
import os
import numpy as np
import platform

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

with open(HERE / 'requirements.txt', 'r') as f:
    install_reqs = [
        s for s in [
            line.split('#', 1)[0].strip(' \t\n') for line in f
        ] if '==' in s
    ]

with open(HERE / 'version.txt', 'r') as f:
    version = f.read().strip()

cython_profiling_activated = os.environ.get('CYTHON_PROFILING', 'False') == 'True'
print(f'CYTHON_PROFILING is set to {cython_profiling_activated}')
directive_defaults = get_directive_defaults()
directive_defaults['profile'] = cython_profiling_activated
directive_defaults['linetrace'] = cython_profiling_activated
directive_defaults['embedsignature'] = cython_profiling_activated

def make_extension_from_pyx(path_to_pyx: str, include_dirs = None, use_openmp: bool = False) -> Extension:
    extra_compile_args = []
    extra_link_args = []
    if use_openmp:
        if platform.system() == 'Windows':
            extra_compile_args.append('/openmp')
            extra_link_args.append('/openmp')
        else:
            extra_compile_args.append('-fopenmp')
            extra_link_args.append('-fopenmp')
    define_macros = []
    if cython_profiling_activated:
        define_macros.append(('CYTHON_TRACE_NO_GIL', '1'))

    return Extension(
        path_to_pyx.replace('/', '.').replace('.pyx', ''),
        sources=[path_to_pyx], language='c++',
        include_dirs=include_dirs,
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
        define_macros=define_macros)

if os.path.exists('prolothar_ca/model/sat/cnf.pyx'):
    extensions = [
        make_extension_from_pyx("prolothar_ca/model/sat/variable.pyx"),
        make_extension_from_pyx("prolothar_ca/model/sat/term.pyx"),
        make_extension_from_pyx("prolothar_ca/model/sat/term_factory.pyx"),
        make_extension_from_pyx("prolothar_ca/model/sat/cnf.pyx"),
        make_extension_from_pyx("prolothar_ca/model/sat/implication_graph.pyx"),
        make_extension_from_pyx("prolothar_ca/model/sat/constraint_graph.pyx"),
        make_extension_from_pyx("prolothar_ca/model/pddl/action.pyx"),
        make_extension_from_pyx("prolothar_ca/model/pddl/condition.pyx"),
        make_extension_from_pyx("prolothar_ca/model/pddl/effect.pyx"),
        make_extension_from_pyx("prolothar_ca/model/pddl/numeric_expression.pyx"),
        make_extension_from_pyx("prolothar_ca/model/pddl/object_type.pyx"),
        make_extension_from_pyx("prolothar_ca/model/pddl/state.pyx"),
        make_extension_from_pyx("prolothar_ca/model/pddl/problem.pyx"),
        make_extension_from_pyx("prolothar_ca/model/pddl/pddl_object.pyx"),
        make_extension_from_pyx("prolothar_ca/model/ca/obj.pyx"),
        make_extension_from_pyx("prolothar_ca/model/ca/relation.pyx"),
        make_extension_from_pyx("prolothar_ca/model/ca/example.pyx"),
        make_extension_from_pyx("prolothar_ca/model/ca/variable_type.pyx"),
        make_extension_from_pyx("prolothar_ca/model/ca/constraints/boolean.pyx"),
        make_extension_from_pyx("prolothar_ca/model/ca/constraints/conjunction.pyx"),
        make_extension_from_pyx("prolothar_ca/model/ca/constraints/constraint.pyx"),
        make_extension_from_pyx("prolothar_ca/model/ca/constraints/numeric.pyx"),
        make_extension_from_pyx("prolothar_ca/model/ca/constraints/objects.pyx"),
        make_extension_from_pyx("prolothar_ca/model/ca/constraints/quantifier.pyx"),
        make_extension_from_pyx("prolothar_ca/model/ca/constraints/query.pyx"),
        make_extension_from_pyx("prolothar_ca/ca/methods/custom/homogenous_candidate.pyx"),
        make_extension_from_pyx("prolothar_ca/ca/methods/custom/heterogenous_candidate.pyx"),
        make_extension_from_pyx("prolothar_ca/ca/methods/custom/mdl_score.pyx"),
        make_extension_from_pyx("prolothar_ca/ca/methods/custom/model/custom_constraint.pyx"),
        make_extension_from_pyx("prolothar_ca/ca/methods/custom/itemset_miner/pattern.pyx", use_openmp=True),
        make_extension_from_pyx("prolothar_ca/ca/methods/custom/itemset_miner/score.pyx", use_openmp=True),
        make_extension_from_pyx("prolothar_ca/ca/methods/custom/itemset_miner/itemset_miner.pyx"),
        make_extension_from_pyx("prolothar_ca/ca/methods/custom/homogenous_ca.pyx"),
        make_extension_from_pyx("prolothar_ca/ca/methods/custom/planning_ca.pyx"),
        make_extension_from_pyx("prolothar_ca/ca/dataset_generator/metaplanning.pyx"),
        make_extension_from_pyx("prolothar_ca/solver/sat/solver/twosat_solver.pyx"),
        make_extension_from_pyx("prolothar_ca/solver/sat/modelcount/mc2.pyx"),
        make_extension_from_pyx("prolothar_ca/solver/sat/modelcount/polynomial_upper_bound.pyx"),
    ]
else:
    extensions = []

# This call to setup() does all the work
setup(
    name="prolothar-constraint-acquisition",
    version=version,
    description="algorithms for scheduling and learning scheduling constraints",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://gitlab.dillinger.de/KI/DataScience/processmining/prolothar-constraint-acquisition",
    author="Boris Wiegand",
    author_email="boris.wiegand@stahl-holding-saar.de",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Topic :: Process Mining",
        "Topic :: Constraint Acquisition"
    ],
    packages=["prolothar_ca"],
    include_package_data=True,
    include_dirs=[np.get_include()],
    ext_modules=cythonize(
        extensions, language_level = "3", annotate=True,
        compiler_directives=directive_defaults
    ),
    zip_safe=False,
    install_requires=install_reqs
)
