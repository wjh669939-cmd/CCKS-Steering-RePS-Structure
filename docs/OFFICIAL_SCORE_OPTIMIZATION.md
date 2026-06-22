# 天池官方分优化方案

> **背景**：首次提交 `绝地邮兵_result.json`（RePS 全调参 + full 后处理，`max_new_tokens=256`）获天池官方分 **0.2583**。  
> **A 版反馈**：`绝地邮兵_result_pre_optimize_long.json`（512 token，无后处理）获官方分 **0.3817**（当前最优，较旧版 +48%）。  
> **B 版反馈**：`绝地邮兵_result_official.json`（512 token + official 后处理）获官方分 **0.355**。  
> **结论**：A > B，后处理对官方 judge 有害，应以 raw RePS 为 baseline。  
> **日期**：2026-06-19

---

## 一、问题诊断

### 1.1 本地 proxy 与官方分严重偏离

| 指标 | 本地 proxy | 旧版 full | B 版 official | **A 版 raw** |
|------|-----------|----------|--------------|-------------|
| mean_hm | ~3.251（full 最高） | — | — | — |
| 天池官方分 | — | 0.2583 | 0.355 | **0.3817** |

**结论**：本地 proxy 与官方分**方向可相反**（full 后处理 proxy 最高、官方分最低）。优化应直接提升 raw 生成质量，而非后处理规则。

### 1.2 已识别的主要扣分项

| 问题 | 规模 | 影响 |
|------|------|------|
| **句末截断** | 旧版 36/120；512 token 重生成后 30/120；official 后处理 **0/120** | 流畅度、完整性大幅扣分 |
| **L1/L2 助手腔** | 大量「I'm an AI…」「However, I can help…」 | 人格对齐分低 |
| **full 后处理过度** | 字面插入 hint、定向改写 | 可能破坏自然度，官方 judge 更敏感 |
| **L3 字面约束** | 部分 concept 未稳定命中 | concept 对齐分低 |

---

## 二、优化策略总览

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: 提高生成长度上限                                    │
│          max_new_tokens: 256 → 512                          │
├─────────────────────────────────────────────────────────────┤
│  Step 2: 用已扫参最优 multiplier 重跑 24 concept valid 生成   │
│          scripts/regen_tuned_all.py                         │
├─────────────────────────────────────────────────────────────┤
│  Step 3: A/B 两版提交                                        │
│    A) 纯 RePS 输出（无后处理）                                │
│    B) official 轻量后处理（免责 + L3 + 截断修复）              │
├─────────────────────────────────────────────────────────────┤
│  Step 4: 天池 A/B 对比，选官方分更高的一版继续迭代              │
└─────────────────────────────────────────────────────────────┘
```

**核心原则**：宁可保留模型自然输出，也不要 aggressive 的字面插入；L3 硬约束仍保留（赛题有明确字面要求）。

---

## 三、具体改动

### 3.1 生成长度：`max_new_tokens` 256 → 512

**文件**：
- `easyedit_reps/config/steer_eval_reps_local.yaml`
- `easyedit_reps/scripts/regen_tuned_all.py`（默认 512，可 `--max-new-tokens` 覆盖）

**原因**：256 token 下约 30% 样本句末不完整（无 `.!?` 等结束符），LLM judge 对「话说一半」惩罚很重。本轮 512 token 重生成将截断从 **36/120 降至 30/120**；配合 `official` 后处理的句末修复可达 **0/120**。

### 3.2 重生成脚本：`regen_tuned_all.py`

读取已扫参结果：
- `outputs/generation/l3_tuned/best_l3_multipliers.json`
- `outputs/generation/l12_tuned/best_l12_multipliers.json`

对每个 concept 用各自最优 multiplier、512 token 重生成 valid 集，输出：
- 原始：`easyedit_reps/outputs/generation/regen_long/all_generation_results_valid.json`
- 提交 A 底稿：`绝地邮兵_result_pre_optimize_long.json`

```bash
cd easyedit_reps
source env.sh
.venv/bin/python scripts/regen_tuned_all.py
# 可选：.venv/bin/python scripts/regen_tuned_all.py --max-new-tokens 768
```

### 3.3 后处理三档模式：`postprocess_submission.py --mode`

| 模式 | 行为 | 用途 |
|------|------|------|
| `minimal` | 仅 `fix_incomplete_sentence` | 兜底截断修复 |
| **`official`** | 免责清理 + L3 硬约束 + 截断修复；**不做** hint 插入 / L12 定向改写 | **推荐提交 B** |
| `full` | 旧版全部逻辑（hint、改写、L3） | 本地 proxy 刷分，**不推荐上天池** |

新增 `fix_incomplete_sentence()`：
- 若句末无结束标点，在 `min_keep` 字符后找最后一个完整句号截断
- 去掉末尾不完整的 markdown 列表项 / bullet

### 3.4 一键导出 A/B：`finalize_official_submission.sh`

```bash
# 需先完成 regen_tuned_all.py
bash scripts/finalize_official_submission.sh
```

产出：
| 文件 | 说明 |
|------|------|
| `绝地邮兵_result_pre_optimize_long.json` | **版本 A**：纯 RePS，无后处理 |
| `绝地邮兵_result_official.json` | **版本 B**：official 轻量后处理 |

脚本会打印两版的 **截断样本数**（>200 字且无句末标点）。

---

## 四、提交结果（A/B 实验）

| 版本 | 文件 | 官方分 | 状态 |
|------|------|--------|------|
| 旧版 | `绝地邮兵_result.json` | 0.2583 | ✅ |
| B 版 | `绝地邮兵_result_official.json` | 0.355 | ✅ |
| **A 版** | `绝地邮兵_result_pre_optimize_long.json` | **0.3817** | ✅ **当前最优** |

**A/B 结论**：

| 对比 | 结果 |
|------|------|
| A vs 旧版 | +0.123（**+48%**）— 512 token + 去掉后处理 |
| A vs B | +0.027（**+7.5%**）— 后处理仍损害自然度 |
| B vs 旧版 | +0.097（+37%）— 512 token 本身有效，但不如 raw |

**核心结论**：

1. **512 token 重生成**是官方分提升的主因（0.2583 → 0.35+）；
2. **任何后处理均不推荐**：A（无）> B（official）> 旧版（full）；
3. **本地 proxy 与官方分方向相反**：proxy 最高的 full 后处理官方分最低；
4. **当前 baseline**：直接提交 `绝地邮兵_result_pre_optimize_long.json`。

**后续优化方向**（不再走后处理）：

- `max_new_tokens=768` 进一步减少截断（A 版仍有 30/120 疑似截断）
- L1/L2 薄弱 concept multiplier 重扫（以官方反馈为导向）
- 生成侧改进（temperature、多候选 rerank 等）

---

## 五、后续可选方向

| 方向 | 说明 | 优先级 |
|------|------|--------|
| `max_new_tokens=768` | 若 512 仍有截断 | 中 |
| L1/L2 multiplier 重扫 | 以官方反馈为导向，非 local proxy | 中 |
| system prompt 微调 | RePS 生成时不加 concept 名，可试空/极短 system | 低 |
| LM-Steer / Vector Prompt | EasyEdit2 支持但无 CCKS qwen3-4b 官方配置 | 低 |
| 多候选 + rerank | 每题生成 3 条，用本地启发式选最「人格化」 | 低（耗 GPU） |

---

## 六、文件索引

| 路径 | 作用 |
|------|------|
| `easyedit_reps/scripts/regen_tuned_all.py` | 512 token 全 concept 重生成 |
| `scripts/postprocess_submission.py` | 后处理（`--mode official/full/minimal`） |
| `scripts/finalize_official_submission.sh` | A/B 提交文件一键导出 |
| `scripts/finalize_submission.sh` | 旧版 full 后处理（proxy 最优，非官方优化） |
| `docs/EXPERIMENT_LOG.md` | 全方法实验日志 |
| `docs/REPS_SETUP.md` | 队友复现 RePS pipeline |

---

## 七、三版提交对比

| 项目 | 旧版 | B 版 | **A 版（最优）** |
|------|------|------|----------------|
| max_new_tokens | 256 | 512 | 512 |
| 后处理 | full | official | **无** |
| 截断（>200字无句末标点） | 36/120 | 0/120 | 30/120 |
| 天池官方分 | 0.2583 | 0.355 | **0.3817** |

---

## 八、复现命令速查

```bash
# 1. 重生成（GPU，约 30–60 min）
cd easyedit_reps && source env.sh
.venv/bin/python scripts/regen_tuned_all.py

# 2. 导出 A/B
cd ..
bash scripts/finalize_official_submission.sh

# 3. 单独跑 official 后处理
python scripts/postprocess_submission.py \
  --in 绝地邮兵_result_pre_optimize_long.json \
  --out 绝地邮兵_result_official.json \
  --mode official

# 4. 检查截断（脚本内置 audit）
python scripts/postprocess_submission.py \
  --in 绝地邮兵_result_pre_optimize_long.json \
  --out /tmp/check.json \
  --mode minimal
```
