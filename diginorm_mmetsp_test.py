import os
import os.path
from os.path import basename
from urllib.parse import urlparse
import subprocess
from subprocess import Popen, PIPE
import glob
# import configuration variables
import dibMMETSP_configuration as dib_conf
# custom Lisa module
import clusterfunc

def interleave_reads(trimdir, sra, interleavedir):
    interleavefile = interleavedir + sra + ".trimmed.interleaved.fq"
    print(interleavedir)
    if os.path.isfile(interleavefile):
        print("already interleaved")
    else:
        interleave_string = "interleave-reads.py " + trimdir + sra + \
            ".trim_1P.fq " + trimdir + sra + ".trim_2P.fq > " + interleavefile
        print(interleave_string)
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
    print("combinding orphans now...")
    with open("combine_orphaned.sh", "w") as combinedfile:
        combinedfile.write(j)
    #s=subprocess.Popen("cat combine_orphaned.sh",shell=True)
    # s.wait()
    print("Combining *.se orphans now...")
    #s = subprocess.Popen("sudo bash combine_orphaned.sh", shell=True)
    #s.wait()
    print("Orphans combined.")
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
    print("renaming pe files now...")
    #s = subprocess.Popen("sudo bash rename.sh", shell=True)
    #s.wait()
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
            clusterfunc.check_dir(interleavedir)
            trimdir = newdir + "trim/"
            interleave_reads(trimdir,SRA,interleavedir)
            run_diginorm(diginormdir,interleavedir,trimdir,SRA)
            run_filter_abund(diginormdir, SRA)
