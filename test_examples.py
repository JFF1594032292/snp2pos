#!/usr/bin/env python3
"""Run real-tabix checks against the bundled GRCh38 example."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(script, args, stdin=None):
    return subprocess.run(
        [sys.executable, str(ROOT / script)] + args,
        cwd=ROOT, input=stdin, text=True, capture_output=True, check=True,
    ).stdout


def main():
    expected = (ROOT / "examples/expected.tsv").read_text()
    for script, query_file, db, single in [
        ("snp2pos", "rs.list", "GRCh38.sample_rs.gz", ["-rs", "rs775809821"]),
        ("pos2snp", "positions.tsv", "GRCh38.sample.vcf.gz", ["-p", "1", "10019"]),
    ]:
        database = ["--dbsnp", "examples/" + db]
        query = (ROOT / "examples" / query_file).read_text()
        assert run(script, database + single) == expected
        assert run(script, database + ["examples/" + query_file]) == expected
        assert run(script, database, query) == expected
        assert run(script, database + ["-"], query) == expected
    assert run("snp2pos", ["-rs", "rs775809821", "--dbsnp",
                           "examples/GRCh38.sample_rs.gz", "-bed", "T"]) == "1\t10018\t10020\trs775809821\n"
    print("test_examples.py: OK")


if __name__ == "__main__":
    main()
