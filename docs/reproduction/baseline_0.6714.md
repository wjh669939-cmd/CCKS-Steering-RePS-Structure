# CCKS2026 Baseline 0.6714 复现指南

> **仓库**：[wjh669939-cmd/CCKS-Steering-RePS-Structure](https://github.com/wjh669939-cmd/CCKS-Steering-RePS-Structure)  
> **分支**：`main`（或 `RePS-Structure`）  
> **当前最优**：Phase F · **L2_2 only** · 天池官方分 **0.6714**  
> **文档版本**：v2.0 · **更新**：2026-06-30

---

## 0. 你要复现什么？

| 目标 | 需要 GPU | 耗时 | 见章节 |
|------|----------|------|--------|
| **A. 拿到官方 0.6714 提交 JSON** | 否 | 1 分钟 | §1 |
| **B. 用冻结配置重生成（验证 pipeline）** | 是 | ~1–2 h | §2–§5（工作区）/ §6（JupyterLab） |
| **C. 从向量训练完整重跑（不推荐）** | 是 | 数天 | §7 |

**推荐路径**：队友先完成 **A**，确认文件无误；有 GPU 再做 **B** 对比 `baseline/submission.json`。

---

## 1. 最快：直接使用冻结提交（无需 GPU）

仓库已包含与天池 0.6714 一致的提交：

```text
baseline/submission.json     # 与根目录 绝地邮兵_result.json 内容一致（若已同步）
```

验证结构：

```bash
python3 -c "
import json
p='baseline/submission.json'
d=json.load(open(p,encoding='utf-8'))
n=sum(len(b['generated_results']) for b in d)
print('concepts', len(d), 'samples', n)
assert len(d)==24 and n==120
print('OK')
"
```

直接交竞赛或本地分析用该文件即可。**这不等于验证了生成 pipeline**，但答案与官方最优一致。

---

## 2. 当前 Baseline 配置一览

| 项 | 值 |
|----|-----|
| 方法 | EasyEdit2 [RePS](https://arxiv.org/html/2505.20809v1) |
| 模型 | `Qwen/Qwen3-4B-Instruct-2507` |
| `max_new_tokens` | **512** |
| `temperature` | **0**（greedy） |
| 后处理 | **无**（raw 生成） |
| 干预层 | **per-concept**（`baseline/layers.json`） |
| multiplier | **per-concept**（`baseline/multipliers.json`） |
| 唯一重训向量 | **L2_2** @ layer **18**，m=**3.5** |
| 向量主目录 | `easyedit_reps/outputs/vectors/per_layer/` |
| layer 18 回退 | `easyedit_reps/outputs/vectors/ccks_baseline_reps/` |

完整快照：`baseline/baseline_manifest.json`

### 2.1 相对 Phase C（0.5583）改了什么

- **仅 L2_2**：重训 RePS 向量（train-only 选 L18），multiplier 3.0→**3.5**
- valid 上 **只有 L2_2 的 5 题**与 phase_c 不同，其余 23×5=115 题不变
- 多 L2 合并（0.6583）、L2_5 only（0.5006）等均已证伪并回滚

回滚命令（若本地配置被改乱）：

```bash
bash scripts/rollback_to_phase_f_l2_2.sh
```

---

## 3. 硬件、软件与环境

| 项目 | 最低 | 推荐（与当前工作区一致） |
|------|------|-------------------------|
| GPU | 16GB VRAM（bf16） | RTX 4090 / 5090 24GB+ |
| 磁盘 | 25GB 可用 | 模型 ~8GB + 向量 ~100MB + 环境 ~3GB |
| Python | 3.10–3.12 | **3.12** |
| CUDA | 与 PyTorch 匹配 | CUDA 12.x |

### 3.1 克隆仓库

```bash
git clone https://github.com/wjh669939-cmd/CCKS-Steering-RePS-Structure.git
cd CCKS-Steering-RePS-Structure
# 若在 RePS-Structure 分支：
# git checkout RePS-Structure
```

### 3.2 安装 PyTorch + 依赖

```bash
# 按你的 CUDA 版本选择，示例（CUDA 12.8）：
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
pip install "transformers>=4.51.0" accelerate

cd easyedit_reps
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -U pip
pip install -r requirements-lite.txt
pip install "transformers>=4.51.0" accelerate
cd EasyEdit && pip install -e . && cd ..
```

验证：

```bash
python -c "import torch, transformers; print(torch.__version__, torch.cuda.is_available())"
```

### 3.3 下载模型

```bash
export REPS_MODEL_PATH=/你的路径/Qwen3-4B-Instruct-2507
huggingface-cli download Qwen/Qwen3-4B-Instruct-2507 --local-dir "$REPS_MODEL_PATH"
```

> 生成脚本通过环境变量 **`REPS_MODEL_PATH`** 读取模型路径（默认 `/root/autodl-tmp/models/Qwen3-4B-Instruct-2507`，与 AutoDL 工作区一致）。

### 3.4 获取 RePS 向量（Git 中不含）

向量约 **97MB**，不在 Git 仓库。三选一：

**方式 1（推荐）**：向队友索取打包文件

```bash
# 队友在 AutoDL 打包：
cd easyedit_reps/outputs
tar czf ~/vectors_0.6714.tar.gz vectors/per_layer vectors/ccks_baseline_reps

# 你解压到项目内：
mkdir -p easyedit_reps/outputs
tar xzf vectors_0.6714.tar.gz -C easyedit_reps/outputs/
```

**方式 2**：网盘 / 内网文件站（由队长上传 `vectors_0.6714.tar.gz`）

**方式 3**：自行训练（见 §7，耗时长，且 L2_2 重训需单独跑 pilot）

**必须存在的路径示例**：

```text
easyedit_reps/outputs/vectors/per_layer/L2_2/layer_18/steer_eval_concept_L2_2/reps_vector/layer_18.pt
easyedit_reps/outputs/vectors/ccks_baseline_reps/steer_eval_concept_L1_1/reps_vector/layer_18.pt
```

---

# 版本 A：工作区 Shell 完全复现（与 AutoDL 一致）

适用于：**Linux 服务器 / AutoDL / SSH 终端**，与当前队长工作区流程一致。

## A.1 环境变量（每次开终端执行）

```bash
cd /path/to/CCKS-Steering-RePS-Structure   # 改成你的项目根目录
export PROJECT_ROOT="$PWD"
export REPS_MODEL_PATH=/你的路径/Qwen3-4B-Instruct-2507

cd easyedit_reps
source env.sh
```

`env.sh` 会设置：

- `EASYEDIT_REPS_ROOT`、`EASYEDIT_ROOT`
- `PYTHONPATH`（venv + EasyEdit + 可选 conda site-packages）

**若 torch 不在 conda 默认路径**，指定：

```bash
export CONDA_SITE=/你的/python/site-packages
source env.sh
```

## A.2 检查清单（生成前必过）

```bash
cd "$PROJECT_ROOT"

# 1) 配置存在
test -f baseline/layers.json && test -f baseline/multipliers.json && echo "config OK"

# 2) 模型存在
test -d "$REPS_MODEL_PATH" && echo "model OK"

# 3) L2_2 重训向量存在
test -f easyedit_reps/outputs/vectors/per_layer/L2_2/layer_18/steer_eval_concept_L2_2/reps_vector/layer_18.pt \
  && echo "L2_2 vector OK"

# 4) GPU
python -c "import torch; assert torch.cuda.is_available(); print('cuda OK')"
```

## A.3 一键重生成（核心命令）

```bash
cd "$PROJECT_ROOT"
bash scripts/regen_from_baseline.sh 512
```

输出：`绝地邮兵_result_regen_baseline_512.json`

内部调用 `regen_mixed_layers.py`：

- 读取 `baseline/layers.json` + `baseline/multipliers.json`
- 每 concept 从 `per_layer/{concept}/layer_{L}/` 或 `ccks_baseline_reps/` 加载向量
- 24 concept × 5 valid 题，约 **1–2 小时**（逐 concept 加载模型）

自定义 tag：

```bash
bash scripts/regen_from_baseline.sh 512 my_run
# → 绝地邮兵_result_regen_my_run.json
```

## A.4 与冻结 baseline 对比

```bash
# 结构 + 条数
python3 scripts/compare_submissions.py \
  --a baseline/submission.json \
  --b 绝地邮兵_result_regen_baseline_512.json

# 本地 proxy 审计（≠ 官方分，仅调试）
python3 scripts/audit_official_proxy.py \
  --submission 绝地邮兵_result_regen_baseline_512.json \
  --label regen_check \
  --out runs/regen_check_audit.json

# L3 keyword 命中
python3 scripts/audit_l3_keywords.py \
  --submission 绝地邮兵_result_regen_baseline_512.json
```

**验收标准（工作区经验）**：

- 与 `baseline/submission.json` 比较：**L2_2 的 5 题应一致或极接近**；其余 concept 应完全一致（若向量与配置未变）
- 若 120 题全部 md5 一致 → pipeline 复现成功

```bash
# 严格逐字对比（可选）
python3 -c "
import json
a=json.load(open('baseline/submission.json',encoding='utf-8'))
b=json.load(open('绝地邮兵_result_regen_baseline_512.json',encoding='utf-8'))
diff=0
for ba,bb in zip(a,b):
    for ga,gb in zip(ba['generated_results'],bb['generated_results']):
        if ga['pred']!=gb['pred']: diff+=1
print('diff samples', diff, '/ 120')
"
```

## A.5 目录与工作区对齐说明

当前活跃工作区（`bash scripts/workspace_cleanup.sh` 后）：

```text
项目根/
├── 绝地邮兵_result.json          # 主提交（0.6714）
├── train.json / valid.json
├── baseline/
│   ├── layers.json
│   ├── multipliers.json
│   ├── submission.json
│   ├── concept_lock.json
│   └── baseline_manifest.json
├── easyedit_reps/
│   ├── env.sh
│   ├── .venv/
│   └── outputs/vectors/
│       ├── per_layer/              # ★ 主向量库
│       └── ccks_baseline_reps/     # L18 回退
├── scripts/regen_from_baseline.sh
└── archive/                        # 历史实验（可不要）
```

## A.6 常见问题（Shell 版）

| 问题 | 处理 |
|------|------|
| `CUDA OOM` | 关闭其他 GPU 进程；确认 `dtype=bfloat16`；24 concept 会反复加载模型属正常 |
| `ModuleNotFoundError: accelerate` | `pip install accelerate` |
| `env.sh` 后找不到 torch | 设置 `CONDA_SITE` 或把 torch 装进 `easyedit_reps/.venv` |
| 向量路径报错 | 检查 §3.4 向量是否解压完整 |
| 生成结果与 baseline 差很多 | 确认 `multipliers.json` 中 **L2_2=3.5**；向量是否为 retrain 版 |
| 想恢复官方最优配置 | `bash scripts/rollback_to_phase_f_l2_2.sh` |

---

# 版本 B：JupyterLab 兼容复现

适用于：**队友在 JupyterLab / Notebook 里交互调试**，不依赖长期 SSH 会话。

## B.1 Jupyter 内核选择

1. 先按 §3.2 创建 `easyedit_reps/.venv`
2. 注册内核：

```bash
cd easyedit_reps
source .venv/bin/activate
pip install ipykernel
python -m ipykernel install --user --name ccks-reps --display-name "CCKS RePS (0.6714)"
```

3. JupyterLab 中新建 Notebook → 内核选 **「CCKS RePS (0.6714)」**

> 若 Jupyter 用系统 Python 而非 venv，后续 `import torch` 会失败。**务必选对内核**。

## B.2 Notebook 路径约定

建议目录：

```text
项目根/docs/reproduction/notebooks/reproduce_baseline_0_6714.ipynb
```

**每个代码单元格开头**建议固定项目根（避免 `cwd` 漂移）：

```python
from pathlib import Path

# 改成你的克隆路径
PROJECT_ROOT = Path("/path/to/CCKS-Steering-RePS-Structure").resolve()
assert (PROJECT_ROOT / "baseline" / "submission.json").exists(), "PROJECT_ROOT 不对"

import os
os.chdir(PROJECT_ROOT / "easyedit_reps")
os.environ["PROJECT_ROOT"] = str(PROJECT_ROOT)
os.environ["REPS_MODEL_PATH"] = "/你的路径/Qwen3-4B-Instruct-2507"
```

## B.3 在 Notebook 里等价于 `source env.sh`

```python
import os
import sys
from pathlib import Path

EE = PROJECT_ROOT / "easyedit_reps"
ED = EE / "EasyEdit"
VENV_SITE = EE / ".venv" / f"lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages"

# 可选：若 torch 在 conda
CONDA_SITE = os.environ.get("CONDA_SITE", "")
extra = [str(VENV_SITE), str(ED)]
if CONDA_SITE:
    extra.append(CONDA_SITE)

for p in extra:
    if Path(p).exists() and p not in sys.path:
        sys.path.insert(0, p)

os.environ["EASYEDIT_REPS_ROOT"] = str(EE)
os.environ["EASYEDIT_ROOT"] = str(ED)
os.chdir(EE)

import torch
import transformers
print("torch", torch.__version__, "cuda", torch.cuda.is_available())
print("cwd", os.getcwd())
```

## B.4 检查向量与配置（Notebook 单元格）

```python
import json
from pathlib import Path

layers = json.loads((PROJECT_ROOT / "baseline/layers.json").read_text())
mult = json.loads((PROJECT_ROOT / "baseline/multipliers.json").read_text())
print("L2_2 layer", layers["concepts"]["L2_2"]["layer"], "mult", mult["L2_2"])

v = PROJECT_ROOT / "easyedit_reps/outputs/vectors/per_layer/L2_2/layer_18/steer_eval_concept_L2_2/reps_vector/layer_18.pt"
assert v.exists(), f"缺少向量: {v}"
print("L2_2 vector OK", v.stat().st_size // 1024, "KB")
```

## B.5 重生成（Notebook 单元格，等价于 Shell 一键脚本）

**方式 1：调用仓库脚本（推荐）**

```python
import subprocess

cmd = [
    "bash", str(PROJECT_ROOT / "scripts/regen_from_baseline.sh"), "512", "jupyter_run"
]
# 继承当前环境变量 REPS_MODEL_PATH
env = os.environ.copy()
proc = subprocess.run(cmd, cwd=str(PROJECT_ROOT), env=env, capture_output=True, text=True)
print(proc.stdout)
if proc.returncode:
    print(proc.stderr)
    raise RuntimeError("regen failed")

out = PROJECT_ROOT / "绝地邮兵_result_regen_jupyter_run.json"
print("written", out, "size", out.stat().st_size)
```

**方式 2：纯 Python 调用（便于单 concept 调试）**

```python
import sys
sys.path.insert(0, str(EE / "scripts"))

from pathlib import Path
from regen_mixed_layers import load_layer_map, vector_root_for, load_multipliers
from regen_tuned_all import generate_concept, to_submission_block, train_meta, ALL_CONCEPTS
from steer.datasets.dataset_loader import DatasetLoader

layers = load_layer_map(PROJECT_ROOT / "baseline/layers.json")
mults = load_multipliers(PROJECT_ROOT / "baseline/multipliers.json")
meta = train_meta(PROJECT_ROOT / "train.json")
loader = DatasetLoader(config_path=str(ED / "hparams/Steer/dataset_format.yaml"))
eval_data = loader.load_file("SteerEval/personality", "valid")

# 先只跑 L2_2 试通（约 5–10 分钟）
cid = "L2_2"
layer = layers[cid]
vroot = vector_root_for(cid, layer, EE / "outputs/vectors/per_layer")
gen = generate_concept(cid, mults[cid], 512, "jupyter_test", eval_data[cid], layer=layer, vector_root=vroot)
block = to_submission_block(cid, gen, meta)
print(block["generated_results"][0]["pred"][0][:200])
```

全量 24 concept 在 Notebook 中跑完约 1–2h，**建议用 `nohup` / `screen` 或在 Shell 里跑方式 1**，Notebook 仅用于单 concept 调试。

## B.6 Notebook 里对比 baseline

```python
import json

ref = json.load(open(PROJECT_ROOT / "baseline/submission.json", encoding="utf-8"))
new = json.load(open(PROJECT_ROOT / "绝地邮兵_result_regen_jupyter_run.json", encoding="utf-8"))

for br, bn in zip(ref, new):
    cid = br["concept_id"]
    for gr, gn in zip(br["generated_results"], bn["generated_results"]):
        if gr["pred"] != gn["pred"]:
            print("DIFF", cid, gr["input"][:60])
```

## B.7 JupyterLab 特有问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `import torch` 失败 | 内核不是 venv | 换 §B.1 注册的内核 |
| `cwd` 跑到 `notebooks/` | Jupyter 默认目录 | 每格设置 `PROJECT_ROOT` 并 `chdir` 到 `easyedit_reps` |
| 长时间生成断连 | SSH/Jupyter 超时 | 用 `subprocess` 调 shell 脚本 + `screen`；或只跑单 concept |
| 重复加载模型很慢 | 设计如此 | 正常；不要在中途重启 kernel |
| `%pip install` 装错环境 | 装到错误 Python | 先 `import sys; print(sys.executable)` 确认是 `.venv` |

## B.8 配套 Notebook

仓库提供：`docs/reproduction/notebooks/reproduce_baseline_0_6714.ipynb`（与本文 §B.3–B.6 单元格一致，可逐格运行）。

---

## 7. 附录：从训练完整复现（仅作参考，不推荐队友首跑）

若既无向量包、又要自己训，需按历史阶段顺序执行（详见 `docs/EXPERIMENT_LOG.md`）：

```text
1. bash easyedit_reps/scripts/run_reps_vectors.sh          # 基础向量 ~2–3h
2. weak8 选层 + phase_c 扫参                                # 官方 0.5583 路径
3. bash scripts/run_pilot_retrain_l2_2.sh                  # 仅 L2_2 重训 → 0.6714
4. bash scripts/regen_from_baseline.sh 512
```

**警告**：

- 完整重跑**不保证**复现 0.6714（L2_2 重训有随机性 / 选层细节）
- 官方已证伪：多 L2 merge、L2_5/L1_7 等单 patch
- 队友首跑请用 §3.4 向量包 + §A.3 重生成

---

## 8. 参考文档

| 文档 | 内容 |
|------|------|
| [EXPERIMENT_LOG.md](../EXPERIMENT_LOG.md) | 全阶段实验记录 v7.0 |
| [STEER_IDEAS.md](../STEER_IDEAS.md) | 后续优化方向（含论文链接） |
| [CONCEPT_LOCK.md](../CONCEPT_LOCK.md) | 哪些 concept 禁止 patch |
| [baseline/README.md](../../baseline/README.md) | 0.6714 配置说明 |
| [REPS_SETUP.md](../REPS_SETUP.md) | 环境快速上手 |
| [SUBMISSIONS.md](../SUBMISSIONS.md) | 历史提交与官方分索引 |

---

*维护：CCKS2026 Steering 组 · baseline 0.6714*
