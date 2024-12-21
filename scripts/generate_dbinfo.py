import os
import gzip
import argparse


def parse_nodes_dmp(nodes_path):
    taxonomy = {}
    with open(nodes_path, 'r') as f:
        for line in f:
            parts = line.strip().split('|')
            taxid = parts[0].strip()
            parent_taxid = parts[1].strip()
            rank = parts[2].strip()
            taxonomy[taxid] = {'parent': parent_taxid, 'rank': rank}
    return taxonomy


def parse_names_dmp(names_path):
    names = {}
    with open(names_path, 'r') as f:
        for line in f:
            parts = line.strip().split('|')
            taxid = parts[0].strip()
            name = parts[1].strip()
            name_class = parts[3].strip()
            if name_class == "scientific name":
                names[taxid] = name
    return names


def get_lineage(taxonomy, names, taxid):
    ranks = ["superkingdom", "phylum", "class", "order", "family", "genus", "species"]
    rank_names = []
    rank_taxids = []

    current_taxid = taxid
    while current_taxid != "1":
        if current_taxid in taxonomy:
            rank = taxonomy[current_taxid]['rank']
            if rank in ranks:
                rank_names.append(names.get(current_taxid, "Unknown"))
                rank_taxids.append(current_taxid)
            current_taxid = taxonomy[current_taxid]['parent']
        else:
            break

    rank_names = "|".join(reversed(rank_names))
    rank_taxids = "|".join(reversed(rank_taxids))
    return rank_names, rank_taxids


def extract_accessions_and_lengths(db_dir):
    entries = []
    for filename in os.listdir(db_dir):
        if filename.startswith("taxid_") and filename.endswith(".fna.gz"):
            taxid = filename.split('_')[1]
            file_path = os.path.join(db_dir, filename)

            with gzip.open(file_path, 'rt') as f:
                for line in f:
                    if line.startswith(">"):
                        parts = line.split()
                        accession = parts[0][1:]  # Remove '>'
                        length = int(parts[2].split('=')[1])
                        entries.append({'accession': accession, 'taxid': taxid, 'length': length})
    return entries


def generate_db_info(data, nodes_path, names_path, db_dir, dbinfo_out_file):
    if not (os.path.exists(nodes_path) and os.path.exists(names_path)):
        raise FileNotFoundError("One or more required files (nodes.dmp, names.dmp) are missing in the specified folder.")

    if not os.path.exists(db_dir):
        raise FileNotFoundError(f"Database files directory not found at {db_dir}.")

    taxonomy = parse_nodes_dmp(nodes_path)
    names = parse_names_dmp(names_path)
    entries = extract_accessions_and_lengths(db_dir)

    with open(dbinfo_out_file, 'w') as out:
        out.write("Accession\tLength\tTaxID\tLineage\tTaxID_Lineage\n")
        for entry in entries:
            accession = entry['accession']
            taxid = entry['taxid']
            length = entry['length']

            if taxid in taxonomy:
                lineage, taxid_lineage = get_lineage(taxonomy, names, taxid)
                out.write(f"{accession}\t{length}\t{taxid}\t{lineage}\t{taxid_lineage}|{taxid}\n")
            else:
                print(f"Warning: TaxID {taxid} not found in nodes.dmp.")

    print(f"db_info.txt has been created at {dbinfo_out_file}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate db_info.txt for MetaTrinity from organism files and taxonomy data.")
    parser.add_argument("data", help="Path to the Kraken2 database folder.")
    parser.add_argument("--nodes", default=None, help="Path to nodes.dmp file. Default is <data>/taxonomy/nodes.dmp.")
    parser.add_argument("--names", default=None, help="Path to names.dmp file. Default is <data>/taxonomy/names.dmp.")
    parser.add_argument("--db_dir", default=None, help="Path to organism files (database) directory. Default is <data>/organism_files.")
    parser.add_argument("--dbinfo_out", default=None, help="Path to db_info.txt output file. Default is <data>/db_info.txt.")

    args = parser.parse_args()

    nodes_path = args.nodes or os.path.join(args.data, "taxonomy", "nodes.dmp")
    names_path = args.names or os.path.join(args.data, "taxonomy", "names.dmp")
    db_dir = args.db_dir or os.path.join(args.data, "organism_files")
    dbinfo_out_file = args.dbinfo_out or os.path.join(args.data, "db_info.txt")

    generate_db_info(args.data, nodes_path, names_path, db_dir, dbinfo_out_file)