# CCKS2026 大模型行为调控（Steering）实验进度日志

> **任务**：CCKS2026 SteerEval Personality（Qwen3-4B-Instruct-2507，valid 120 条 / 24 concept）  
> **模型**：Qwen3-4B-Instruct-2507  
> **评测说明**：下表 `mean_hm_proxy` 均为本地 proxy 分数（matching/not_matching token F1 近似），**不等于天池官方 LLM judge 分数**，仅供方法对比与调试。  
> **日志日期**：2026-06-19 | **文档版本**：v2.2（含 A/B 官方分反馈）

---

## 一、任务背景

- **赛题目标**：在不在 prompt 中显式写入 concept 的前提下，通过模型内部干预（Steering）使生成结果对齐目标人格/行为概念。
- **数据规模**：`train.json` 1680 条，`valid.json` 120 条；24 个 concept（L1/L2/L3 各 8 个）。
- **实验分两阶段**：
  - **第一阶段**：基于自研 **CAA 框架**探索多种 steering 方法与变体；
  - **第二阶段**：阅读竞赛官方文档后切换至 **EasyEdit2 RePS**，并在此基础上持续优化与提交。

---

## 二、实验总览（两阶段对比）

| 阶段 | 框架 / 方法 | 本地 mean_hm（proxy） | 天池官方分 | 结论 |
|------|------------|----------------------|-----------|------|
| **第一阶段** | 自研 CAA 及变体（最优） | **3.044** | **0**（格式/流程未对齐） | CAA 框架对初赛数据效果有限，未继续深挖 |
| **第一阶段** | BiPO / Conceptors 等 | 2.608 ~ 3.026 | — | 均未超过 CAA 基线 |
| **第二阶段** | RePS baseline (m=3) | 2.660 | — | 需分 concept 调参 |
| **第二阶段** | RePS + L3 分档扫参 | 2.899 | — | L3 明显改善 |
| **第二阶段** | RePS + L1/L2/L3 全扫参 | 3.210 | — | 本地超越 CAA |
| **第二阶段** | RePS 全扫参 + full 后处理 | 3.251 | **0.2583** | 格式通过，full 后处理损害自然度 |
| **第二阶段** | RePS 512 token + official 后处理（**B 版**） | — | **0.355** | 轻量后处理仍略损自然度 |
| **第二阶段** | RePS 512 token 无后处理（**baseline v1**） | — | **0.3817** | 已冻结至 `baseline/` |
| **第二阶段** | RePS 768 token 无后处理（Round 1） | — | 待天池 | 截断 26/120（512 为 30/120） |

**核心转折**：第一阶段在 CAA 框架下多轮优化后，本地 proxy 最高约 3.044，且天池提交得 0 分；阅读 [EasyEdit CCKS2026 文档](https://github.com/zjunlp/EasyEdit/blob/main/examples/CCKS2026.md) 后确认 **RePS** 为赛方推荐 pipeline，遂切换至第二阶段。

---

## 三、第一阶段：CAA 自研框架探索

> 代码目录：项目根目录 `ccks_steering/`、`configs/`、`runs/`

### 3.1 框架思路

采用 **Contrastive Activation Addition（CAA）** 作为自研 steering 框架：

1. 按 concept 对 train 中 matching / not_matching 回答提取隐藏层激活；
2. 求差并平均得到 steering 向量；
3. valid 生成时通过 hook 注入向量，使输出对齐目标人格。

在此基础上，围绕 **层数 / 强度 / 向量构造方式** 展开一系列变体实验。

### 3.2 CAA 基线与扫参

| 实验 | 配置 / 说明 | mean_hm（proxy） |
|------|------------|-----------------|
| **CAA 基线** | `configs/baseline_caa.json`，默认 layer/strength | **3.044** |
| layer × strength 网格扫参 | layer 16/20/24/28/32 × strength 0.5~2.0 | 最优 **3.031**（layer=16, strength=0.5） |

扫参未显著超越默认基线，说明单纯调 layer/strength 边际收益有限。

### 3.3 CAA 变体实验

均在 CAA 框架下调整向量构造或注入策略，**均未超过 CAA 基线**：

| 变体 | 配置文件 | mean_hm | 相对基线 |
|------|---------|---------|---------|
| centered | `baseline_caa_centered.json` | 2.661 | −0.383 |
| centered_balanced | `baseline_caa_centered_balanced.json` | 2.947 | −0.097 |
| push | `baseline_caa_push.json` | 2.893 | −0.151 |
| all_s4 | `baseline_caa_all_s4.json` | 2.907 | −0.137 |
| PCA | `baseline_caa_pca.json` | 2.900 | −0.144 |

### 3.4 同期对比方法（同属第一阶段探索）

| 方法 | 思路 | mean_hm | 结论 |
|------|------|---------|------|
| **BiPO** | 对比偏好优化类干预（自研） | 3.026 | 略低于 CAA，未采用 |
| **Conceptors** | 基于 Conceptors 论文的差分 steering | 2.608 | 明显低于 CAA，停止投入 |

### 3.5 第一阶段暴露的问题

1. **concept 对齐分偏低**：L1/L2 生成偏「助手腔」，L3 字面约束难以稳定命中。
2. **本地优化遇瓶颈**：CAA 及全部变体 local proxy 最高 **~3.044**，继续改向量构造方式收益递减。
3. **天池提交 0 分**：自研流程与赛方要求的 **嵌套 JSON 格式** 及 **官方 RePS pipeline** 不一致，无法有效验证方法。

### 3.6 第一阶段结论与转向

**结论**：自研 **CAA 框架对初赛数据集起不到好的作用**——无论基线、扫参还是多种变体，均无法在本地 proxy 上取得突破性提升，且与官方评测流程不对齐。

**转向**：浏览竞赛提供文档（EasyEdit2 / CCKS2026 示例）后，发现赛方推荐使用 **RePS（Representation Engineering Steering）** 方法，具备：

- 官方 qwen3-4b-it 超参与数据格式；
- 按 concept 训练 steering 向量的完整 pipeline；
- 与天池提交格式直接对接。

**决策**：放弃继续深挖 CAA 框架，进入 **第二阶段 — RePS 官方方法与优化**。

---

## 四、第二阶段：RePS 方法与优化

> 代码目录：`easyedit_reps/` | 复现文档：`docs/REPS_SETUP.md` | 官方分优化：`docs/OFFICIAL_SCORE_OPTIMIZATION.md`

### 4.1 方法简介

**RePS** 通过 preference model 在指定层学习 steering 向量，使模型生成更贴近 concept 所描述的人格/行为。赛方配置要点：

- **模型**：Qwen3-4B-Instruct-2507
- **干预层**：layer 18
- **框架**：EasyEdit2（`examples/steer_eval.py` + CCKS2026 hparams）

### 4.2 环境搭建

- 独立环境 `easyedit_reps/.venv`，复用主项目 torch/transformers
- **CCKS 兼容补丁**：
  - `steer/vector_generators/reps/utils.py` — BatchEncoding 兼容
  - `steer/trainer/PreferenceModelTrainer.py` — 末 batch 越界
  - `examples/steer_eval.py` — `method=reps` 与 concept_description fallback

### 4.3 Pipeline 与实验步骤

```text
Step 1  RePS 向量训练（24 concept, layer=18）
           ↓
Step 2  valid 生成（统一 multiplier=3）
           ↓
Step 3  L3 分档 multiplier 扫参（0.5 ~ 3.0）
           ↓
Step 4  L1/L2 分档 multiplier 扫参
           ↓
Step 5  导出 submission → 后处理 → 天池提交
           ↓
Step 6  官方分反馈 → 512 token 重生成 + official 轻量后处理
```

| 步骤 | 脚本 / 配置 | 输出 | mean_hm（proxy） |
|------|------------|------|-----------------|
| 向量训练 | `run_reps_vectors.sh` | `outputs/vectors/ccks_baseline_reps/` | — |
| baseline 生成 | multiplier=3 统一 | `runs/reps_baseline/` | 2.660 |
| L3 扫参 | `sweep_l3_multipliers.py` | `outputs/generation/l3_tuned/` | 2.899 |
| L1/L2 扫参 | `sweep_l12_multipliers.py` | `outputs/generation/l12_tuned/` | **3.210** |
| full 后处理 | `postprocess_submission.py --mode full` | `绝地邮兵_result.json` | **3.251** |
| 512 token 重生成 | `regen_tuned_all.py` | `绝地邮兵_result_pre_optimize_long.json` | — |
| official 后处理 | `postprocess_submission.py --mode official` | `绝地邮兵_result_official.json` | — |

### 4.4 分档扫参结果摘要

**L3 最优 multiplier（部分）**：

| Concept | 最优 multiplier | concept hm |
|---------|----------------|------------|
| L3_1 | 3.0 | 3.607 |
| L3_2 | 2.0 | 3.240 |
| L3_3 | 1.0 | 2.876 |
| L3_7 | 2.5 | 3.583 |
| L3_8 | 2.0 | 3.161 |

**薄弱 concept（全扫参后）**：L2_1 (2.856)、L3_3 (2.876)、L2_3 (2.958)

**未采纳实验**：L2_1 更高 multiplier 重生成（最优 hm=2.380，低于扫参版 2.856）

### 4.5 后处理优化（两版策略）

| 策略 | 模式 | 内容 | 用途 |
|------|------|------|------|
| **full 后处理** | `--mode full` | L3 硬约束 + 免责清理 + hint 插入 + 定向改写 | 本地 proxy 最优（3.251），已提交天池 |
| **official 后处理** | `--mode official` | 免责清理 + L3 硬约束 + 句末截断修复；不做 hint/改写 | 官方 judge 导向，当前推荐提交 |

**full 后处理效果（本地 proxy）**：

| 指标 | 全扫参 RePS | full 后处理 | Δ |
|------|------------|-------------|---|
| mean_hm | 3.210 | **3.251** | +0.041 |
| L2_1 | 2.856 | 3.050 | +0.194 |
| L3_3 | 2.876 | 3.053 | +0.177 |
| L3_8 | 3.161 | 3.394 | +0.233 |

### 4.6 天池提交与官方分反馈

| 提交文件 | 生成配置 | 后处理 | 天池官方分 |
|---------|---------|--------|-----------|
| `绝地邮兵_result.json` | max_new_tokens=256 | full | **0.2583** |
| `绝地邮兵_result_official.json` | max_new_tokens=512 | official | **0.355** |
| `绝地邮兵_result_pre_optimize_long.json` | max_new_tokens=512 | 无 | **0.3817** |

**官方分对比（A/B 实验）**：

| 版本 | 官方分 | 相对旧版 Δ | 相对 A 版 Δ | 说明 |
|------|--------|-----------|------------|------|
| 旧版 full 后处理 | 0.2583 | — | −0.123 | 256 token + hint/改写 |
| B 版 official | 0.355 | +0.097（+37%） | −0.027 | 512 token + 轻量后处理 |
| **A 版 raw RePS** | **0.3817** | **+0.123（+48%）** | — | 512 token，无后处理 |

**A/B 实验结论**（天池反馈）：

- **主增益来自 512 token 重生成 + 分档扫参**，而非后处理；
- **A > B（0.3817 vs 0.355）**：即使 official 轻量后处理（L3 硬约束、免责清理、截断修复）仍略损害官方 LLM judge 对自然度的评价；
- **后处理与本地 proxy 方向相反**：full 后处理 local proxy 最高（3.251）但官方分最低（0.2583）；纯 RePS 无后处理官方分最高；
- **当前 baseline**：`绝地邮兵_result_pre_optimize_long.json`（A 版），后续优化应围绕 raw 生成质量，而非后处理规则。

### 4.7 第二阶段结论（汇报要点）

1. **方法切换正确**：RePS 本地 proxy 从 2.660（baseline）提升至 3.210（全扫参），超越第一阶段 CAA 最优 3.044。
2. **分档扫参有效**：L3 / L1/L2 按 concept 独立调 multiplier 是主要增益来源。
3. **512 token 重生成是官方分关键**：旧版 0.2583 → A 版 **0.3817（+48%）**。
4. **后处理对官方 judge 有害**：A（无后处理）> B（official）> 旧版（full）；本地 proxy 最高的 full 后处理官方分反而最低。
5. **下一步**：以 A 版 raw RePS 为 baseline，优先调 multiplier / 768 token / 生成质量，**不再依赖后处理刷分**。

---

## 五、当前方案与关键文件

**当前 baseline**：`baseline/`（reps_raw_v1，官方分 **0.3817**）

```bash
# 复现 baseline
bash scripts/regen_from_baseline.sh 512

# Round 1：768 token 实验
bash scripts/regen_from_baseline.sh 768
```

| 文件 | 说明 |
|------|------|
| `baseline/submission.json` | 冻结 baseline v1（512 token，官方分 0.3817） |
| `baseline/multipliers.json` | 24 concept multiplier |
| `绝地邮兵_result_regen_768.json` | Round 1：768 token 实验（待提交，截断 26/120） |
| `docs/REPS_SETUP.md` | 队友复现指南 |
| `docs/OFFICIAL_SCORE_OPTIMIZATION.md` | 官方分优化方案 |
| `easyedit_reps/` | RePS 完整 pipeline |

---

## 六、已评估但未实验的方法

| 方法 | EasyEdit2 支持 | CCKS 官方配置 | 评估 |
|------|---------------|--------------|------|
| LM-Steer | ✅ | ❌ | 工程量大，无官方 qwen3-4b 配置 |
| Vector Prompt | ✅ | ❌ | 预期接近 CAA，优先级低 |
| STA / SAE Feature | ✅ | ❌ | 依赖 SAE，未排期 |

**决策**：复赛阶段以 **RePS raw 生成（512 token + 分档扫参）** 为主方案，**不再依赖后处理**。

---

## 七、工程与协作进展

| 项 | 状态 |
|----|------|
| 第一阶段 CAA 框架探索 | ✅ 已完成，结论：效果有限 |
| EasyEdit RePS 环境 + 向量训练 | ✅ |
| 分档扫参 + 后处理脚本 | ✅ |
| 512 token 重生成 + official 后处理 | ✅ |
| 协作文档 `docs/REPS_SETUP.md` | ✅ |
| Git 分支 `RePS-Structure` push | ⏳ 待 SSH / HTTPS Token |

---

## 八、后续计划

- [x] 第一阶段 CAA 探索 → 结论：转向 RePS
- [x] RePS pipeline 搭建 + 分档扫参 + full 后处理
- [x] 天池首次提交 → 官方分 **0.2583**
- [x] 512 token 重生成 + official 后处理（版本 B）
- [x] 天池提交 B → 官方分 **0.355**
- [x] 天池提交 A → 官方分 **0.3817** → 冻结为 `baseline/`（reps_raw_v1）
- [x] 768 token 重生成 → `绝地邮兵_result_regen_768.json`（截断 26/120 vs baseline 30/120）
- [ ] 天池提交 768 版，对比 baseline 0.3817

---

## 九、附录：结果文件索引

| 阶段 | 方法 | 评测文件 |
|------|------|---------|
| 第一阶段 | CAA 基线 | `runs/baseline_caa/local_eval.json` |
| 第一阶段 | BiPO | `runs/baseline_bipo/local_eval.json` |
| 第一阶段 | Conceptors | `runs/baseline_conceptor_diff/local_eval.json` |
| 第二阶段 | RePS baseline | `runs/reps_baseline/local_eval.json` |
| 第二阶段 | RePS L3 tuned | `runs/reps_l3_tuned/local_eval.json` |
| 第二阶段 | RePS 全扫参 | `runs/reps_full_tuned/local_eval.json` |
| 第二阶段 | RePS full 后处理 | `runs/reps_postprocessed/local_eval.json` |

---

*维护：CCKS2026 Steering 组*
