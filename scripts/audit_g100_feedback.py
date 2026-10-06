"""Independently check IDs and recompute probabilities, entropy and label mass."""
import math
from agent_pipeline_common import rows, sha256, write_json
from collect_agent_feedback import ROLES


def audit(inputs, feedback, expected, version, output):
    source={r['pair_id']:r for r in rows(inputs)}
    completed=list(rows(feedback)); seen=set(); minimum_mass=1.0
    assert len(completed)==expected,(len(completed),expected)
    for record in completed:
        pair=record['pair_id']; assert pair in source and pair not in seen;seen.add(pair)
        assert record['source_user_id']==source[pair]['source_user_id']
        assert record['target_item_id']==source[pair]['target_item_id']
        assert record['prompt_version']==version and set(record['agents'])==set(ROLES)
        for result in record['agents'].values():
            scores=result['label_logprobs']; assert set(scores)=={'A','B','C'}
            assert all(math.isfinite(v) for v in scores.values())
            peak=max(scores.values()); weights={k:math.exp(v-peak) for k,v in scores.items()}
            probabilities={k:v/sum(weights.values()) for k,v in weights.items()}
            entropy=-sum(p*math.log(p) for p in probabilities.values() if p>0)
            mass=sum(math.exp(v) for v in scores.values());minimum_mass=min(minimum_mass,mass)
            assert .5 <= mass <= 1.0001,'Unusable label probability mass'
            assert result['prediction']==max(('A','B','C'),key=lambda k:probabilities[k])
            for k in probabilities: assert math.isclose(probabilities[k],result['label_probabilities'][k],abs_tol=1e-12)
            assert math.isclose(mass,result['label_mass'],abs_tol=1e-12)
            assert math.isclose(1-entropy/math.log(3),result['confidence'],abs_tol=1e-12)
            assert isinstance(result['reasoning'],str) and result['reasoning'].strip()
    report={'state':'passed','pairs':expected,'judgments':expected*4,'prompt_version':version,
            'minimum_label_mass':minimum_mass,'feedback_sha256':sha256(feedback),'input_sha256':sha256(inputs),
            'checks':'identity;role completeness;all ABC logprobs;independent normalization/entropy/mass',
            'judgment_quality_validated':False}
    write_json(output,report);return report
