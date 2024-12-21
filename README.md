# MetaKraken pipeline created for the 2024 Clinical Genomics P&S at ETHZ

* Uses the Projects [MetaTrinity](https://github.com/CMU-SAFARI/MetaTrinity) and [kraken2](https://github.com/DerrickWood/kraken2) to increase speed of metagenomic analysis.
* Tested with 50GB db built with fna files obtained from [Metalign's](https://github.com/nlapier2/Metalign) setup\_db.py script.
* Tested with SRR2584863.fastq file obtained from [NCBI](https://trace.ncbi.nlm.nih.gov/Traces/?view=run_browser&acc=SRR2584863&display=metadata).

Easiest way to run this project is using Anaconda, most of those packages are obtained from the bioconda channel. Also you need to clone the MetaTrinity and Metalign repositories (by default the scripts assume that the repositories are cloned inside the current working directory).

```
conda install -c conda-forge -c biopython kmc CMash minimap2 kraken2
```

Download the desired fna files for comparison into a folder inside your database named "organism_files".
After this setup the kraken2 database from those files using those commands from outside the databse folder (replacing $DBNAME with your desired database name):

```
kraken2-build --download-taxonomy --db $DBNAME
find $DBNAME/organism_files/ -name '*.fna.gz' -print0 | xargs -0 -I{} -n1 kraken2-build --add-to-library {} --db $DBNAME
kraken2-build --build --db $DBNAME
```

After this you should be able to use the run_kraken and run_metalign scripts for comparison.
