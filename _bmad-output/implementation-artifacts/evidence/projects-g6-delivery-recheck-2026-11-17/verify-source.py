#!/usr/bin/env python3
"""Read exact Git objects; never acquire missing objects or edit a checkout."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
OWNER = HERE.parents[3]
PROJECTS = OWNER / 'references/Hexalith.Projects'
ENV = os.environ.copy()
ENV.update(GIT_NO_LAZY_FETCH='1', GIT_NO_REPLACE_OBJECTS='1', GIT_OPTIONAL_LOCKS='0')
BASE = '4511105bb1f00b8cf762097523de74acc828a001'
DELIVERED = '146d0f7e9964c82da23d31b51e6ab62efdcfdda6'
CURRENT = '3361f2e3b5655fa1ad50a2d12c640bbd5edcbb4b'
OWNER_SOURCE = '4db3776e444f0ec6e5f97d1ff089a0d83f990082'


def git(root, *args):
    return subprocess.check_output(['git', '-c', 'submodule.recurse=false', '-C', str(root), *args], env=ENV)


def tree(source):
    result = {}
    for item in git(PROJECTS, 'ls-tree', '-r', '-z', source).split(b'\0'):
        if item:
            meta, path = item.split(b'\t', 1)
            result[path.decode()] = meta.decode().split()
    return result


def main():
    manifest = json.loads(git(OWNER, 'show', OWNER_SOURCE + ':docs/proposals/projects-g6-catalog.json'))
    before, after, current = map(tree, [BASE, DELIVERED, CURRENT])
    changed = {p: {'before': before.get(p), 'after': after.get(p)} for p in before.keys() | after.keys()
               if before.get(p) != after.get(p)}
    assert set(changed) == set(manifest['after'])
    assert all(before.get(p) == value for p, value in manifest['before'].items())
    assert all(after.get(p) == value for p, value in manifest['after'].items())
    assert git(PROJECTS, 'rev-parse', DELIVERED + '^{tree}').decode().strip() == manifest['result_tree']
    headers = git(PROJECTS, 'cat-file', 'commit', DELIVERED).split(b'\n\n', 1)[0].splitlines()
    assert [x[7:].decode() for x in headers if x.startswith(b'parent ')] == [BASE]
    assert all(before.get(p) == value for p, value in after.items() if p not in changed)
    assert all(current.get(p) == value for p, value in manifest['after'].items())
    for path in list(manifest['after'])[1:]:
        assert git(PROJECTS, 'show', CURRENT + ':' + path) == git(OWNER, 'show', OWNER_SOURCE + ':' + path)
    workflow = git(PROJECTS, 'show', CURRENT + ':.github/workflows/ci.yml').decode()
    assert workflow.index('name: Acquire reviewed G-6 catalog') < workflow.index('name: Restore effective G-6 package graphs')
    assert workflow.index('name: Restore effective G-6 package graphs') < workflow.index('prepare-build')
    result = {'status': 'passed', 'owner_source': OWNER_SOURCE, 'reviewed_base': BASE,
              'delivered_sha': DELIVERED, 'result_tree': manifest['result_tree'], 'single_parent': BASE,
              'changed_paths': changed, 'all_other_entries_preserved': True,
              'gitlinks_at_delivery': {p: v[2] for p, v in after.items() if v[:2] == ['160000', 'commit']},
              'current_projects_source': CURRENT, 'current_correction_payload_unchanged': True,
              'invocation_before_prepare_build': True,
              'patch_sha256': hashlib.sha256(git(OWNER, 'show', OWNER_SOURCE + ':docs/proposals/projects-g6-catalog.patch')).hexdigest(),
              'current_gitlinks': {p: v[2] for p, v in current.items() if v[:2] == ['160000', 'commit']},
              'scope': 'read-only exact object proof; no hosted acceptance inferred'}
    (HERE / 'source-proof.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k in {'status', 'delivered_sha', 'current_projects_source', 'current_correction_payload_unchanged'}}))


if __name__ == '__main__':
    main()
