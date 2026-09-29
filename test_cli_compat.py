#!/usr/bin/env python3
# coding=utf-8

import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent


FAKE_TABIX = r'''#!/usr/bin/env python
import os
import sys

SNP_LINES = [
    "rs\t3\t13:31872705\tC\tT",
    "rs\t17\t7:11544172\tT\tA,G",
]
VCF_LINES = [
    "1\t10039\trs978760828\tA\tC\t.\t.\tRS=978760828",
    "1\t10051\trs1052373574\tA\tG\t.\t.\tRS=1052373574",
    "1\t10051\trs1326880612\tA\tAC\t.\t.\tRS=1326880612",
    "X\t12345\trsX12345\tG\tA\t.\t.\tRS=12345",
]


def read_regions(args):
    if len(args) >= 3 and args[1] == "-R":
        with open(args[2], encoding="utf-8") as fh:
            regions = []
            for line in fh:
                if not line.strip():
                    continue
                chrom, start, end = line.strip().split("\t")
                regions.append("%s:%s-%s" % (chrom, start, end))
            return regions
    return [args[1]]


def parse_region(region):
    chrom, span = region.split(":", 1)
    start, end = span.split("-", 1)
    return chrom, int(start), int(end)


def main():
    args = sys.argv[1:]
    expected_dbsnp = os.environ.get("EXPECT_DBSNP")
    if expected_dbsnp and args[0] != expected_dbsnp:
        sys.stderr.write("unexpected dbSNP path: %s\n" % args[0])
        sys.exit(2)
    regions = read_regions(args)
    use_snp_table = any(region.startswith("rs:") for region in regions)
    lines = SNP_LINES if use_snp_table else VCF_LINES

    for region in regions:
        chrom, start, end = parse_region(region)
        for line in lines:
            fields = line.split("\t")
            if use_snp_table:
                pos = int(fields[1])
                if chrom == "rs" and start <= pos <= end:
                    print(line)
            else:
                pos = int(fields[1])
                if fields[0] == chrom and start <= pos <= end:
                    print(line)


if __name__ == "__main__":
    main()
'''


def make_fake_tabix(tmpdir):
    tabix = Path(tmpdir) / "tabix"
    tabix.write_text(FAKE_TABIX, encoding="utf-8")
    tabix.chmod(tabix.stat().st_mode | stat.S_IXUSR)
    return tabix


def run_script(env, args, input_text=None):
    proc = subprocess.run(
        [sys.executable] + args,
        cwd=str(ROOT),
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def write_small_vcf(path):
    path.write_text(
        "\n".join([
            "##fileformat=VCFv4.2",
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO",
            "1\t10039\trs978760828\tA\tC\t.\t.\tRS=978760828",
            "13\t31872705\trs3\tC\tT\t.\t.\tRS=3",
            "7\t11544172\trs17\tT\tA,G\t.\t.\tRS=17",
            "1\t10050\t.\tA\tG\t.\t.\t.",
        ]) + "\n",
        encoding="utf-8",
    )


def main():
    with tempfile.TemporaryDirectory(prefix="snp2pos_test_") as tmpdir:
        make_fake_tabix(tmpdir)
        env = os.environ.copy()
        env["PATH"] = tmpdir + os.pathsep + env.get("PATH", "")

        assert run_script(env, ["snp2pos", "-rs", "rs3", "-g", "38"]) == "13\t31872705\trs3\tC\tT\n"
        assert run_script(env, ["snp2pos", "-rs", "17", "-g", "38", "-s", "T"]) == (
            "7\t11544172\trs17\tT\tA\n"
            "7\t11544172\trs17\tT\tG\n"
        )
        assert run_script(env, ["snp2pos", "-rs", "3", "-g", "38", "-bed", "T"]) == "13\t31872704\t31872706\trs3\n"
        assert run_script(env, ["snp2pos", "-g", "38"], "rs3\n3\n") == "13\t31872705\trs3\tC\tT\n"
        assert run_script(env, ["snp2pos", "-rs", "rs3", "-g", "38", "--dbsnp", "/tmp/custom_rs.gz"]) == "13\t31872705\trs3\tC\tT\n"

        linked_snp2pos = Path(tmpdir) / "snp2pos"
        linked_snp2pos.symlink_to(ROOT / "snp2pos")
        linked_env = env.copy()
        linked_env["EXPECT_DBSNP"] = str(ROOT / "GCF_000001405.38_rs-chrall.gz")
        proc = subprocess.run(
            [sys.executable, str(linked_snp2pos), "-rs", "rs3", "-g", "38"],
            cwd=tmpdir,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=linked_env,
        )
        assert proc.returncode == 0, proc.stderr

        assert run_script(env, ["pos2snp", "-p", "1", "10039", "-g", "38"]) == "1\t10039\trs978760828\tA\tC\n"
        assert run_script(env, ["pos2snp", "-g", "38"], "1\t10039\n1\t10051\n") == (
            "1\t10039\trs978760828\tA\tC\n"
            "1\t10051\trs1052373574\tA\tG\n"
            "1\t10051\trs1326880612\tA\tAC\n"
        )
        assert run_script(env, ["pos2snp", "-g", "38"], "1\t10039\n1\t10039\n") == "1\t10039\trs978760828\tA\tC\n"
        assert run_script(env, ["pos2snp", "-g", "38"], "X\t12345\n") == "X\t12345\trsX12345\tG\tA\n"
        assert run_script(env, ["pos2snp", "-g", "38"], "1\tbad\n1\t10039\n") == "1\t10039\trs978760828\tA\tC\n"
        assert run_script(env, ["pos2snp", "-p", "1", "10039", "-g", "38", "--dbsnp", "/tmp/custom_vcf.gz"]) == "1\t10039\trs978760828\tA\tC\n"

        small_vcf = Path(tmpdir) / "small.vcf"
        small_out = Path(tmpdir) / "small_rs-chrall.gz"
        write_small_vcf(small_vcf)
        proc = subprocess.run(
            [sys.executable, "vcf2rs_chrall", str(small_vcf), "-o", str(small_out), "-f", "--no-index"],
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        assert proc.returncode == 0, proc.stderr
        converted = subprocess.run(
            ["gzip", "-dc", str(small_out)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert converted.returncode == 0, converted.stderr
        assert converted.stdout == (
            "rs\t3\t13:31872705\tC\tT\n"
            "rs\t17\t7:11544172\tT\tA,G\n"
            "rs\t978760828\t1:10039\tA\tC\n"
        )

    print("test_cli_compat.py: OK")


if __name__ == "__main__":
    main()
