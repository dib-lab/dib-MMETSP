import os
import os.path
from os.path import basename
import subprocess
from urllib.parse import urlparse
from subprocess import Popen, PIPE
# import configuration variables
import dibMMETSP_configuration as dib_conf
# custom Lisa module
import clusterfunc

# run trimmomatic

def run_trimmomatic_TruSeq(missing, trimmed, remaining, trimdir, file1, file2, sra):
    bash_filename=trimdir+sra+".trim.TruSeq.sh"
    clusterfunc.check_dir(trimdir+"qsub_files/")
    listoffile = os.listdir(trimdir+"qsub_files/")
	# print listoffile
    trim_file = trimdir+"qsub_files/"+"trim."+sra+".log"
	# print trim_file
    matching = [s for s in listoffile if "trim."+sra+".log" in s]
    matching_string = "TrimmomaticPE: Completed successfully"
    if os.path.isfile(trim_file):
        with open(trim_file) as f:
            content = f.readlines()
    if len(matching)!=0:
        trim_complete = [m for m in content if matching_string in m]
        if len(trim_complete)!=0:
            print("Already trimmed:",matching)
            trimmed.append(sra)
        else:
            missing.append(trimdir)
            j="""
java -jar /mnt/home/ljcohen/bin/Trimmomatic-0.33/trimmomatic-0.33.jar PE \\
-baseout {}.trim.fq \\
{} {} \\
ILLUMINACLIP:/mnt/home/ljcohen/bin/Trimmomatic-0.33/adapters/combined.fa:2:40:15 \\
SLIDINGWINDOW:4:2 \\
LEADING:2 \\
TRAILING:2 \\
MINLEN:25 &> trim.{}.log
""".format(sra,file1,file2,sra)
            orphan_string=make_orphans(trimdir,sra)
            commands = [j,orphan_string]
            process_name="trim"
            module_name_list=""
            filename=sra
            clusterfunc.qsub_file(trimdir,process_name,module_name_list,filename,commands)
    else:
        remaining.append(trimdir)
        j="""
java -jar /mnt/home/ljcohen/bin/Trimmomatic-0.33/trimmomatic-0.33.jar PE \\
-baseout {}.trim.fq \\
{} {} \\
ILLUMINACLIP:/mnt/home/ljcohen/bin/Trimmomatic-0.33/adapters/combined.fa:2:40:15 \\
SLIDINGWINDOW:4:2 \\
LEADING:2 \\
TRAILING:2 \\
MINLEN:25 &> trim.{}.log
""".format(sra,file1,file2,sra)
        orphan_string=make_orphans(trimdir,sra)
        commands = [j,orphan_string]
        process_name="trim"
        module_name_list=""
        filename=sra
        clusterfunc.qsub_file(trimdir,process_name,module_name_list,filename,commands)
    return missing,trimmed,remaining

def make_orphans(trimdir,sra):
    file1 = trimdir+"qsub_files/"+sra+".trim_1U.fq"
    file2 = trimdir+"qsub_files/"+sra+".trim_2U.fq"
    orphanlist=file1 + " " + file2
    orphan_string="gzip -9c "+orphanlist+" > "+trimdir+"orphans.fq.gz"
    return orphan_string

def move_files(trimdir,sra):
	tmp_trimdir = trimdir + "qsub_files/"
	file1 = tmp_trimdir+sra+".trim_1P.fq"
	file2 = tmp_trimdir+sra+".trim_2P.fq"
	print(file1)
	print(file2)
	if os.path.isfile(file1):
		if os.path.isfile(file2):
			mv_string1 = "cp "+file1+" "+trimdir
			mv_string2 = "cp "+file2+" "+trimdir
	return mv_string1,mv_string2

def run_move_files(trimdir,sra):
	orphan_string=make_orphans(trimdir,sra)
	mv_string1,mv_string2 = move_files(trimdir,sra)
	commands = [orphan_string,mv_string1,mv_string2]
	process_name = "move"
	module_name_list= ""
	filename=sra
    #clusterfunc.qsub_file(trimdir,process_name,module_name_list,filename,commands)

def check_files(trimdir,sra):
    file1 = trimdir+sra+".trim_1P.fq"
    file2 = trimdir+sra+".trim_2P.fq"
    if os.path.isfile(file1):
        if os.path.isfile(file2):
            print("Files all here:",os.listdir(trimdir))
    else:
        print("Still waiting:",trimdir)

def execute(url_data,datadir):
    missing = []
    trimmed = []
    remaining = []
    for item in url_data.keys():
        organism=item[0].replace("'","")
        org_seq_dir=datadir+organism+"/"
        clusterfunc.check_dir(org_seq_dir)
        url_list=url=url_data[item]
    for url in url_list:
        sra=basename(urlparse(url).path)
        newdir=org_seq_dir+sra+"/"
        clusterfunc.check_dir(newdir)
        trimdir=newdir+"trim/"
        interleavedir=newdir+"interleave/"
        clusterfunc.check_dir(trimdir)
        clusterfunc.check_dir(interleavedir)
        file1=newdir+sra+"_1.fastq"
        file2=newdir+sra+"_2.fastq"
        missing,trimmed,remaining= run_trimmomatic_TruSeq(missing,trimmed,remaining,trimdir,file1,file2,sra)
    print("Missing trimmed:",len(missing))
    print(missing)
    print("Trimmed:",len(trimmed))
    print("remaining:",len(remaining))
    print(remaining)
