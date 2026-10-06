"""Verify feedback completeness/probability arithmetic and summarize pilot outputs."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import math
from pathlib import Path
import numpy as np
from agent_pipeline_common import read_json, rows, sha256, write_json
from collect_agent_feedback import LABELS, ROLES, PROMPT_VERSION


def summarize(inputs, feedback, output, bundle=None):
    inputs_by_id={r['pair_id']:r for r in rows(inputs)}
    outputs=list(rows(feedback))
    assert len(outputs)==len(inputs_by_id)==len({r['pair_id'] for r in outputs})
    assert {r['pair_id'] for r in outputs}==set(inputs_by_id)
    stats={}
    for role in ROLES:
        labels=Counter()
        confidences,masses=[],[]
        for row in outputs:
            assert row['prompt_version']==outputs[0]['prompt_version']
            expected=inputs_by_id[row['pair_id']]
            assert row['source_user_id']==expected['source_user_id'] and row['target_item_id']==expected['target_item_id']
            agent=row['agents'][role]
            logprobs=agent['label_logprobs']
            offset=max(logprobs.values())
            weights={label:math.exp(logprobs[label]-offset) for label in LABELS}
            total=sum(weights.values())
            probs={label:weights[label]/total for label in LABELS}
            for label in LABELS:
                assert math.isclose(probs[label],agent['label_probabilities'][label],abs_tol=1e-12)
            entropy=-sum(p*math.log(p) for p in probs.values() if p>0)
            confidence=max(0,min(1,1-entropy/math.log(3)))
            assert math.isclose(confidence,agent['confidence'],abs_tol=1e-12)
            assert agent['prediction']==max(LABELS,key=lambda label:probs[label])
            mass=sum(math.exp(logprobs[label]) for label in LABELS)
            assert math.isclose(mass,agent['label_mass'],abs_tol=1e-12)
            assert len(set(agent['label_token_ids'].values()))==3
            assert agent['reasoning'].strip()
            labels[agent['prediction']]+=1
            confidences.append(confidence)
            masses.append(mass)
        stats[role]={'labels':{label:labels[label] for label in LABELS},'mean_confidence':float(np.mean(confidences)),
                     'median_confidence':float(np.median(confidences)),'min_confidence':min(confidences),
                     'confidence_ge_095_share':float(np.mean(np.asarray(confidences)>=.95)),
                     'mean_label_mass':float(np.mean(masses)),'min_label_mass':min(masses),
                     'low_label_mass_count':sum(mass<.5 for mass in masses)}
    examples=sorted(outputs,key=lambda r:(-len({r['agents'][role]['prediction'] for role in ROLES}),r['pair_id']))[:3]
    result={'state':'complete_verified','pairs':len(outputs),'users':len({r['source_user_id'] for r in outputs}),
            'judgments':len(outputs)*len(ROLES),'prompt_version':outputs[0]['prompt_version'],'roles':stats,
            'inputs_sha256':sha256(inputs),'feedback_sha256':sha256(feedback),
            'confidence_is_correctness_probability':False,'held_out_target_accuracy_evaluated':False,
            'examples':[{'input':inputs_by_id[r['pair_id']],'output':r} for r in examples]}
    if bundle:
        mapping=read_json(Path(bundle)/'id_mapping.json')
        with np.load(Path(bundle)/'interactions.npz',allow_pickle=False) as arrays: source=arrays['source']
        selected={row['source_user_id'] for row in outputs}
        source_asins=defaultdict(set)
        for user,item in source[np.isin(source[:,0],list(selected))]:
            source_asins[int(user)].add(mapping['src']['id2item'][int(item)])
        shared=sum(mapping['tgt']['id2item'][row['target_item_id']] in source_asins[row['source_user_id']] for row in outputs)
        result['candidate_same_asin_as_source_history_count']=shared
    write_json(output,result)
    print({k:v for k,v in result.items() if k!='examples'},flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['inputs','feedback','output']: parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--bundle',type=Path)
    args=parser.parse_args()
    summarize(args.inputs,args.feedback,args.output,args.bundle)
