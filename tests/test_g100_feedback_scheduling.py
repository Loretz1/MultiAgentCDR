import json
from pathlib import Path
import sys
import tempfile
import math
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import collect_g100_feedback as collector
import collect_agent_feedback as base
from agent_pipeline_common import read_json
import run_g100_v6_background as background
from audit_g100_feedback import audit


class G100SchedulingTests(unittest.TestCase):
    def tearDown(self):collector.configure_prompt('v4')

    def test_capped_run_resumes_without_changing_request_or_repeating_pairs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            records=[{'pair_id':str(n),'source_user_id':1,'target_item_id':n,
                'source_preference':'Fixture','candidate_description':'Fixture',
                'evidence':{role:{'fixture':True} for role in base.ROLES}} for n in (1,2)]
            source=root/'input.jsonl';source.write_text(''.join(json.dumps(r)+'\n' for r in records),encoding='utf-8')
            args=SimpleNamespace(input=source,output=root/'out.jsonl',model='fixture',workers=2,
                base_url='http://fixture/v1',timeout=10,min_label_mass=.5,prompt_style='v6',limit_new=1)
            def result(record,*unused):
                return {'pair_id':record['pair_id'],'model':'fixture','prompt_version':collector.PROMPT_VERSION,
                        'agents':{role:{} for role in base.ROLES},'elapsed_seconds':.01}
            with patch.object(collector,'VLLMClient'),patch.object(collector,'collect_pair',side_effect=result) as worker:
                collector.run(args)
                request=read_json(args.output.with_suffix('.request.json'))
                self.assertEqual(read_json(args.output.with_suffix('.summary.json'))['state'],'partial_by_limit')
                args.limit_new=0;collector.run(args)
                self.assertEqual(worker.call_count,2)
                self.assertEqual(request,read_json(args.output.with_suffix('.request.json')))
                self.assertEqual(read_json(args.output.with_suffix('.summary.json'))['state'],'complete')
                args.prompt_style='v5_short'
                with self.assertRaisesRegex(base.PipelineError,'configuration/input changed'):collector.run(args)

    def test_v6_then_v5_restores_original_score_prompt_and_question(self):
        collector.configure_prompt('v6')
        self.assertNotEqual(base.ROLE_QUESTIONS,collector.BASE_QUESTIONS)
        collector.configure_prompt('v5_short')
        self.assertEqual(base.ROLE_QUESTIONS,collector.BASE_QUESTIONS)
        for role in base.ROLES:
            self.assertEqual(base.system_prompt(role,'score'),collector.BASE_SYSTEM_PROMPT(role,'score'))

    def test_role_payloads_are_isolated(self):
        record={'source_preference':'Visible history','candidate_description':'Visible catalog',
                'evidence':{role:{'marker':'only_'+role} for role in base.ROLES}}
        collector.configure_prompt('v6')
        for role in base.ROLES:
            prompt=base.user_prompt(record,role)
            for other in base.ROLES:
                self.assertEqual('only_'+other in prompt,role==other)

    def test_warmup_retry_only_requests_remaining_pairs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'outputs').mkdir();(root/'logs').mkdir()
            calls=[]
            def execute(command,**unused):
                calls.append(command)
                summary={'completed':198 if len(calls)==1 else 200}
                (root/'outputs/v6.summary.json').write_text(json.dumps(summary),encoding='utf-8')
                return SimpleNamespace(returncode=1 if len(calls)==1 else 0)
            with patch.object(background,'ROOT',root),patch.object(background.subprocess,'run',side_effect=execute),patch.object(background.time,'sleep'):
                background.collect('v6','full.jsonl','v6.jsonl',200)
            self.assertEqual(calls[0][-2:],['--limit-new','200'])
            self.assertEqual(calls[1][-2:],['--limit-new','2'])

    def test_numerical_audit_rejects_modified_confidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'input.jsonl';feedback=root/'feedback.jsonl'
            source.write_text(json.dumps({'pair_id':'x','source_user_id':1,'target_item_id':2})+'\n',encoding='utf-8')
            p={'A':.6,'B':.3,'C':.1}
            confidence=1+sum(v*math.log(v) for v in p.values())/math.log(3)
            result={'prediction':'A','reasoning':'Visible evidence supports A.','label_probabilities':p,
                    'label_logprobs':{k:math.log(v*.9) for k,v in p.items()},'confidence':confidence,'label_mass':.9}
            row={'pair_id':'x','source_user_id':1,'target_item_id':2,'prompt_version':'fixture',
                 'agents':{role:dict(result) for role in base.ROLES}}
            feedback.write_text(json.dumps(row)+'\n',encoding='utf-8')
            audit(source,feedback,1,'fixture',root/'audit.json')
            row['agents']['semantic']['confidence']=.99
            feedback.write_text(json.dumps(row)+'\n',encoding='utf-8')
            with self.assertRaises(AssertionError):audit(source,feedback,1,'fixture',root/'audit.json')


if __name__=='__main__':unittest.main()
