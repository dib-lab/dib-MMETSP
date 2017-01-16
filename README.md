# dib-MMETSP
This is the pipeline code used to generate re-assemblies of the Marine Microbial Eukaryote Transcriptome Sequencing Project (MMETSP).
Originally https://github.com/ljcohen/MMETSP

Instructions

1. Clone this repo 

```
git clone https://github.com/dib-lab/dib-MMETSP.git
```

2. edit `dibMMETSP_configuration.py` with absolute path names specific to your system. The file `SraRunInfo.csv` was obtained from NCBI for NCBI Bioproject accession: [PRJNA231566](http://www.ncbi.nlm.nih.gov/bioproject/PRJNA231566/). This set of code could be used with `SraRunInfo.csv` input from any collection of SRA records from NCBI or ENA. 

3. Run the main python function

```
python main.py
```

This pipeline was constructed to authomate the khmer protocols over a large-scale RNAseq data set:

https://khmer-protocols.readthedocs.org/en/ctb/mrnaseq/

The Marine Microbial Eukaryotic Transcriptome Sequencing Project (MMETSP) data set contains 678 cultured samples of 306 pelagic and endosymbiotic marine eukaryotic species representing more than 40 phyla (Keeling et al. 2014).

The main pipeline scripts in this repository:

<ol type="a">
  <li>`getdata.py`, download data from NCBI and organize into individual directories for each sample/accession ID</li>
  <li>`trim_qc.py`, trim reads for quality, interleave reads</li>
  <li>`diginorm_mmetsp.py`, normalize-by-median and filter-abund from khmer, rename, combined orphans</li>
  <li>`assembly.py`, runs Trinity de novo transcriptome assembly software</li>
</ol>

![](mmetsp_pipeline1.png)

Annotation and expression counts (run separately):

* `dammit.py`, annotation https://github.com/camillescott/dammit/tree/master/dammit
* `salmon.py`, runs salmon reference-free transcript quantification https://github.com/COMBINE-lab/salmon


Additional scripts (run separately):

* `rapclust.py`, clustering contigs https://github.com/COMBINE-lab/rapclust
* `busco.py`, assessing assembly and annotation completeness with single-copy orthologs http://busco.ezlab.org/
* `clusterfunc.py`, cluster control module
* `sourmash.py`, MinHash signatures to cluster unassembled reads https://github.com/dib-lab/sourmash/tree/v0.9.4
* `transdecoder.py`, translate nucleotide contigs to amino acid contigs http://transdecoder.github.io/
* `transrate.py`, evaluate assembly with reads http://hibberdlab.com/transrate/
* `transrate_reference.py`, evaluate assembly with reference assembly http://hibberdlab.com/transrate/

References:

Keeling et al. 2014: http://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.1001889

Supporting information with methods description:
http://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.1001889#s6

Preliminary assembly protocol run by NCGR:
https://github.com/ncgr/rbpa

MMETSP website: http://marinemicroeukaryotes.org/

iMicrobe project with data and combined assembly downloads: ftp://ftp.imicrobe.us/projects/104/
