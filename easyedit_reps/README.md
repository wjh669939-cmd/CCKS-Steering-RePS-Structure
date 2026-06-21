# EasyEdit2 RePS（CCKS2026 官方 baseline）

本目录集中存放 **RePS 官方 pipeline** 所需的代码、环境、配置与脚本，与自研 CAA 流程（项目根目录）隔离。

**详细协作文档**：[`../docs/REPS_SETUP.md`](../docs/REPS_SETUP.md)

## 目录结构

```text
easyedit_reps/
├── .venv/              # 独立虚拟环境（不提交 Git）
├── EasyEdit/           # 官方 EasyEdit2 源码（含 CCKS 补丁）
├── config/             # 本地 Hydra 配置
├── scripts/            # 一键运行脚本
├── outputs/            # 向量与生成结果（不提交 Git）
├── env.sh
└── README.md
```

## 快速开始

```bash
cd easyedit_reps
source env.sh

# 第一步：训练 24 个 concept 的 RePS 向量
bash scripts/run_reps_vectors.sh

# 第二步：在 valid 上生成
bash scripts/run_reps_generate.sh

# 可选：L3 / L1-L2 multiplier 扫参
bash scripts/run_l3_sweep.sh
bash scripts/run_l12_sweep.sh

# 导出 + 后处理（在项目根目录）
.venv/bin/python scripts/export_submission.py \
  --in outputs/generation/l12_tuned/all_generation_results_valid.json \
  --out ../submission_pre_optimize.json

cd .. && bash scripts/finalize_submission.sh submission_pre_optimize.json submission_final.json
```

## 配置说明

| 项 | 值 |
|----|-----|
| 模型 | `Qwen/Qwen3-4B-Instruct-2507`（路径见 yaml，首次需修改） |
| 方法 | RePS, layer=18 |
| 数据 | `../train.json`, `../valid.json` |
| 官方文档 | [CCKS2026.md](https://github.com/zjunlp/EasyEdit/blob/main/examples/CCKS2026.md) |

## 环境说明

`.venv` 复用上级 `.venv` 中的 PyTorch/Transformers，额外安装 `hydra-core` 等轻量依赖。使用前：

```bash
source env.sh
```
