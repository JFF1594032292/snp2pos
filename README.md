# Snp2pos

English | [简体中文](README.zh-CN.md)

Query rsIDs and genomic positions using a local dbSNP database and tabix.

- `snp2pos`: convert rsIDs to genomic positions.
- `pos2snp`: find rsIDs at genomic positions.
- `vcf2rs_chrall`: build a lookup table indexed by numeric rsID from a VCF.

## Requirements

Python 3.6+ (standard library only), HTSlib's `tabix` and `bgzip`, and the system `sort` command. Examples were tested with tabix 1.23.
Run the commands below from this directory. No Python packages need to be installed.

## Quick start

The repository includes only 10 example GRCh38 variants, not a full database.

```bash
python3 snp2pos examples/rs.list --dbsnp examples/GRCh38.sample_rs.gz
python3 pos2snp examples/positions.tsv --dbsnp examples/GRCh38.sample.vcf.gz

printf 'rs775809821\n' | python3 snp2pos --dbsnp examples/GRCh38.sample_rs.gz
printf '1\t10019\n' | python3 pos2snp --dbsnp examples/GRCh38.sample.vcf.gz
```

Each command returns the following tab-separated record without a header:

```text
1	10019	rs775809821	TA	T
```

Single queries and command help:

```bash
python3 snp2pos -rs rs775809821 --dbsnp examples/GRCh38.sample_rs.gz
python3 pos2snp -p 1 10019 --dbsnp examples/GRCh38.sample.vcf.gz
python3 snp2pos --help
python3 pos2snp --help
python3 vcf2rs_chrall --help
```

## Input and output conventions

- Default output has five tab-separated columns: `CHR POS ID REF ALT`. POS is **1-based**.
- rsID input has one ID per line; `rs123`, `RS123`, and `123` are accepted.
- Position input has `CHR<TAB>POS` on each line, with **1-based** POS. Chromosome names must match the database.
- Omit the input file or use `-` to read standard input; use `-o` to select an output file.
- `snp2pos -s T` splits multiple ALT alleles; `-prefix chr` adds a prefix to output chromosome names.
- `snp2pos -bed T` preserves the existing behavior: `[POS-1, POS+1)`, a **0-based, end-exclusive 2 bp interval**. This is neither a single-base BED interval nor an interval based on REF length.
- Batch input is deduplicated and input order is not guaranteed. Unmatched queries produce no output; some invalid input is silently skipped.
- Batch queries run after all input has been read and keep results in memory. Split large workloads into batches as needed.
- `-t T` enables timing. Both query scripts write timing information to standard output, so leave it disabled when producing TSV files.

## Persistent database paths

Save each database path once for each assembly (replace the example paths with your indexed files):

```bash
./pos2snp -g 37 --set-dbsnp /path/to/GRCh37.vcf.gz
./snp2pos -g 37 --set-dbsnp /path/to/GRCh37_rs.gz
./pos2snp -g 38 --set-dbsnp /path/to/GRCh38.vcf.gz
./snp2pos -g 38 --set-dbsnp /path/to/GRCh38_rs.gz

./snp2pos -g 38 -rs rs3
./pos2snp -g 38 -p 13 31872705
```

Paths are saved in `.snp2pos_config` beside the installed scripts. `--set-dbsnp` checks that the file and a CSI/TBI index exist, saves an absolute path, and exits without querying. It does not build indexes or verify the assembly. Other assembly/tool entries are preserved. The installation directory must be writable.

Priority: `--dbsnp` (this invocation only) > saved path for `-g` > default filename below. The default assembly remains 37. You may also copy `.snp2pos_config.example` to `.snp2pos_config` and edit it manually; relative paths in the config are relative to the installation directory. The active config is ignored by Git to avoid publishing local paths. Keep `snp2pos_config.py` beside both scripts.

## Using a full database

Download locations:

- [dbSNP b152 archive](https://ftp.ncbi.nih.gov/snp/archive/b152/VCF/): the original database download location for the bundled example, as provided by the author.
- [Latest dbSNP release](https://ftp.ncbi.nih.gov/snp/latest_release/VCF/): current release data. This directory changes with new releases and is not a fixed-version link.

Choose a file for the correct reference assembly and record the download date, dbSNP release, and filename. Newer filenames may differ from the defaults below; explicitly selecting the database with `--dbsnp` is recommended.

Full databases and their indexes are not distributed with this repository. Prepare a coordinate-sorted BGZF VCF for your reference assembly.
Chromosome names may be `1`, `chr1`, or reference sequence accessions; the tool does not convert them automatically.

```bash
mkdir -p data
# Place your BGZF VCF at data/dbsnp.vcf.gz, then run:
tabix -C -p vcf data/dbsnp.vcf.gz
python3 vcf2rs_chrall data/dbsnp.vcf.gz -o data/dbsnp_rs.gz
python3 snp2pos -rs rs3 --dbsnp data/dbsnp_rs.gz
python3 pos2snp -p 13 31872705 --dbsnp data/dbsnp.vcf.gz
```

The final coordinate is a GRCh38 example only; queries must match the assembly and chromosome naming in your database.
The converter preserves VCF coordinates and chromosome names, extracts numeric rsIDs from the ID column, and uses `sort` and `bgzip` to generate the lookup table and a CSI index. Full database conversion requires sufficient disk space, including temporary space for sorting.

Without `--dbsnp`, `-g 37` (default) or `-g 38` selects these files next to the scripts:

| Assembly | pos2snp | snp2pos |
| --- | --- | --- |
| 37 | GCF_000001405.25.gz | GCF_000001405.25_rs-chrall.gz |
| 38 | GCF_000001405.38.gz | GCF_000001405.38_rs-chrall.gz |

`-g` only selects a default filename; it does not convert coordinates. An explicit `--dbsnp` overrides that selection.

## Example data provenance

`examples/GRCh38.sample.vcf` contains 10 records extracted from the local GRCh38 dbSNP reference file `GCF_000001405.38.gz`, in region `1:10001-10100`.
Only CHROM, POS, ID, REF, and ALT were retained; QUAL/FILTER/INFO were set to `.`, and a minimal VCF header was generated. No samples or genotypes are included.
The author identified the [dbSNP b152 archive](https://ftp.ncbi.nih.gov/snp/archive/b152/VCF/) as the original database download location. The original download date was not recorded. This subset is for functional demonstrations, not formal analysis or release benchmarking.
The compressed files and CSI indexes were regenerated from this small VCF.

## Validation

```bash
python3 test_cli_compat.py
python3 test_examples.py
python3 test_config.py
```

The first checks CLI compatibility; the second uses real tabix to check example files, standard input, single queries, and BED output.

## License

Code is distributed under the [MIT License](LICENSE). The dbSNP example data is sourced from NCBI and is not relicensed by this code license.

`test_config.py` checks persistent paths and overrides in a temporary installation.
