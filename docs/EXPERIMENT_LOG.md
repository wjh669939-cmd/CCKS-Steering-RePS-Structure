# CCKS2026 SteerEval 实验进度日志

> **任务**：SteerEval Personality · Qwen3-4B-Instruct-2507 · valid 120 条 / 24 concept  
> **日志截止**：2026-06-30 · **v7.0**（phase_f **0.6714** 锁定；概念锁定 + BA-BoN 结案）  
> **说明**：表中「本地 proxy」为 matching/not_matching token F1 近似，**≠ 天池官方分**。**0.5583 之后 proxy 与官方分常反向**，禁止用 proxy 驱动 patch 提交。

---

## 一、阶段性成果总览

| 阶段 | 关键动作 | 天池官方分 | 结论 |
|------|----------|-----------|------|
| **I** CAA 自研探索 | 基线 + 变体 + BiPO/Conceptors | **0** | 本地 proxy 见顶 ~3.04，流程未对齐官方 → **转向 RePS** |
| **II-A** RePS 搭建与扫参 | 向量训练 + L3/L1/L2 分档 multiplier | — | 本地 proxy 2.66 → **3.21** |
| **II-B** 首次天池提交 | 256 token + full 后处理 | **0.2583** | 格式通过，后处理损害自然度 |
| **II-C** 官方分对比实验 | 512 token；official vs raw | official **0.355** / raw **0.3817** | 增益来自 512 token + 扫参，非后处理 |
| **II-D** 冻结 baseline | layer 18，512 token，raw | **0.3817** | 较 II-B **+48%**，已冻结为对照基线 |
| **III** multiplier / token 微调 | 768 token / personality trial / Round 2 扫参 | 768 **0.2967** / trial **0.33** | 均未超越 baseline |
| **IV** 后处理 / 全局 layer 试验 | l3only / trunc_fix / layer20 全量 / matching_pick / L3-CAA | l3only **0.2583** / trunc **0.3633** / 其余未提交或本地证伪 | 后处理与全量换法均不如 raw |
| **V** weak8 逐 concept 选层 | 8 薄弱 concept 换层 + baseline multipliers | **0.385** | 换层方向正确，较 baseline **+0.9%** |
| **VI** L3 mult + L1/L2 选层 + merge | weak8_l3_mult + round2 layer pilot → best_merge | **0.4517** | 较 baseline **+18.3%** |
| **VII** Phase C：L1/L2 弱项 mult/layer 扫参 | L2_1/3/6 mult↑ + L1_4/5/6 换层 → phase_c | **0.5583** | 较 best_merge **+23.6%** |
| **VIII** Phase F：L2_2 重训向量 | train-only 选 L18，m=3.5，仅改 5 题 | **0.6714** | **当前官方最优**，较 phase_c **+20.3%** |
| **VIII-b** Phase F 批量 L2 重训 | L2_3/5/6/7 等重训 + **多 concept 合并** | **0.6583** | 较 0.6714 **−2.0%**，**已回滚** |
| **VIII-c** Phase F 单 L2_5 patch | 0.6714 base + 仅 L2_5 重训 L18 m=3.5 | **0.5006** | 较 0.6714 **−25.4%**；L2_2 模式不可推广 |
| **VIII-d** Phase F 单 L2_6+7 patch | 0.6714 base + L2_6/7 重训 | **0.5433** | 已证伪 |
| **VIII-e** Phase F 批量重训（扫参） | 7 concept 产出候选 | — | 除 L2_2 外 **禁止 merge** |
| **IX** 概念锁定 + L1 重训试点 | `concept_lock.json`；L1_2–7 重训 sweep | L1_7 only **0.55** | 够好 concept 禁止 patch |
| **X** BA-BoN（Baseline-Anchored BoN） | mult 扫参 + 采样；baseline 锚定选优 | L1_8 **0.5183** | 本地 proxy **证伪**；L3 mult 0 改 |
| **XI** 工作区整理 + 新方向 brainstorm | `workspace_cleanup.sh`；`STEER_IDEAS.md` | — | 暂停官方 A/B，待新 steer 机制 |

**当前最优方案**：`绝地邮兵_result.json`（**phase_f L2_2-only**：Phase C + L2_2 重训 · L18 · m=3.5 · 官方 **0.6714**）

**配置快照**：`baseline/layers.json` + `baseline/multipliers.json` + `baseline/submission.json` + `baseline/concept_lock.json`

**新方向文档**：[STEER_IDEAS.md](STEER_IDEAS.md)（含论文引用）

---

## 二、第一阶段：CAA 自研框架（已结束）

**目标**：基于 Contrastive Activation Addition 自研 steering，按 concept 提取激活差分并注入。

**成果**：完成基线（proxy **3.044**）、layer×strength 扫参、5 种向量变体及 BiPO/Conceptors 对比；**均未突破基线**。

**失败/终止原因**：
1. L1/L2 人格对齐弱、L3 字面约束不稳，本地优化遇瓶颈；
2. 天池首次提交 **0 分**——自研流程与官方嵌套 JSON / RePS pipeline 不一致，无法有效评测。

**决策**：切换至赛方推荐 **RePS** 方法。

---

## 三、第二阶段：RePS 方法与官方分优化

### 3.1 方法与工程（II-A）

- **框架**：EasyEdit2 RePS，Qwen3-4B-Instruct-2507，干预层 **layer 18**
- **流程**：24 concept 向量训练 → 分档 multiplier 扫参（L3 → L1/L2）→ valid 生成 → 提交
- **本地进展**：统一 m=3 基线 proxy 2.66 → 全扫参 **3.21**（超越 CAA）

### 3.2 天池官方分优化（II-B ~ II-D）

| 版本 | 配置要点 | 提交文件 | 官方分 | 相对最优 |
|------|----------|----------|--------|----------|
| **reps_full_v256**（旧版） | 256 token + full 后处理 | `绝地邮兵_result.json` | 0.2583 | −0.127 |
| **reps_official_v1** | 512 token + official 轻量后处理 | `绝地邮兵_result_official.json` | 0.355 | −0.030 |
| **reps_raw_v1**（baseline） | 512 token + raw，无后处理 | `baseline/submission.json` | **0.3817** | −0.003 |

**核心结论**：
- 主增益来自 **512 token 重生成 + 分档扫参**；
- 后处理与 local proxy 同向、与官方分**反向**；
- **512 token 为 sweet spot**；官方 judge 重自然度，不宜靠规则改写。

**已冻结**：`baseline/`（`multipliers.json` + `submission.json`，复现 `bash scripts/regen_from_baseline.sh 512`）

---

## 四、第三阶段：未超越 baseline 的尝试

| 实验 | 改动 | 官方分 | 失败原因 |
|------|------|--------|----------|
| **768 token** | max_new_tokens 512→768 | **0.2967** | 加长略减截断，自然度下降 |
| **Personality trial** | L2_1 m↓、L1_2 m↑ | **0.33** | 降 multiplier 削弱 steering |
| **Round 2（本地）** | L3_6 / L2_3 重扫 | 未提交 | 预期收益低 |
| **L3-only 后处理** | `--mode l3_only` 插词 | **0.2583** | 破坏自然度 |
| **trunc_fix** | 截断样本重生成 + 轻量修复 | **0.3633** | 改动损害整体对齐 |
| **matching_pick** | 4 候选 + train margin 选优 | 未提交 | L3 10/40 与 weak8 持平，120/120 全改，风险大 |
| **L3-only CAA** | L3 用 CAA，L1/L2 保持 baseline | 未提交 | 本地 L3 **0/40**，弱于 RePS |
| **Layer 20 全量** | 24 concept 重训 layer 20 | 未提交 | 本地样本更差 |

**归纳教训**：
1. 不以 local proxy、截断数、免责声明作为提交决策依据（但 **官方分可与 weak8 本地 L3 audit 同向**）；
2. 不将 multiplier 降至 baseline 以下；
3. **禁止后处理插词**；512 token raw 为固定约束；
4. 换维度（**per-concept layer**）优于全局 multiplier / 后处理 / 换方法（CAA）。

---

## 五、第四阶段：weak8 逐 concept 选层

**动机**：layer 18 上 multiplier 扫参已到顶；薄弱 concept（L3 硬约束 + L2_1）需不同干预深度。

**方案**：
- 对 **8 个 concept**（L3_1–L3_6、L3_8、L2_1）在 train 上从 layer **16/18/20** 选层（L3 用 keyword + margin，L2 用 margin）；
- 其余 **16 个 concept** 保持 baseline layer 18；
- multiplier 仍用 `baseline/multipliers.json`（未重扫）；
- 512 token · raw · 无后处理。

**weak8 层配置**（`baseline/weak8_layers.json`）：

| Concept | Layer | 说明 |
|---------|-------|------|
| L2_1 | 16 | 人格对齐薄弱 |
| L3_1 | 16 | `??` |
| L3_2 | 16 | `let's improvise` |
| L3_3 | 20 | `sonder` |
| L3_4 | 16 | `mos maiorum` |
| L3_5 | 16 | `variance is the point` |
| L3_6 | 16 | `self-authored` |
| L3_7 | 18 | baseline 层（pareto 已较好） |
| L3_8 | 18 | baseline 层 |
| 其余 L1/L2 | 18 | 不变 |

**本地 audit（valid）**：

| 指标 | baseline | weak8 |
|------|----------|-------|
| L3 keyword | 4/40 | **10/40** |
| vs baseline 改动 | 0/120 | 92/120 |
| 截断 | 30/120 | 19/120 |
| 免责声明 | 2/120 | 1/120 |

**天池官方分**：**0.385**（较 baseline **+0.0033，+0.9%**）— 已提交验证有效；后被 **best_merge（0.4517）** 超越。

**复现**：
```bash
bash scripts/run_weak8_layer_pilot.sh   # train + pick + regen
# 产出：绝地邮兵_result_weak8_layer.json
```

**相关文件**：

| 文件 | 说明 |
|------|------|
| `scripts/run_weak8_layer_pilot.sh` | weak8 一键流程 |
| `easyedit_reps/scripts/train_single_concept_layer.py` | 单 concept 单层训练 |
| `easyedit_reps/scripts/pick_layer_on_train.py` | train 选层 |
| `easyedit_reps/scripts/regen_mixed_layers.py` | 混合层重生成 |
| `runs/weak8_layer/` | 运行日志 |

---

## 六、Layer 20 全量试验（已结案，未提交）

**方案**：24 concept 统一 layer 20 重训，沿用 baseline multipliers。

**结论**：本地生成质量未优于 layer 18 baseline，**未提交天池**。weak8 中仅 **L3_3 单独采用 layer 20**，全量迁移 layer 20 不可行。

**相关**：`easyedit_reps/config/steer_eval_reps_layer20.yaml`、`scripts/run_layer20_trial.sh`、`runs/layer20_trial/`

---

## 七、第五阶段：best_merge（L3 mult + round2 + merge）

**动机**：weak8（0.385）换层有效但 L3 multiplier 未调；L1/L2 仍全 layer 18。

**天池官方分**：**0.4517**（较 baseline **+18.3%**）— 已被 phase_c 超越，归档于 `baseline/archive/submission_best_merge_0.4517.json`。

**复现**：
```bash
bash scripts/run_weak8_l3_mult_sweep.sh
bash scripts/run_round2_optimize.sh
bash scripts/run_best_merge.sh
```

---

## 八、第六阶段：Phase A/B/C 诊断与 L1/L2 优化 — 当前最优

### 8.1 Phase A：诊断（proxy + 词表投影）

**结论**：
- best_merge proxy：Overall HM≈0.66；**L1/L2 CS 低** 是真正瓶颈，非 L3 keyword
- 最弱 concept：L1_1、L1_8、L2_1、L2_3、L2_6、L3_3、L3_5（proxy HM=0）
- L3_3 `sonder` rank **151480**；L3_5 `variance is the point` rank **149805** — 向量 steering 未推向目标 token

**产出**：`runs/phase_a/best_merge_official_proxy.json`、`runs/phase_a/l3_vocab_projection.json`

### 8.2 Phase B：L3_3 RePS-LoRA（已证伪）

- L3_3 @ L20 LoRA 训练 acc=1.0，regen 后 L3_3 仍 **0/5**，输出重复退化
- **结论**：LoRA 不适用；勿提交 `phase_b_l3_3_lora.json`

### 8.3 Phase C：L1/L2 弱项 mult/layer 扫参（已提交，官方验证）

**方案**（冻结 best_merge 的 L3，只动 L1/L2 弱项）：

| Concept | 变更 | proxy HM |
|---------|------|----------|
| L2_1 | m 1.5→**3.5** | 0→0.600 |
| L2_3 | m 1.0→**2.0** | 0→1.000 |
| L2_6 | m 2.5→**4.0** | 0→0.600 |
| L1_4 | L18→**L16** | 0.300→0.600 |
| L1_5 | L18→**L20** | 0.900→1.200 |
| L1_6 | L18→**L16** | 0.900→0.600 |
| L1_1 / L1_8 | 无改善 | 仍 HM=0 |

**本地 audit（valid）**：

| 指标 | best_merge | phase_c |
|------|------------|---------|
| L3 keyword | 25/40 | 25/40 |
| Official proxy HM | 0.662 | **0.766** |
| L2 proxy HM | 0.443 | **0.718** |

**天池官方分**：**0.5583**（较 best_merge **+0.1066，+23.6%**；较 reps_raw_v1 **+46.3%**）— **已提交验证**。

**归因**：L2 multiplier 上调为主增益；L1 换层次要；L3 未动；proxy 与官方分**同向**。

**复现**：
```bash
bash scripts/run_phase_c_l12_optimize.sh
# 产出: 绝地邮兵_result_phase_c_l12.json
```

**已固化为 baseline**：见 `baseline/README.md`、`baseline/baseline_manifest.json`、`baseline/concept_lock.json`。

---

## 十、第七阶段：Phase F 后续 — 概念锁定与证伪实验（2026-06-30）

### 10.1 动机

0.6714 后多次单 concept patch 官方大跌，确立策略：**先锁够好的 concept，只对顽固项实验**；任何 merge 前用 `check_concept_lock.py` 校验。

### 10.2 四类概念划分（`baseline/concept_lock.json`）

| 类别 | 数量 | 含义 |
|------|------|------|
| **PROVEN** | 1 | L2_2（唯一官方涨分点） |
| **LOCKED 够好** | 10 | L1_4–6, L2_1/3/4/8, L3_4/7/8 — **禁止 patch** |
| **PATCH_FORBIDDEN** | 5 | 官方 patch 已跌 — **禁止再实验** |
| **STUBBORN** | 8 | 仍有改进空间 — 唯一允许专项实验 |

详见 `docs/CONCEPT_LOCK.md`。

### 10.3 L1 重训试点（retrain_pilot_l1）

| 提交 | 改动 | 官方分 | 结论 |
|------|------|--------|------|
| L1_7 only（L20 m=3.5 重训） | 5/5 | **0.55** | ❌ 基线够好，提 mult 过 steer |
| L1_2–6 本地 sweep | — | 未交 | 无官方验证，**不再作为 L1 主路径** |

**教训**：L1 重训 + 提 mult 与 L2_5 模式类似，对「够好」concept **减损 > 增益**。

### 10.4 BA-BoN（Baseline-Anchored Best-of-N）

**方法**：对单 STUBBORN concept 扫 mult + 温度采样；baseline 答案始终在候选池；**仅当候选严格优于 baseline 排名才替换**。

| concept | 本地改动 | 官方分 | 结论 |
|---------|----------|--------|------|
| L3_3 | 0/5 | 未交 | keyword 仍 0/5；mult 扫参死路 |
| L3_5 | 0/5 | 未交 | 同上 |
| L1_1 | 4/5 | 未交 | **禁止提交**（L1_8 证伪 proxy） |
| L1_8 | 4/5 | **0.5183** | ❌ 本地「更优」→ 官方 **−15.3%** |

**脚本**：`scripts/run_ba_bon.sh`、`easyedit_reps/scripts/regen_ba_bon.py`  
**归档**：`archive/submissions/06_ba_bon/`、`archive/runs/ba_bon_*`

### 10.5 Phase F 官方 patch 完整记录

| 提交 | 官方分 | vs 0.6714 |
|------|--------|-----------|
| L2_2 only（当前 baseline） | **0.6714** | — |
| L2_2+3+5+6+7 merge | 0.6583 | −2.0% |
| L2_5 only | 0.5006 | −25.4% |
| L2_6+7 only | 0.5433 | −19.1% |
| L1_7 retrain only | 0.55 | −18.1% |
| L1_8 BA-BoN only | 0.5183 | −22.8% |

---

## 十一、当前瓶颈（0.6714 baseline 审计）

基于 `runs/baseline_concept_audit.json`（本地 proxy，**仅作定位参考**）：

### 11.1 分档 HM（valid proxy）

| 档位 | Overall | L1 | L2 | L3 |
|------|---------|----|----|-----|
| 0.6714 baseline | **0.766** | 0.518 | 0.718 | 1.063 |

**真正短板在 L1**（CS=0.35），L3 本地 proxy 已较高但仍有 keyword 空洞。

### 11.2 顽固 concept（官方 patch 难啃）

| ID | 类型 | proxy HM | keyword | 已尝试且失败 |
|----|------|----------|---------|-------------|
| L1_1 | antagonistic | **0** | — | BA-BoN（未交，L1_8 证伪同类） |
| L1_8 | antagonistic | **0** | — | BA-BoN **0.5183** |
| L3_3 | keyword | **0** | **0/5** | mult/LoRA/BA-BoN；词表 rank ~15 万 |
| L3_5 | keyword | **0** | **0/5** | 同上 |
| L1_2 | personality | 0.3 | — | L1 重训未验证 |
| L1_3 | personality | 0.3 | — | 同上 |

### 11.3 结构性瓶颈（归纳）

1. **L2_2 重训不可复制**：L2_5/6/7、L1_7 单 patch 均大跌；多 concept merge 亦跌。
2. **L3 keyword 顽固项**：现有 RePS 向量**推不动目标 token**（logit rank 15 万+）；全程固定 mult 无法让模型自然写出 `sonder` 等词。
3. **本地 proxy 在 0.5583 后不可信**：BA-BoN antagonistic 排名与官方**负相关**；禁止 proxy 驱动提交。
4. **L1 antagonistic 与 RLHF 冲突**：L1_1/8 CS=0 可能为 rubric 固有难点，patch 风险极高。
5. **改进空间收窄**：11/24 concept 已锁；有效自由度仅剩 **干预形态创新**（非 mult 扫参 / 非多 concept merge）。

### 11.4 下一方向（详见 `docs/STEER_IDEAS.md`）

| 优先级 | 方向 | 说明 |
|--------|------|------|
| **1** | Decay Steer | 分阶段 multiplier（前 k token 高 mult → 衰减） |
| **2** | pos_only RePS | L3 keyword 专用训练；试点 L3_2（4/5 kw） |
| 3 | 正交化向量 | 去除与 helpfulness 共线分量 |
| — | ~~BA-BoN mult~~ | 已结案 |
| — | ~~L1 patch~~ | 已证伪 |

---

## 十二、Round 4 方案（基于 phase_c = 0.5583）— 已由 Phase F 超越

**现状**：官方 **0.5583**；L3 keyword **25/40**；顽固 concept：**L1_1、L1_8**（CS=0）、**L3_3、L3_5**（kw 0/5）。

**冻结基线（勿动）**：
- 层：`baseline/layers.json`
- mult：`baseline/multipliers.json`
- 提交对照：`baseline/submission.json` / `绝地邮兵_result.json`

**原则**：512 token raw · 无后处理 · 一次只改一类变量 · 有官方分再动下一维。

### 9.1 优先：L3_3 / L3_5 专项

| 项 | 内容 |
|----|------|
| **问题** | 词表 rank 15 万+；mult/LoRA/pos_only 均已证伪 |
| **下一步** | `local_weight` 干预试点；或极高 mult（8–12）单 concept |
| **提交条件** | valid keyword ≥2/5 再 merge |

### 9.2 次要：L3_1 / L3_6 keyword 补全（3/5→5/5）

- L3_6 round3 partial 曾 m 3.5→6.0 本地 +1 kw，可再扫

### 9.3 低优先：L1_1 / L1_8

- RLHF 与 antagonistic/boundary-testing 方向冲突；matching_pick 或 CAA 对照，ROI 低

### 9.4 不建议再试

- 后处理插词、768 token、全量 CAA、LoRA（L3_3）、pos_only（L3_3/5）

**预期**：L3_3/5 全突破约 +0.02~0.04 官方分；目标 **0.58+**。

---

## 十三、历史：Round 3 方案（基于 best_merge = 0.4517，部分已由 Phase C 完成）

**现状（历史）**：官方 **0.4517** — 详见第八节 Phase C 及 `baseline/archive/`。

**Round 3-A（L2 mult）**：✅ 已由 Phase C 完成并验证（L2_1/3/6 mult 上调 → 官方 **0.5583**）。

### 10.1 Round 3-A：L2-only multiplier 扫参（✅ Phase C 完成）

| 项 | 内容 |
|----|------|
| **改什么** | 仅 L2_1–L2_8 的 m；L1/L3 层+mult 全冻结 |
| **重点** | **L2_3**（m=1.0，round2 已换 L16）、L2_1（m=1.5 偏低） |
| **扫参范围** | m ∈ {1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0}，只升不降 |
| **选优** | train 上 personality margin（neg/trunc/disc 次之），valid audit |
| **产出** | `baseline/round3_l2_mult.json` → regen → `绝地邮兵_result_round3_l2.json` |
| **提交条件** | vs best_merge：L2 块有改善且 trunc/disc 不恶化 |

### 10.2 Round 3-B：L1 multiplier 微调（次选，仅当 3-A 无增益）

| 项 | 内容 |
|----|------|
| **改什么** | 仅 round2 中**已换层且输出变化**的 L1：L1_1/2/3/7/8 |
| **不改** | L1_4/5/6（round2 仍 L18）、全部 L2/L3 |
| **理由** | 0.4517 中 L1 换层已贡献 5/7 改动 concept，mult 可能未饱和 |

### 10.3 Round 3-C：L3_3 / L3_5 专项（中成本，需重训）

| 项 | 内容 |
|----|------|
| **问题** | keyword 恒 0/5；train 激活方向一致性差（directional agreement 低） |
| **步骤 1** | 向量词表投影 audit：确认 steering 是否推对 target token |
| **步骤 2** | **pos_only 子集**重训 RePS（pos 含词、neg 不含） |
| **步骤 3** | 试 **L20/L22** 或 **L16+L20 双层**（仅该 2 concept） |
| **提交** | 仅当 valid keyword ≥2/5 再 merge 进 best_merge |

### 10.4 不建议再试

- 后处理插词、768 token、全量 CAA、matching_pick 全量、keyword 多候选无池

### 10.5 推荐执行顺序（历史，Round 3-A 已由 Phase C 完成）

```
Round 3-A（L2 mult 扫参）
    ↓ 有本地改善
提交 round3_l2 → 看官方分
    ↓ 若仍有余量
Round 3-C（L3_3/L3_5 专项，并行度低）
    ↓
Round 3-B（L1 mult，最后微调）
```

**预期**：3-A 低成本挖 L2 manner 对齐；3-C 攻 L3 剩余 10 分 keyword 空间；官方分目标 **0.48+**（保守）、**0.50+**（若 L3_3/5 突破）。

---

## 九、历史优化方向备忘（weak8 时代，部分已完成）

<details>
<summary>v3.1 基于 weak8=0.385 的旧计划（点击展开）</summary>

### 7.1 高优先级 — **A/B 已完成并验证（→ 0.4517）**

| 方向 | 状态 |
|------|------|
| A. weak8 上重扫 L3 multiplier | ✅ → weak8_l3_mult，L3 25/40 |
| B. L1/L2 layer pilot | ✅ → round2_layers.json |
| C. 混合提交 merge | ✅ → best_merge **0.4517** |

### 7.2 中优先级

| 方向 | 状态 |
|------|------|
| D. pos_only 重训 L3 | ⏳ Round 3-C |
| E. 24 concept 全量 per-layer | ❌ 成本高，round2 已覆盖 L1/L2 |

</details>

---

## 十二、Phase IX–XI：概念锁定、L1 重训、BA-BoN（2026-06-30）

### 12.1 概念四类锁定

在 0.6714 上逐 concept 审计（`runs/baseline_concept_audit.json`）后，将 24 concept 划分为：

| 类别 | 数量 | 策略 |
|------|------|------|
| **PROVEN** | 1 | L2_2：唯一官方涨分点 |
| **LOCKED 够好** | 10 | L1_4–6, L2_1/3/4/8, L3_4/7/8：**禁止 patch** |
| **PATCH_FORBIDDEN** | 5 | 官方单 patch 已跌：L1_7/8, L2_5/6/7 |
| **STUBBORN** | 8 | 仅存实验队列（见 `concept_lock.json`） |

检查：`python3 scripts/check_concept_lock.py L3_2`（允许）/ `L1_5`（禁止）

### 12.2 L1 重训试点（`run_pilot_retrain_l1.sh`）

- 向量目录：`retrain_pilot_l1/`（与失败 L2 pilot 隔离）
- 已跑 L1_2–L1_7；本地 sweep 产出归档于 `archive/submissions/04_pilot/`
- **L1_7 官方**：单 patch m=3.5 → **0.55**（基线够好，提 mult 过 steer）
- **结论**：L1 重训 + 提 mult **不可作为顽固 concept 主路径**

### 12.3 BA-BoN（Baseline-Anchored Best-of-N）

脚本：`easyedit_reps/scripts/regen_ba_bon.py`、`scripts/run_ba_bon.sh`

- 单 STUBBORN concept：mult 网格 + 可选 temperature 采样
- baseline 答案始终在候选池；**仅当候选严格优于 baseline 排名才替换**
- L3：keyword 硬门槛；L1：长度 + disclaimer 惩罚（本地 proxy）

| 提交 | concept | 改动 | 官方分 | 结论 |
|------|---------|------|--------|------|
| `ba_bon_L3_3` | L3_3 | 0/5 | — | 未交；kw 仍 0/5 |
| `ba_bon_L3_5` | L3_5 | 0/5 | — | 未交；kw 仍 0/5 |
| `ba_bon_L1_8` | L1_8 | 4/5 | **0.5183** | ❌ 本地「更优」→ 官方大跌 |
| `ba_bon_L1_1` | L1_1 | 4/5 | — | **禁止提交** |

归档：`archive/submissions/06_ba_bon/`

### 12.4 当前瓶颈（2026-06-30）

| 瓶颈 | 证据 | 含义 |
|------|------|------|
| **L2_2 不可复制** | L2_5 only 0.5006；多 L2 merge 0.6583 | 重训向量仅 L2_2 有效，勿推广 |
| **L3 顽固 keyword** | L3_3/5 kw 0/5；词表 rank 15 万+ | 固定 mult RePS **推不动目标 token** |
| **L1 antagonistic** | L1_1/8 proxy HM=0；L1_8 BA-BoN 0.5183 | RLHF 与对抗人格冲突；**本地 L1 proxy 不可信** |
| **够好 concept 减损>增益** | L1_7 0.55、L1_8 0.5183 | 11 个 concept 应冻结，patch 风险极高 |
| **评测黑盒** | proxy 与官方在 0.5583 后常反向 | **仅以官方分为 merge 依据** |
| **长文生成控制衰减** | 高 mult 全程注入易重复/退化 | 需分阶段或稀疏干预（见 STEER_IDEAS） |

**0.6714 baseline 审计（本地 proxy，仅参考）**：

| Level | HM | CS | 薄弱 concept |
|-------|-----|-----|--------------|
| L1 | 0.52 | 0.35 | L1_1/8 HM=0；L1_2/3 CS 弱 |
| L2 | 0.72 | 0.50 | L2_2 为 PROVEN；L2_5–7 已禁 patch |
| L3 | 1.06 | 1.18 | L3_3/5 kw 0/5；L3_1/2/6 差 1–2 题 |

### 12.5 下一步（暂停官方提交）

见 [STEER_IDEAS.md](STEER_IDEAS.md)。优先：**Decay Steer**（分阶段 mult）、**pos_only RePS**（L3_2 试点）；L1 全线观察。

---

## 十三、关键文件索引

| 用途 | 路径 |
|------|------|
| **当前最优提交** | `绝地邮兵_result.json` / `baseline/submission.json`（**0.6714**） |
| **概念锁定** | `baseline/concept_lock.json` · [CONCEPT_LOCK.md](CONCEPT_LOCK.md) |
| **新 steer 方向** | [STEER_IDEAS.md](STEER_IDEAS.md) |
| **BA-BoN 官方记录** | [ba_bon_official.md](ba_bon_official.md) |
| **逐 concept 审计** | `runs/baseline_concept_audit.json`（本地，未入库） |
| 历史提交归档 | `archive/submissions/`（JSON 被 .gitignore） |
| best_merge 对照 | `baseline/archive/submission_best_merge_0.4517.json` |
| reps_raw_v1 对照 | `baseline/archive/submission_reps_raw_v1_0.3817.json`（0.3817） |
| **层配置（当前）** | `baseline/layers.json` |
| **multiplier（当前）** | `baseline/multipliers.json` |
| baseline 说明 | `baseline/README.md` |
| 工作区整理 | `scripts/workspace_cleanup.sh` |
| 概念锁定检查 | `scripts/check_concept_lock.py` |
| BA-BoN | `scripts/run_ba_bon.sh` |
| 回滚 0.6714 | `scripts/rollback_to_phase_f_l2_2.sh` |
| Phase C 复现 | `scripts/run_phase_c_l12_optimize.sh` |
| 从 baseline 重生成 | `scripts/regen_from_baseline.sh` |
| L3 keyword audit | `scripts/audit_l3_keywords.py` |
| Official proxy audit | `scripts/audit_official_proxy.py` |
| merge 工具 | `scripts/merge_submission.py` |
| 复现指南 | [reproduction/](reproduction/) · [baseline_0.6714.md](reproduction/baseline_0.6714.md) |
| 官方分优化记录 | [OFFICIAL_SCORE_OPTIMIZATION.md](OFFICIAL_SCORE_OPTIMIZATION.md) |
| RePS 环境搭建 | [REPS_SETUP.md](REPS_SETUP.md) |
| 实验计划 | [NEXT_EXPERIMENTS.md](NEXT_EXPERIMENTS.md) |

---

## 附录：方法论文献（本赛题已用 / 拟借鉴）

| 方法 | 论文 | 在本项目中的角色 |
|------|------|------------------|
| **RePS** | [Improved Representation Steering (NeurIPS 2025)](https://arxiv.org/html/2505.20809v1) | 赛方推荐；当前主 pipeline |
| **EasyEdit2** | [EMNLP 2025 Demo](https://arxiv.org/html/2504.15133v1) · [项目页](https://zjunlp.github.io/project/EasyEdit2/) | 工程框架 |
| **RepE** | [Zou et al. 2023](https://arxiv.org/html/2310.01405v4) | 激活空间操控范式 |
| **ActAdd** | [Turner et al. 2023](https://arxiv.org/html/2308.10248v4) | 对比激活差分 → 转向量 |
| **CAA** | [Panickssery et al. ACL 2024](https://arxiv.org/html/2312.06681v4) | 阶段 I 探索；L3 hybrid 证伪 |
| **BiPO** | [Cao et al. 2024](https://arxiv.org/abs/2406.00045) | RePS 前置；偏好优化转向量 |
| **Conceptors** | [Postmus & Abreu 2024](https://arxiv.org/html/2410.16314v2) | 多 concept 正交组合（拟借鉴） |
| **RepE Survey** | [Wehner et al. 2025](https://arxiv.org/html/2502.19649v3) | 干预形式分类 |
| **SVF** | [Steering Vector Fields 2026](https://arxiv.org/html/2602.01654v1) | 动态/分阶段 mult 理论依据 |
| **Validity decay** | [Why Steering Works 2026](https://arxiv.org/html/2602.02343v2) | 高 mult 损害流畅度解释 |
| **Sparse junction** | [SIA 2026](https://arxiv.org/html/2602.21215v1) | 仅关键 token 干预 |

---

*维护：CCKS2026 Steering 组 · 最后更新 2026-06-30*
