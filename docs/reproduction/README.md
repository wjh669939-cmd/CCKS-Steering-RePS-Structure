# 复现指南目录

> **仓库**：[wjh669939-cmd/CCKS-Steering-RePS-Structure](https://github.com/wjh669939-cmd/CCKS-Steering-RePS-Structure)

| 文档 | 官方分 | 说明 |
|------|--------|------|
| [**baseline_0.6714.md**](baseline_0.6714.md) | **0.6714** | **当前最优** · Shell 工作区版 + JupyterLab 版 |
| [**TEAMMATE_IMPROVEMENT_PLAN.md**](TEAMMATE_IMPROVEMENT_PLAN.md) | — | **队友改善方案**（分阶段复现 + 验收） |
| [TEAMMATE_FIX_GARBLED_OUTPUT.md](TEAMMATE_FIX_GARBLED_OUTPUT.md) | — | 乱码 / issue_comment 根因排查 |
| [baseline_0.3817.md](baseline_0.3817.md) | **0.3817** | 历史 baseline · layer 18 统一 · `baseline/reps_raw_v1/` |
| [notebooks/reproduce_baseline_0_6714.ipynb](notebooks/reproduce_baseline_0_6714.ipynb) | 0.6714 | JupyterLab 一键复现 Notebook |

## 快速命令

**0.6714（当前 per-concept 最优）**：

```bash
export REPS_MODEL_PATH=/你的路径/Qwen3-4B-Instruct-2507
bash scripts/regen_from_baseline.sh 512
```

**0.3817（历史 reps_raw_v1）**：

```bash
export REPS_MODEL_PATH=/你的路径/Qwen3-4B-Instruct-2507
bash scripts/regen_from_baseline_0.3817.sh 512
# 或直接用冻结提交: baseline/reps_raw_v1/submission.json
```

环境搭建速查：[../REPS_SETUP.md](../REPS_SETUP.md)
