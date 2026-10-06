"""Select a paired prompt diagnostic sample using visible evidence only."""
import argparse
import json
from collections import defaultdict
from pathlib import Path
import random
import shutil
from agent_pipeline_common import rows, read_json, sha256, write_json
from collect_agent_feedback import validate_record


def prepare(source, output):
    records = list(rows(source / 'agent_inputs.jsonl'))
    manifest = read_json(source / 'manifest.json')
    assert manifest['request']['config']['group'] == 'prompt_dev'
    assert len(records) == 15600
    users = defaultdict(list)
    identifiers = set()
    for n, record in enumerate(records, 1):
        validate_record(record, n)
        assert record['pair_id'] not in identifiers
        identifiers.add(record['pair_id'])
        users[record['source_user_id']].append(record)
    assert set(users) == set(manifest['users']) and len(users) == 156
    assert all(len(group) == 100 and {r['evidence']['collaborative']['rank'] for r in group} == set(range(1,101)) for group in users.values())
    rng = random.Random(999)
    selected = [rng.choice(sorted(users[u],key=lambda r:r['evidence']['collaborative']['rank'])) for u in sorted(users)]
    used = {r['pair_id'] for r in selected}
    # Enrich the diagnostic sample with direct-support and rank extremes.
    # No target outcomes are loaded or consulted.
    pools = [sorted(records,key=lambda r:(-r['evidence']['overlap']['direct_support_users'],r['pair_id'])),
             sorted(records,key=lambda r:(r['evidence']['overlap']['union_support_users'],r['pair_id'])),
             sorted(records,key=lambda r:(r['evidence']['collaborative']['rank'],r['pair_id'])),
             sorted(records,key=lambda r:(-r['evidence']['collaborative']['rank'],r['pair_id']))]
    cursors = [0]*4
    while len(selected) < 200:
        for p, pool in enumerate(pools):
            while pool[cursors[p]]['pair_id'] in used: cursors[p] += 1
            record=pool[cursors[p]]; cursors[p]+=1
            selected.append(record); used.add(record['pair_id'])
            if len(selected)==200: break
    output.mkdir(parents=True,exist_ok=True)
    def save(name, data):
        with (output/name).open('w',encoding='utf-8',newline='\n') as stream:
            for record in data: stream.write(json.dumps(record,ensure_ascii=False,allow_nan=False)+'\n')
    save('pilot.jsonl',selected)
    save('full.jsonl',selected+[r for r in records if r['pair_id'] not in used])
    shutil.copyfile(source/'manifest.json',output/'manifest.json')
    write_json(output/'selection.json',{'seed':999,'pairs':200,'users':156,'pair_ids':[r['pair_id'] for r in selected],
        'rule':'one uniform rank per development user;44 additions round-robin direct-support high,union-support low,G rank high and low',
        'hidden_target_feedback_read':False,'source_input_sha256':sha256(source/'agent_inputs.jsonl'),
        'full_sha256':sha256(output/'full.jsonl'),'pilot_sha256':sha256(output/'pilot.jsonl'),
        'population_pairs':len(records),'population_users':len(users)})
    print(json.dumps({'state':'passed','pairs':len(records),'users':len(users),'diagnostic_pairs':len(selected)}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();prepare(args.source,args.output)
