"""Persist the assistant's case-by-case review of 50 frozen visible-only cases.

Annotations were assigned after reading the 200 role reasons and their evidence;
the identifiers below are explicit judgments, not an automated keyword classifier.
No hidden target feedback is read. An unflagged output is not proven correct.
"""
from collections import Counter
import csv
import json

from agent_pipeline_common import read_json, rows, sha256, write_json, utc_now
from evaluate_agent_pilot import OUT, ROLES


# Fact errors are separated from debatable support criteria and causal hypotheses.
FACTS = {
 ('42:14054','semantic'): [('invented_rating_average','理由称4条正评价平均5.0星；实际4/4/5/5星，均值4.5。')],
 ('1773:7553','semantic'): [('description_vector_confusion','missing_target_description=true，但missing_target_text_vector=false；缺少描述不等于文本向量不存在。')],
 ('1773:5292','semantic'): [('false_absence_of_source_evidence','理由称源正历史没有socks；输入列出4星New Balance袜子且matched_concepts含socks。')],
 ('2174:46','semantic'): [('unavailable_target_rating_claim','理由将没有目标域正评分当作局限；Semantic输入不提供该用户隐藏目标评分，不能作此事实断言。')],
 ('42:14055','collaborative'): [('mapping_scope_confusion','2816是跨域映射训练用户数，不是物品热度；own evidence没有支持“邻居支持低”的计数。')],
 ('42:14764','collaborative'): [('mapping_scope_confusion','2816位映射用户不能直接证明候选邻居可靠。')],
 ('1365:9741','collaborative'): [('target_source_user_confusion','7是候选目标可见训练用户数，不是源用户数。')],
 ('1365:7337','collaborative'): [('target_source_user_confusion','6是候选目标可见训练用户数，不是源用户数。'),('mapping_scope_confusion','2816映射用户不是物品热门度。')],
 ('1365:5822','collaborative'): [('false_absence_of_target_support','理由说训练中没有可见目标支持；candidate_visible_train_users=266。')],
 ('1365:2456','collaborative'): [('mapping_scope_confusion','375位候选训练用户和2816映射用户不能推出“足够邻居证据”；no observed target support表述范围不清。')],
 ('1773:5292','collaborative'): [('mapping_scope_confusion','2816映射用户被解释成物品热门度，证据类型错误。')],
 ('1773:5822','collaborative'): [('false_absence_of_target_support','理由说训练中没有目标支持；candidate_visible_train_users=266。')],
 ('1991:6506','collaborative'): [('percentile_direction_reversed','理由称99.98排名百分位很低；该字段数值越高代表排名越靠前。'),('mapping_scope_confusion','映射训练人数不能推断源用户交集稀疏程度。')],
 ('2174:46','collaborative'): [('mapping_scope_confusion','145候选训练用户及2816映射用户不能证明邻居交集充分。')],
 ('2174:15025','collaborative'): [('invented_exposure','2816映射用户不是物品曝光指标，输入没有曝光日志。')],
 ('42:15483','popularity_bias'): [('rate_comparison_reversed','理由称平滑局部率6.7%接近全局0.12%；实际约56倍，比较错误。')],
 ('1773:7399','popularity_bias'): [('rate_comparison_reversed','理由称局部5.88%远低于全局0.65%；实际局部约9倍于全局。')],
 ('1991:2634','popularity_bias'): [('rate_comparison_reversed','理由称局部5%远低于全局0.28%；实际局部约17.6倍于全局。')],
 ('2174:1825','popularity_bias'): [('invented_ranking_denominator','理由给出热门排名5465/7740；证据没有7740这个分母，目标目录18357件。')],
}
EXPOSURE_ASSERTIONS = {
 '1365:5822','1365:2456','1365:37','1773:9068','2174:3388',
}
VISIBILITY_ASSERTIONS = {
 '42:15748','1365:8587','1365:6672','1773:1371','1991:3388',
 '1991:46','1991:6506','2174:15025','2174:15121',
}
# Inferences that need revised criteria; do not count these as exact numerical errors.
POP_INFERENCE_REVIEW = {
 '42:14055','42:15748','42:14764','42:13517','42:14060','42:15483','42:16722',
 '1365:4069','1365:5822','1365:2456','1365:7137','1365:6672','1365:18157','1365:37','1365:7337',
 '1773:1371','1773:11712','1773:12349','1773:7399','1773:9068','1773:15269',
 '1991:3388','1991:13437','1991:2634','1991:46','1991:2786','1991:14663','1991:6506','1991:15190',
 '2174:3388','2174:12562','2174:46','2174:5973','2174:7579','2174:15025','2174:1371',
 '2174:1825','2174:732','2174:15121',
}
SPECIAL = {
 ('42:14055','semantic'): [('reason_label_tension','A但理由明确称强语义迁移证据有限；watch来自修表工具而非正评价腕表，collection来自通用类别。')],
 ('42:13979','semantic'): [('generic_concept_transfer','collection是通用词；watch来自工具，银饰与银色腕表的迁移强度需要准则。')],
 ('42:14060','semantic'): [('generic_concept_transfer','watch来自修表工具，不能单独当作喜爱腕表的强证据；A需复核。')],
 ('42:14061','semantic'): [('generic_concept_transfer','collection与watch/tool不能直接当作腕表偏好的强依据。')],
 ('42:16722','semantic'): [('generic_concept_transfer','yellow把黄金饰品与黄色胶带联系起来；字面匹配不等于产品用途迁移。')],
 ('1365:2456','semantic'): [('reason_label_tension','唯一字面词pack；全目录rank13692，理由称支持有限却判A，依据薄弱。')],
 ('2174:732','semantic'): [('generic_concept_transfer','fashion是通用类别词；源正评价鞋/太阳镜不直接支持腕表。')],
 ('1991:13437','overlap'): [('strong_weak_boundary','14/20直接支持仍判B；相邻样例17/20直接支持判A，阈值/样本充分性需明确。')],
 ('42:13517','overlap'): [('rating_availability_penalty','Overlap依据是观察到的训练交互；缺少明确正评分不应额外推断为缺少直接行为支持。')],
 ('1773:7399','overlap'): [('support_scope_ambiguity','仅1人直接支持候选不意味着只有1位重叠用户具有跨域历史；actual_neighbors=17。')],
}
SEMANTIC_REFERENCE = {
 42:{14055:'B',15748:'C',13979:'B',14764:'C',13517:'C',14060:'B',14061:'B',15483:'C',14054:'B',16722:'C'},
 1365:{4069:'C',8587:'A',5822:'C',9741:'A',2456:'C',7137:'A',6672:'C',18157:'A',37:'C',7337:'A'},
 1773:{1371:'C',7553:'A',11712:'C',12349:'A',7399:'C',16236:'A',5292:'A',5822:'C',9068:'B',15269:'A'},
 1991:{3388:'C',13437:'A',2634:'C',12064:'A',46:'C',2786:'A',4:'C',14663:'A',6506:'C',15190:'A'},
 2174:{3388:'C',12562:'A',46:'C',5973:'A',7579:'C',15025:'C',1371:'C',1825:'B',732:'C',15121:'C'},
}


def main():
    cases=list(rows(OUT/'review_inputs.jsonl'))
    assert len(cases)==50
    reviews=[]
    known=set()
    for case in cases:
        r=case['input'];uid=r['source_user_id'];item=r['target_item_id'];key=f'{uid}:{item}'
        known.add(key)
        for role in ROLES:
            a=case['output']['agents'][role];e=r['evidence'][role]
            facts=list(FACTS.get((key,role),[]));concerns=list(SPECIAL.get((key,role),[]))
            if role=='popularity_bias':
                if key in EXPOSURE_ASSERTIONS:facts.append(('invented_exposure','exposure_available=false，理由仍断言global exposure高。'))
                if key in VISIBILITY_ASSERTIONS:concerns.append(('unsupported_visibility','热门度/交互数不能识别实际曝光或visibility，曝光字段不可用。'))
                if key in POP_INFERENCE_REVIEW:concerns.append(('unsupported_bias_attribution','理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。'))
                if e['local_support_users']>=4 and e['relative_support']>1 and a['prediction']=='C':
                    concerns.append(('enrichment_ignored','局部支持多人且平滑后高于全局，仍拒绝；需说明样本充分性和全局基准，而非热门即拒绝。'))
            reference='U';reference_note='当前准则不足以给出独立可靠ABC金标签，保留人工确认。'
            if role=='semantic':
                reference=SEMANTIC_REFERENCE[uid][item]
                reference_note='助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。'
            elif role=='overlap':
                if not e['union_support_users']:reference='C'
                elif e['direct_support_users']>=10:reference='A'
                else:reference='B'
                reference_note='助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。'
            elif role=='collaborative' and e['rank']<=5 and e['g_raw']>0:
                reference='A';reference_note='助手暂定：此候选在G自身Top5且正分，支持A；分数/排名不解释为交互概率。'
            elif role=='popularity_bias' and e['local_support_users']>=4:
                reference='A_or_B';reference_note='明显局部富集至少需讨论A/B；样本小和全局分母稀疏，不能凭比率给确定A，更不能从热门直接断言偏差。'
            status='confirmed_evidence_error' if facts else 'needs_criteria_review' if concerns else 'no_specific_error_found'
            reviews.append({'pair_id':r['pair_id'],'user_id':uid,'item_id':item,'role':role,
                'prediction':a['prediction'],'reasoning':a['reasoning'],'confidence':a['confidence'],
                'reviewer':'AI_assistant','review_status':status,
                'fact_errors':[{'type':t,'explanation':v} for t,v in facts],
                'inference_or_criteria_concerns':[{'type':t,'explanation':v} for t,v in concerns],
                'provisional_reference_label':reference,'reference_note':reference_note,
                'expert_confirmed':False,'hidden_target_labels_used':False})
    assert set(FACTS.keys()) <= {(key,role) for key in known for role in ROLES}
    assert (EXPOSURE_ASSERTIONS|VISIBILITY_ASSERTIONS|POP_INFERENCE_REVIEW) <= known
    assert len(reviews)==200
    with (OUT/'assistant_review.jsonl').open('w',encoding='utf-8') as f:
        for r in reviews:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    stats={}
    for role in ROLES:
        selected=[r for r in reviews if r['role']==role]
        stats[role]={'reviewed':len(selected),'confirmed_evidence_error_outputs':sum(bool(r['fact_errors']) for r in selected),
                     'inference_or_criteria_concern_outputs':sum(bool(r['inference_or_criteria_concerns']) for r in selected),
                     'statuses':dict(Counter(r['review_status'] for r in selected))}
    write_json(OUT/'assistant_review_summary.json',{'reviewer':'AI_assistant','cases':50,'role_outputs':200,
               'expert_gold_labels':False,'hidden_target_labels_used':False,'roles':stats,
               'annotation_source_sha256':sha256(__file__),'completed_at':utc_now(),
               'notes':'purposive cases; provisional references not universal thresholds; no specific error found is not correctness'})
    text='# AI助手证据复核：50对 / 200角色输出\n\n按原输入逐条审阅，未读取隐藏目标反馈。不是独立人工金标签；暂定ABC供研究者讨论，不用于计算模型准确率或自动作为few-shot。U表示准则不足，A_or_B表示需要人工判断支持强度。无具体错误记录不代表输出正确。\n'
    for case in cases:
        pair=case['input']['pair_id']
        text+='\n## '+pair+'\n\n'+case['input']['candidate_description'].split('\n')[0]+'\n'
        for r in [r for r in reviews if r['pair_id']==pair]:
            text+='\n### '+r['role']+'\n\n'+f'原预测：{r["prediction"]}；Confidence：{r["confidence"]:.6f}；助手暂定参考：{r["provisional_reference_label"]}；状态：{r["review_status"]}。\n\n'
            text+='原理由：'+r['reasoning']+'\n\n'
            for issue in r['fact_errors']+r['inference_or_criteria_concerns']:text+='- '+issue['type']+'：'+issue['explanation']+'\n'
            if not r['fact_errors'] and not r['inference_or_criteria_concerns']:text+='本轮未发现明确事实错误；不表示已证明ABC正确。\n'
            text+='\n参考说明：'+r['reference_note']+'\n'
    (OUT/'assistant_review.md').write_text(text,encoding='utf-8')
    print(json.dumps(stats,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
