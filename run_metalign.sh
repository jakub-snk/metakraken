#!/bin/bash

if [ "$#" -ne 2 ]; then
  echo "Usage $0 <reads> <data>"
  exit 1
fi

cmashBaseName="cmash_db_n1000_k60"
cmashDatabase="${cmashBaseName}.h5"
cmashDump="${cmashBaseName}_dump.fa"
prefilterName="cmash_db_n1000_k60_30-60-10.bf"
trainingFiles="training_files.txt"
numThreads=16

READS=$1
DB_DIR=$2

cd "$DB_DIR" || exit 1

rm db_info.txt 2> /dev/null
rm headers.txt 2> /dev/null
rm trainingFiles.txt 2> /dev/null
rm metalign_out.csv 2> /dev/null
rm -r temp_metalign 2> /dev/null

for file in $(find organism_files/ -type f -name "*.fna.gz")
do
   zcat "${file}" | grep '>' | cut -d' ' -f1 | sed 's/>//g' >> headers.txt
done

grep -F -w -f headers.txt ../data/db_info.txt > db_info.txt
rm headers.txt

rm $trainingFiles 2> /dev/null
fullPath="$(pwd)/organism_files"
find $fullPath -type f -name "*.fna.gz" > ${trainingFiles}

echo "re-training CMash"
rm ${cmashDatabase} 2> /dev/null
MakeStreamingDNADatabase.py ${trainingFiles} ${cmashDatabase} -n 1000 -k 60 -v

echo "making streaming pre-filter"
rm ${prefilterName} 2> /dev/null
MakeStreamingPrefilter.py ${cmashDatabase} ${prefilterName} 30-60-10

echo "dumping training k-mers"
rm ${cmashDump} 2> /dev/null
python ~/scripts/dump_kmers.py "${DB_DIR}/${cmashDatabase}" "${DB_DIR}/${cmashDump}"

echo "running kmc"
rm "${cmashBaseName}.kmc_pre" 2> /dev/null
rm "${cmashBaseName}.kmc_suf" 2> /dev/null
kmc -v -k60 -fa -ci0 -cs3 -t"${numThreads}" -jlogsample "${DB_DIR}/${cmashDump}" "${DB_DIR}/${cmashBaseName}_dump" .

python ~/Metalign/scripts/metalign.py ${READS} ${DB_DIR} --output ~/metalign_out.csv --threads ${numThreads} --verbose --keep_temp_files --temp_dir ~/temp_metalign