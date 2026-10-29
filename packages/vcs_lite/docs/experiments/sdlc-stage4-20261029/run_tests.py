"""Run selected existing tests on an extracted pilot baseline; retain successful measurements."""
import argparse, contextlib, hashlib, json, os, platform, sys, time
from pathlib import Path
from datetime import datetime
p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
a.base=a.base.resolve();a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=True)
pkg=a.base/'packages/vcs_lite';sys.path.insert(0,str(pkg/'src'));os.chdir(a.base)
import pytest
files=['tests/test_footprint.py','tests/ui/test_repo_notes.py','tests/core/test_gitlog.py','tests/core/test_change_details.py','tests/ui/test_recent_changes.py','tests/ui/test_file_list_viewport.py','tests/app/test_history_session.py']
args=['-p','no:cacheprovider','-vv']+[str(pkg/f) for f in files]
results=[];measurements={}
class Capture:
 def pytest_runtest_makereport(self,item,call):
  if call.when=='call' and 'measured' in item.funcargs:measurements[item.nodeid]=item.funcargs['measured']
 def pytest_runtest_logreport(self,report):
  if report.when=='call' or report.failed or report.skipped:results.append({'id':report.nodeid,'phase':report.when,'outcome':report.outcome})
def hashes():return {str(f.relative_to(pkg)):hashlib.sha256(f.read_bytes()).hexdigest() for folder in ['src','tests'] for f in (pkg/folder).rglob('*.py')}
before=hashes();started=datetime.now().astimezone().isoformat();t=time.monotonic()
with (a.output/'existing-tests.log').open('w') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):code=pytest.main(args,plugins=[Capture()])
report={'baseline':'c19208dd4ce797ec5183c3127e832c5282a30aba','date':started,'python':sys.version,'platform':platform.platform(),'pytest':pytest.__version__,'args':args,'exit_code':int(code),'elapsed_s':time.monotonic()-t,'results':results,'measurements':measurements,'source_hashes':before,'source_unchanged':before==hashes(),'note':'Archive has no .git: measurement commit may be empty. Baseline and source hashes above identify the measured code.'}
(a.output/'existing-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('exit',code,'outcomes',len(results),'seconds',round(report['elapsed_s'],2));sys.exit(code)
