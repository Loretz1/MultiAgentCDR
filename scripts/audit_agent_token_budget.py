"""Check every real role prompt against the serving tokenizer and 4096 context."""
import argparse
from pathlib import Path
import numpy as np
from agent_pipeline_common import rows, write_json
from collect_agent_feedback import VLLMClient, make_messages, ROLES


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    lengths={role:[] for role in ROLES}
    with VLLMClient('http://127.0.0.1:8000/v1','Qwen/Qwen3-30B-A3B-Instruct-2507-FP8',180) as client:
        client.check_model()
        for record in rows(args.input):
            for role in ROLES:
                messages=[*make_messages(record,role,'score'),{'role':'assistant','content':'Reasoning: '}]
                length=len(client.tokenize(messages))
                if length+160>4096:
                    raise RuntimeError('Prompt exceeds safe context reserve: '+record['pair_id']+' '+role)
                lengths[role].append(length)
    result={'state':'passed','context_limit':4096,'reasoning_and_label_reserve':160,
            'role_tokens':{role:{'count':len(values),'max':max(values),'mean':round(float(np.mean(values)),2)} for role,values in lengths.items()}}
    write_json(args.output,result)
    print(result,flush=True)


if __name__=='__main__': main()
