# Configuration file for the running of MMETSP assembly pipeline
# Simplicity at its best, my friends: http://stackoverflow.com/questions/8225954/python-configuration-file-any-file-format-recommendation-ini-format-still-appr

# Base directory where scripts are run and files will be stored
#base_dir = '/mnt/home/ljcohen/'
base_dir = '/Users/cohenl06/Documents/UCDavis/dib/MMETSP/test/'
# CSV file containing the MMETSP ids and SRA ids for the samples you want to run
sra_csv = 'SraRunInfo.csv'

# Assembly script to be run
assembly_version = 'assembly_trinity_test.py'

# Directory where scripts will be written within base_dir
scripts_dir = '/Users/cohenl06/Documents/UCDavis/dib/MMETSP/dib-MMETSP'

# Directory where final output will be stored within base_dir
output_dir = '/Users/cohenl06/Documents/UCDavis/dib/MMETSP/test/assembly_trinity_2.2.0/'

# Extension added to the end of the output files
output_extension = '.trinity_out_2.2.0'

# Extension for Trinity
output_trinity_extension = '.Trinity.fasta'
# Directory where intermediate files will be stored
#data_dir = '/mnt/scratch/ljcohen/mmetsp/'
data_dir = '/Users/cohenl06/Documents/UCDavis/dib/MMETSP/test_temp/'
