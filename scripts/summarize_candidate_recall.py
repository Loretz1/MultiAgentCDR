"""Render the frozen candidate diagnostics as tables and an exportable figure."""
from pathlib import Path
import json

from agent_pipeline_common import ROOT, read_json
from diagnose_candidate_recall import OUT, BUDGETS


def percent(value):
    return '—' if value is None else f'{100*value:.2f}%'


def table(headers, values):
    return '\n'.join(['| '+' | '.join(headers)+' |',
                      '| '+' | '.join(['---']*len(headers))+' |'] +
                     ['| '+' | '.join(map(str,row))+' |' for row in values])


def native_tables(markdown):
    lines=markdown.splitlines();out=[];index=0
    while index<len(lines):
        if lines[index].startswith('|'):
            records=[]
            while index<len(lines) and lines[index].startswith('|'):
                fields=[v.strip() for v in lines[index].strip().strip('|').split('|')]
                if not all(v=='---' for v in fields):records.append(fields)
                index+=1
            out.append('<table header-row="true">')
            out.extend('<tr>'+''.join('<td>'+v+'</td>' for v in row)+'</tr>' for row in records)
            out.append('</table>')
        else:out.append(lines[index]);index+=1
    return '\n'.join(out)


def main():
    result=read_json(OUT/'results.json');audit=read_json(OUT/'generation_audit.json')
    names={'semantic':'语义','g':'G','rrf':'RRF合并','union':'两路并集'}
    lookup={(r['policy'],r['method'],r['k']):r for r in result['metrics']}
    main_rows=[]
    for k in BUDGETS:
        for method in ('semantic','g','rrf'):
            r=lookup['standard',method,k]
            main_rows.append([names[method],k,r['candidates'],r['observed_hits'],percent(r['recall_micro']),
                              r['same_asin_hits'],r['different_asin_hits'],percent(r['different_asin_recall_micro'])])
    header=['方法','每人K','候选数','全部命中','总体Recall','同ASIN命中','不同ASIN命中','不同ASIN Recall']
    union_rows=[]
    for k in BUDGETS:
        r=lookup['standard','union',k]
        union_rows.append([k,r['candidates'],r['observed_hits'],percent(r['recall_micro']),
                           r['different_asin_hits'],percent(r['different_asin_recall_micro'])])
    exclude_rows=[]
    for k in BUDGETS:
        for method in ('semantic','g','rrf'):
            r=lookup['exclude_source_asin',method,k]
            exclude_rows.append([names[method],k,r['candidates'],r['different_asin_hits'],percent(r['different_asin_recall_micro'])])
    macro_rows=[]
    for method in ('semantic','g','rrf'):
        r=lookup['standard',method,200]
        macro_rows.append([names[method],percent(r['recall_micro']),percent(r['recall_macro']),
                           percent(r['different_asin_recall_micro']),percent(r['different_asin_recall_macro']),r['users_with_hit']])
    content='''## 结论摘要

全部156位开发用户召回诊断已完成；隐藏Sports历史1,577条，其中源历史已有同ASIN165条、不同ASIN1,412条。当前165条只按物品ASIN对应分类，没有逐条证明原始评论相同；此前20用户中的9条重复评论已在上一轮核验。

1. 增加候选有用：标准RRF从每人10个扩大到200个，全部已观察命中69→221，总体Recall 4.38%→14.01%；不同ASIN命中11→92。
2. 当前语义召回主要覆盖源历史已有物品：Top200命中142条，其中133条同ASIN、不同ASIN仅9条；不同ASIN Recall只有0.64%。该结论限定现有BGE画像与当前开发集，不代表语义方法普遍无效。
3. 不同ASIN覆盖以G更好：G Top200不同ASIN命中146条/1,412=10.34%，RRF Top200为92条/1,412=6.52%。固定等权RRF虽然总体命中更多，但不同ASIN覆盖低于G单独召回。
4. 每路Top200并集有61,674候选，全部命中290、不同ASIN154（10.91%）；G Top200有31,200候选、不同ASIN146。扩大两路并集几乎翻倍候选预算，仅额外覆盖8条不同ASIN交互。
5. 用户1753没有可用的正评价语义画像，其语义召回为空，G仍正常。因此语义总候选数是155×K，G/RRF是156×K；不同ASIN隐藏历史存在于155位用户，分层macro分母为155而不是156。

## 标准目录：同总预算比较

总体Recall=命中/1,577；不同ASIN Recall=不同ASIN命中/1,412。表中候选集合含两种ASIN，原Benchmark不修改。语义有1位用户无画像，其他用户使用相同K预算。

'''+table(header,main_rows)+'''

## 两路并集：更大预算参照

每路各取K后并集去重，最多每人2K；不能把该表与总预算K的上表当作等预算收益。

'''+table(['每路K','实际候选总数','全部命中','总体Recall','不同ASIN命中','不同ASIN Recall'],union_rows)+'''

## 补充：召回前排除用户源历史同ASIN并补足K

过滤仅根据可见源历史，不使用隐藏目标历史。此为新物品迁移诊断，不覆盖或替代标准Benchmark结果。该版本的命中均为不同ASIN，Recall分母为1,412。

'''+table(['方法','每人K','候选数','不同ASIN命中','不同ASIN Recall'],exclude_rows)+'''

## 每用户指标：标准Top200

micro按隐藏交互总数加权；macro先计算各用户召回再平均。完整逐用户结果见 `per_user_metrics.csv`，包含无命中用户。

'''+table(['方法','总体micro','总体macro','不同ASIN micro','不同ASIN macro','有命中用户/156'],macro_rows)+'''

## 复现与完整性

- 原20用户/200候选完全复现，语义分数最大绝对误差2.38e-7，G为4.77e-7；旧候选隐藏历史匹配11条、不同ASIN2条复现。
- 新RRF采用固定每路Top200，旧试点是每路Top50，因此新Top10与旧Top10可能不是同一名单；候选深度已经在计算前登记，不把两种配置混作同一方案。
- 32组结果=2种ASIN策略×4种召回方法×4个K。候选随K嵌套、无重复、ID/分数合法；统计与逐用户/隐藏历史记录独立核对。
- 候选缓存的bundle、BGE、G与源码SHA256均已固定；候选生成阶段不读取隐藏目标标签。仅评价阶段读取内部prompt_dev.pkl，内部prompt_val及正式测试未读取。
- 5项指标测试通过，含完整历史分母、无命中用户、不同ASIN分母为空、RRF并列/并集预算、ASIN跨域编号和先过滤再补足候选。
- 本机候选生成6.459秒，开发历史匹配0.280秒，不含脚本编写、检查与文档同步；Qwen调用0次、GPU使用0次。

## 完成范围与后续建议

本轮完成所有156位开发用户的候选排名与覆盖评价，未为这些新增候选生成完整四角色输入或LLM反馈。已有排名可供下一步导出四类证据，评价CSV中的目标标签不得回填到Agent输入。

建议下一轮以G Top100/200作为不同ASIN召回基准，并保留标准RRF和语义对照；先小规模修正v6字段解释与判断准则、在固定候选上对照v5/v6。是否采用排除同ASIN版本需与标准Benchmark结果分开登记。当前G Top200不同ASIN覆盖仍只有10.34%，召回改进也需继续推进。

本轮指标描述已观察隐藏交互覆盖，不是喜欢/不喜欢准确率、完整推荐HR/NDCG、Agent筛选增益或下游训练收益；未匹配不能作为C金标签。所有开发用户已用于诊断，独立内部验证仍留待方案冻结后评价。
'''
    doc=ROOT/'doc/experiments/2026-10-06_Cloth_Sports候选召回诊断.md'
    prefix=doc.read_text(encoding='utf-8').split('## 结果\n')[0]
    prefix=prefix.replace('状态：已登记，尚未运行召回诊断；','状态：全部156位开发用户的召回诊断已完成；')
    prefix=prefix.replace('源码：`scripts/diagnose_candidate_recall.py`；测试：','源码：`scripts/diagnose_candidate_recall.py`；汇总/绘图：`scripts/summarize_candidate_recall.py`；测试：')
    prefix=prefix.replace('- `evaluation_manifest.json`、`evaluation_status.json`：评价完整性与最终状态。',
                          '- `evaluation_manifest.json`、`evaluation_status.json`、`verification.json`：评价完整性与最终状态。\n- `recall_curves.png`、`recall_curves.svg`：标准目录下的总体/不同ASIN召回曲线。')
    doc.write_text(prefix+'## 结果\n\n'+content+
                   '\n## 召回曲线\n\n![固定候选预算下总体与不同ASIN召回率](2026-10-06_candidate_recall/recall_curves.png)\n\n'+
                   'Notion：[候选召回诊断](https://app.notion.com/p/3f16864168f5816e9834ee1b6ab84306)。\n',encoding='utf-8')
    (OUT/'notion_results.md').write_text(native_tables(content),encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter
    fig,axes=plt.subplots(1,2,figsize=(10.5,4.2),layout='constrained')
    labels={'semantic':'Semantic','g':'G (EMCDR)','rrf':'RRF (equal weights)'}
    colors={'semantic':'#3D8C72','g':'#2769AE','rrf':'#D47B26'}
    for ax,key,title in zip(axes,['recall_micro','different_asin_recall_micro'],
                            ['All observed history (n=1,577)','Different-ASIN history (n=1,412)']):
        for method in labels:
            ax.plot(BUDGETS,[lookup['standard',method,k][key] for k in BUDGETS],
                    marker='o',linewidth=2,label=labels[method],color=colors[method])
        ax.set(title=title,xlabel='Candidates per user (K)',ylabel='Micro recall')
        ax.set_xticks(BUDGETS);ax.yaxis.set_major_formatter(PercentFormatter(1));ax.set_ylim(bottom=0)
        ax.grid(alpha=.2);ax.legend(frameon=False,fontsize=9)
    fig.suptitle('Cloth to Sports: 156 development users / frozen models',fontsize=13)
    fig.savefig(OUT/'recall_curves.png',dpi=170)
    fig.savefig(OUT/'recall_curves.svg')
    plt.close(fig)
    print('Rendered report, native Notion tables and PNG/SVG recall curves.')


if __name__=='__main__':main()
