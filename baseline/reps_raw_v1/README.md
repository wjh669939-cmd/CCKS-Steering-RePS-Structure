# RePS Raw v1 — 官方分 0.3817

> **方法**：EasyEdit2 RePS · 全 concept **layer 18** · 分档 multiplier 扫参 · **512 token raw** · 无后处理  
> **天池官方分**：**0.3817**（2026-06-22 冻结）  
> **复现指南**：[`docs/reproduction/baseline_0.3817.md`](../../docs/reproduction/baseline_0.3817.md)

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `baseline_manifest.json` | 配置快照（layer、generation、向量路径） |
| `multipliers.json` | 24 concept 最优 multiplier（L3 + L1/L2 扫参合并） |
| `layers.json` | 全部为 **18**（与 0.6714 per-concept 层不同） |
| `submission.json` | 冻结提交 JSON（120 条，可直接交天池对照） |

---

## 最快复现（已有向量）

```bash
export REPS_MODEL_PATH=/path/to/Qwen3-4B-Instruct-2507
bash scripts/regen_from_baseline_0.3817.sh 512
# → 绝地邮兵_result_regen_baseline_0.3817_512.json
```

向量目录默认：`easyedit_reps/outputs/vectors/ccks_baseline_reps/`

---

## 从零完整流程

```bash
export REPS_MODEL_PATH=/path/to/Qwen3-4B-Instruct-2507
bash scripts/run_baseline_0_3817.sh all    # Step1 训向量 + L3/L12 扫参 + 重生成
# 或分步：
bash scripts/run_baseline_0_3817.sh step1  # 训练 24 concept 向量
bash scripts/run_baseline_0_3817.sh step3  # L3 multiplier 扫参
bash scripts/run_baseline_0_3817.sh step4  # L1/L2 multiplier 扫参
bash scripts/run_baseline_0_3817.sh step5  # 用本目录 multipliers 重生成
```

---

## 与 0.6714 baseline 的区别

| 项 | 0.3817 (reps_raw_v1) | 0.6714 (phase_f) |
|----|----------------------|------------------|
| 干预层 | 统一 L18 | per-concept（见 `baseline/layers.json`） |
| multiplier | 本目录 `multipliers.json` | `baseline/multipliers.json` |
| 重生成脚本 | `regen_from_baseline_0.3817.sh` | `regen_from_baseline.sh` |
| 向量目录 | `ccks_baseline_reps/` | `per_layer/` + L2_2 重训 |

**勿混用**两套 multipliers / 向量 / 脚本。
