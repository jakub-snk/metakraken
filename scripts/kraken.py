import os
import sys
import csv
import argparse
import subprocess

def check_file_exists(file_path, file_description):
    if not os.path.isfile(file_path):
        print(f"Error: {file_description} file '{file_path}' does not exist.")
        sys.exit(1)

def check_kraken2_installed(kraken_path):
    try:
        subprocess.run([kraken_path, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"Error: Kraken2 was not found at '{kraken_path}'.")
        sys.exit(1)

def build_taxid_report_dict(kraken_report, level):
    taxid_report_dict = {}
    level_prefix = f"S{level}"
    with open(kraken_report, 'r') as report:
        reader = csv.reader(report, delimiter='\t')
        for row in reader:
            if row[3] == "U":
                continue
            if row[3] == level_prefix:
                tax_id = row[4]
                score = float(row[0])
                taxid_report_dict[tax_id] = score
    return taxid_report_dict

def run_kraken2(data, reads, threads, results_dir, kraken_path):
    kraken_output = os.path.join(results_dir, "kraken_output.txt")
    kraken_report = os.path.join(results_dir, "kraken_report.txt")
    command = [
        kraken_path, "--db", data,
        "--output", kraken_output,
        "--report", kraken_report,
        reads
    ]
    if threads:
        command.extend(["--threads", str(threads)])

    subprocess.run(command, check=True)
    return kraken_output, kraken_report

def create_containment_csv(csv_path, taxid_report_dict):
    sorted_entries = sorted(taxid_report_dict.items(), key=lambda item: item[1], reverse=True)
    
    with open(csv_path, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        for tax_id, score in sorted_entries:
            writer.writerow([f"taxid_{tax_id}_genomic.fna.gz", f"{score:.5e}"])

def main():
    parser = argparse.ArgumentParser(description="Run Kraken2 and generate ContainmentResults.csv.")
    parser.add_argument('data', help="Path to Kraken2 database")
    parser.add_argument('reads', help="Path to input FASTQ file")
    parser.add_argument('--results_dir', required=True, help="Directory to store results (outputs and reports)")
    parser.add_argument('--threads', type=int, default=1, help="Number of threads for Kraken2 (default is 1)")
    parser.add_argument('--kraken_path', default="kraken2", help="Path to the Kraken2 binary (default: use 'kraken2' in PATH)")
    parser.add_argument('--taxonomy_level', type=int, default=1, help="Taxonomy level to filter (1-3, default is 1)")
    parser.add_argument('--containment_results', default=None, help="Path to save the ContainmentResults.csv file (default: results_dir/ContainmentResults.csv)")
    args = parser.parse_args()

    check_kraken2_installed(args.kraken_path)

    results_dir = args.results_dir
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    csv_output = args.containment_results or os.path.join(results_dir, "ContainmentResults.csv")

    kraken_output, kraken_report = run_kraken2(args.data, args.reads, args.threads, results_dir, args.kraken_path)

    taxid_report_dict = build_taxid_report_dict(kraken_report, args.taxonomy_level)
    if not taxid_report_dict:
        print(f"Error: No entries found for taxonomy level '{args.taxonomy_level}'.")
        return

    create_containment_csv(csv_output, taxid_report_dict)

if __name__ == "__main__":
    main()