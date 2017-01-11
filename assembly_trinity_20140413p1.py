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


def run_trinity(trinitydir, SRA):
    trinity_command = """
set -x
# stops execution if there is an error
set -e
if [ -f {}trinity_out/Trinity.fasta ]; then exit 0 ; fi
#if [ -d {}trinity_out ]; then mv {}trinity_out_dir {}trinity_out_dir0 || true ; fi

Trinity --left {}{}.left.fq \\
--right {}{}.right.fq --output {}trinity_out --seqType fq --JM 20G --CPU 16

""".format(trinitydir, trinitydir, trinitydir, trinitydir, trinitydir, SRA, trinitydir, SRA, trinitydir)
    commands = [trinity_command]
    process_name = "trinity"
    module_name_list = ["trinity/20140413p1"]
    filename = SRA
    clusterfunc.qsub_file(trinitydir, process_name,
                          module_name_list, filename, commands)


def check_trinity(seqdir, SRA, count):
    trinity_dir = seqdir + "trinity/"
    trinity_file = trinity_dir + "trinity_out/Trinity.fasta"
    if os.path.isfile(trinity_file) == False:
        if os.path.isdir(trinity_dir) == False:
            print "Still need to run.", trinity_dir
            run_trinity(trinity_dir, SRA)
            count += 1
        else:
            print "Incomplete:", trinity_dir
            run_trinity(trinity_dir, SRA)
            count += 1
    return count


def fix_fasta(trinity_fasta, trinity_dir, sample):
    os.chdir(trinity_dir)
    trinity_out = trinity_dir + sample + ".Trinity.fixed.fasta"
    fix = """
sed 's_|_-_g' {} > {}
""".format(trinity_fasta, trinity_out)
    s = subprocess.Popen(fix, shell=True)
    print fix
    s.wait()
    os.chdir("/mnt/home/ljcohen/MMETSP/")
    return trinity_out


def execute(trinity_fail, count, basedir, url_data):
    for item in url_data.keys():
        # Directory will be located according to organism and read type (single
        # or paired)
        organism = item[0]
        seqtype = item[1]
        org_seq_dir = basedir + organism + "/"
        # from here, split paired reads
        # then go do assembly
        # clusterfunc.check_dir(org_seq_dir)
        url_list = url_data[item]
        for url in url_list:
            SRA = basename(urlparse(url).path)
            sample = organism + "_" + SRA
            newdir = org_seq_dir + SRA + "/"
            diginormdir = newdir + "diginorm/"
            diginormfile = diginormdir + "qsub_files/" + SRA + \
                ".trimmed.interleaved.fq.keep.abundfilt.pe"
            trinitydir = newdir + "trinity/"
            # trinity_fasta=trinitydir+"trinity_out/"+"Trinity.fasta"
            # 648 assemblies
            # trinity_fasta=trinitydir+SRA+".Trinity.fasta"
            # 596 assemblies
            # 656 assemblies
            trinity_fasta = trinitydir + sample + ".Trinity.fixed.fasta"
            # clusterfunc.check_dir(trinitydir)
            if os.path.isfile(trinity_fasta) == False:
                # if os.path.isfile(diginormfile):
                # print "file exists:",diginormfile
                # rename_files(trinitydir,diginormdir,diginormfile,SRA)
                # run_trinity(trinitydir,SRA)
                print "Trinity failed:", trinity_fasta
                trinity_fail.append(newdir)
            else:
                print "Trinity completed successfully.", trinity_fasta
                count += 1
                assemblydir = "/mnt/scratch/ljcohen/mmetsp_assemblies/"
                copy_string = "cp " + trinity_fasta + " " + assemblydir
                print copy_string
                s = subprocess.Popen(copy_string, shell=True)
                s.wait()
                # trinity_out=fix_fasta(trinity_fasta,trinitydir,sample)
                # print "Needs to be fixed:",trinity_fasta
                # print trinity_out
                #"Re-run diginorm:",diginormfile
            #count = check_trinity(newdir,SRA,count)
    print "This is the number of Trinity de novo transcriptome assemblies:"
    print count
    print "This is the number of times Trinity failed:"
    print len(trinity_fail)
    print trinity_fail
    return trinity_fail, count

basedir = "/mnt/scratch/ljcohen/mmetsp/"

datafiles = ["SraRunInfo.csv"]
# datafiles=["MMETSP_SRA_Run_Info_subset_msu1.csv","MMETSP_SRA_Run_Info_subset_msu2.csv","MMETSP_SRA_Run_Info_subset_msu3.csv","MMETSP_SRA_Run_Info_subset_msu4.csv",
#        "MMETSP_SRA_Run_Info_subset_msu5.csv","MMETSP_SRA_Run_Info_subset_msu6.csv","MMETSP_SRA_Run_Info_subset_msu7.csv"]
trinity_fail = []
count = 0
for datafile in datafiles:
    url_data = get_data(datafile)
    trinity_fail, count = execute(trinity_fail, count, basedir, url_data)
print "Number of Trinity assemblies:"
print count
print "Total number of times Trinity failed:"
print len(trinity_fail)
print trinity_fail

# for dirname in trinity_fail:
#	SRA=dirname.split("/")[6]
#	genus_species=dirname.split("/")[5]
#	sample=genus_species+"_"+SRA
#	trinitydir=dirname+"trinity/"
#	trinity_out_dir=trinitydir+"trinity_out/"
#	print trinitydir
#	#clusterfunc.check_dir(trinitydir)
#	run_trinity(trinitydir,SRA)
# trinity_fasta = trinitydir+
#	trinity_fasta = trinity_out_dir+"Trinity.fasta"
#	if os.path.isfile(trinity_fasta):
#		print "file exists:",trinity_fasta
#		new_trinity_fasta=fix_fasta(trinity_fasta,trinitydir,sample)
#		print "New file created:",new_trinity_fasta
#	else:
#		print "Still failed:",trinity_out_dir
