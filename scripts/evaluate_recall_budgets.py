"""Evaluate nested Top10/20/50/100 prefixes of three frozen recall rankings.

Uses existing visible-only rankings and development evaluation artifacts.
No rescoring, model loading, internal validation, formal test, or LLM calls.
"""
import csv
import json
from pathlib import Path
import math
import time
from agent_pipeline_common import ROOT, read_json, rows, sha256, write_json, stage, complete_stage, verify_files, utc_now, file_records
from diagnose_candidate_recall import summarize

POP=ROOT/'doc/experiments/2026-10-06_popularity_recall'
OTHER=ROOT/'doc/experiments/2026-10-06_candidate_recall'
OUT=ROOT/'doc/experiments/2026-10-06_recall_budgets'
BUDGETS=(10,20,50,100)
METHODS=('popularity','g','semantic')
NAMES={'popularity':'Popularity','g':'G','semantic':'语义'}


def table(headers, records):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+
        ['| '+' | '.join(map(str,record))+' |' for record in records])


def native_table(headers, records):
    lines=['<table header-row="true">']
    for record in [headers,*records]:
        lines+=['<tr>']+['<td>'+str(value)+'</td>' for value in record]+['</tr>']
    return '\n'.join(lines+['</table>'])


def main():
    started=time.monotonic()
    pop_manifest=read_json(POP/'manifest.json');old_manifest=read_json(OTHER/'manifest.json')
    for path,manifest in ((POP,pop_manifest),(OTHER,old_manifest)):
        assert manifest['state']=='complete';verify_files(path,manifest)
    assert pop_manifest['request']['bundle_sha256']==old_manifest['request']['bundle_sha256']
    config={'script_sha256':sha256(Path(__file__)),'common_sha256':sha256(ROOT/'scripts/agent_pipeline_common.py'),
        'metrics_source_sha256':sha256(ROOT/'scripts/diagnose_candidate_recall.py'),'budgets':list(BUDGETS),
        'methods':list(METHODS),'group':'prompt_dev','users':156,'policy':'standard;source_ASIN_stratification_only',
        'source_candidate_manifests':{'popularity':sha256(POP/'manifest.json'),'g_and_semantic':sha256(OTHER/'manifest.json')},
        'nested_prefixes':True,'rescoring':False,'label_source':'cached_internal_development_evaluation_only',
        'internal_prompt_val_read':False,'formal_evaluation_read':False,'llm_calls':0,'gpu_used':False}
    with stage(OUT,'recall_budget_prefixes',pop_manifest['request']['bundle_sha256'],config) as run:
        if run:
            pop={r['user_id']:r for r in rows(POP/'rankings.jsonl')}
            old={r['user_id']:r for r in rows(OTHER/'rankings.jsonl')}
            assert len(pop)==len(old)==156 and set(pop)==set(old)
            merged=[]
            for user in sorted(pop):
                assert pop[user]['source_seen_target_items']==old[user]['source_seen_target_items']
                rankings={'popularity':pop[user]['rankings']['interaction_count'],
                    'g':old[user]['rankings']['standard']['g'][:100],
                    'semantic':old[user]['rankings']['standard']['semantic'][:100]}
                assert all(len(v)==len(set(v)) and len(v) in (0,100) for v in rankings.values())
                assert len(rankings['popularity'])==len(rankings['g'])==100
                merged.append({'user_id':user,'source_seen_target_items':pop[user]['source_seen_target_items'],'rankings':rankings})
            with (OUT/'rankings_top100.jsonl').open('w',encoding='utf-8',newline='\n') as stream:
                for record in merged:stream.write(json.dumps(record,separators=(',',':'))+'\n')
            complete_stage(OUT,['rankings_top100.jsonl'],users=156,hidden_labels_read=False,nested_prefixes=True)
    # All candidates are fixed and verified before any evaluation traces are read.
    for folder in (POP,OTHER):verify_files(folder,read_json(folder/'evaluation_manifest.json'))
    previous_pop=read_json(POP/'results.json');previous_old=read_json(OTHER/'results.json')
    assert previous_pop['label_source']['sha256']==previous_old['label_source']['sha256']
    with (POP/'observed_history_evaluation_only.csv').open(encoding='utf-8-sig',newline='') as stream:
        traces=list(csv.DictReader(stream))
    records=list(rows(OUT/'rankings_top100.jsonl'));users=[r['user_id'] for r in records]
    truth={u:set() for u in users};seen={r['user_id']:set(r['source_seen_target_items']) for r in records}
    for trace in traces:
        user,item=int(trace['user_id']),int(trace['target_item_id'])
        assert user in truth and int(trace['same_asin_source_history'])==int(item in seen[user])
        assert item not in truth[user];truth[user].add(item)
    assert sum(map(len,truth.values()))==1577 and sum(len(truth[u]-seen[u]) for u in users)==1412
    metrics=[];per_user=[];reproduced=0
    for method in METHODS:
        previous={u:set() for u in users}
        for k in BUDGETS:
            selected={r['user_id']:set(r['rankings'][method][:k]) for r in records}
            assert all(previous[u]<=selected[u] for u in users)
            details=summarize(selected,truth,seen)
            details['different_asin_users_with_hit']=sum(r['different_asin_hits']>0 for r in details['per_user'])
            direct=[t for t in traces if int(t['target_item_id']) in selected[int(t['user_id'])]]
            assert len(direct)==details['observed_hits']
            assert sum(int(t['same_asin_source_history']) for t in direct)==details['same_asin_hits']
            metadata={'method':method,'k':k,'policy':'standard'}
            per_user.extend({**metadata,**r} for r in details.pop('per_user'))
            metrics.append({**metadata,**details});previous=selected
            known=next((r for r in previous_old['metrics'] if r['policy']=='standard' and r['method']==method and r['k']==k),None)
            if method=='popularity' and k==100:known=next(r for r in previous_pop['metrics'] if r['cohort']=='all_dev_156' and r['primary'])
            if known:
                for key,value in details.items():
                    if key in known:
                        assert (value is None and known[key] is None) or (value is not None and math.isclose(value,known[key],abs_tol=1e-12)),(method,k,key,value,known[key])
                reproduced+=1
    for name,data in (('aggregate_metrics.csv',metrics),('per_user_metrics.csv',per_user)):
        with (OUT/name).open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(data[0]));writer.writeheader();writer.writerows(data)
    write_json(OUT/'results.json',{'state':'complete','completed_at':utc_now(),'users':156,'budgets':list(BUDGETS),
        'metrics':metrics,'hidden_interactions':1577,'different_asin_hidden_interactions':1412,
        'source_label_sha256':previous_pop['label_source']['sha256'],'evaluation_trace_sha256':sha256(POP/'observed_history_evaluation_only.csv'),
        'existing_metric_rows_reproduced':reproduced,'internal_prompt_val_read':False,'formal_evaluation_read':False,
        'llm_calls':0,'gpu_used':False,'elapsed_seconds':round(time.monotonic()-started,3)})
    write_json(OUT/'verification.json',{'state':'passed','metric_rows':12,'per_user_rows':len(per_user),
        'independent_trace_intersection_checks':12,'nested_budgets_verified':True,'existing_rows_reproduced':reproduced})
    headers=['K','方法','总体Recall','同ASIN命中','不同ASIN命中','不同ASIN Recall','不同ASIN逐用户平均','不同ASIN命中用户']
    values=[]
    lookup={(r['method'],r['k']):r for r in metrics}
    for k in BUDGETS:
        for method in METHODS:
            r=lookup[method,k];values.append([k,NAMES[method],f"{r['recall_micro']*100:.2f}%",r['same_asin_hits'],r['different_asin_hits'],
                f"{r['different_asin_recall_micro']*100:.2f}%",f"{r['different_asin_recall_macro']*100:.2f}%",r['different_asin_users_with_hit']])
    intro='同一156位开发用户、同一冻结排名前缀；总体Recall分母1,577，不同ASIN Recall分母1,412。不同ASIN逐用户平均仅包含155位具有对应隐藏历史的用户；命中用户列按156位计数。Popularity/G候选数156×K，语义155×K（一位用户无可用画像）。'
    (OUT/'results_table.md').write_text(intro+'\n\n'+table(headers,values)+'\n',encoding='utf-8',newline='\n')
    (OUT/'notion_results.md').write_text(intro+'\n'+native_table(headers,values)+'\n',encoding='utf-8',newline='\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter
    fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    for ax,key,title in zip(axes,('recall_micro','different_asin_recall_micro'),('All observed target interactions','Different-ASIN interactions')):
        for method in METHODS:
            ax.plot(BUDGETS,[lookup[method,k][key] for k in BUDGETS],marker='o',label={'popularity':'Popularity','g':'G','semantic':'Semantic'}[method])
        ax.set(title=title,xlabel='Candidates per user (K)',ylabel='Recall');ax.set_xticks(BUDGETS)
        ax.yaxis.set_major_formatter(PercentFormatter(1));ax.set_ylim(bottom=0);ax.grid(alpha=.25);ax.legend()
    fig.savefig(OUT/'recall_vs_budget.png',dpi=180);fig.savefig(OUT/'recall_vs_budget.svg');plt.close(fig)
    names=['results.json','aggregate_metrics.csv','per_user_metrics.csv','verification.json','results_table.md','notion_results.md','recall_vs_budget.png','recall_vs_budget.svg']
    write_json(OUT/'evaluation_manifest.json',{'state':'complete','files':file_records(OUT,names),'candidate_manifest_sha256':sha256(OUT/'manifest.json')})
    print(table(headers,values),flush=True)


if __name__=='__main__':main()
