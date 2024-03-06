# Prolothar Constraint Acquisition

Algorithms for constraint acquisition, e.g. discovery of scheduling constraints

Based on the publication
> Boris Wiegand, Dietrich Klakow, and Jilles Vreeken.
> **What Are the Rules? Discovering Constraints from Data.**
> In: *Proceedings of the 38th AAAI Conference on Artificial Intelligence (AAAI), Vancouver, Canada.* 2024, pp. 4237–4244.

### Prerequisites

Python 3.11+

## Usage

See prolothar_tests/prolothar_ca/ca/methods/custon/test_urpils.py for some simple examples.

If you want to run the algorithms on your own data, follow the steps below.

### Installing

```bash
pip install prolothar-constraint-acquisition
```

### Discovering Constraints for Constraint Programming Problems

In this example, we acquire constraints for the N-Queens problem,
in which we want to place 8 queens on a 8x8 checkerboard, such that no two queens attack each other.

First, we need to create a dataset with examples from which we want to acquire constraints.

```python
from prolothar_ca.model.ca.dataset import CaDataset
from prolothar_ca.model.ca.example import CaExample
from prolothar_ca.model.ca.obj import CaObject, CaObjectType
from prolothar_ca.model.ca.relation import CaRelation, CaRelationType
from prolothar_ca.model.ca.targets import CaTarget, RelationTarget
from prolothar_ca.model.ca.variable_type import CaBoolean, CaNumber

# this is the relation for which we want to find constraints
queen_on_square = CaRelationType(
    'queen_on_square',
    ('Queen', 'Square'),
    CaBoolean()
)

dataset = CaDataset({
    'Square': CaObjectType(
        'Square',
        {
            'x': CaNumber(),
            'y': CaNumber(),
        }
    ),
    'Queen': CaObjectType('Queen', {})
},
{
    'queen_on_square': queen_on_square
})

queen_list = [CaObject(f'queen{i+1}', QUEEN_TYPE_NAME, {}) for i in range(8)]
square_set = set(
    CaObject(f'square_{x}_{y}', SQUARE_TYPE_NAME, {'x': x, 'y': y})
    for x in range(8)
    for y in range(8)
)

#the following 2d array defines a valid solution
# 0 = no queen on this square
# a number != 0 is the ID of the queen on this square
solution = [
    [0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 2, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 3],
    [0, 4, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 5, 0],
    [6, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 7, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 8, 0, 0, 0]
]

# Let us create an example from this solution
# 1. parameter defines which types of objects are involved
# 2. parameter defines values for relations
# 3. parameter defines whether this example is a valid solution or not
example = CaExample(
    {
        'Queen': set(queen_list),
        'Square': square_set
    },
    {
        'queen_on_square': set(
            CaRelation(
                'queen_on_square', (queen, square),
                solution[square.features['x']][square.features['y']] == i+1
            ) for square in square_set
        )
    },
    True
)
for square in example.all_objects_per_type[SQUARE_TYPE_NAME]:
    for i,queen in enumerate(queen_list):
        example.add_relation(CaRelation(
            'queen_on_square',
            (queen, square),
            solution[square.features['x']][square.features['y']] == i + 1
        ))
dataset.add_example(example)

#Now, you can add multiple valid examples to the dataset
```

Having a dataset with examples, we can now learn constraints.

```python
from prolothar_ca.ca.methods import URPiLs

urpils = URPiLs(verbose=True)
constraints = urpils.acquire_constraints(dataset, RelationTarget('queen_on_square'))
for constraint in constraints:
    print(constraint)

# If your problem has a higher dimensionality, you can speed up computations by activating sampling (can reduce accuracy):
# "max_nr_of_target_zeros" determines how many zeros of the target relation are used to compute the MDL score (we had good results with 50-100)
# "implication_pairs_limit" controls the datset size to learn complex constraints (we had good results 1000). set it to 0 to turn off search for complex constraints.
urpils = URPiLs(verbose=True, max_nr_of_target_zeros=100, implication_pairs_limit=1000)
```

### Discovering Constraints for AI planning Problems

```python
from prolothar_ca.ca.dataset_generator.metaplanning import MetaplanningCaDatasetGenerator

#the directory contains
# 1. a file "empty", which contains an empty domain (actions do not have defined effects or preconditions)
# 2. files "trajectory-{number}" with exemplary execution trajectories (states and action executions)
# 3. an optional file "reference", which contains the full domain with preconditions and effects (only necessary if you want to generate negative examples or additional positive examples)
dataset_generator = MetaplanningCaDatasetGenerator(
    'prolothar_tests/resources/meta_planning/hanoi',
    filter_actions_with_duplicate_parameter=True)

#create a dataset with 30 examples of valid action executions
dataset = dataset_generator.generate(30, 0, random_seed=20022023)

#learn constraints for the planning problem
urpils = URPiLs(planning_dataset=True, verbose=True)
for constraint in constraints:
    print(constraint)
```

## Development

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Additional Prerequisites
- make (optional)

### Compile Cython code

```bash
make cython
```

### Running the tests

```bash
make test
```

### Deployment

```bash
make clean_package || make package && make publish
```

## Versioning

We use [SemVer](http://semver.org/) for versioning.

## Authors

If you have any questions, feel free to ask one of our authors:

* **Boris Wiegand** - boris.wiegand@stahl-holding-saar.de
