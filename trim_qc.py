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

# 1. Get data from spreadsheet


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

# run trimmomatic


def run_trimmomatic_TruSeq(missing, trimmed, remaining, trimdir, file1, file2, sra):
	bash_filename=trimdir+sra+".trim.TruSeq.sh"
	clusterfunc.check_dir(trimdir+"qsub_files/")
	listoffile = os.listdir(trimdir+"qsub_files/")
	# print listoffile
	trim_file = trimdir+"qsub_files/""trim."+sra+".log"
	# print trim_file
	matching = [s for s in listoffile if "trim."+sra+".log" in s]
	matching_string = "TrimmomaticPE: Completed successfully"
	if os.path.isfile(trim_file):
		with open(trim_file) as f:
    			content = f.readlines()
	if len(matching)!=0:
		trim_complete = [m for m in content if matching_string in m]
		if len(trim_complete)!=0:
			print "Already trimmed:",matching
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
    # if os.path.isfile(trimdir+"orphans.fq.gz"):
	# if os.stat(trimdir+"orphans.fq.gz").st_size != 0:
	#	print "orphans file exists:",trimdir+"orphans.fq.gz"
    	# else:
	#	print "orphans file exists but is empty:",trimdir+"orphans.fq.gz"
    # else:
    	file1 = trimdir+"qsub_files/"+sra+".trim_1U.fq"
	file2 = trimdir+"qsub_files/"+sra+".trim_2U.fq"
	orphanlist=file1 + " " + file2
    	orphan_string="gzip -9c "+orphanlist+" > "+trimdir+"orphans.fq.gz"
    	#print orphan_string
    	# s=subprocess.Popen(orphan_string,shell=True)
    	# s.wait()
	return orphan_string

def move_files(trimdir,sra):
	tmp_trimdir = trimdir + "qsub_files/"
	file1 = tmp_trimdir+sra+".trim_1P.fq"
	file2 = tmp_trimdir+sra+".trim_2P.fq"
	print file1
	print file2
	if os.path.isfile(file1):
		if os.path.isfile(file2):
			mv_string1 = "cp "+file1+" "+trimdir
			mv_string2 = "cp "+file2+" "+trimdir
			# s=subprocess.Popen(mv_string1,shell=True)
        		# s.wait()
			# t=subprocess.Popen(mv_string2,shell=True)
        		# t.wait()
	# if os.path.isfile(trimdir+sra+".trim_1P.fq"):
	#	if os.path.isfile(trimdir+sra+".trim_2P.fq"):
	#		print "Files all here:",os.listdir(trimdir)
	return mv_string1,mv_string2

def run_move_files(trimdir,sra):
	orphan_string=make_orphans(trimdir,sra)
        mv_string1,mv_string2 = move_files(trimdir,sra)
	commands = [orphan_string,mv_string1,mv_string2]
        process_name="move"
        module_name_list=""
        filename=sra
        #clusterfunc.qsub_file(trimdir,process_name,module_name_list,filename,commands)	

def check_files(trimdir,sra):
	file1 = trimdir+sra+".trim_1P.fq"
	file2 = trimdir+sra+".trim_2P.fq"
	if os.path.isfile(file1):
        	if os.path.isfile(file2):
                       	print "Files all here:",os.listdir(trimdir)
		else:
			print "Still waiting:",trimdir

def execute(url_data,datadir):
    missing = []
    trimmed = []
    remaining = []
    for item in url_data.keys():
	organism=item[0].replace("'","")
	org_seq_dir=datadir+organism+"/"
	url_list=url=url_data[item]
	for url in url_list:
		sra=basename(urlparse(url).path)
		newdir=org_seq_dir+sra+"/"
		trimdir=newdir+"trim/"
		interleavedir=newdir+"interleave/"
		clusterfunc.check_dir(trimdir)
		clusterfunc.check_dir(interleavedir)
		file1=newdir+sra+"_1.fastq"
		file2=newdir+sra+"_2.fastq"
		#if os.path.isfile(file1) and os.path.isfile(file2):
		#	print file1
		#	print file2
		missing,trimmed,remaining= run_trimmomatic_TruSeq(missing,trimmed,remaining,trimdir,file1,file2,sra)
		#run_move_files(trimdir,sra)
		# check_files(trimdir,sra)
		# else:
		#	print "Files do not exist:",file1,file2 	
    print "Missing trimmed:",len(missing)
    print missing
    print "Trimmed:",len(trimmed)
    print "remaining:",len(remaining)
    print remaining

datafile="SraRunInfo.csv"
datadir="/mnt/scratch/ljcohen/mmetsp/"
url_data=get_data(datafile)
print url_data
execute(url_data,datadir)
