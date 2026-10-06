# AI助手证据复核：50对 / 200角色输出

按原输入逐条审阅，未读取隐藏目标反馈。不是独立人工金标签；暂定ABC供研究者讨论，不用于计算模型准确率或自动作为few-shot。U表示准则不足，A_or_B表示需要人工判断支持强度。无具体错误记录不代表输出正确。

## cloth_sports:prompt_dev:42:14055

Invicta Men's 10665 Pro Diver Collection Bracelet and Rubber Watch Set

### semantic

原预测：A；Confidence：0.395690；助手暂定参考：B；状态：needs_criteria_review。

原理由：Positive ratings for "watch" and "collection" in source history support target candidate; 2 matched concepts, 4 positive history items, but 11 unmatched concepts including key terms like "diver" and "bracelet"; limited evidence for strong semantic transfer.

- reason_label_tension：A但理由明确称强语义迁移证据有限；watch来自修表工具而非正评价腕表，collection来自通用类别。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：B；Confidence：0.996726；助手暂定参考：U；状态：confirmed_evidence_error。

原理由：G score 0.277 and 3 visible training users suggest weak signal; 2816 mapping support users indicate broad item popularity, but low neighbor support limits confidence in pseudo-interaction.

- mapping_scope_confusion：2816是跨域映射训练用户数，不是物品热度；own evidence没有支持“邻居支持低”的计数。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

### overlap

原预测：B；Confidence：0.999926；助手暂定参考：B；状态：no_specific_error_found。

原理由：6 overlap users show indirect support via co-occurrence with similar items, but no direct support; weak evidence due to low support rate (30%) and lack of strong behavioral signals.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999998；助手暂定参考：U；状态：needs_criteria_review。

原理由：Only 3 train interactions and 0 local support users suggest no personalized support; low local support rate (0.0) and minimal global support (8.7e-5) indicate popularity bias dominates; evidence limitation: no exposure data. C=Reject.

- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:42:15748

Smart Health Walking FIT

### semantic

原预测：C；Confidence：0.999848；助手暂定参考：C；状态：no_specific_error_found。

原理由：No positive-rated source categories match the target's concepts (fit, health, pedometers, smart, smarthealth, walking); unmatched concepts are 6, with no literal positive-history support found.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.999809；助手暂定参考：A；状态：no_specific_error_found。

原理由：G score 4.61 and 150 visible train users with full support from 2,816 mapping users indicate strong collaborative evidence, though limited by sparse source history.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：此候选在G自身Top5且正分，支持A；分数/排名不解释为交互概率。

### overlap

原预测：B；Confidence：0.999979；助手暂定参考：B；状态：no_specific_error_found。

原理由：17/20 overlap users show indirect support, with 2 direct; evidence is sparse and indirect, so support is weak despite high union rate.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.989693；助手暂定参考：U；状态：needs_criteria_review。

原理由：Popularity percentile 99.48 and local support rate 10% (2 users) with global rate 0.43% suggest strong popularity bias; limited personalized support despite high visibility.

- unsupported_visibility：热门度/交互数不能识别实际曝光或visibility，曝光字段不可用。
- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:42:13979

Invicta Men's 1463 Reserve Collection Chronograph Silver Dial Stainless Steel Watch

### semantic

原预测：A；Confidence：0.958661；助手暂定参考：B；状态：needs_criteria_review。

原理由：Matched 3 positive concepts (collection, silver, watch) from 4 positive source reviews; 11 unmatched concepts lack positive support; evidence is limited to literal matches without semantic depth.

- generic_concept_transfer：collection是通用词；watch来自工具，银饰与银色腕表的迁移强度需要准则。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.999717；助手暂定参考：U；状态：no_specific_error_found。

原理由：G score 0.909 and 2,816 mapping support users strongly indicate collaborative alignment, though limited to 7 visible train users.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

### overlap

原预测：B；Confidence：0.999946；助手暂定参考：B；状态：no_specific_error_found。

原理由：3 indirect support users out of 20 overlap neighbors show weak cross-domain alignment; no direct support; insufficient evidence for strong pseudo-interaction.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999997；助手暂定参考：U；状态：no_specific_error_found。

原理由：Local support rate is 0.0 with 0 local support users, while global support is 0.0002; low local support despite moderate popularity suggests no trustworthy personalized support, rejecting the pseudo-interaction.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:42:14764

Tasc Performance Men's Carrollton Performance Running Tee Shirt

### semantic

原预测：C；Confidence：0.999991；助手暂定参考：C；状态：no_specific_error_found。

原理由：No matching concepts between source preferences (jewelry, gemstones, repair tools) and target (running shirt, performance, big & tall), with 12 unmatched concepts and no positive history support; evidence limitation: no semantic overlap.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.999926；助手暂定参考：A；状态：confirmed_evidence_error。

原理由：G score 4.42 and rank 2 among 18,357 items indicate strong collaborative support; 2816 mapping users confirm neighbor reliability, though limited visible target support may affect generalization.

- mapping_scope_confusion：2816位映射用户不能直接证明候选邻居可靠。

参考说明：助手暂定：此候选在G自身Top5且正分，支持A；分数/排名不解释为交互概率。

### overlap

原预测：A；Confidence：0.999903；助手暂定参考：A；状态：no_specific_error_found。

原理由：17 direct support users and 12 indirect support users show strong cross-domain alignment; 85% union support rate indicates consistent behavior, though limited by sparse interaction evidence.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999986；助手暂定参考：A_or_B；状态：needs_criteria_review。

原理由：Local support rate of 85% (17/20) is high, but global support rate of 0.49% and popularity percentile of 99.6% suggest strong popularity bias; limited evidence due to lack of exposure data. Reject.

- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。
- enrichment_ignored：局部支持多人且平滑后高于全局，仍拒绝；需说明样本充分性和全局基准，而非热门即拒绝。

参考说明：明显局部富集至少需讨论A/B；样本小和全局分母稀疏，不能凭比率给确定A，更不能从热门直接断言偏差。

## cloth_sports:prompt_dev:42:13517

Contigo 24-Ounce Autospout Addison Water Bottle, Purple

### semantic

原预测：C；Confidence：0.999980；助手暂定参考：C；状态：no_specific_error_found。

原理由：No positive concept matches between source preferences (jewelry, gemstones, tools) and target (water bottle, spout, purple), with 8 unmatched concepts and no literal positive-history support despite 4 positive source reviews.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.999973；助手暂定参考：A；状态：no_specific_error_found。

原理由：G score 4.24 and rank 3 among 18,357 items indicate strong collaborative support; 71 visible training users and 2,816 mapping support users reinforce reliability, though limited by sparse source user history.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：此候选在G自身Top5且正分，支持A；分数/排名不解释为交互概率。

### overlap

原预测：B；Confidence：0.998694；助手暂定参考：B；状态：needs_criteria_review。

原理由：17/20 overlap users show indirect support, with 2 direct, but no explicit positive ratings; weak evidence due to lack of direct positive behavior.

- rating_availability_penalty：Overlap依据是观察到的训练交互；缺少明确正评分不应额外推断为缺少直接行为支持。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.970087；助手暂定参考：U；状态：needs_criteria_review。

原理由：Popularity percentile 97.5% and local support rate 10% (2/20) suggest strong popularity bias; limited personalized support despite high rank.

- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:42:14060

Invicta Men's Pro Diver 1773

### semantic

原预测：A；Confidence：0.617164；助手暂定参考：B；状态：needs_criteria_review。

原理由：The target shares a literal "watch" concept with positive source reviews and has high similarity (0.74) to positive history, but lacks direct evidence for "diver" or "sport" preferences; limited by no explicit positive history match beyond one concept.

- generic_concept_transfer：watch来自修表工具，不能单独当作喜爱腕表的强证据；A需复核。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.999141；助手暂定参考：U；状态：no_specific_error_found。

原理由：G score 0.92 and 2,816 mapping support users strongly indicate collaborative alignment, though limited visible train users (6) constrain confidence.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

### overlap

原预测：B；Confidence：0.999683；助手暂定参考：B；状态：no_specific_error_found。

原理由：3 indirect support users with 15% union support rate; sparse overlap behavior limits strong inference despite some cooccurrence.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999991；助手暂定参考：U；状态：needs_criteria_review。

原理由：Only 6 train interactions and 0 local support users; global support rate is extremely low (0.017%), with local support rate at 0%; evidence suggests popularity bias dominates, not personalized support.

- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:42:14061

Invicta Men's 1775 Pro Diver Collection Chronograph Watch

### semantic

原预测：A；Confidence：0.427672；助手暂定参考：B；状态：needs_criteria_review。

原理由：The target shares two literal concept matches (collection, watch) with positive source reviews, and 4 positive history items are semantically linked, but key terms (chronograph, diver, sport) lack direct support; evidence is limited to 2 of 12 concepts.

- generic_concept_transfer：collection与watch/tool不能直接当作腕表偏好的强依据。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.999965；助手暂定参考：U；状态：no_specific_error_found。

原理由：G score 0.897 and 2,816 mapping support users strongly indicate collaborative signal, though limited to 7 visible train users; evidence is decisive despite small visible user set.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

### overlap

原预测：B；Confidence：0.999988；助手暂定参考：B；状态：no_specific_error_found。

原理由：Only 1 indirect support user and 0 direct supporters among 20 overlap neighbors; weak cross-domain signal with union support rate of 5%.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999998；助手暂定参考：U；状态：no_specific_error_found。

原理由：Local support rate is 0.0 with 0 local support users, while global support is 0.0002; low local support despite moderate popularity suggests no trustworthy personalized support, rejecting the pseudo-interaction.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:42:15483

3M Smart Lens Protective Eyewear, 13407-00000-5 Photochromatic Lens, Black Frame (Pack of 1)

### semantic

原预测：C；Confidence：0.999868；助手暂定参考：C；状态：no_specific_error_found。

原理由：No positive concept matches found; 9 unmatched concepts including key terms like "eyewear" and "safety"; limited evidence from 4 positive source reviews with no semantic overlap; insufficient support for pseudo-interaction.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.999595；助手暂定参考：A；状态：no_specific_error_found。

原理由：G score 3.87 and 41 visible train users indicate strong collaborative signal; 2816 mapping support users further validate relevance, though limited by sparse target-side support.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：此候选在G自身Top5且正分，支持A；分数/排名不解释为交互概率。

### overlap

原预测：B；Confidence：0.999837；助手暂定参考：B；状态：no_specific_error_found。

原理由：17/20 overlap users show indirect support, with 2 direct; weak evidence due to low direct support despite high indirect overlap.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999986；助手暂定参考：U；状态：confirmed_evidence_error。

原理由：Local support rate (10%) is low despite high popularity percentile (93.7%), and smoothed local rate (6.7%) is close to global rate (0.12%), suggesting support is likely due to popularity bias; evidence limitation: exposure data unavailable. C. Reject.

- rate_comparison_reversed：理由称平滑局部率6.7%接近全局0.12%；实际约56倍，比较错误。
- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:42:14054

Invicta Men's 10664 Pro Diver Collection Bracelet and Rubber Watch Set

### semantic

原预测：B；Confidence：0.666687；助手暂定参考：B；状态：confirmed_evidence_error。

原理由：Positive source history includes 4 items with 5.0 avg rating, and 2 matched concepts (watch, collection) align with target; however, 11 unmatched concepts lack positive history support, limiting strong inference.

- invented_rating_average：理由称4条正评价平均5.0星；实际4/4/5/5星，均值4.5。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.995576；助手暂定参考：U；状态：no_specific_error_found。

原理由：G score 1.15 and 2,816 mapping support users indicate strong collaborative signal; 8 target users observed, but limited by low visible support.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

### overlap

原预测：B；Confidence：0.999755；助手暂定参考：B；状态：no_specific_error_found。

原理由：2 direct and 2 indirect support users show limited cross-domain overlap; only 10% union support rate with weak cosine weights, insufficient for strong evidence.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.992344；助手暂定参考：U；状态：no_specific_error_found。

原理由：Local support rate (10%) is low despite moderate popularity percentile (50.09), and relative support (287.88) is driven by low global rate; insufficient personalized evidence.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:42:16722

3M Vinyl Tape 471 Yellow, 2 in x 36 yd, Conveniently Packaged (Pack of 1)

### semantic

原预测：B；Confidence：0.994765；助手暂定参考：C；状态：needs_criteria_review。

原理由：The target shares "yellow" with a positive source item, but no other semantic overlap; only 1 of 12 concepts matched, and no positive history supports the target's meaning, limiting strong inference.

- generic_concept_transfer：yellow把黄金饰品与黄色胶带联系起来；字面匹配不等于产品用途迁移。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.999595；助手暂定参考：A；状态：no_specific_error_found。

原理由：G score 3.87 and 54 visible training users indicate strong collaborative signal; 2816 mapping support users reinforce reliability, though limited target-side visibility may affect generalization.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：此候选在G自身Top5且正分，支持A；分数/排名不解释为交互概率。

### overlap

原预测：B；Confidence：0.999782；助手暂定参考：B；状态：no_specific_error_found。

原理由：4 out of 20 overlap users (20%) show indirect support via cooccurrence, but no direct support; sparse evidence limits strong inference.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999996；助手暂定参考：U；状态：needs_criteria_review。

原理由：Popularity percentile 96.04 and rank 760 suggest high popularity, but local support rate is 0.0 with 0 local support users, indicating no personalized support despite strong popularity bias; evidence limitation: no exposure data. C=Reject.

- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1365:4069

Rothco 550lb. Type III Nylon Paracord

### semantic

原预测：C；Confidence：0.996563；助手暂定参考：C；状态：no_specific_error_found。

原理由：No literal positive-history support found; 6 unmatched concepts including key terms like "paracord," "nylon," and "Rothco" indicate weak semantic alignment despite moderate similarity score (0.586).

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.999647；助手暂定参考：A；状态：no_specific_error_found。

原理由：G score 2.62 and 2816 mapping support users indicate strong collaborative signal; 626 visible train users support target; evidence limitation: no explicit positive rating history.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：此候选在G自身Top5且正分，支持A；分数/排名不解释为交互概率。

### overlap

原预测：B；Confidence：0.999967；助手暂定参考：B；状态：no_specific_error_found。

原理由：Only 2 out of 20 overlap users show indirect support, with no direct support; weak evidence limits confidence in strong support.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.992593；助手暂定参考：U；状态：needs_criteria_review。

原理由：Popularity percentile 99.99 and rank 3 indicate extreme popularity; local support rate 0.0 with 0 users contradicts personalized support despite global rate 1.8%, suggesting bias dominates.

- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1365:8587

Yupoong 6277 Flexfit Wooly 6-Panel Cap

### semantic

原预测：A；Confidence：0.999288；助手暂定参考：A；状态：no_specific_error_found。

原理由：Strong match in "baseball cap" and brand "Yupoong" with 5 positive source reviews; 3 unmatched semantic elements (Flexfit, panel, wooly) limit full alignment.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：B；Confidence：0.998939；助手暂定参考：U；状态：no_specific_error_found。

原理由：G score of -0.36 and only 4 visible train users suggest weak collaborative signal; limited support despite 2,816 mapping users, but low rank percentile (29.4) indicates poor relative position.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

### overlap

原预测：C；Confidence：0.999890；助手暂定参考：C；状态：no_specific_error_found。

原理由：0 direct/indirect support users among 20 overlap neighbors; no observed positive interactions; weak evidence for pseudo-interaction.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999365；助手暂定参考：U；状态：needs_criteria_review。

原理由：Only 4 train interactions and 0 local support users; popularity percentile 4.1% suggests low visibility; insufficient personalized support despite low exposure availability.

- unsupported_visibility：热门度/交互数不能识别实际曝光或visibility，曝光字段不可用。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1365:5822

Rayovac Sportsman LED Lantern SE3DLN

### semantic

原预测：C；Confidence：0.998844；助手暂定参考：C；状态：no_specific_error_found。

原理由：No positive concept matches found; 6 unmatched key concepts (e.g., lantern, LED, Rayovac); similarity 0.579 not sufficient; evidence limitation: no semantic overlap with positive history.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.999911；助手暂定参考：A；状态：confirmed_evidence_error。

原理由：G score 2.41 and rank 2 among 18,357 items indicate strong collaborative support; 2816 mapping users confirm structural relevance, though limited by no visible target support in training.

- false_absence_of_target_support：理由说训练中没有可见目标支持；candidate_visible_train_users=266。

参考说明：助手暂定：此候选在G自身Top5且正分，支持A；分数/排名不解释为交互概率。

### overlap

原预测：C；Confidence：0.999705；助手暂定参考：C；状态：no_specific_error_found。

原理由：0 direct/indirect support users among 20 overlap neighbors; no observed positive interactions; weak evidence for pseudo-interaction.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999988；助手暂定参考：U；状态：confirmed_evidence_error。

原理由：Popularity percentile 99.89 and rank 22 indicate extreme popularity, but local support rate is 0.0 with 0 local support users, suggesting no personalized support despite high global exposure; evidence limitation: no exposure data available. Reject.

- invented_exposure：exposure_available=false，理由仍断言global exposure高。
- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1365:9741

Flexfit 6477 Structured Wool Cap

### semantic

原预测：A；Confidence：0.999782；助手暂定参考：A；状态：no_specific_error_found。

原理由：Strong semantic match in "baseball", "cap", "caps", and "wool" with 5 positive source reviews; 4/4 matched concepts support relevance despite unmatched "Flexfit" and "structured"; limited by no explicit preference for wool or structured caps.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：B；Confidence：0.997698；助手暂定参考：U；状态：confirmed_evidence_error。

原理由：G score of -0.47 and low visible support (7 users) indicate weak collaborative signal; limited evidence from 7 source users despite 2,816 mapping support users.

- target_source_user_confusion：7是候选目标可见训练用户数，不是源用户数。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

### overlap

原预测：C；Confidence：0.999945；助手暂定参考：C；状态：no_specific_error_found。

原理由：0 direct/indirect support users among 20 overlap neighbors; no observed positive interactions; weak evidence limits confidence in strong support.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999992；助手暂定参考：U；状态：no_specific_error_found。

原理由：Local support rate is 0.0 with 0 support users, while global support is 0.0002; low local support despite moderate popularity suggests no trustworthy personalized support, rejecting the pseudo-interaction due to lack of direct evidence.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1365:2456

Emergency Mylar Thermal Blankets (Pack of 10)

### semantic

原预测：A；Confidence：0.877647；助手暂定参考：C；状态：needs_criteria_review。

原理由：Matched "pack" concept in title; 5 positive source reviews with no negative history; 4 unmatched concepts (emergency, mylar, thermal, blankets) lack positive history support; limited evidence for pseudo-interaction.

- reason_label_tension：唯一字面词pack；全目录rank13692，理由称支持有限却判A，依据薄弱。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.999968；助手暂定参考：A；状态：confirmed_evidence_error。

原理由：G score 2.29 and rank 3 among 18,357 items indicate strong collaborative support; 375 visible train users and 2,816 mapping support users confirm sufficient neighbor evidence, though limited by no observed target support.

- mapping_scope_confusion：375位候选训练用户和2816映射用户不能推出“足够邻居证据”；no observed target support表述范围不清。

参考说明：助手暂定：此候选在G自身Top5且正分，支持A；分数/排名不解释为交互概率。

### overlap

原预测：B；Confidence：0.999981；助手暂定参考：B；状态：no_specific_error_found。

原理由：Only 2 out of 20 overlap users show indirect support, with no direct support; sparse cross-domain behavior limits confidence in strong endorsement.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.994042；助手暂定参考：U；状态：confirmed_evidence_error。

原理由：Popularity percentile 99.96 and rank 8 indicate extreme popularity; local support rate 0.0 with 0 local support users shows no personalized evidence despite high global exposure, suggesting support is due to popularity bias.

- invented_exposure：exposure_available=false，理由仍断言global exposure高。
- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1365:7137

Scala Hats Brushed Twill Safari

### semantic

原预测：A；Confidence：0.916075；助手暂定参考：A；状态：no_specific_error_found。

原理由：Matched "caps" in category; 5 positive source reviews; 1 matched concept; 6 unmatched concepts with no negative evidence; limited by lack of target description.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：B；Confidence：0.753975；助手暂定参考：U；状态：no_specific_error_found。

原理由：G score 0.0073 is very low; only 9 visible training users support the candidate, with 2,816 mapping support users, indicating weak user-item alignment despite moderate ranking.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

### overlap

原预测：C；Confidence：0.999697；助手暂定参考：C；状态：no_specific_error_found。

原理由：0 direct/indirect support users among 20 overlap neighbors; no observed positive interactions; weak evidence for pseudo-interaction.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999997；助手暂定参考：U；状态：needs_criteria_review。

原理由：Low local support rate (0.0%) and zero local support users despite moderate popularity percentile (55.7%) suggest support is due to popularity, not personalized preference; evidence limitation: no exposure data. Reject.

- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1365:6672

Light My Fire Titanium Spork

### semantic

原预测：C；Confidence：0.999960；助手暂定参考：C；状态：no_specific_error_found。

原理由：No matching concepts between source preferences and target; 5 unmatched key terms (spork, titanium, flatware, light, fire); no positive history support despite high similarity score; evidence limitation: no semantic overlap in categories or items.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.999107；助手暂定参考：A；状态：no_specific_error_found。

原理由：G score 2.23 and 2816 mapping support users indicate strong collaborative signal, though limited by 222 visible train users and no missing target support.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：此候选在G自身Top5且正分，支持A；分数/排名不解释为交互概率。

### overlap

原预测：C；Confidence：0.999562；助手暂定参考：C；状态：no_specific_error_found。

原理由：0 direct/indirect support users among 20 overlap neighbors; no observed positive interactions; weak cooccurrence signals; insufficient evidence for strong support.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999990；助手暂定参考：U；状态：needs_criteria_review。

原理由：Popularity percentile 99.8 and rank 38 indicate extreme popularity, but local support rate is 0% with 0 local support users, suggesting no personalized support despite high global visibility; evidence limitation: no exposure data. Reject.

- unsupported_visibility：热门度/交互数不能识别实际曝光或visibility，曝光字段不可用。
- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1365:18157

Crazy Shopping Top Seller Newest Motorcycle Fleece Neck Hat Winter Ski Full Face Mask Cover Cap

### semantic

原预测：A；Confidence：0.996001；助手暂定参考：A；状态：no_specific_error_found。

原理由：5 positive source reviews contain "cap", "hat", "face", "full", "mask", "neck", "winter" — 7 matched concepts; 10 unmatched concepts lack positive support; evidence is limited to literal matches without semantic depth.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：C；Confidence：0.999834；助手暂定参考：U；状态：no_specific_error_found。

原理由：G score of -0.43 indicates negative collaborative signal; only 10 visible training users support the candidate, with 2,816 mapping support users; low G score and sparse visible support weaken evidence.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

### overlap

原预测：C；Confidence：0.999770；助手暂定参考：C；状态：no_specific_error_found。

原理由：0 direct/indirect support users among 20 overlap neighbors; no observed positive interactions; weak evidence limits confidence in strong support.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999998；助手暂定参考：U；状态：needs_criteria_review。

原理由：Low local support rate (0.0%) and zero local support users despite 10 train interactions suggest no personalized support; popularity bias likely dominates, rejecting the pseudo-interaction.

- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1365:37

Victorinox Swiss Army Classic SD Pocket Knife

### semantic

原预测：C；Confidence：0.999903；助手暂定参考：C；状态：no_specific_error_found。

原理由：No matched concepts between source preferences and target; 8 unmatched key concepts including "swiss", "victorinox", "knife", and "pocket"; no literal positive-history support found; evidence limitation: no semantic overlap in categories or items.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.999465；助手暂定参考：A；状态：no_specific_error_found。

原理由：G score 2.12 and 139 visible train users indicate strong collaborative signal; 2816 mapping support users further validate relevance, though limited by sparse target-side support.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：此候选在G自身Top5且正分，支持A；分数/排名不解释为交互概率。

### overlap

原预测：C；Confidence：0.992549；助手暂定参考：C；状态：no_specific_error_found。

原理由：0 direct/indirect support users among 20 overlap neighbors; no observed positive interactions; weak evidence limits confidence in strong support.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999894；助手暂定参考：U；状态：confirmed_evidence_error。

原理由：Popularity percentile 99.38 and 139 train interactions suggest strong popularity bias; local support rate 0.0 with 0 local support users indicates no personalized support despite high global exposure, rejecting the pseudo-interaction.

- invented_exposure：exposure_available=false，理由仍断言global exposure高。
- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1365:7337

Nike Feather Light Cap

### semantic

原预测：A；Confidence：0.995400；助手暂定参考：A；状态：no_specific_error_found。

原理由：Matched 3 concepts (baseball, cap, caps) with high similarity (0.76) to positive-rated source items; unmatched concepts (feather, light, Nike) lack positive history support, limiting strong inference.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：B；Confidence：0.999345；助手暂定参考：U；状态：confirmed_evidence_error。

原理由：G score of -0.167 and 6 visible source users suggest weak signal; 2,816 mapping support users indicate broad item popularity, but low G score and moderate rank percentile (47.1%) offer insufficient collaborative support for a pseudo-interaction.

- target_source_user_confusion：6是候选目标可见训练用户数，不是源用户数。
- mapping_scope_confusion：2816映射用户不是物品热门度。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

### overlap

原预测：C；Confidence：0.999996；助手暂定参考：C；状态：no_specific_error_found。

原理由：0 direct/indirect support users among 20 overlap neighbors; no observed positive interactions; weak evidence for pseudo-interaction.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999998；助手暂定参考：U；状态：needs_criteria_review。

原理由：Only 6 train interactions and 0 local support users indicate no personalized support; low local support rate (0.0) despite moderate popularity rank (13,053) suggests bias dominates, rejecting pseudo-interaction.

- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1773:1371

Polar Bottle Insulated Water Bottle

### semantic

原预测：C；Confidence：0.998956；助手暂定参考：C；状态：no_specific_error_found。

原理由：No literal positive-history support found; unmatched concepts (bottle, insulated, polar, water) lack semantic alignment with source preferences, despite moderate similarity score (0.579).

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.822261；助手暂定参考：A；状态：no_specific_error_found。

原理由：G score 2.42 and 261 visible train users indicate strong collaborative support; however, limited source history (6 interactions) constrains confidence.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：此候选在G自身Top5且正分，支持A；分数/排名不解释为交互概率。

### overlap

原预测：B；Confidence：0.999830；助手暂定参考：B；状态：no_specific_error_found。

原理由：3 overlap users showed support, with only 1 direct and 2 indirect; weak evidence due to low support rate (17.6%) and sparse cross-domain behavior.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.879425；助手暂定参考：U；状态：needs_criteria_review。

原理由：Popularity percentile 99.88 and rank 23 indicate extreme popularity; local support rate 5.88% from only 1 user suggests minimal personalized support despite high global visibility, likely driven by popularity bias.

- unsupported_visibility：热门度/交互数不能识别实际曝光或visibility，曝光字段不可用。
- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1773:7553

Champion Women's Mesh Hot Short

### semantic

原预测：A；Confidence：0.999982；助手暂定参考：A；状态：confirmed_evidence_error。

原理由：Strong semantic match in 7 literal tokens (e.g., "Champion", "mesh", "hot", "shorts", "workout") and 5 positive source ratings; limited by lack of target description text vector.

- description_vector_confusion：missing_target_description=true，但missing_target_text_vector=false；缺少描述不等于文本向量不存在。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：C；Confidence：0.999052；助手暂定参考：U；状态：no_specific_error_found。

原理由：G score of -0.188 indicates negative collaborative signal; only 8 visible train users support the candidate, with 2,816 mapping support users, suggesting weak local evidence despite moderate global ranking.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

### overlap

原预测：B；Confidence：0.999338；助手暂定参考：B；状态：no_specific_error_found。

原理由：6 direct support users and 4 indirect support users show cross-domain overlap, but only 6 of 17 actual neighbors support, indicating weak evidence; limited by sparse direct interaction data.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：B；Confidence：0.504415；助手暂定参考：A_or_B；状态：no_specific_error_found。

原理由：Local support rate (35.3%) is high but based on only 6 users; global support is extremely low (0.023%), and popularity rank (9,699) suggests median popularity, not extreme. Limited evidence from few users undermines trust.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：明显局部富集至少需讨论A/B；样本小和全局分母稀疏，不能凭比率给确定A，更不能从热门直接断言偏差。

## cloth_sports:prompt_dev:1773:11712

Camelbak Podium Big Chill 25 oz Bottle

### semantic

原预测：C；Confidence：0.999923；助手暂定参考：C；状态：no_specific_error_found。

原理由：No literal positive-history support found; unmatched concepts (e.g., bottle, water) lack alignment with source preference in shoes, apparel, or accessories. Evidence limitation: No shared semantic concepts between source preferences and target candidate.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.999964；助手暂定参考：A；状态：no_specific_error_found。

原理由：G score 2.13 and rank percentile 99.99% indicate strong collaborative support; 229 visible train users confirm signal presence, though limited to source-side history.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：此候选在G自身Top5且正分，支持A；分数/排名不解释为交互概率。

### overlap

原预测：B；Confidence：0.999891；助手暂定参考：B；状态：no_specific_error_found。

原理由：1 direct and 4 indirect support users among 17 overlap neighbors; weak support due to low overlap behavior count and sparse cross-domain evidence.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.973196；助手暂定参考：U；状态：needs_criteria_review。

原理由：Popularity percentile 99.83 and rank 32 indicate extreme popularity; local support rate 5.88% with only 1 user is negligible despite high global support, suggesting bias dominates.

- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1773:12349

Champion Women's Absolute Bike Short

### semantic

原预测：A；Confidence：0.996741；助手暂定参考：A；状态：no_specific_error_found。

原理由：5 positive source reviews match "active", "champion", "short", "shorts"; 2 unmatched concepts ("absolute", "bike") lack positive history support; evidence is limited to literal token matches.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：C；Confidence：0.999765；助手暂定参考：U；状态：no_specific_error_found。

原理由：G score of -0.25 indicates negative collaborative signal; only 12 visible training users support the candidate, with low mapping support (2,816), suggesting weak evidence for a pseudo-interaction.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

### overlap

原预测：B；Confidence：0.999995；助手暂定参考：B；状态：no_specific_error_found。

原理由：Only 1 indirect support user among 17 overlap neighbors; weak evidence (5.9% support rate) with no direct support; insufficient for strong endorsement.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999991；助手暂定参考：U；状态：needs_criteria_review。

原理由：Only 12 train interactions and 0 local support users suggest minimal personalized support; despite 67.6% popularity percentile, lack of local engagement indicates bias. Evidence limitation: no exposure data. C.

- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1773:7399

Serfas TCPG Bicycle Floor Pump

### semantic

原预测：C；Confidence：0.999834；助手暂定参考：C；状态：no_specific_error_found。

原理由：No positive history matches target concepts; 6 unmatched concepts including key terms like "bicycle," "floor," and "pump"; evidence limitation: no semantic overlap with source preferences.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.999604；助手暂定参考：A；状态：no_specific_error_found。

原理由：G score 2.08 and rank 3 among 18,357 items with 225 visible users and 2,816 mapping support indicate strong collaborative signal, though limited by sparse source history.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：此候选在G自身Top5且正分，支持A；分数/排名不解释为交互概率。

### overlap

原预测：B；Confidence：0.998776；助手暂定参考：B；状态：needs_criteria_review。

原理由：Only 1 user historically interacted with both the source and target, with no direct or indirect support beyond that; evidence is too sparse for strong support.

- support_scope_ambiguity：仅1人直接支持候选不意味着只有1位重叠用户具有跨域历史；actual_neighbors=17。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.982428；助手暂定参考：U；状态：confirmed_evidence_error。

原理由：Only 1 user in local group supported it (local support rate 5.88%), far below global rate (0.65%); high popularity percentile (99.8%) suggests bias; insufficient personalized support despite high visibility.

- rate_comparison_reversed：理由称局部5.88%远低于全局0.65%；实际局部约9倍于全局。
- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1773:16236

Champion Women's Mesh Short

### semantic

原预测：A；Confidence：0.999947；助手暂定参考：A；状态：no_specific_error_found。

原理由：Strong semantic match in 6 literal tokens (active, champion, mesh, short, shorts, workout) and 5 positive source ratings; similarity 0.839, high relevance. Limitation: no explicit user preference for "mesh" or "workout shorts" beyond category.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：B；Confidence：0.999896；助手暂定参考：U；状态：no_specific_error_found。

原理由：G score 0.136 is low; only 4 visible train users, 2,816 mapping support users, and 69.2% rank percentile suggest weak collaborative signal; limited visible support undermines strong evidence.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

### overlap

原预测：B；Confidence：0.999943；助手暂定参考：B；状态：no_specific_error_found。

原理由：7 indirect support users out of 17 overlap users show weak cross-domain behavior; no direct support; insufficient evidence for Strong support.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999628；助手暂定参考：U；状态：no_specific_error_found。

原理由：Only 4 train interactions and 0 local support users; popularity percentile 4.1% suggests low visibility, but global support rate 0.012% and zero local support indicate no trustworthy personalized signal despite low popularity.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1773:5292

Champion Women's Extended Size 6-Pack Performance Low Cut Socks

### semantic

原预测：A；Confidence：0.999566；助手暂定参考：A；状态：confirmed_evidence_error。

原理由：Strong semantic match in core concepts (active, athletic, champion, pack, socks) with 5 positive history items; unmatched concepts (low, extended, performance, cut) are minor descriptors; evidence limitation: no direct mention of socks in source positive history.

- false_absence_of_source_evidence：理由称源正历史没有socks；输入列出4星New Balance袜子且matched_concepts含socks。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：B；Confidence：0.998673；助手暂定参考：U；状态：confirmed_evidence_error。

原理由：G score of -0.039 and 9 visible train users suggest weak signal; mapping support of 2,816 users indicates broad item popularity, but low source-user interaction history limits confidence in pseudo-interaction.

- mapping_scope_confusion：2816映射用户被解释成物品热门度，证据类型错误。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

### overlap

原预测：B；Confidence：0.999840；助手暂定参考：B；状态：no_specific_error_found。

原理由：Only 1 overlap user indirectly supports the candidate (0.059 union support rate), with no direct support; sparse evidence limits strong inference.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999959；助手暂定参考：U；状态：no_specific_error_found。

原理由：Local support rate is 0.0 with 0 support users; global support is very low (0.026%), and local support is negligible despite moderate popularity percentile (55.7%), indicating no trustworthy personalized support.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1773:5822

Rayovac Sportsman LED Lantern SE3DLN

### semantic

原预测：C；Confidence：0.999083；助手暂定参考：C；状态：no_specific_error_found。

原理由：No matched concepts from positive source history; 6 unmatched key terms (e.g., lantern, LED, Rayovac); similarity 0.54 not sufficient; no semantic overlap despite high similarity score; evidence limitation: no positive concept matches.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.998022；助手暂定参考：A；状态：confirmed_evidence_error。

原理由：G score 2.07 and 2816 mapping support users indicate strong collaborative signal, though limited by no visible target support in training data.

- false_absence_of_target_support：理由说训练中没有目标支持；candidate_visible_train_users=266。

参考说明：助手暂定：此候选在G自身Top5且正分，支持A；分数/排名不解释为交互概率。

### overlap

原预测：C；Confidence：0.999970；助手暂定参考：C；状态：no_specific_error_found。

原理由：0 direct/indirect support users among 17 overlap neighbors; no observed positive interactions; weak evidence for pseudo-interaction.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.996558；助手暂定参考：U；状态：no_specific_error_found。

原理由：Popularity percentile 99.89 and rank 22 indicate extreme popularity, but local support rate is 0.0 with 0 local support users; insufficient personalized support despite high global popularity.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1773:9068

Pearl iZUMi Men's Quest Cycling Short

### semantic

原预测：B；Confidence：0.516690；助手暂定参考：B；状态：no_specific_error_found。

原理由：The target shares two literal concepts (short, shorts) with positive source reviews, but lacks semantic alignment beyond these tokens; no meaningful positive history support for cycling or compression categories, limiting evidence strength.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.998533；助手暂定参考：A；状态：no_specific_error_found。

原理由：G score 2.06 and 2816 mapping support users indicate strong collaborative signal, though limited by 214 visible train users and no missing target support.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：此候选在G自身Top5且正分，支持A；分数/排名不解释为交互概率。

### overlap

原预测：B；Confidence：0.999895；助手暂定参考：B；状态：no_specific_error_found。

原理由：Only 1 indirect support user and 17 actual neighbors; weak overlap evidence with 5.9% union support rate, insufficient for strong support.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999992；助手暂定参考：U；状态：confirmed_evidence_error。

原理由：Popularity percentile 99.77 and rank 45 indicate extreme popularity, but local support rate is 0% with 0 local support users, suggesting no personalized support despite high global exposure; evidence limitation: no exposure data available. Reject.

- invented_exposure：exposure_available=false，理由仍断言global exposure高。
- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1773:15269

Champion Women's Favorite Short

### semantic

原预测：A；Confidence：0.999886；助手暂定参考：A；状态：no_specific_error_found。

原理由：5 positive source reviews with strong concept matches (active, champion, short, shorts); 90% similarity to a 5-star rated item; unmatched "favorite" lacks negative evidence; limited by no explicit preference for "favorite" in source.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：C；Confidence：0.999968；助手暂定参考：U；状态：no_specific_error_found。

原理由：G score of -0.32 indicates negative collaborative signal; only 8 visible train users support the candidate, with low mapping support (2,816), suggesting weak evidence for a pseudo-interaction.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

### overlap

原预测：C；Confidence：0.998848；助手暂定参考：C；状态：no_specific_error_found。

原理由：0 direct/indirect support users among 17 overlap neighbors; no observed positive interactions; weak evidence for pseudo-interaction.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999996；助手暂定参考：U；状态：needs_criteria_review。

原理由：Low local support rate (0.0%) and zero local support users despite moderate popularity percentile (50.09), with no exposure data, suggest apparent support is likely due to popularity bias; reject.

- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1991:3388

Nalgene Tritan Wide Mouth BPA-Free Water Bottle, 1-Quart

### semantic

原预测：C；Confidence：0.999795；助手暂定参考：C；状态：no_specific_error_found。

原理由：No literal positive-history support found; 9 unmatched concepts including key features like "bottle," "water," and "BPA-Free," with no semantic alignment to source preferences in Shop by Designer, Socks, or Women.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.999702；助手暂定参考：A；状态：no_specific_error_found。

原理由：G score 1.62 and rank 1/18357 with 223 visible train users and 2816 mapping support indicate strong collaborative signal, though limited by no observed target support.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：此候选在G自身Top5且正分，支持A；分数/排名不解释为交互概率。

### overlap

原预测：B；Confidence：0.999990；助手暂定参考：B；状态：no_specific_error_found。

原理由：Only 1 indirect support user and 0 direct supporters among 20 overlap neighbors; weak cross-domain signal with 5% union support rate, insufficient for strong evidence.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999876；助手暂定参考：U；状态：needs_criteria_review。

原理由：Popularity percentile 99.8% and 223 train interactions suggest strong popularity bias; local support rate 0.0% with 0 local support users indicates no personalized support despite high global visibility.

- unsupported_visibility：热门度/交互数不能识别实际曝光或visibility，曝光字段不可用。
- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1991:13437

Injinji 2012 Performance Lightweight No Show Toe Socks

### semantic

原预测：A；Confidence：0.999183；助手暂定参考：A；状态：no_specific_error_found。

原理由：2 positive source history items match target concepts (Injinji, lightweight, performance, show, socks, toe); 6/6 matched concepts are literal; similarity 0.85; evidence limitation: no explicit preference for 'no show' or 'toe' socks in source.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.999420；助手暂定参考：U；状态：no_specific_error_found。

原理由：G score 0.54 and 2816 mapping support users indicate strong collaborative signal, though limited by 58 visible train users and no missing target support.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

### overlap

原预测：B；Confidence：0.999654；助手暂定参考：A；状态：needs_criteria_review。

原理由：14 direct support users and 7 indirect support users (70% union support rate) show consistent cross-domain cooccurrence, but sparse interaction patterns limit strong inference; evidence is insufficient for Strong.

- strong_weak_boundary：14/20直接支持仍判B；相邻样例17/20直接支持判A，阈值/样本充分性需明确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999948；助手暂定参考：A_or_B；状态：needs_criteria_review。

原理由：Local support rate (70%) is high but driven by 14 users in a small group (20); global support is very low (0.17%); popularity percentile is 96.5%, indicating strong bias; evidence suggests popularity dominates, so reject.

- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。
- enrichment_ignored：局部支持多人且平滑后高于全局，仍拒绝；需说明样本充分性和全局基准，而非热门即拒绝。

参考说明：明显局部富集至少需讨论A/B；样本小和全局分母稀疏，不能凭比率给确定A，更不能从热门直接断言偏差。

## cloth_sports:prompt_dev:1991:2634

TERRO PreFilled Liquid Ant Killer II Baits 6 Pack T300

### semantic

原预测：C；Confidence：0.999823；助手暂定参考：C；状态：no_specific_error_found。

原理由：No literal positive-history support found; 9 unmatched concepts including key terms like "ant," "killer," and "repellent" indicate semantic disconnect despite moderate similarity score (0.488).

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.994720；助手暂定参考：A；状态：no_specific_error_found。

原理由：G score 1.56 and rank 2 among 18,357 items indicate strong collaborative signal; 98 visible training users support the candidate, but limited source user history (5 interactions) constrains confidence.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：此候选在G自身Top5且正分，支持A；分数/排名不解释为交互概率。

### overlap

原预测：B；Confidence：0.998426；助手暂定参考：B；状态：no_specific_error_found。

原理由：Only 1 user directly supported the target via cooccurrence; 1 indirect supporter; 5% union support rate; sparse overlap behavior limits strong inference.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.998218；助手暂定参考：U；状态：confirmed_evidence_error。

原理由：Only 1 user in local group supported it (local support rate 5%), far below global rate (0.28%), and high popularity percentile (98.7%) suggests bias; insufficient personalized support despite high rank.

- rate_comparison_reversed：理由称局部5%远低于全局0.28%；实际局部约17.6倍于全局。
- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1991:12064

Injinji 2012 Performance Midweight Mini Crew Toe Socks

### semantic

原预测：A；Confidence：0.996314；助手暂定参考：A；状态：no_specific_error_found。

原理由：Strong semantic match in 4 literal tokens (Injinji, Performance, Socks, Toe) and 2 positive source ratings; unmatched concepts lack negative evidence, but 4 key terms missing from source preference limit confidence.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：B；Confidence：0.989390；助手暂定参考：U；状态：no_specific_error_found。

原理由：G score 0.345 and 7 visible train users suggest weak support; 2816 mapping support users indicate sparse collaboration, limiting confidence in the interaction.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

### overlap

原预测：B；Confidence：0.999981；助手暂定参考：B；状态：no_specific_error_found。

原理由：Only 1 indirect support user among 20 overlap neighbors (5% support rate) shows sparse, non-explicit interaction; insufficient for strong support.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999996；助手暂定参考：U；状态：no_specific_error_found。

原理由：Low local support rate (0.0) and zero local support users despite moderate popularity percentile (42.9) suggest no personalized support; evidence limitation: exposure data unavailable. Reject.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1991:46

Dr. Bronner 18-in-1 Pure-Castile Soap, Hemp Almond - 16 fl oz

### semantic

原预测：C；Confidence：0.428645；助手暂定参考：C；状态：no_specific_error_found。

原理由：No literal positive-history support found; 7 unmatched concepts including key terms like "soap," "hemp," and "almond" indicate weak semantic alignment despite moderate similarity score (0.49).

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.999795；助手暂定参考：A；状态：no_specific_error_found。

原理由：G score 1.52 and 2816 mapping support users indicate strong collaborative signal, though only 145 visible train users limit confidence; evidence supports pseudo-interaction.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：此候选在G自身Top5且正分，支持A；分数/排名不解释为交互概率。

### overlap

原预测：C；Confidence：0.999990；助手暂定参考：C；状态：no_specific_error_found。

原理由：0 direct/indirect support users among 20 overlap neighbors; no observed positive interactions; weak cooccurrence signals; insufficient evidence for strong support.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999947；助手暂定参考：U；状态：needs_criteria_review。

原理由：Popularity percentile 99.45 and rank 102 suggest strong popularity bias; local support rate 0.0 with 0 local support users indicates no personalized support despite high global visibility, rejecting the pseudo-interaction due to lack of localized evidence.

- unsupported_visibility：热门度/交互数不能识别实际曝光或visibility，曝光字段不可用。
- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1991:2786

Injinji 2012 Performance Original Weight Micro Toe Socks

### semantic

原预测：A；Confidence：0.997171；助手暂定参考：A；状态：no_specific_error_found。

原理由：2 positive source history items match target's "Injinji", "Performance", "Socks", "Toe"; 4/4 matched concepts are positive, but 7 unmatched concepts lack semantic support; evidence is limited to title matches only.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.998791；助手暂定参考：U；状态：no_specific_error_found。

原理由：G score 0.62 and 2816 mapping support users indicate strong collaborative signal, though limited by 66 visible train users and no missing target support.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

### overlap

原预测：B；Confidence：0.997108；助手暂定参考：B；状态：no_specific_error_found。

原理由：16/20 overlap users show indirect support, 1 shows direct support; sparse cross-domain behavior limits strong evidence despite high union support rate.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.993849；助手暂定参考：U；状态：needs_criteria_review。

原理由：Local support rate (5%) is 17.8× higher than global rate (0.19%), but only 1 user supports it locally; low personalized support despite high popularity (97.2 percentile) suggests bias.

- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1991:4

Black Mountain Products Resistance Band Set with Door Anchor, Ankle Strap, Exercise Chart, and Resistance Band Carrying Case

### semantic

原预测：C；Confidence：0.999929；助手暂定参考：C；状态：no_specific_error_found。

原理由：No literal positive-history support found; 14 unmatched concepts including key terms like resistance, band, and exercise; evidence limitation: no shared semantic concepts with positive source history.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.999648；助手暂定参考：A；状态：no_specific_error_found。

原理由：G score 1.51 and top 0.017% rank among 18,357 items indicate strong collaborative support, though limited to 103 visible training users.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：此候选在G自身Top5且正分，支持A；分数/排名不解释为交互概率。

### overlap

原预测：C；Confidence：0.999984；助手暂定参考：C；状态：no_specific_error_found。

原理由：0 direct/indirect support users among 20 overlap neighbors; no observed positive interactions; weak evidence for pseudo-interaction.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999996；助手暂定参考：U；状态：no_specific_error_found。

原理由：Popularity percentile 98.79 and rank 223 indicate high popularity, but local support rate 0.0 and 0 local support users show no personalized support; evidence lacks exposure data, limiting confidence. Reject.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1991:14663

Injinji 2012 Performance Midweight No Show Toe Socks

### semantic

原预测：A；Confidence：0.998962；助手暂定参考：A；状态：no_specific_error_found。

原理由：Strong match in key product terms (Injinji, Performance, No Show, Toe, Socks) with 2 positive source reviews; 5 matched concepts, 2 unmatched (midweight, athletic); limited by no explicit positive history for "Men" category.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：B；Confidence：0.999046；助手暂定参考：U；状态：no_specific_error_found。

原理由：G score of -0.042 is near zero, with only 8 visible training users and 2816 mapping support users; low signal and limited user overlap suggest weak collaborative support.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

### overlap

原预测：B；Confidence：0.999964；助手暂定参考：B；状态：no_specific_error_found。

原理由：14 indirect support users and 1 direct support user among 20 overlap neighbors show moderate cross-domain alignment, but sparse direct evidence limits strong support; indirect support is not sufficient for Strong.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.946428；助手暂定参考：U；状态：needs_criteria_review。

原理由：Local support rate (5%) is 144× higher than global rate (0.023%), but only 1 user supports it; low personalized support despite moderate popularity suggests bias.

- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1991:6506

SABRE RED Pepper Spray - Police Strength - Compact, Pink Case with Quick Release Key Ring (Max Protection - 25 shots, up to 5X's more)

### semantic

原预测：C；Confidence：0.999926；助手暂定参考：C；状态：no_specific_error_found。

原理由：No literal positive-history support found; unmatched concepts (e.g., pepper, police, pink) lack semantic alignment with source preferences (socks, designer, women); evidence limitation: no shared concepts between source and target.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：B；Confidence：0.813049；助手暂定参考：A；状态：confirmed_evidence_error。

原理由：G score 1.47 and 73 visible training users suggest moderate support, but low rank percentile (99.98) and high mapping support (2816) indicate sparse user overlap; evidence is limited by low target-side visibility.

- percentile_direction_reversed：理由称99.98排名百分位很低；该字段数值越高代表排名越靠前。
- mapping_scope_confusion：映射训练人数不能推断源用户交集稀疏程度。

参考说明：助手暂定：此候选在G自身Top5且正分，支持A；分数/排名不解释为交互概率。

### overlap

原预测：C；Confidence：0.999654；助手暂定参考：C；状态：no_specific_error_found。

原理由：0 direct/indirect support users among 20 overlap neighbors; no observed positive interactions; weak evidence for pseudo-interaction.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999703；助手暂定参考：U；状态：needs_criteria_review。

原理由：Popularity percentile 97.6% and 73 train interactions suggest strong popularity bias; local support rate 0.0% with 0 local support users indicates no personalized support despite high visibility.

- unsupported_visibility：热门度/交互数不能识别实际曝光或visibility，曝光字段不可用。
- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:1991:15190

Injinji - 2012 - Women's Performance Lightweight No-Show Sock, Canyon Pink, Large

### semantic

原预测：A；Confidence：0.999769；助手暂定参考：A；状态：no_specific_error_found。

原理由：2 positive history items match key concepts (Injinji, lightweight, performance, socks); similarity score 0.77 supports strong alignment despite unmatched attributes like color and size; limitation: no explicit preference for no-show or pink.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：B；Confidence：0.986922；助手暂定参考：U；状态：no_specific_error_found。

原理由：G score 0.13 and 7 visible train users suggest weak support; mapping support 2,816 users indicates broad relevance, but low G and sparse user overlap limit confidence.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

### overlap

原预测：B；Confidence：0.999976；助手暂定参考：B；状态：no_specific_error_found。

原理由：14 indirect support users (70% of 20 neighbors) show cooccurrence with the target, but no direct support; sparse indirect support suggests Weak, not Strong, evidence.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999918；助手暂定参考：U；状态：needs_criteria_review。

原理由：Local support rate is 0.0 with 0 support users, while global support is 0.0002; low local support despite moderate popularity suggests bias, not personalized relevance.

- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:2174:3388

Nalgene Tritan Wide Mouth BPA-Free Water Bottle, 1-Quart

### semantic

原预测：C；Confidence：0.999635；助手暂定参考：C；状态：no_specific_error_found。

原理由：No literal positive-history support found; 9 unmatched concepts including key features like "bottle", "water", "wide mouth", and "BPA-free" indicate weak semantic alignment despite moderate similarity score (0.56).

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.994425；助手暂定参考：A；状态：no_specific_error_found。

原理由：G score 2.14 and rank 1/18357 with 223 visible train users suggest strong collaborative support, though limited by no observed target support in training.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：此候选在G自身Top5且正分，支持A；分数/排名不解释为交互概率。

### overlap

原预测：C；Confidence：0.996996；助手暂定参考：C；状态：no_specific_error_found。

原理由：0 direct/indirect support users among 17 overlap neighbors; no observed positive interactions; weak cross-domain support despite 20 target neighbors.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999995；助手暂定参考：U；状态：confirmed_evidence_error。

原理由：Popularity percentile 99.8% and rank 37 indicate extreme popularity, but local support rate is 0% with 0 local support users, suggesting no personalized support despite high global exposure; evidence limitation: no exposure data available. Reject.

- invented_exposure：exposure_available=false，理由仍断言global exposure高。
- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:2174:12562

Oakley Men's Plaintiff Round Sunglasses

### semantic

原预测：B；Confidence：0.982324；助手暂定参考：A；状态：no_specific_error_found。

原理由：Positive history includes Ray-Ban sunglasses and related items; target is Oakley round sunglasses, sharing "sunglasses" concept but lacking direct positive history match; similarity score 0.825 supports weak semantic link, but no direct evidence of preference for Oakley or round style.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：B；Confidence：0.944761；助手暂定参考：U；状态：no_specific_error_found。

原理由：G score 0.103 is low; only 5 visible train users and 2,816 mapping support users; insufficient collaborative evidence to support pseudo-interaction.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

### overlap

原预测：C；Confidence：0.999941；助手暂定参考：C；状态：no_specific_error_found。

原理由：0 direct/indirect support users among 17 overlap neighbors; no observed positive interactions; weak cooccurrence signals; insufficient evidence for strong support.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999938；助手暂定参考：U；状态：needs_criteria_review。

原理由：Only 5 train interactions and 0 local support users indicate no personalized support; low local support rate (0.0) despite moderate popularity rank (16,503) suggests bias dominates.

- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:2174:46

Dr. Bronner 18-in-1 Pure-Castile Soap, Hemp Almond - 16 fl oz

### semantic

原预测：C；Confidence：0.999977；助手暂定参考：C；状态：confirmed_evidence_error。

原理由：No literal positive-history support found; unmatched concepts (e.g., soap, shampoo, hemp, almond) lack semantic alignment with source preferences in footwear/apparel. Evidence limitation: No shared categories or positive ratings in target domain.

- unavailable_target_rating_claim：理由将没有目标域正评分当作局限；Semantic输入不提供该用户隐藏目标评分，不能作此事实断言。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.999957；助手暂定参考：A；状态：confirmed_evidence_error。

原理由：G score 1.71 and rank 2 among 18,357 items indicate strong collaborative support; 145 visible training users and 2,816 mapping support users confirm sufficient neighbor overlap, though limited by sparse source user history.

- mapping_scope_confusion：145候选训练用户及2816映射用户不能证明邻居交集充分。

参考说明：助手暂定：此候选在G自身Top5且正分，支持A；分数/排名不解释为交互概率。

### overlap

原预测：C；Confidence：0.999983；助手暂定参考：C；状态：no_specific_error_found。

原理由：0 direct/indirect support users among 17 overlap neighbors; no observed positive interactions; weak evidence for pseudo-interaction.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999790；助手暂定参考：U；状态：needs_criteria_review。

原理由：Popularity percentile 99.45 and 145 train interactions suggest strong popularity bias; local support rate 0.0 with 0 local support users indicates no personalized support despite high global visibility.

- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:2174:5973

Wigwam Men's Ironman Thunder Pro Low-Cut Sock

### semantic

原预测：A；Confidence：0.999328；助手暂定参考：A；状态：no_specific_error_found。

原理由：4 positive source history items match target via literal tokens (e.g., "athletic", "sock", "Ironman"); similarity score 0.82 supports strong semantic alignment; limited by lack of explicit preference for socks in source.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：B；Confidence：0.999809；助手暂定参考：U；状态：no_specific_error_found。

原理由：G score 0.057 is low; only 5 visible train users support the candidate, with 2,816 mapping support users; limited collaborative signal suggests weak support.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

### overlap

原预测：B；Confidence：0.999741；助手暂定参考：B；状态：no_specific_error_found。

原理由：4 direct and 4 indirect support users from 17 overlap neighbors show limited cross-domain behavior; weak evidence for strong support due to low overlap and sparse interaction patterns.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999986；助手暂定参考：A_or_B；状态：needs_criteria_review。

原理由：Local support rate (23.5%) is high but based on only 4 users; global support is negligible (0.014%); low visibility and sparse interactions suggest popularity bias dominates, so reject.

- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。
- enrichment_ignored：局部支持多人且平滑后高于全局，仍拒绝；需说明样本充分性和全局基准，而非热门即拒绝。

参考说明：明显局部富集至少需讨论A/B；样本小和全局分母稀疏，不能凭比率给确定A，更不能从热门直接断言偏差。

## cloth_sports:prompt_dev:2174:7579

humangear capCAP Water Bottle Lid

### semantic

原预测：C；Confidence：0.999489；助手暂定参考：C；状态：no_specific_error_found。

原理由：No literal positive-history support found; 6 unmatched concepts including core items like "bottle," "water," and "lid" indicate weak semantic alignment despite moderate similarity score (0.58).

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.999966；助手暂定参考：A；状态：no_specific_error_found。

原理由：G score 1.68 and rank 3 among 18,357 items indicate strong collaborative support; 87 visible training users and 2,816 mapping support users reinforce reliability, though limited by sparse source-user history.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：此候选在G自身Top5且正分，支持A；分数/排名不解释为交互概率。

### overlap

原预测：C；Confidence：0.999725；助手暂定参考：C；状态：no_specific_error_found。

原理由：0 direct or indirect support users among 17 overlap neighbors; no observed positive interactions; weak evidence for pseudo-interaction.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.997501；助手暂定参考：U；状态：needs_criteria_review。

原理由：Popularity percentile 98.28 and rank 320 suggest high popularity, but local support rate 0.0 and 0 local support users indicate no personalized support despite strong global popularity, implying bias.

- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:2174:15025

Puma Faas 200 Gents Watch

### semantic

原预测：B；Confidence：0.999017；助手暂定参考：C；状态：no_specific_error_found。

原理由：Positive history includes fashion items (ECCO, Ray-Ban) with 5-star ratings; target is a fashion watch with literal "fashion" match, but 8 unmatched concepts (e.g., "watch", "sport") limit semantic alignment; evidence is weak due to mismatched core product type.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：B；Confidence：0.998078；助手暂定参考：U；状态：confirmed_evidence_error。

原理由：G score 0.33 and 11 visible train users suggest weak support; 2,816 mapping support users indicate broad item exposure, but low user overlap limits confidence in pseudo-interaction.

- invented_exposure：2816映射用户不是物品曝光指标，输入没有曝光日志。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

### overlap

原预测：C；Confidence：0.999905；助手暂定参考：C；状态：no_specific_error_found。

原理由：0 direct/indirect support users among 17 actual neighbors; no observed positive interactions; weak cooccurrence signals; insufficient evidence for strong support.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999996；助手暂定参考：U；状态：needs_criteria_review。

原理由：Local support rate is 0.0 despite 11 train interactions; popularity percentile 64.3 suggests moderate exposure, but no direct user support found; evidence limitation: no exposure data available. C. Reject.

- unsupported_visibility：热门度/交互数不能识别实际曝光或visibility，曝光字段不可用。
- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:2174:1371

Polar Bottle Insulated Water Bottle

### semantic

原预测：C；Confidence：0.999965；助手暂定参考：C；状态：no_specific_error_found。

原理由：No literal positive-history support found; unmatched concepts (bottle, insulated, polar, water) lack semantic alignment with source preferences in footwear, apparel, or accessories.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.999809；助手暂定参考：A；状态：no_specific_error_found。

原理由：G score 1.62 and 261 visible train users indicate strong collaborative signal; 2816 mapping support users further validate relevance, though limited by lack of target-side support data.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：此候选在G自身Top5且正分，支持A；分数/排名不解释为交互概率。

### overlap

原预测：B；Confidence：0.999889；助手暂定参考：B；状态：no_specific_error_found。

原理由：4 overlap users supported the candidate or its neighbors, with only 1 direct support; weak evidence due to low direct support and sparse cross-domain behavior.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999989；助手暂定参考：U；状态：needs_criteria_review。

原理由：Popularity percentile 99.88 and rank 23 indicate extreme popularity; local support rate 5.88% is low despite high global support, suggesting bias; evidence lacks exposure data, limiting confidence. Reject.

- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:2174:1825

Tingley Men's Storm Stretch Overshoe

### semantic

原预测：B；Confidence：0.428004；助手暂定参考：B；状态：no_specific_error_found。

原理由：Positive semantic match on "athletic" category and high similarity (0.81) with positive history, but no direct support for rain, storm, or overshoe; limited by lack of positive history for target-specific concepts.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：B；Confidence：0.999173；助手暂定参考：U；状态：no_specific_error_found。

原理由：G score 0.09 is low; only 13 visible train users, 2,816 mapping support users; limited collaborative signal; evidence insufficient for strong support.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

### overlap

原预测：B；Confidence：0.999997；助手暂定参考：B；状态：no_specific_error_found。

原理由：Only 1 direct and 1 indirect support user among 17 overlap neighbors, with union support rate of 5.9%, indicating weak evidence; sparse cross-domain support limits strong inference.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999257；助手暂定参考：U；状态：confirmed_evidence_error。

原理由：Only 1 local support user among 17 in the local group (5.9% rate) with low global support (0.038%) and high popularity rank (5,465/7,740), suggesting support is likely due to popularity bias rather than personalized relevance.

- invented_ranking_denominator：理由给出热门排名5465/7740；证据没有7740这个分母，目标目录18357件。
- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:2174:732

Invicta Men's Speedway 9212

### semantic

原预测：A；Confidence：0.372446；助手暂定参考：C；状态：needs_criteria_review。

原理由：Positive semantic alignment with "fashion" category and high similarity (0.81) to positive history items, but no direct support for watches or Invicta; limited by lack of explicit preference for sport watches.

- generic_concept_transfer：fashion是通用类别词；源正评价鞋/太阳镜不直接支持腕表。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：C；Confidence：0.980479；助手暂定参考：U；状态：no_specific_error_found。

原理由：G score of -0.13 is negative, and only 10 visible training users support the candidate, with low mapping support (2,816), indicating weak collaborative evidence for a pseudo-interaction.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

### overlap

原预测：C；Confidence：0.999963；助手暂定参考：C；状态：no_specific_error_found。

原理由：0 direct/indirect support users among 17 overlap neighbors; no observed positive interactions; weak evidence for pseudo-interaction.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999957；助手暂定参考：U；状态：needs_criteria_review。

原理由：Local support rate is 0.0 with 0 support users, while global support is 0.00029; low local support despite moderate popularity suggests bias, not personalized relevance.

- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。

## cloth_sports:prompt_dev:2174:15121

MSR - GroundHog Stakes - 8 Pack

### semantic

原预测：C；Confidence：0.999961；助手暂定参考：C；状态：no_specific_error_found。

原理由：No literal positive-history support found; unmatched concepts indicate no semantic alignment with source preferences despite high similarity score.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：看核心产品类型/用途、正评价源物品与语义排名；通用词重合不给Strong。不是用户偏好真值。

### collaborative

原预测：A；Confidence：0.401484；助手暂定参考：A；状态：no_specific_error_found。

原理由：G score 1.53 and 73 visible training users indicate strong collaborative signal, but limited source history (5 interactions) constrains confidence in pseudo-interaction validity.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：此候选在G自身Top5且正分，支持A；分数/排名不解释为交互概率。

### overlap

原预测：C；Confidence：0.999401；助手暂定参考：C；状态：no_specific_error_found。

原理由：0 direct/indirect support users among 17 overlap neighbors; no observed positive interactions; weak cross-domain support despite 20 target neighbors.

本轮未发现明确事实错误；不表示已证明ABC正确。

参考说明：助手暂定：本样本无支持为C；1–6人或主要间接支持为B；14/17人直接支持视为A候选。不是预先校准的通用阈值。

### popularity_bias

原预测：C；Confidence：0.999787；助手暂定参考：U；状态：needs_criteria_review。

原理由：Popularity percentile 97.6% and 73 train interactions suggest strong popularity bias; local support rate 0.0% with 0 local support users indicates no personalized support despite high visibility.

- unsupported_visibility：热门度/交互数不能识别实际曝光或visibility，曝光字段不可用。
- unsupported_bias_attribution：理由由热门度或稀疏局部计数推断bias dominates/支持归因热门，缺少充分排除个性化富集的依据。

参考说明：当前准则不足以给出独立可靠ABC金标签，保留人工确认。
