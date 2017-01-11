# Lisa Cohen
# commonly-used functions
# to use, "import clusterfunc"

import os
import subprocess
from subprocess import Popen, PIPE


def check_dir(dirname):
    if os.path.isdir(dirname) == False:
        os.mkdir(dirname)
        print("Directory created:"), dirname


def get_qsub_filename(basedir, process_name, filename):
    qsub_dir = basedir + "qsub_files/"
    check_dir(qsub_dir)
    qsub_filename = qsub_dir + process_name + "_" + filename + ".qsub"
    return qsub_dir, qsub_filename


def get_module_load_list(module_name_list):
    module_list = []
    for module in module_name_list:
        module_load = "module load " + module
        module_list.append(module_load)
    return module_list


def qsub_file(basedir, process_name, module_name_list, filename, process_string):
    working_dir = os.getcwd()
    qsub_dir, qsub_filename = get_qsub_filename(
        basedir, process_name, filename)
    os.chdir(qsub_dir)
    module_load = get_module_load_list(module_name_list)
# directive to use Laconia
# #PBS -l feature=intel16
#export MKL_NUM_THREADS=8
#export OMP_NUM_THREADS=8
    f = """#!/bin/bash
#PBS -l walltime=4:00:00,nodes=1:ppn=8
#PBS -l mem=32gb
#PBS -l feature=intel16
#PBS -j oe
#export MKL_NUM_THREADS=8
#export OMP_NUM_THREADS=8
cd ${{PBS_O_WORKDIR}}
""".format()
    with open(qsub_filename, "w") as qsub:
        qsub.write(f)
        for module_string in module_load:
            qsub.write(module_string + "\n")
            # print(module_string)
        for string in process_string:
            qsub.write(string + "\n")
            print(string)
        qsub.write("qstat -f ${PBS_JOBID}\n")
        qsub.write(
            "cat ${PBS_NODEFILE} # Output Contents of the PBS NODEFILE\n")
        qsub.write(
            "env | grep PBS # Print out values of the current jobs PBS environment variables\n")
    qsub_string = 'qsub -V ' + qsub_filename
    print(qsub_string)
    s = subprocess.Popen(qsub_string, shell=True)
    s.wait()
    os.chdir(working_dir)
