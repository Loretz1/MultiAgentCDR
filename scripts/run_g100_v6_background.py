"""Run paired diagnostics and resume frozen full v6 collection unattended."""
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from agent_pipeline_common import rows, read_json, sha256, write_json
import collect_g100_feedback as collector
from collect_agent_feedback import make_messages, user_prompt, VLLMClient, ROLES
from audit_g100_feedback import audit

ROOT=Path(__file__).resolve().parents[1]
MODEL='Qwen/Qwen3-30B-A3B-Instruct-2507-FP8'
API='http://127.0.0.1:8000/v1'


def status(stage, **extra):
    value={'stage':stage,'pid':os.getpid(),'updated_unix':time.time(),'v6_expected_pairs':15600,
           'v5_expected_pairs':200,**extra}
    write_json(ROOT/'experiment_status.json',value)
    print(json.dumps(value),flush=True)


def collect(style, input_name, output_name, limit=0):
    path=ROOT/'outputs'/output_name
    command=[sys.executable,'-u',str(ROOT/'scripts/collect_g100_feedback.py'),
             '--input',str(ROOT/'inputs'/input_name),'--output',str(path),'--prompt-style',style,
             '--workers','4','--timeout','180','--base-url',API,'--model',MODEL]
    for attempt in range(1,4):
        summary_path=path.with_suffix('.summary.json')
        previous=read_json(summary_path) if summary_path.exists() else {}
        remaining=limit-previous.get('completed',0) if limit else 0
        if limit and remaining<=0:return path
        attempt_command=command+(['--limit-new',str(remaining)] if limit else [])
        with (ROOT/'logs'/f'{style}_attempts.log').open('a',encoding='utf-8') as log:
            log.write(f'\nAttempt {attempt}, limit_new={limit}\n');log.flush()
            result=subprocess.run(attempt_command,stdout=log,stderr=subprocess.STDOUT,cwd=ROOT)
        summary=read_json(path.with_suffix('.summary.json')) if path.with_suffix('.summary.json').exists() else {}
        expected=limit if limit else (15600 if style=='v6' else 200)
        if result.returncode==0 and summary.get('completed',0)>=expected:return path
        status('retrying_'+style,attempt=attempt,completed=summary.get('completed',0),returncode=result.returncode)
        time.sleep(3)
    raise RuntimeError(f'{style} collection failed after three attempts; successful outputs retained')


def main():
    (ROOT/'outputs').mkdir(exist_ok=True);(ROOT/'logs').mkdir(exist_ok=True)
    status('verifying_package')
    frozen=read_json(ROOT/'package_manifest.json')
    for name, expected in frozen['files'].items():assert sha256(ROOT/name)==expected,('File hash mismatch',name)
    versions={name:importlib.metadata.version(name) for name in ('vllm','torch','transformers','httpx','numpy')}
    write_json(ROOT/'outputs/runtime_versions.json',versions)
    with VLLMClient(API,MODEL,30) as client:client.check_model()
    full=list(rows(ROOT/'inputs/full.jsonl'));pilot=list(rows(ROOT/'inputs/pilot.jsonl'))
    assert len(full)==15600 and len(pilot)==200 and full[:200]==pilot
    assert len({r['source_user_id'] for r in pilot})==156
    assert len({r['pair_id'] for r in full})==15600
    status('checking_token_budget')
    token_results={}
    with VLLMClient(API,MODEL,180) as client:
        for style in ('v5_short','v6'):
            collector.configure_prompt(style); maxima={}
            for role in ROLES:
                # All paired examples plus the ten longest payloads in the full population.
                largest=sorted(full,key=lambda r:len(user_prompt(r,role)),reverse=True)[:10]
                checks={r['pair_id']:r for r in pilot+largest}
                lengths=[len(client.tokenize([*make_messages(r,role,'score'),
                    {'role':'assistant','content':'Reasoning: Evidence review.\nPrediction:'}])) for r in checks.values()]
                maximum=max(lengths);assert maximum+160<=8192,(style,role,maximum)
                maxima[role]={'checked_pairs':len(checks),'max_prefix_tokens':maximum,'reserved_tokens':160}
            token_results[style]=maxima
    write_json(ROOT/'outputs/token_budget.json',{'state':'passed','max_context':8192,'styles':token_results,
        'scope':'200 diagnostic pairs plus ten longest rendered user payloads per role/style;not exhaustive full tokenization'})
    status('collecting_v6_diagnostic')
    v6=collect('v6','full.jsonl','v6_feedback.jsonl',200)
    collector.configure_prompt('v6')
    audit(ROOT/'inputs/full.jsonl',v6,200,collector.PROMPT_VERSION,ROOT/'outputs/v6_diagnostic_audit.json')
    status('collecting_v5_diagnostic')
    v5=collect('v5_short','pilot.jsonl','v5_feedback.jsonl')
    collector.configure_prompt('v5_short')
    audit(ROOT/'inputs/pilot.jsonl',v5,200,collector.PROMPT_VERSION,ROOT/'outputs/v5_diagnostic_audit.json')
    status('collecting_v6_full',v6_completed_pairs=200,numerical_interface_passed=True,
           judgment_quality_validated=False)
    v6=collect('v6','full.jsonl','v6_feedback.jsonl')
    collector.configure_prompt('v6')
    report=audit(ROOT/'inputs/full.jsonl',v6,15600,collector.PROMPT_VERSION,ROOT/'outputs/v6_full_audit.json')
    status('complete',v6_completed_pairs=15600,v5_completed_pairs=200,audit=report)


if __name__=='__main__':
    try:main()
    except Exception as error:
        status('failed',error_type=type(error).__name__,error=str(error));raise
