"""Resolve pinned third-party inspection archives into disposable scratch only."""
import json
from pathlib import Path
import shutil
import urllib.request
from verification_core import digest, require

ARTIFACT_ROOT = Path('/home/administrator/verification/eventstore-release-readiness-20261117')


def resolve_artifact(metadata, scratch):
    """Use a verified durable local copy or the exact pinned NuGet URL."""
    expected = metadata['sha256']
    require(len(expected) == 64 and all(ch in '0123456789abcdef' for ch in expected), 'Invalid artifact digest')
    name = metadata.get('filename', Path(metadata['url']).name)
    require(Path(name).name == name, 'Artifact filename must be a basename')
    target = Path(scratch) / ('artifact-' + expected[:12] + '-' + name)
    local = Path(metadata.get('local_path', ARTIFACT_ROOT / name))
    if local.is_file() and digest(local) == expected:
        shutil.copy2(local, target)
    else:
        require(metadata['url'].startswith('https://api.nuget.org/v3-flatcontainer/dotnet-inspect'), 'Unpinned artifact origin')
        with urllib.request.urlopen(metadata['url'], timeout=30) as response:
            target.write_bytes(response.read())
    require(digest(target) == expected, 'Artifact does not match pinned digest')
    return target


def retained_artifact(directory, relative, expected, scratch, packet):
    """Resolve historical retained paths without editing their immutable receipts."""
    candidate = directory / relative
    if candidate.is_file():
        require(digest(candidate) == expected, 'Retained artifact changed')
        return candidate
    index = json.loads((packet / 'external-artifacts.json').read_text())
    key = str(candidate.relative_to(packet))
    metadata = index['historical_paths'][key]
    require(metadata['sha256'] == expected, 'Historical artifact sidecar digest mismatch')
    return resolve_artifact(metadata, scratch)
