# 复现指南目录

> **仓库**：[wjh669939-cmd/CCKS-Steering-RePS-Structure](https://github.com/wjh669939-cmd/CCKS-Steering-RePS-Structure)

| 文档 | 官方分 | 说明 |
|------|--------|------|
| [**baseline_0.6714.md**](baseline_0.6714.md) | **0.6714** | **当前最优** · Shell 工作区版 + JupyterLab 版 |
| [baseline_0.3817.md](baseline_0.3817.md) | 0.3817 | 历史 baseline（layer 18 统一） |
| [notebooks/reproduce_baseline_0_6714.ipynb](notebooks/reproduce_baseline_0_6714.ipynb) | 0.6714 | JupyterLab 一键复现 Notebook |

## 快速命令（0.6714）

```bash
export REPS_MODEL_PATH=/你的路径/Qwen3-4B-Instruct-2507
bash scripts/regen_from_baseline.sh 512
```

环境搭建速查：[../REPS_SETUP.md](../REPS_SETUP.md)
