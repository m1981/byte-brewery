"""Reproduce stage 3 against a fixed Git baseline; outputs stay in --output."""
from pathlib import Path
import argparse
import collections
from datetime import datetime
import difflib
import hashlib
import importlib.util
import io
import json
import platform
import subprocess
import sys
import tarfile
import tempfile
import time

BASE = 'c19208dd4ce797ec5183c3127e832c5282a30aba'
p = argparse.ArgumentParser()
p.add_argument('--repo', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=True)
started = datetime.now().astimezone().isoformat()
tick = time.monotonic()
def digest(data):
    return hashlib.sha256(data).hexdigest()
def write_json(name, value):
    (a.output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
with tempfile.TemporaryDirectory(prefix='vcs-sdlc-stage3-') as tmp:
    root = Path(tmp)
    archive = subprocess.check_output(['git', '-C', str(a.repo), 'archive', BASE])
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(root, filter='data')
    pkg = root / 'packages/vcs_lite'
    inputs = [f for f in pkg.rglob('*') if f.is_file()]
    before = {str(f.relative_to(pkg)): digest(f.read_bytes()) for f in inputs}
    trace = pkg / 'docs/TRACE.md'
    original = trace.read_bytes()
    command = [sys.executable, '-m', 'pytest', '-p', 'no:cacheprovider', '-vv', 'packages/vcs_lite/tests/test_traceability.py']
    result = subprocess.run(command, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    (a.output / 'pytest-baseline.log').write_text(result.stdout)
    generated = trace.read_bytes()
    delta = ''.join(difflib.unified_diff(original.decode().splitlines(True), generated.decode().splitlines(True), fromfile='baseline/TRACE.md', tofile='generated/TRACE.md'))
    (a.output / 'TRACE.diff').write_text(delta)
    changed = [name for name, h in before.items() if digest((pkg / name).read_bytes()) != h]
    spec = importlib.util.spec_from_file_location('stage3_traceability', pkg / 'tests/traceability.py')
    tr = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = tr
    spec.loader.exec_module(tr)
    c = tr.load_corpus(pkg/'docs', pkg/'src/vcs_lite', pkg/'tests')
    reqs = tr._rows(c, 'REQ')
    active = {k:v for k,v in reqs.items() if not tr.superseded(v)}
    tests_by_req, modules_by_req = tr.req_to_tests(c), tr.module_ids(c)
    checks = {str(n): getattr(tr, f'check_{n}')(c) for n in range(200,207)}
    report = {
        'baseline': BASE, 'started': started, 'python': sys.version, 'executable': sys.executable,
        'platform': platform.platform(), 'command': command, 'cwd': 'isolated git archive at baseline',
        'exit_code': result.returncode, 'trace_before_sha256': digest(original),
        'trace_after_sha256': digest(generated), 'trace_diff_bytes': len(delta.encode()),
        'changed_existing_package_files_after_baseline_test': changed,
        'checker_sha256': before['tests/traceability.py'], 'test_module_sha256': before['tests/test_traceability.py'],
        'definitions_by_prefix': dict(sorted(collections.Counter(k.split('-')[0] for k in c.definitions).items())),
        'definition_count': len(c.definitions), 'scenario_count': len(c.scenarios),
        'confirmed_scenarios': sum(s.confirmed for s in c.scenarios),
        'ast_test_functions': len(c.tests), 'test_files': len(list((pkg/'tests').rglob('test_*.py'))),
        'source_modules': len(c.modules), 'checks_200_to_206': checks,
        'non_superseded_requirements': len(active),
        'non_superseded_reqs_without_named_test_link': sorted(k for k in active if not tests_by_req[k]),
        'non_superseded_reqs_without_module_link': sorted(k for k in active if not modules_by_req[k]),
        'reference_only_docs': list(tr.REFERENCE_ONLY_DOCS),
    }
    # Controlled negative probe: stale generated artifact, in the disposable copy only.
    trace.write_text('# Deliberately stale TRACE for stage 3 probe\n')
    probe = subprocess.run(command + ['-k', 'test_req_vcs_207_matrix_is_generated'], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    (a.output/'pytest-stale-trace-probe.log').write_text(probe.stdout)
    report['stale_trace_probe'] = {'deliberately_modified': 'docs/TRACE.md only in disposable copy', 'command': command + ['-k','test_req_vcs_207_matrix_is_generated'], 'exit_code': probe.returncode, 'restored_generated_trace': trace.read_bytes() == generated}
    report['elapsed_seconds'] = round(time.monotonic()-tick,3)
    write_json('result.json', report)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if result.returncode or probe.returncode:
        raise SystemExit(1)
