#!/bin/bash

usage() {
    echo "Usage: $0 <data> <reads> [--cutoff <cutoff>] [--threads <threads>] [--results_dir <results_dir>] [--temp_dir <temp_dir>] [--names <names.dmp>] [--nodes <nodes.dmp>] [--kraken_path <path_to_kraken2>] [--metatrinity_dir <path_to_metatrinity>]"
    echo "  <data>              Database directory (required)"
    echo "  <reads>             Input FASTQ file (required)"
    echo "  --cutoff            Cutoff value (default: 0.0001)"
    echo "  --threads           Number of threads (default: 1)"
    echo "  --results_dir       Root of the results directory (default: results)"
    echo "  --temp_dir          Temporary directory (default: temp_dir)"
    echo "  --names             Path to names.dmp file (default: <data>/taxonomy/names.dmp)"
    echo "  --nodes             Path to nodes.dmp file (default: <data>/taxonomy/nodes.dmp)"
    echo "  --kraken_path       Path to the kraken2 binary (default: kraken2 in PATH)"
    echo "  --metatrinity_dir   Path to the MetaTrinity directory (default: current working directory)"
    exit 1
}

cutoff=0.0001
threads=1
results_dir="results_kraken"
temp_dir="temp_kraken"
names_dmp=""
nodes_dmp=""
kraken_path="kraken2"
metatrinity_dir="MetaTrinity"

if [[ $# -lt 2 ]]; then
    echo "Error: <data> and <reads> are required arguments."
    usage
fi

data="$1"
reads="$2"
shift 2

while [[ $# -gt 0 ]]; do
    case "$1" in
        --cutoff)
            cutoff="$2"
            shift 2
            ;;
        --threads)
            threads="$2"
            shift 2
            ;;
        --results_dir)
            results_dir="$2"
            shift 2
            ;;
        --temp_dir)
            temp_dir="$2"
            shift 2
            ;;
        --names)
            names_dmp="$2"
            shift 2
            ;;
        --nodes)
            nodes_dmp="$2"
            shift 2
            ;;
        --kraken_path)
            kraken_path="$2"
            shift 2
            ;;
        --metatrinity_dir)
            metatrinity_dir="$2"
            shift 2
            ;;
        *)
            echo "Error: Unknown option $1"
            usage
            ;;
    esac
done

names_dmp="${names_dmp:-$data/taxonomy/names.dmp}"
nodes_dmp="${nodes_dmp:-$data/taxonomy/nodes.dmp}"

if [[ -d "$results_dir" ]]; then
    echo "Results directory exists. Overwriting..."
    rm -rf "$results_dir"
fi
echo "Creating results directory structure..."
mkdir -p "$results_dir/k2" "$results_dir/cs" "$results_dir/rm" "$results_dir/organism_files"

if [[ ! -d "$temp_dir" ]]; then
    echo "Creating temporary directory: $temp_dir"
    mkdir -p "$temp_dir"
fi

echo "Running Kraken..."
python3 ~/scripts/kraken.py \
    "$data" "$reads" \
    --results_dir "$results_dir/k2/" \
    --containment_results "$results_dir/ContainmentResults.csv" \
    --threads "$threads" \
    --kraken_path "$kraken_path"

echo "Generating .fna files..."
python3 ~/scripts/generate_fna.py \
    "$data" "$reads" \
    --containment_results "$results_dir/ContainmentResults.csv" \
    --kraken_output "$results_dir/k2/kraken_output.txt" \
    --kraken_report "$results_dir/k2/kraken_report.txt" \
    --cutoff "$cutoff" \
    --db_dir "$results_dir/organism_files"

echo "Generating database info..."
python3 ~/scripts/generate_dbinfo.py \
    "$data" \
    --db_dir "$results_dir/organism_files" \
    --dbinfo_out "$results_dir/db_info.txt" \
    --names "$names_dmp" \
    --nodes "$nodes_dmp"

echo "Running containment search..."
python3 "$metatrinity_dir/MetaTrinity/Scripts/containment_search.py" \
    "$reads" "$data" \
    --db "$results_dir/cs/subset_db.fna" \
    --db_dir "$results_dir/organism_files" \
    --dbinfo_in "$results_dir/db_info.txt" \
    --dbinfo_out "$results_dir/cs/db_info.txt" \
    --cutoff "$cutoff" \
    --metalign_results "$results_dir/ContainmentResults.csv" \
    --temp_dir "$temp_dir" \
    --threads "$threads"

echo "Running read mapping..."
python3 "$metatrinity_dir/MetaTrinity/Scripts/read_mapping.py" \
    "$reads" "$data" \
    --db "$results_dir/cs/subset_db.fna" \
    --dbinfo "$results_dir/cs/db_info.txt" \
    --threads "$threads" \
    --output "$results_dir/rm/profile.tsv"

echo "Cleaning up temporary directory: $temp_dir"
rm -rf "$temp_dir"

echo "Pipeline completed successfully!"
