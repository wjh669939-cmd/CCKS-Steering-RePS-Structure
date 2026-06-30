# CCKS2026 RePS 实验复现指南（历史 · baseline 0.3817）

> ⚠️ **当前最优 baseline 为 0.6714**，请优先阅读：  
> **[`baseline_0.6714.md`](baseline_0.6714.md)**（含 Shell 工作区版 + JupyterLab 版）

---

# CCKS2026 RePS 实验复现指南（0.3817 历史版）

> **仓库**：[wjh669939-cmd/CCKS-Steering-RePS-Structure](https://github.com/wjh669939-cmd/CCKS-Steering-RePS-Structure)  
> **方法**：EasyEdit2 官方 RePS（Representation Engineering Steering）  
> **模型**：Qwen3-4B-Instruct-2507 | **干预层**：layer 18  
> **文档版本**：v1.0 | **更新**：2026-06-22

---

## 一、赛题与方案概述

### 1.1 任务目标

在 **不在 prompt 中显式写入 concept** 的前提下，通过模型内部干预（Steering）使生成结果对齐目标人格/行为概念。

- **训练集** `train.json`：1680 条（24 concept × 70 条）
- **验证集** `valid.json`：120 条（24 concept × 5 条）
- **Concept 层级**：L1（基础人格）、L2（行为倾向）、L3（字面/风格约束）

### 1.2 方法选型

| 阶段 | 方法 | 天池官方分 | 结论 |
|------|------|-----------|------|
| 探索期 | 自研 CAA 框架 | 0（格式未对齐） | 效果有限，已弃用 |
| **当前方案** | **EasyEdit2 RePS + 分档扫参 + raw 生成** | **0.3817** | 当前 baseline |

**核心结论**（经天池 A/B 验证）：

- **512 token raw 生成** 优于 256 token + 后处理（0.3817 vs 0.2583）
- **无后处理** 优于 official 轻量后处理（0.3817 vs 0.355）
- 本地 `local_eval.py` proxy 分数 **不能** 预测天池 LLM judge 分数

---

## 二、仓库目录结构

```text
CCKS-Steering-RePS-Structure/
├── train.json / valid.json              # 赛方数据（需自行下载或随仓库提供）
├── baseline/                            # 冻结 baseline v1（官方分 0.3817）
│   ├── baseline_manifest.json           # 配置快照
│   ├── multipliers.json                 # 24 concept 最优 multiplier
│   ├── submission.json                  # 参考提交（512 token raw）
│   └── README.md
├── scripts/
│   ├── regen_from_baseline.sh           # ★ 从 baseline 一键重生成
│   ├── postprocess_submission.py        # 后处理（默认不建议用于天池提交）
│   ├── finalize_submission.sh
│   ├── finalize_official_submission.sh
│   ├── local_eval.py                    # 本地 proxy 评测（仅供参考）
│   └── make_official_submission.py
├── ccks_steering/
│   ├── config.py                        # JSON 读写（后处理脚本依赖）
│   └── data.py
├── docs/
│   └── reproduction/                    # 复现指南（0.6714 / 0.3817 + Notebook）
│   ├── EXPERIMENT_LOG.md                # 完整实验日志
│   ├── OFFICIAL_SCORE_OPTIMIZATION.md   # 官方分优化记录
│   └── REPS_SETUP.md                    # 快速上手指南
└── easyedit_reps/
    ├── env.sh                           # 环境变量（含 torch 路径）
    ├── requirements-lite.txt
    ├── config/                          # Hydra 配置
    ├── scripts/                         # 向量训练、生成、扫参、重生成
    └── EasyEdit/                        # 官方源码 + CCKS 兼容补丁
```

**不在 Git 中（需本地生成/下载）**：

| 内容 | 路径 | 说明 |
|------|------|------|
| 模型权重 | 任意本地路径 | Qwen3-4B-Instruct-2507，约 8GB |
| RePS 向量 | `easyedit_reps/outputs/vectors/` | Step 1 训练产出，约 24×layer |
| 虚拟环境 | `.venv/`、`easyedit_reps/.venv/` | 本地安装 |
| 生成中间结果 | `easyedit_reps/outputs/generation/` | 扫参/重生成产出 |

---

## 三、硬件与环境要求

| 项目 | 最低要求 | 推荐 |
|------|---------|------|
| GPU | 16GB VRAM（bf16） | RTX 4090 / 5090 24GB+ |
| 磁盘 | 20GB 可用 | 模型 8GB + 环境 2GB + 向量/输出 1GB |
| Python | 3.10 – 3.12 | 3.12 |
| CUDA | 与 PyTorch 匹配 | CUDA 12.x |

---

## 四、环境安装（逐步）

### 4.1 克隆仓库

```bash
git clone https://github.com/wjh669939-cmd/CCKS-Steering-RePS-Structure.git
cd CCKS-Steering-RePS-Structure
```

### 4.2 安装 PyTorch（含 CUDA）

推荐使用 conda 或 pip 安装与 GPU 匹配的 PyTorch。**示例**（按你的 CUDA 版本调整）：

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
pip install "transformers>=4.51.0" accelerate
```

验证：

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

### 4.3 下载模型

```bash
export MODEL_PATH=/path/to/Qwen3-4B-Instruct-2507
huggingface-cli download Qwen/Qwen3-4B-Instruct-2507 --local-dir "$MODEL_PATH"
```

### 4.4 创建 RePS 轻量环境

```bash
cd easyedit_reps
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements-lite.txt
pip install "transformers>=4.51.0" accelerate
cd EasyEdit && pip install -e . && cd ..
```

### 4.5 配置 torch 路径（`env.sh`）

`easyedit_reps/env.sh` 默认从 miniconda 加载 torch。若 torch 安装在其他位置，设置环境变量：

```bash
# 示例：torch 在 conda 环境中
export CONDA_SITE=/path/to/your/env/lib/python3.12/site-packages
```

然后：

```bash
cd easyedit_reps && source env.sh
python -c "import torch, transformers; print('OK', torch.__version__)"
```

---

## 五、配置路径（首次必改）

以下文件中的模型路径需改为你的 `MODEL_PATH`：

| 文件 | 字段 |
|------|------|
| `easyedit_reps/config/steer_eval_reps_local.yaml` | `model_name_or_path` |
| `easyedit_reps/config/steer_eval_reps_generate.yaml` | `model_name_or_path` |
| `easyedit_reps/scripts/regen_tuned_all.py` | `build_cfg()` 内硬编码路径 |
| `easyedit_reps/scripts/sweep_l3_multipliers.py` | 同上 |
| `easyedit_reps/scripts/sweep_l12_multipliers.py` | 同上 |

```yaml
model_name_or_path: /path/to/Qwen3-4B-Instruct-2507
```

---

## 六、完整复现流程

### 流程总览

```text
Step 1  训练 RePS 向量（24 concept）
Step 2  valid 生成（统一 multiplier=3，可选）
Step 3  L3 分档 multiplier 扫参
Step 4  L1/L2 分档 multiplier 扫参
Step 5  从 baseline multipliers 重生成提交文件
Step 6  （可选）本地 proxy 评测
Step 7  提交天池（raw，无后处理）
```

预计 GPU 时间（RTX 5090 参考）：

| 步骤 | 耗时 |
|------|------|
| Step 1 向量训练 | ~2–3 h |
| Step 3 L3 扫参 | ~1 h |
| Step 4 L1/L2 扫参 | ~1.5 h |
| Step 5 重生成（512 token × 24 concept） | ~15 min |
| Step 5 重生成（768 token × 24 concept） | ~15 min |

---

### Step 1：训练 RePS 向量

```bash
cd easyedit_reps
source env.sh
bash scripts/run_reps_vectors.sh
```

输出：`outputs/vectors/ccks_baseline_reps/steer_eval_concept_{Lx_y}/reps_vector/layer_18.pt`

每个 concept 独立训练一个向量，共 24 个。

---

### Step 2：Baseline 生成（可选，用于对比）

```bash
bash scripts/run_reps_generate.sh
```

统一 `multiplier=3`，本地 proxy 约 2.66，仅作起点参考。

---

### Step 3：L3 multiplier 扫参

```bash
bash scripts/run_l3_sweep.sh
```

- 范围：0.5, 1.0, 1.5, 2.0, 2.5, 3.0
- 输出：`outputs/generation/l3_tuned/best_l3_multipliers.json`

**L3 最优 multiplier 摘要**：

| Concept | multiplier | 说明 |
|---------|-----------|------|
| L3_1 | 3.0 | 需 `??` 字面约束 |
| L3_2 | 2.0 | 需 `let's improvise` |
| L3_3 | 1.0 | 需 `sonder`（薄弱） |
| L3_7 | 2.5 | 需 `pareto frontier` |

---

### Step 4：L1/L2 multiplier 扫参

```bash
bash scripts/run_l12_sweep.sh
```

- 输出：`outputs/generation/l12_tuned/best_l12_multipliers.json`
- 合并 L3 tuned 结果，本地 proxy 约 **3.21**

**薄弱 concept**：L2_1 (m=1.5)、L2_3 (m=1.0)

---

### Step 5：从 baseline 重生成提交（★ 推荐路径）

仓库已冻结 baseline multiplier（`baseline/multipliers.json`），无需重跑扫参即可复现最优配置：

```bash
# 复现 baseline v1（512 token，官方分 0.3817）
bash scripts/regen_from_baseline.sh 512

# Round 1 实验：768 token
bash scripts/regen_from_baseline.sh 768
```

输出文件：

| 命令 | 提交文件 |
|------|---------|
| `regen_from_baseline.sh 512` | `绝地邮兵_result_regen_512.json` |
| `regen_from_baseline.sh 768` | `绝地邮兵_result_regen_768.json` |

**提交策略**：直接提交上述 JSON，**不做后处理**。

---

### Step 6：本地 proxy 评测（可选，仅供参考）

```bash
cd easyedit_reps && source env.sh
.venv/bin/python scripts/export_submission.py \
  --in outputs/generation/regen_512/all_generation_results_valid.json \
  --out ../runs/predictions.json

cd ..
python scripts/local_eval.py \
  --gold valid.json \
  --pred runs/predictions.json \
  --out runs/local_eval.json
```

> ⚠️ 本地 proxy 与天池官方分方向可能相反，勿以 proxy 作为最终优化目标。

---

### Step 7：提交天池

提交文件为嵌套 JSON 格式，结构如下：

```json
[
  {
    "concept_id": "L1_1",
    "concept_name": "...",
    "concept_description": "...",
    "generation_prompt": null,
    "generated_results": [
      {
        "input": "问题文本",
        "pred": ["模型回答"],
        "complete_output": ["模型回答"],
        ...
      }
    ]
  }
]
```

要求：24 concept × 5 条 = 120 条，无空 `pred`。

---

## 七、已有实验结果

### 7.1 天池官方分

| 版本 | max_new_tokens | 后处理 | 官方分 |
|------|---------------|--------|--------|
| 旧版 | 256 | full（hint+改写+L3） | 0.2583 |
| B 版 | 512 | official 轻量 | 0.355 |
| **baseline v1（A 版）** | **512** | **无** | **0.3817** |
| Round 1 | 768 | 无 | **0.2967** | ❌ 低于 baseline |

### 7.2 Baseline v1 配置

见 `baseline/baseline_manifest.json`，核心参数：

```json
{
  "layer": 18,
  "max_new_tokens": 512,
  "temperature": 0,
  "postprocess": "none",
  "official_score": 0.3817
}
```

完整 multiplier 见 `baseline/multipliers.json`。

### 7.3 768 token 初步对比（本地）

| 指标 | baseline 512 | 768 实验 |
|------|-------------|---------|
| 天池官方分 | **0.3817** | 0.2967 |
| 疑似截断 | 30/120 | 26/120 |
| 平均回答长度 | ~1066 字 | ~1360 字 |

**结论**：截断略减，但官方分 **下降 22%**。LLM judge 更 penalize 冗长、发散；512 token 是当前最优长度，**不再尝试 768/1024**。

---

## 八、EasyEdit 补丁说明

相对官方 [zjunlp/EasyEdit](https://github.com/zjunlp/EasyEdit)，本仓库 `easyedit_reps/EasyEdit/` 含 CCKS 兼容修改：

| 文件 | 修改内容 |
|------|---------|
| `steer/vector_generators/reps/utils.py` | BatchEncoding 兼容 |
| `steer/trainer/PreferenceModelTrainer.py` | 末 batch 越界修复 |
| `examples/steer_eval.py` | `method=reps` 及 concept_description fallback |

官方文档：[CCKS2026.md](https://github.com/zjunlp/EasyEdit/blob/main/examples/CCKS2026.md)

---

## 九、常见问题

**Q: CUDA OOM？**  
确认 `dtype: bfloat16`，关闭其他 GPU 进程；24 concept 逐一生成时会反复加载模型，属正常行为。

**Q: `ModuleNotFoundError: accelerate`？**  
`pip install accelerate`（transformers 5.x 加载模型需要）。

**Q: `env.sh` 后 torch 找不到？**  
设置 `CONDA_SITE` 指向你的 torch 安装目录（见 4.5 节）。

**Q: 已有向量，能否跳过 Step 1？**  
可以。将向量放到 `outputs/vectors/ccks_baseline_reps/`，直接从 Step 3 或 Step 5 开始。

**Q: 后处理要不要用？**  
**不建议。** 天池 A/B 已证明 raw 生成（0.3817）> official 后处理（0.355）。

**Q: `regen_from_baseline.sh` 报 multiplier 路径错误？**  
确保使用 `PROJECT_ROOT` 而非 `ROOT` 传路径（脚本已修复）；或手动指定：

```bash
.venv/bin/python scripts/regen_tuned_all.py \
  --max-new-tokens 768 \
  --multipliers /path/to/baseline/multipliers.json
```

---

## 十、后续优化方向

按 **投入产出比** 排序，均基于「raw 生成、无后处理、天池反馈驱动」原则。

### 10.1 ~~提高生成长度~~（已证伪，勿再试）

- 768 token 天池 **0.2967** < 512 token **0.3817**
- 本地截断减少（30→26）但官方分大幅下降，说明 judge 更重简洁与人格对齐
- **512 token 为当前 sweet spot**，勿试 1024

### 10.2 薄弱 concept 定向调 multiplier（优先级：最高）

本地与官方 judge 均可能偏低的 concept：

| Concept | 当前 m | 建议 |
|---------|--------|------|
| L2_1 | 1.5 | 细 grid 0.5–3.0，人工检查 5 条输出 |
| L2_3 | 1.0 | 同上 |
| L3_3 | 1.0 | 同上 |
| L3_6 | 1.0 | 同上 |

做法：只重生成目标 concept，合并进 baseline 其余 20 个，单变量提交验证。

### 10.3 L1/L2 整体 multiplier 重扫（优先级：中）

- L1/L2 人格对齐是 0.3817 继续提升的主要瓶颈
- 在 L3 multiplier 固定前提下，对 L1/L2 试更宽范围（1.0–4.0，步长 0.25）
- **不要**以 local proxy 为唯一指标，每轮挑 2–3 个 concept 人工看输出质量

### 10.4 多候选生成 + 筛选（优先级：中）

- 每题 `temperature=0.7` 生成 3 条，启发式选最优（最短免责声明、句末完整、人格化关键词等）
- 仅对薄弱 concept 试点，GPU 时间 ×3

### 10.5 向量层 / 训练数据（优先级：低）

- 尝试 layer 16 / 20 ablation（官方默认 18）
- 检查 train matching 样本是否足够「人格化」；若 train 偏正式，向量上限受限

### 10.6 不建议的方向

| 方向 | 原因 |
|------|------|
| full / official 后处理 | A/B 证伪，损害官方 judge |
| 刷 local proxy | 与官方分方向可相反 |
| LM-Steer / Vector Prompt | 无 CCKS qwen3-4b 官方配置 |
| 自研 CAA 框架 | 第一阶段已验证效果有限 |

### 10.7 实验节奏建议

```
每次只改一个变量 → 天池提交 → 对比 baseline 0.3817 → 保留更优版本
```

---

## 十一、参考文档

| 文档 | 内容 |
|------|------|
| `docs/EXPERIMENT_LOG.md` | 两阶段实验全记录（CAA 探索 → RePS） |
| `docs/OFFICIAL_SCORE_OPTIMIZATION.md` | 官方分优化与 A/B 结论 |
| `docs/REPS_SETUP.md` | 快速上手指南 |
| `baseline/README.md` | baseline v1 说明 |

---

*维护：CCKS2026 Steering 组*
