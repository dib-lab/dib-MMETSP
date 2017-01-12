import os
import os.path
from os.path import basename
import subprocess
from subprocess import Popen, PIPE
# import configuration variables
import dibMMETSP_configuration as dib_conf
# custom Lisa module
import clusterfunc

def get_data(thefile):
    count = 0
    url_data = {}
    with open(thefile, "rU") as inputfile:
        headerline = next(inputfile).split(',')
        position_name = headerline.index("ScientificName")
        position_reads = headerline.index("Run")
        position_ftp = headerline.index("download_path")
        for line in inputfile:
            line_data = line.split(',')
            name = "_".join(line_data[position_name].split())
            read_type = line_data[position_reads]
            ftp = line_data[position_ftp]
            name_read_tuple = (name, read_type)
            print(name_read_tuple)
            # check to see if Scientific Name and run exist
            if name_read_tuple in url_data.keys():
                # check to see if ftp exists
                if ftp in url_data[name_read_tuple]:
                    print("url already exists:", ftp)
                else:
                    url_data[name_read_tuple].append(ftp)
            else:
                url_data[name_read_tuple] = [ftp]
        return url_data

def combine_orphans(diginormdir):
    diginorm_files_dir = diginormdir + "qsub_files/"
    rename_orphans = """
gzip -9c {}orphans.fq.gz.keep.abundfilt > {}orphans.keep.abundfilt.fq.gz
for file in {}*.se
do
        gzip -9c ${{file}} >> {}orphans.keep.abundfilt.fq.gz
done
""".format(diginorm_files_dir, diginormdir, diginorm_files_dir, diginormdir)
    return rename_orphans

def rename_files(trinitydir, diginormdir, diginormfile, SRA):
    # takes diginormfile in,splits reads and put into newdir
    rename_orphans = combine_orphans(diginormdir)
    split_paired = "split-paired-reads.py -d " + diginormdir + " " + diginormfile
    rename_string1 = "cat " + diginormdir + "*.1 > " + trinitydir + SRA + ".left.fq"
    rename_string2 = "cat " + diginormdir + \
        "*.2 > " + trinitydir + SRA + ".right.fq"
    rename_string3 = "gunzip -c " + diginormdir + \
        "orphans.keep.abundfilt.fq.gz >> " + trinitydir + SRA + ".left.fq"
    commands = [rename_orphans, split_paired,
                rename_string1, rename_string2, rename_string3]
    process_name = "rename"
    module_name_list = ["GNU/4.8.3", "khmer/2.0"]
    filename = SRA
    # clusterfunc.qsub_file(diginormdir,process_name,module_name_list,filename,commands)


def run_trinity(trinitydir,left,right,mmetsp,output_dir, file_extension):
    trinity_command = """
set -x
# stops execution if there is an error
set -e

Trinity --left {} \\
--right {} --output /tmp/{}{} --full_cleanup --seqType fq --max_memory 20G --CPU 16

cp /tmp/{}*.fasta {}
rm -rf /tmp/{}*
""".format(left, right, mmetsp, file_extension, mmetsp, output_dir, mmetsp)
    commands = [trinity_command]
    process_name = "trinity_2.2.0"
    module_name_list = ["trinity/2.2.0"]
    filename = mmetsp
    clusterfunc.qsub_file(trinitydir, process_name,
                          module_name_list, filename, commands)

def execute(trinity_fail, count, data_dir):
    id_list = os.listdir(data_dir)
    for mmetsp in id_list:
        print(mmetsp)
        if mmetsp.startswith("MMETSP"):
            mmetspdir = data_dir + mmetsp + "/"
            trinitydir = data_dir + mmetsp + "/" + "trinity/"
            trinity_files = os.listdir(mmetspdir)
            trinity_fasta=trinitydir + dib_conf.output_extension
            clusterfunc.check_dir(trinitydir)
            if os.path.isfile(trinity_fasta) == False:
                if os.path.isfile(dib_conf.output_dir + mmetsp + dib_conf.output_extension):
                    print("Trinity finished.")
                    count += 1
                else:
                    print(mmetspdir)
                    right = mmetspdir + mmetsp + ".right.fq"
                    left = mmetspdir + mmetsp + ".left.fq"
                    run_trinity(trinitydir, left, right, mmetsp, dib_conf.output_dir, dib_conf.output_extension)
            else:
                print("Trinity completed successfully.", trinity_fasta)
                count += 1
                assemblydir = dib_conf.output_dir
    print("Number of Trinity de novo transcriptome assemblies:", count)
    print("Number of times Trinity failed:", len(trinity_fail), trinity_fail)
    return trinity_fail, count
