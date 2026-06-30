# RePS Baseline — phase_f v1（当前最优 · L2_2 only）

> 天池官方分 **0.6714** | 512 token | raw 生成 | 无后处理 | 仅 L2_2 重训 merge

## 回滚说明（2026-06-28）

多 L2 合并版官方 **0.6583**，已回滚。恢复命令：

```bash
bash scripts/rollback_to_phase_f_l2_2.sh
```

## 内容

| 文件 | 说明 |
|------|------|
| `baseline_manifest.json` | 当前最优配置快照（官方分 0.6714） |
| `layers.json` | 24 concept per-concept 干预层 |
| `multipliers.json` | 24 concept multiplier（**L2_2 m=3.5**） |
| `submission.json` | 冻结提交（等同 `绝地邮兵_result.json`） |
| `archive/` | 历史 baseline（phase_c **0.5583**、best_merge **0.4517** 等） |

## 相对 Phase C（0.5583）的变更

- **L2_2**：重训 RePS 向量（train-only 选层 L18），multiplier **3.0 → 3.5**
- 仅 L2_2 的 5 条 valid 答案变化，其余 23 concept 不变
- 向量路径：`easyedit_reps/outputs/vectors/per_layer/L2_2/layer_18/`（来自 `retrain_pilot`）

## 复现当前 baseline 生成

```bash
bash scripts/regen_from_baseline.sh 512
# 输出: 绝地邮兵_result_regen_baseline_512.json
```

## 重训 L2_2 全流程

```bash
bash scripts/run_pilot_retrain_l2_2.sh
# 产出: archive/submissions/04_pilot/绝地邮兵_result_pilot_retrain_L2_2_m35.json
```

## 历史 baseline

| 版本 | 官方分 | 归档路径 |
|------|--------|----------|
| reps_raw_v1 | 0.3817 | `archive/submission_reps_raw_v1_0.3817.json` |
| best_merge | 0.4517 | `archive/submission_best_merge_0.4517.json` |
| phase_c | 0.5583 | `archive/submissions/01_milestones/绝地邮兵_result_phase_c_l12.json` |
| **phase_f（当前）** | **0.6714** | `submission.json` |

## 关键参数

- 模型：Qwen3-4B-Instruct-2507，**per-concept layer**（见 `layers.json`）
- `max_new_tokens`: **512**
- `temperature`: 0，`do_sample`: false
- 后处理：**无**
