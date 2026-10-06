"""Advance through audited real inputs, local vLLM readiness and feedback collection."""
from pathlib import Path
import subprocess
import sys
import time

import httpx
from agent_pipeline_common import ROOT, read_json, write_json


RUN=ROOT/'runs/pilot_v1'
PY=Path.home()/'venvs/agent-evidence/bin/python'
LOGS=RUN/'logs'


def status(state, **details):
    write_json(RUN/'pilot_status.json', {'state':state,'updated_unix':time.time(),**details})
    print(state, details,flush=True)


def command(args, log):
    with (LOGS/log).open('w',encoding='utf-8') as stream:
        subprocess.run([str(PY),*args],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)


def main():
    LOGS.mkdir(parents=True,exist_ok=True)
    inputs=RUN/'inputs_prompt_dev/agent_inputs.jsonl'
    status('waiting_for_offline_inputs')
    while not (inputs.parent/'manifest.json').exists():
        for directory in ('encoder','g','inputs_prompt_dev'):
            path=RUN/directory/'status.json'
            if path.exists() and read_json(path).get('state')=='failed':
                raise RuntimeError('Offline stage failed: '+directory)
        time.sleep(10)
    status('auditing_real_inputs')
    command(['scripts/audit_real_agent_inputs.py','--bundle','bundle','--encoder',str(RUN/'encoder'),
             '--g',str(RUN/'g'),'--inputs',str(inputs),'--output',str(RUN/'input_audit.json')],'input_audit.log')
    status('waiting_for_qwen_download')
    while 'Qwen environment and frozen model ready' not in (LOGS/'qwen_setup.log').read_text(errors='replace'):
        time.sleep(10)
    status('starting_vllm')
    healthy=False
    try: healthy=httpx.get('http://127.0.0.1:8000/health',timeout=3,trust_env=False).status_code==200
    except httpx.HTTPError: pass
    process=None
    if not healthy:
        stream=(LOGS/'vllm.log').open('a',encoding='utf-8')
        process=subprocess.Popen(['bash','scripts/start_agent_vllm.sh'],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
        write_json(RUN/'vllm_process.json',{'pid':process.pid})
    started=time.monotonic()
    while not healthy:
        if process is not None and process.poll() is not None:
            raise RuntimeError('vLLM failed to start; see vllm.log')
        if time.monotonic()-started>1200:
            raise RuntimeError('vLLM readiness exceeded 20 minutes')
        try: healthy=httpx.get('http://127.0.0.1:8000/health',timeout=3,trust_env=False).status_code==200
        except httpx.HTTPError: pass
        time.sleep(5)
    status('collecting_two_pair_probe')
    command(['scripts/audit_agent_token_budget.py','--input',str(inputs),'--output',str(RUN/'token_budget.json')],'token_budget.log')
    probe=RUN/'feedback_probe.jsonl'
    if not probe.exists() or len(probe.read_text().splitlines())!=2:
        command(['scripts/collect_agent_feedback.py','--input',str(inputs),'--output',str(probe),
                 '--model','Qwen/Qwen3-30B-A3B-Instruct-2507-FP8','--limit','2','--overwrite'],'probe.log')
    status('collecting_v5_pairs',workers=4)
    command(['scripts/finalize_real_agent_pilot.py'],'finalization.log')
    result=read_json(RUN/'result_summary.json')
    status('complete',pairs=result['pairs'],judgments=result['judgments'],prompt_version=result['prompt_version'])


if __name__=='__main__':
    try: main()
    except Exception as exc:
        status('failed',error=str(exc))
        raise
