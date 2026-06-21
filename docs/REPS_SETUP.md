# CCKS2026 RePS Pipeline — 团队协作与复现指南

> **仓库**：[Horizonyjw/CCKS2026-Steering](https://github.com/Horizonyjw/CCKS2026-Steering)  
> **分支**：`RePS-Structure`  
> **方法**：官方 EasyEdit2 RePS  
> **模型**：Qwen3-4B-Instruct-2507

---

## 1. 拉取分支

### 首次克隆

```bash
git clone https://github.com/Horizonyjw/CCKS2026-Steering.git
cd CCKS2026-Steering
git checkout RePS-Structure
git pull origin RePS-Structure
```

### 已有仓库

```bash
cd CCKS2026-Steering
git fetch origin
git checkout RePS-Structure
git pull origin RePS-Structure
```

验证：

```bash
git branch --show-current   # RePS-Structure
ls easyedit_reps/scripts/run_reps_vectors.sh
ls scripts/postprocess_submission.py
```

---

## 2. 目录结构

```text
CCKS2026-Steering/
├── train.json / valid.json
├── scripts/
│   ├── postprocess_submission.py   # L3 硬约束 + L1/L2 清理
│   ├── finalize_submission.sh      # 后处理 + 本地评测
│   ├── make_official_submission.py
│   └── local_eval.py
├── docs/REPS_SETUP.md              # 本文档
└── easyedit_reps/
    ├── README.md
    ├── env.sh
    ├── requirements-lite.txt
    ├── config/                     # Hydra 配置
    ├── scripts/                    # 向量训练、生成、扫参
    └── EasyEdit/                   # 官方源码（含 CCKS 兼容补丁）
```

**不在 Git 中（需本地生成）：**

- 模型权重 `Qwen3-4B-Instruct-2507`
- RePS 向量 `easyedit_reps/outputs/vectors/**/*.pt`
- 虚拟环境 `.venv/`、`easyedit_reps/.venv/`

---

## 3. 环境安装

### 3.1 主项目环境

```bash
cd CCKS2026-Steering
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

### 3.2 下载模型

```bash
export MODEL_PATH=/path/to/Qwen3-4B-Instruct-2507
# huggingface-cli download Qwen/Qwen3-4B-Instruct-2507 --local-dir $MODEL_PATH
```

### 3.3 RePS 轻量环境

```bash
cd easyedit_reps
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-lite.txt

# 复用主环境 torch/transformers（Python 3.12 示例，按实际版本调整）
MAIN_VENV="$(cd .. && pwd)/.venv"
PYVER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
ln -sf "$MAIN_VENV/lib/python${PYVER}/site-packages/torch" .venv/lib/python${PYVER}/site-packages/torch
ln -sf "$MAIN_VENV/lib/python${PYVER}/site-packages/transformers" .venv/lib/python${PYVER}/site-packages/transformers

cd EasyEdit && pip install -e .
```

### 3.4 加载环境变量

```bash
cd easyedit_reps && source env.sh
```

---

## 4. 配置路径（首次必改）

编辑以下文件，将 AutoDL 绝对路径改为本地模型路径：

- `easyedit_reps/config/steer_eval_reps_local.yaml`
- `easyedit_reps/config/steer_eval_reps_generate.yaml`

```yaml
model_name_or_path: /path/to/Qwen3-4B-Instruct-2507
```

扫参脚本 `sweep_l3_multipliers.py`、`sweep_l12_multipliers.py` 内也有硬编码模型路径，需同步修改。

---

## 5. 运行流程

```text
Step 1  bash easyedit_reps/scripts/run_reps_vectors.sh      # 训练 24 concept 向量
Step 2  bash easyedit_reps/scripts/run_reps_generate.sh       # valid 生成
Step 3  bash easyedit_reps/scripts/run_l3_sweep.sh            # L3 扫参（推荐）
Step 4  bash easyedit_reps/scripts/run_l12_sweep.sh           # L1/L2 扫参（推荐）
Step 5  导出 pre_optimize 提交文件
Step 6  bash scripts/finalize_submission.sh                   # 后处理 + 评测
```

### Step 5：导出

```bash
cd easyedit_reps && source env.sh
.venv/bin/python scripts/export_submission.py \
  --in outputs/generation/l12_tuned/all_generation_results_valid.json \
  --out ../submission_pre_optimize.json
```

### Step 6：后处理

```bash
cd CCKS2026-Steering
bash scripts/finalize_submission.sh submission_pre_optimize.json submission_final.json
```

L3 约束应全部 `5/5` 命中。

---

## 6. EasyEdit 补丁说明

分支内 `easyedit_reps/EasyEdit/` 已包含以下兼容修改（相对官方 [zjunlp/EasyEdit](https://github.com/zjunlp/EasyEdit)）：

| 文件 | 说明 |
|------|------|
| `steer/vector_generators/reps/utils.py` | BatchEncoding 兼容 |
| `steer/trainer/PreferenceModelTrainer.py` | 末 batch 越界修复 |
| `examples/steer_eval.py` | `method=reps` 及 concept_description fallback |

官方文档：[CCKS2026.md](https://github.com/zjunlp/EasyEdit/blob/main/examples/CCKS2026.md)

---

## 7. 本地评测参考

| 阶段 | mean_hm_proxy（本地近似） |
|------|--------------------------|
| RePS 全调参 | ~3.21 |
| 后处理版 | ~3.25 |

> 本地 proxy ≠ 天池 LLM judge 分数。

---

## 8. 常见问题

**Q: 分支不存在？**

```bash
git fetch origin && git checkout -b RePS-Structure origin/RePS-Structure
```

**Q: CUDA OOM？** 确认 `dtype: bfloat16`，且无其他进程占 GPU。

**Q: 已有向量，跳过 Step 1？** 将向量放到 `easyedit_reps/outputs/vectors/ccks_baseline_reps/`，从 Step 2 开始。

---

**维护者**：Horizonyjw  
**文档版本**：v1.0
