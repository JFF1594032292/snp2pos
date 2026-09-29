"""Test saved paths in an isolated installation, without changing local config."""
import configparser
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    with tempfile.TemporaryDirectory() as tmp:
        install = Path(tmp) / 'install'
        install.mkdir()
        for name in ('snp2pos', 'pos2snp', 'snp2pos_config.py'):
            shutil.copy2(ROOT / name, install / name)

        def run(tool, *args):
            return subprocess.run([sys.executable, str(install / tool), *args],
                                  cwd=tmp, text=True, capture_output=True)

        config_path = install / '.snp2pos_config'
        for assembly in ('37', '38'):
            for tool, db in [('pos2snp', 'GRCh38.sample.vcf.gz'),
                             ('snp2pos', 'GRCh38.sample_rs.gz')]:
                # Same fixture tests independent assembly slots, not a liftover.
                result = run(tool, '-g', assembly, '--set-dbsnp',
                             str(ROOT / 'examples' / db))
                assert result.returncode == 0, result.stderr
        config = configparser.ConfigParser()
        config.read(config_path)
        assert all(config.has_option(g, t) for g in ('37', '38')
                   for t in ('snp2pos', 'pos2snp'))
        expected = (ROOT / 'examples/expected.tsv').read_text()
        for g in ('37', '38'):
            result = run('pos2snp', '-g', g, '-p', '1', '10019')
            assert result.returncode == 0 and result.stdout == expected, result.stderr
            result = run('snp2pos', '-g', g, '-rs', 'rs775809821')
            assert result.returncode == 0 and result.stdout == expected, result.stderr
        before = config_path.read_bytes()
        assert run('snp2pos', '--set-dbsnp', 'missing.gz').returncode != 0
        assert config_path.read_bytes() == before
        # A manually configured relative path is relative to the installation.
        shutil.copy2(ROOT / 'examples/GRCh38.sample_rs.gz', install / 'local.gz')
        shutil.copy2(ROOT / 'examples/GRCh38.sample_rs.gz.csi', install / 'local.gz.csi')
        config_path.write_text('[38]\nsnp2pos = local.gz\n')
        assert run('snp2pos', '-g', '38', '-rs', 'rs775809821').stdout == expected
        config_path.write_text('[38]\nsnp2pos = missing.gz\n')
        result = run('snp2pos', '-g', '38', '-rs', 'rs775809821', '--dbsnp',
                     str(ROOT / 'examples/GRCh38.sample_rs.gz'))
        assert result.returncode == 0 and result.stdout == expected
        config_path.write_text('invalid config')
        assert run('snp2pos', '-rs', 'rs3').returncode != 0
    print('test_config.py: OK')


if __name__ == '__main__':
    main()
