import os
import csv
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description="Process Kraken taxid results with a cutoff value.")
    parser.add_argument("data", help="Path to the Kraken database directory.")
    parser.add_argument("reads", help="Path to the FASTQ file.")
    parser.add_argument("--containment_results", required=True, help="Path to the ContainmentResults.csv file.")
    parser.add_argument("--kraken_output", required=True, help="Path to the Kraken2 output file.")
    parser.add_argument("--kraken_report", required=True, help="Path to the Kraken2 report file.")
    parser.add_argument("--cutoff", type=float, default=0.0001, help="Cutoff value for filtering (default: 0.0001).")
    parser.add_argument("--db_dir", default=None, help="Directory to output the .fna.gz files. Default is <data>/organism_files.")
    args = parser.parse_args()

    output_dir = args.db_dir or os.path.join(args.data, "organism_files")
    os.makedirs(output_dir, exist_ok=True)

    taxids = []
    with open(args.containment_results, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            taxid_file, value = row
            taxid = taxid_file.split('_')[1]
            if float(value) >= args.cutoff:
                taxids.append(taxid)

    for taxid in taxids:
        output_file = f"taxid_{taxid}_genomic.fna"
        output_path = os.path.join(output_dir, output_file)
        
        subprocess.run([
            "python3", "scripts/extract_kraken_reads.py",
            "-s", args.reads,
            "-k", args.kraken_output,
            "-r", args.kraken_report,
            "-t", taxid,
            "-o", output_path,
            "--include-children"
        ])
        
        subprocess.run(["gzip", "-f", output_path])

    print(f"Processing complete. Output files saved in {output_dir}.")

if __name__ == "__main__":
    main()