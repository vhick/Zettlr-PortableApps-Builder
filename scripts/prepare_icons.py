#!/usr/bin/env python3
"""Copy and validate Zettlr's ACTUAL upstream icon files (no substitutions).

Use only files from the verified upstream release checkout. The builder repository
must not embed Zettlr's separately restricted corporate identity assets.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

OFFICIAL_FILES = (
    ('resources/icons/icon.ico', 'icon.ico', None),
    ('resources/icons/png/16x16.png', 'icon_16.png', 16),
    ('resources/icons/png/32x32.png', 'icon_32.png', 32),
)
PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'


def png_dimensions(blob: bytes):
    if len(blob) < 33 or blob[:8] != PNG_SIGNATURE or blob[12:16] != b'IHDR':
        raise RuntimeError('Invalid official PNG signature/IHDR')
    width, height = struct.unpack('>II', blob[16:24])
    if not (0 < width <= 4096 and 0 < height <= 4096):
        raise RuntimeError('Unsafe official PNG dimensions')
    return width, height


def ico_dimensions(blob: bytes):
    if len(blob) < 22:
        raise RuntimeError('Official ICO too short')
    reserved, icon_type, count = struct.unpack_from('<HHH', blob, 0)
    if (reserved, icon_type) != (0, 1) or not (1 <= count <= 128) or len(blob) < 6 + 16 * count:
        raise RuntimeError('Invalid official ICO directory')
    result = []
    for i in range(count):
        width, height, colors, reserved, planes, bpp, length, offset = struct.unpack_from('<BBBBHHII', blob, 6 + 16 * i)
        width = width or 256
        height = height or 256
        if not length or offset < 6 + 16 * count or offset + length > len(blob):
            raise RuntimeError('Invalid/truncated official ICO frame')
        result.append((width, height))
    if (16, 16) not in result or (32, 32) not in result:
        raise RuntimeError('Official ICO missing 16x16 or 32x32 image')
    return result


def prepare(upstream: Path, output: Path):
    if not upstream.is_dir():
        raise RuntimeError(f'Verified upstream checkout missing: {upstream}')
    # First validate ALL inputs, then create build output. Never copy partial art.
    items = []
    for official, dest, size in OFFICIAL_FILES:
        source = upstream / official
        if not source.is_file() or source.is_symlink():
            raise RuntimeError(f'Official icon absent or unsafe: {source}; refusing generic substitute')
        blob = source.read_bytes()
        if size is None:
            ico_dimensions(blob)
        elif png_dimensions(blob) != (size, size):
            raise RuntimeError(f'Incorrect official {size}x{size} icon: {source}')
        items.append((official, dest, blob))
    output.mkdir(parents=True, exist_ok=True)
    manifest = {'source': 'verified Zettlr release checkout, not an external image provider', 'files': {}}
    for official, dest, blob in items:
        (output / dest).write_bytes(blob)
        manifest['files'][dest] = {'upstream_path': official, 'sha256': hashlib.sha256(blob).hexdigest()}
    (output / 'ICON-PROVENANCE.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print('OFFICIAL ICONS VALIDATED: Windows ICO + PNG 16x16 + PNG 32x32')
    for name, data in manifest['files'].items():
        print(name, data['upstream_path'], data['sha256'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--upstream', default='upstream')
    parser.add_argument('--output', default='assets-build')
    options = parser.parse_args()
    prepare(Path(options.upstream), Path(options.output))
