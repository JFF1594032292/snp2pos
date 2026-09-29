"""Shared installation-local database path configuration."""
import configparser
import os
import tempfile
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent / '.snp2pos_config'


def read_config():
    config = configparser.ConfigParser(interpolation=None)
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open() as fh:
            config.read_file(fh)
    return config


def database_path(tool, assembly, override, default):
    if override:
        return os.path.expanduser(override)
    value = read_config().get(assembly, tool, fallback='').strip()
    if not value:
        return default
    return str(CONFIG_PATH.parent / Path(value).expanduser())


def save_database(tool, assembly, value):
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise ValueError('Database file does not exist: %s' % path)
    if not any(Path(str(path) + suffix).is_file() for suffix in ('.csi', '.tbi')):
        raise ValueError('Database requires a .csi or .tbi index: %s' % path)
    config = read_config()
    if not config.has_section(assembly):
        config.add_section(assembly)
    config.set(assembly, tool, str(path))
    # Replace only after a complete write, preserving the old config on failure.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=CONFIG_PATH.parent,
                                         delete=False) as fh:
            temporary = fh.name
            config.write(fh)
        os.replace(temporary, CONFIG_PATH)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)
