import os
import os.path
from os.path import basename
from urllib.parse import urlparse
import subprocess
import glob
from subprocess import Popen, PIPE
# import configuration variables
import dibMMETSP_configuration as dib_conf
# custom Lisa module
import clusterfunc

def get_data_dict(thefile):
    count = 0
    mmetsp_data = {}
    with open(thefile, "rU") as inputfile:
        headerline = next(inputfile).split(',')
        # print headerline
        position_reads = headerline.index("Run")
        position_mmetsp = headerline.index("SampleName")
        position_ftp = headerline.index("download_path")
        for line in inputfile:
            line_data = line.split(',')
            read_type = line_data[position_reads]
            ftp = line_data[position_ftp]
            mmetsp = line_data[position_mmetsp]
            test_mmetsp = mmetsp.split("_")
            if len(test_mmetsp) > 1:
                mmetsp = test_mmetsp[0]
            name_read_tuple = (mmetsp,read_type)
            if name_read_tuple in mmetsp_data.keys():
                if mmetsp in mmetsp_data[name_read_tuple]:
                    print("url already exists:", ftp)
                else:
                    mmetsp_data[name_read_tuple].append(ftp)
            else:
                mmetsp_data[name_read_tuple] = [ftp]
        return mmetsp_data

def get_data_dict_old(thefile):
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

# 2. Download data

def download(url, newdir, newfile):
    filestring = newdir + newfile
    if os.path.isfile(filestring):
        print("file exists:", filestring)
    else:
        urlstring = "wget -O " + newdir + newfile + " " + url
        print(urlstring)
    #s = subprocess.Popen(urlstring, shell=True)
    #s.wait()
    print("Finished downloading from NCBI.")

# 3. Extract with fastq-dump (sratools)


def sra_extract(newdir, filename):
    # if seqtype=="single":
    #    sra_string="fastq-dump -v "+newdir+file
    #    print sra_string
    # elif seqtype=="paired":
        # check whether .fastq exists in directory
    if glob.glob(newdir + "*.fastq"):
        print("SRA has already been extracted", filename)
    else:
        sra_string = "fastq-dump -v -O " + newdir + " --split-3 " + newdir + filename
        print(sra_string)
        print("extracting SRA...")
        #s = subprocess.Popen(sra_string, shell=True, stdout=PIPE)
        #s.wait()
        print("Finished SRA extraction.")


def execute(basedir, url_data):
    for item in url_data:
        # Creates directory for each file to be downloaded
        # Directory will be located according to organism and read type (single
        # or paired)
        mmetsp = item[0]
        org_seq_dir = basedir + mmetsp + "/"
        print(org_seq_dir)
        clusterfunc.check_dir(org_seq_dir)
        sra = item[1]
        url_list = url_data[item]
        for url in url_list:
            print(url)
            filename = basename(urlparse(url).path)
            print(filename)
            newdir = org_seq_dir + filename + "/"
            full_filename = newdir + filename
            clusterfunc.check_dir(newdir)
            fastqcdir = newdir + "fastqc/"
            clusterfunc.check_dir(fastqcdir)
            # check to see if filename exists in newdir
            if filename in os.listdir(newdir):
                print("sra exists:", filename)
                if os.stat(full_filename).st_size == 0:
                    print("SRA file is empty:", filename)
                    os.remove(full_filename)
            else:
                print("file will be downloaded:", filename)
                download(url, newdir, filename)
            sra_extract(newdir, filename)
