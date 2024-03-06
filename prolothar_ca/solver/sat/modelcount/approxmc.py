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

from math import log2
import os
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from prolothar_common import validate

from prolothar_ca.model.sat.cnf import CnfFormula
from prolothar_ca.solver.sat.modelcount.model_counter import ModelCounter

if os.name == 'nt':
    PATH_TO_APPROX_MC = 'thirdparties/approxmc/amd64-windows/approxmc.exe'
else:
    PATH_TO_APPROX_MC = 'thirdparties/approxmc/amd64-linux/approxmc'
PATH_TO_APPROX_MC = os.environ.get('APPROXMC', PATH_TO_APPROX_MC)

NR_OF_SOLUTIONS_LINE_PREFIX = '[appmc] Number of solutions is: '
ALTERNATIVE_NR_OF_SOLUTIONS_LINE_PREFIX = f'c {NR_OF_SOLUTIONS_LINE_PREFIX}'
NR_OF_SOLUTION_SPLIT_REGEX = re.compile(r' x |\^|\*\*|\*')

class ApproxMC(ModelCounter):
    """
    python interface to ApproxMC
    https://github.com/meelgroup/approxmc
    """

    def __init__(
            self, random_seed: int|None = None, verbose: bool = False, epsilon: float = 0.8,
            use_docker: bool = False):
        if random_seed is not None:
            validate.is_instance(random_seed, int)
        self.__random_seed = random_seed
        self.__verbose = verbose
        validate.in_left_open_interval(epsilon, 0, 1)
        self.__epsilon = epsilon
        self.__use_docker = use_docker

    def count(self, cnf: CnfFormula) -> int:
        try:
            return round(2**self.countlog2(cnf))
        except ValueError:
            #ValueError is thrown if the number of solutions is 0 and log2(0) is undefined
            return 0

    def countlog2(self, cnf: CnfFormula) -> float:
        with TemporaryDirectory() as temp_directory:
            with open(self.__write_cnf_file(cnf, temp_directory)) as cnf_file:
                with self.__open_approxmc_process(cnf, cnf_file) as approxmc_process:
                    while approxmc_process.stdout.readable():
                        line = approxmc_process.stdout.readline()
                        if not line:
                            break
                        if self.__verbose:
                            sys.stdout.write(line)
                        for prefix in [NR_OF_SOLUTIONS_LINE_PREFIX, ALTERNATIVE_NR_OF_SOLUTIONS_LINE_PREFIX]:
                            if line.startswith(prefix):
                                return self.__parse_log2_number_of_solutions(line, prefix)
        raise NotImplementedError('should not reach this line. missed solution in approxmc output')

    def __write_cnf_file(self, cnf: CnfFormula, temp_directory: str):
        cnf_file = os.path.join(temp_directory, 'input.cnf')
        with open(cnf_file, 'w') as f:
            f.write(f'c ind {" ".join(map(str, sorted(cnf.get_variable_nr_set())))} 0')
            f.write(cnf.to_dimacs())
        return cnf_file

    def __open_approxmc_process(self, cnf: CnfFormula, cnf_file):
        if self.__use_docker:
            command = ['docker', 'run', '--rm', '-i', '-a', 'stdin', '-a', 'stdout', 'msoos/approxmc']
        else:
            command = [PATH_TO_APPROX_MC]
        command.extend(('--epsilon', str(self.__epsilon)))
        if self.__random_seed is not None:
            command.append('--seed')
            command.append(str(self.__random_seed))
        return subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            stdin=cnf_file,
            universal_newlines=True)

    def __parse_log2_number_of_solutions(self, line: str, prefix: str) -> int:
        #-1 to remove '\n' at end of line
        a,_,b = NR_OF_SOLUTION_SPLIT_REGEX.split(line[len(prefix):-1])
        return log2(int(a)) + int(b)
