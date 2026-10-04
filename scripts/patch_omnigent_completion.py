"""Apply one reproducible, version-scoped fix in the project venv only."""
import hashlib
import json
import sys
from importlib.metadata import distribution
from pathlib import Path

OLD = '        elif not _is_native_harness(conv_id) and not has_buffered:\n            _mark_subagent_terminal_and_wake(\n'
NEW = '''        elif not _is_native_harness(conv_id) and not has_buffered and not any(
            (entry := _subagent_work_by_child.get(child)) is not None
            and entry.status in ("launching", "running", "waiting")
            for child in _subagent_work_by_parent.get(conv_id, set())
        ):  # Pufibara: pending descendants are not terminal completion.
            _mark_subagent_terminal_and_wake(
'''

def patch_text(source):
    if NEW in source:
        if source.count(NEW) != 1 or OLD in source:
            raise ValueError('Ambiguous already-patched source')
        return source
    if source.count(OLD) != 1:
        raise ValueError('Unexpected upstream source; revalidate instead of guessing')
    return source.replace(OLD, NEW, 1)

def main():
    root = Path(__file__).resolve().parents[1]
    if Path(sys.prefix).resolve() != (root / '.venv').resolve():
        raise PermissionError('Only this project venv may be patched')
    package = distribution('omnigent')
    if package.version != '0.16.0':
        raise ValueError('Revalidate fix for this Omnigent version')
    path = Path(package.locate_file('omnigent/runner/app.py')).resolve()
    if not path.is_relative_to((root / '.venv').resolve()):
        raise PermissionError('Upstream source outside project venv')
    original = path.read_text()
    updated = patch_text(original)
    compile(updated, str(path), 'exec')
    if updated != original:
        path.write_text(updated)
    record = {'kind':'project_local_upstream_completion_fix','version':package.version,
              'changed':updated != original,'before_sha256':hashlib.sha256(original.encode()).hexdigest(),
              'after_sha256':hashlib.sha256(updated.encode()).hexdigest(),
              'scope':'Defer successful runner completion while registered children remain pending; native dispatch, inbox and wake preserved',
              'live_verified':False}
    proof = root / 'evidence/omnigent-completion-patch.json'
    if proof.exists():
        record['previous_application'] = json.loads(proof.read_text())
    proof.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))

if __name__ == '__main__':
    main()
