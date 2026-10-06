import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from collect_real_agent_feedback import run,configure_prompt,BASE_SYSTEM_PROMPT
import collect_agent_feedback as base_collector
from collect_agent_feedback import PipelineError, ROLES, PROMPT_VERSION
from agent_pipeline_common import read_json


class SchedulingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        root=Path(self.temp.name)
        self.records=[{'pair_id':str(n),'source_user_id':1,'target_item_id':n,'source_preference':'Fixture',
                      'candidate_description':'Fixture','evidence':{role:{'fixture':True} for role in ROLES}} for n in (1,2)]
        (root/'input.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in self.records))
        self.args=SimpleNamespace(input=root/'input.jsonl',output=root/'feedback.jsonl',model='fixture_model',workers=2,
                                  base_url='http://fixture',timeout=10,min_label_mass=.5)
    def tearDown(self): self.temp.cleanup()
    def result(self,record,*args):
        return {'pair_id':record['pair_id'],'model':'fixture_model','prompt_version':PROMPT_VERSION,
                'agents':{role:{'fixture':True} for role in ROLES},'elapsed_seconds':0.01}
    def test_successful_resume_and_config_rejection(self):
        with patch('collect_real_agent_feedback.VLLMClient'),patch('collect_real_agent_feedback.collect_pair',side_effect=self.result) as worker:
            run(self.args)
            run(self.args)
            self.assertEqual(worker.call_count,2)
            self.assertEqual(read_json(self.args.output.with_suffix('.summary.json'))['completed'],2)
            self.args.workers=1
            with self.assertRaisesRegex(PipelineError,'configuration/input changed'): run(self.args)
    def test_failed_pair_retained_and_only_failed_pair_resumed(self):
        def fail(record,*args):
            if record['pair_id']=='2': raise PipelineError('fixture failure')
            return self.result(record)
        with patch('collect_real_agent_feedback.VLLMClient'),patch('collect_real_agent_feedback.collect_pair',side_effect=fail):
            with self.assertRaisesRegex(PipelineError,'failed pairs'): run(self.args)
        self.assertEqual(read_json(self.args.output.with_suffix('.summary.json'))['state'],'partial')
        with patch('collect_real_agent_feedback.VLLMClient'),patch('collect_real_agent_feedback.collect_pair',side_effect=self.result) as worker:
            run(self.args)
            self.assertEqual(worker.call_count,1)
            self.assertEqual({json.loads(line)['pair_id'] for line in self.args.output.read_text().splitlines()},{'1','2'})
    def test_short_reason_style_preserves_label_prompt_and_decision_rules(self):
        configure_prompt('v5_short')
        self.assertEqual(base_collector.system_prompt('semantic','score'),BASE_SYSTEM_PROMPT('semantic','score'))
        self.assertTrue(base_collector.system_prompt('popularity_bias','reason').startswith(BASE_SYSTEM_PROMPT('popularity_bias','reason')))
        self.assertIn('at most 35 words',base_collector.system_prompt('popularity_bias','reason'))
        configure_prompt('v4')


if __name__=='__main__': unittest.main()
