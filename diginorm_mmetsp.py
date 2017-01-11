import os
import os.path
from os.path import basename
from urllib import urlopen
from urlparse import urlparse
import subprocess
from subprocess import Popen, PIPE
import urllib
import shutil
import glob
# custom Lisa module
import clusterfunc


def get_data(thefile):
    count = 0
    url_data = {}
    with open(thefile, "rU") as inputfile:
        headerline = next(inputfile).split(',')
        # print headerline
        position_name = headerline.index("ScientificName")
        position_reads = headerline.index("Run")
        position_ftp = headerline.index("download_path")
        for line in inputfile:
            line_data = line.split(',')
            name = "_".join(line_data[position_name].split())
            read_type = line_data[position_reads]
            ftp = line_data[position_ftp]
            name_read_tuple = (name, read_type)
            print name_read_tuple
            # check to see if Scientific Name and run exist
            if name_read_tuple in url_data.keys():
                # check to see if ftp exists
                if ftp in url_data[name_read_tuple]:
                    print "url already exists:", ftp
                else:
                    url_data[name_read_tuple].append(ftp)
            else:
                url_data[name_read_tuple] = [ftp]
        return url_data


def interleave_reads(trimdir, sra, interleavedir):
    interleavefile = interleavedir + sra + ".trimmed.interleaved.fq"
    if os.path.isfile(interleavefile):
        print "already interleaved"
    else:
        interleave_string = "interleave-reads.py " + trimdir + sra + \
            ".trim_1P.fq " + trimdir + sra + ".trim_2P.fq > " + interleavefile
        print interleave_string
        interleave_command = [interleave_string]
        process_name = "interleave"
        module_name_list = ["GNU/4.8.3", "khmer/2.0"]
        filename = sra
        clusterfunc.qsub_file(interleavedir, process_name,
                              module_name_list, filename, interleave_command)


def run_filter_abund(diginormdir, sra):
    keep_dir = diginormdir + "qsub_files/"
    filter_string = """
filter-abund.py -V -Z 18 {}norm.C20k20.ct {}*.keep
""".format(diginormdir, keep_dir)
    extract_paired_string = extract_paired()
    commands = [filter_string, extract_paired_string]
    process_name = "filtabund"
    module_name_list = ["GNU/4.8.3", "khmer/2.0"]
    filename = sra
    clusterfunc.qsub_file(diginormdir, process_name,
                          module_name_list, filename, commands)

def run_streaming_diginorm(trimdir, SRA, diginormdir):
    # from Jessica's streaming protocol:
    diginormfile = diginormdir + SRA + ".stream.diginorm.sh"
    # os.chdir(diginormdir)
    stream_string = """#!/bin/bash
(interleave-reads.py {}{}.trim_1P.fq {}{}.trim_2P.fq && zcat {}orphans.fq.gz)| \\
(trim-low-abund.py -V -k 20 -Z 18 -C 2 - -o - -M 4e9 --diginorm --diginorm-coverage=20) | \\
(extract-paired-reads.py --gzip -p {}{}.paired.gz -s {}{}.single.gz) > /dev/null
""".format(trimdir, SRA, trimdir, SRA, trimdir, diginormdir, SRA, diginormdir, SRA)
    print stream_string
    # with open(diginormfile,"w") as diginorm_script:
    #	diginorm_script.write(stream_string)
    #s=subprocess.Popen("sudo bash "+diginormfile,shell=True)
    # s.wait()
    # print "file written:",diginormfile
    # os.chdir("/home/ubuntu/MMETSP/")
    streaming_diginorm_command = [stream_string]
    module_load_list = []
    process_name = "diginorm_stream"
    clusterfunc.qsub_file(diginormdir, process_name,
                          module_load_list, SRA, streaming_diginorm_command)

def extract_paired():
    extract_paired_string = """
for file in *.abundfilt
do
	extract-paired-reads.py ${{file}}
done
""".format()
    return extract_paired_string

def run_diginorm(diginormdir, interleavedir, trimdir, sra):
    normalize_median_string = """
normalize-by-median.py -p -k 20 -C 20 -M 4e9 \\
--savegraph {}norm.C20k20.ct \\
-u {}orphans.fq.gz \\
{}*.fq
""".format(diginormdir, trimdir, interleavedir)
    #s=subprocess.Popen("cat diginorm.sh",shell=True)
    # s.wait()
    normalize_median_command = [normalize_median_string]
    process_name = "diginorm"
    module_name_list = ["GNU/4.8.3", "khmer/2.0"]
    filename = sra
    clusterfunc.qsub_file(diginormdir, process_name,
                          module_name_list, filename, normalize_median_command)


def combine_orphaned(diginormdir):
    # if glob.glob(diginormdir+"orphans.keep.abundfilt.fq.gz"):
    #		print "orphan reads already combined"
    #	else:
    j = """
gzip -9c {}orphans.fq.gz.keep.abundfilt > {}orphans.keep.abundfilt.fq.gz
for file in {}*.se
do
	gzip -9c ${{file}} >> orphans.keep.abundfilt.fq.gz
done
""".format(diginormdir, diginormdir, diginormdir, diginormdir)
    os.chdir(diginormdir)
    print "combinding orphans now..."
    with open("combine_orphaned.sh", "w") as combinedfile:
        combinedfile.write(j)
    #s=subprocess.Popen("cat combine_orphaned.sh",shell=True)
    # s.wait()
    print "Combining *.se orphans now..."
    s = subprocess.Popen("sudo bash combine_orphaned.sh", shell=True)
    s.wait()
    print "Orphans combined."
    os.chdir("/home/ubuntu/MMETSP/")


def rename_pe(diginormdir):
    j = """
for file in {}*trimmed.interleaved.fq.keep.abundfilt.pe
do
	newfile=${{file%%.fq.keep.abundfilt.pe}}.keep.abundfilt.fq
	mv ${{file}} ${{newfile}}
	gzip ${{newfile}}
done
""".format(diginormdir)
    os.chdir(diginormdir)
    with open("rename.sh", "w") as renamefile:
        renamefile.write(j)
    #s=subprocess.Popen("cat rename.sh",shell=True)
    # s.wait()
    print "renaming pe files now..."
    s = subprocess.Popen("sudo bash rename.sh", shell=True)
    s.wait()
    os.chdir("/home/ubuntu/MMETSP/")


def execute(basedir, url_data):
    for item in url_data.keys():
        organism = item[0]
        seqtype = item[1]
        org_seq_dir = basedir + organism + "/"
        clusterfunc.check_dir(org_seq_dir)
        url_list = url_data[item]
        for url in url_list:
            SRA = basename(urlparse(url).path)
            newdir = org_seq_dir + SRA + "/"
            interleavedir = newdir + "interleave/"
            diginormdir = newdir + "diginorm/"
            clusterfunc.check_dir(diginormdir)
            trimdir = newdir + "trim/"
            # run_streaming_diginorm(trimdir,SRA,diginormdir)
            # interleave_reads(trimdir,SRA,interleavedir)
            # run_diginorm(diginormdir,interleavedir,trimdir,SRA)
            run_filter_abund(diginormdir, SRA)

basedir = "/mnt/scratch/ljcohen/mmetsp/"
datafile = "MMETSP_SRA_Run_Info_subset_msu7.csv"
url_data = get_data(datafile)
execute(basedir, url_data)
