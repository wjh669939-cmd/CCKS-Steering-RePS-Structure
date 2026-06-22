# CCKS2026 SteerEval — RePS Pipeline

> 基于 EasyEdit2 官方 **RePS** 方法的 CCKS2026 大模型行为调控（Steering）方案。  
> **当前 baseline**：512 token raw 生成，天池官方分 **0.3817**。

**仓库**：https://github.com/wjh669939-cmd/CCKS-Steering-RePS-Structure

---

## 快速开始

```bash
git clone https://github.com/wjh669939-cmd/CCKS-Steering-RePS-Structure.git
cd CCKS-Steering-RePS-Structure

# 1. 安装环境（见 docs/REPRODUCTION_GUIDE.md 第四节）
cd easyedit_reps && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-lite.txt transformers accelerate
cd EasyEdit && pip install -e . && cd ..

# 2. 修改 config 中的 model_name_or_path 为你的模型路径

# 3. 训练向量 → 扫参 → 重生成（完整流程见复现指南）
source env.sh
bash scripts/run_reps_vectors.sh      # Step 1: 训练向量（~2h）
bash scripts/run_l3_sweep.sh          # Step 3: L3 扫参
bash scripts/run_l12_sweep.sh         # Step 4: L1/L2 扫参

# 4. 从 baseline multiplier 一键重生成（跳过扫参时使用）
bash ../scripts/regen_from_baseline.sh 512
```

---

## 目录结构

| 路径 | 说明 |
|------|------|
| `easyedit_reps/` | RePS 完整 pipeline（EasyEdit + 脚本 + 配置） |
| `baseline/` | 冻结 baseline v1（multiplier + 参考提交） |
| `scripts/` | 重生成、后处理、本地评测 |
| `train.json` / `valid.json` | 赛方数据 |
| `docs/REPRODUCTION_GUIDE.md` | **详细复现指南（推荐阅读）** |

---

## 实验结果摘要

| 版本 | 官方分 | 说明 |
|------|--------|------|
| 256 token + full 后处理 | 0.2583 | 已弃用 |
| 512 token + official 后处理 | 0.355 | 已弃用 |
| **512 token raw（baseline v1）** | **0.3817** | 当前最优 |
| 768 token raw | 待验证 | Round 1 实验 |

**关键结论**：无后处理 raw 生成 > 任何后处理；优化应直接提升生成质量。

---

## 文档

- [**复现实验完整指南**](docs/REPRODUCTION_GUIDE.md) — 环境、流程、结果、优化方向
- [实验日志](docs/EXPERIMENT_LOG.md) — 两阶段实验记录
- [官方分优化](docs/OFFICIAL_SCORE_OPTIMIZATION.md) — A/B 实验结论
- [快速上手](docs/REPS_SETUP.md)

---

## 模型与数据

- **模型**：[Qwen3-4B-Instruct-2507](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)（需自行下载）
- **数据**：`train.json`（1680 条）、`valid.json`（120 条）
- **不在 Git 中**：模型权重、RePS 向量（`.pt`）、虚拟环境

---

*CCKS2026 Steering 组*
