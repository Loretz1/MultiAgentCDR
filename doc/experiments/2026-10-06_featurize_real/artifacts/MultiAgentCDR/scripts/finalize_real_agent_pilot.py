"""Complete missing v5 pairs, verify outputs, and record final experiment status."""
from pathlib import Path
import shutil
import subprocess
import sys
import time
from agent_pipeline_common import ROOT, read_json, write_json, file_records


def main():
    run=ROOT/'runs/pilot_v1'
    inputs=run/'inputs_prompt_dev/agent_inputs.jsonl'
    first=run/'feedback_v5.summary.json'
    if first.exists() and not (run/'feedback_v5_first_attempt.summary.json').exists():
        shutil.copyfile(first,run/'feedback_v5_first_attempt.summary.json')
    with (run/'logs/feedback_v5_resume.log').open('w') as stream:
        subprocess.run([sys.executable,'scripts/collect_real_agent_feedback.py','--input',str(inputs),
                        '--output',str(run/'feedback_v5.jsonl'),'--prompt-style','v5_short'],
                       cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)
    with (run/'logs/result_validation.log').open('w') as stream:
        subprocess.run([sys.executable,'scripts/summarize_real_agent_feedback.py','--inputs',str(inputs),
                        '--feedback',str(run/'feedback_v5.jsonl'),'--output',str(run/'result_summary.json'),
                        '--bundle','bundle'],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)
    result=read_json(run/'result_summary.json')
    write_json(run/'pilot_status.json',{'state':'complete','prompt_version':result['prompt_version'],
               'pairs':result['pairs'],'judgments':result['judgments'],'updated_unix':time.time(),
               'feedback_sha256':result['feedback_sha256']})
    names=['scripts/'+p.name for p in (ROOT/'scripts').glob('*') if p.is_file()]
    write_json(run/'final_code_manifest.json',{'files':file_records(ROOT,names)})
    print('COMPLETE',result['pairs'],result['judgments'],flush=True)


if __name__=='__main__':
    try: main()
    except Exception as exc:
        write_json(ROOT/'runs/pilot_v1/finalization_status.json',{'state':'failed','error':str(exc)})
        raise
