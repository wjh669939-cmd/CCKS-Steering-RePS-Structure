# CCKS2026 SteerEval — RePS Pipeline

> 基于 EasyEdit2 官方 **RePS** 方法的 CCKS2026 大模型行为调控（Steering）方案。  
> **当前最优**：phase_f · 天池官方分 **0.6714**（仅 L2_2 重训，多 L2 合并 0.6583 已回滚）。

**仓库**：https://github.com/wjh669939-cmd/CCKS-Steering-RePS-Structure

---

## 快速开始

```bash
cd easyedit_reps && source env.sh

# 从当前 baseline 重生成（per-concept layer + multiplier）
bash ../scripts/regen_from_baseline.sh 512
# → 绝地邮兵_result_regen_baseline_512.json

# 完整 Phase C 复现（需 GPU，~12min 扫参部分）
bash ../scripts/run_phase_c_l12_optimize.sh
```

首次搭建环境见 [`docs/reproduction/baseline_0.6714.md`](docs/reproduction/baseline_0.6714.md)（**0.6714 双版本复现：Shell + JupyterLab**）。  
复现文档目录：[`docs/reproduction/`](docs/reproduction/)。

---

## 目录结构

```text
CCKS2026-Steering/
├── 绝地邮兵_result.json      # 当前提交（0.6714）
├── train.json / valid.json    # 赛方数据
├── baseline/                  # 冻结配置（layers + mult + submission）
├── easyedit_reps/             # RePS pipeline + 向量
│   └── outputs/vectors/
│       ├── per_layer/         # ★ 当前 regen 主向量库
│       └── ccks_baseline_reps/  # layer 18 回退向量
├── scripts/                   # 活跃工具脚本
├── docs/
│   └── reproduction/          # ★ 复现指南（0.6714 / 0.3817 + Notebook）
├── runs/                      # 活跃实验日志（phase_a/c）
└── archive/                   # 历史提交、runs、向量（可删，不影响复现）
    └── submissions/           # 按阶段归档的提交 JSON
```

---

## 实验结果摘要

| 版本 | 官方分 | 说明 |
|------|--------|------|
| reps_raw_v1 | 0.3817 | 512 token · layer 18 统一 |
| best_merge | 0.4517 | L3 mult + round2 选层 |
| **phase_f（当前）** | **0.6714** | L2_2 重训向量 @ L18 m=3.5 |
| phase_c | 0.5583 | L2 mult↑ + L1 换层 |

配置：`baseline/layers.json` + `baseline/multipliers.json`

---

## 文档

- [**提交索引**](docs/SUBMISSIONS.md) — 各阶段提交文件、官方分与可否再交
- [**复现指南目录**](docs/reproduction/) — **队友首选**（0.6714 Shell + JupyterLab）
- [**实验日志**](docs/EXPERIMENT_LOG.md) — 完整实验记录（v7.0）
- [Baseline 说明](baseline/README.md)
- [归档说明](archive/README.md)

---

## 模型与数据

- **模型**：Qwen3-4B-Instruct-2507（本地路径见 `easyedit_reps/env.sh`）
- **不在 Git 中**：模型权重、`.venv`、大部分向量与 archive

---

*CCKS2026 Steering 组*
