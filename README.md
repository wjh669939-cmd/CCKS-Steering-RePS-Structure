# CCKS2026 大模型行为调控评测 Baseline

本项目用于完成 CCKS2026 大模型行为调控评测任务，提供一套可复现的 Steering baseline 流程。

当前实现采用 Contrastive Activation Addition（CAA）思路：

1. 按 `concept_id` 对 `train.json` 分组。
2. 对每个目标行为概念，分别计算 `matching` 与 `not_matching` 回答在模型隐藏层上的激活差。
3. 将同一概念下的激活差求平均，得到每个概念、每个层的 steering 向量。
4. 在 `valid.json` 生成阶段，根据样本的 `concept_id` 取对应向量，并通过 hook 注入指定 Transformer 层。

生成 prompt 中不会加入 concept 文本，目标行为通过模型内部激活干预实现，符合比赛对 Steering 方法的要求。

## 环境安装

建议使用项目内虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

正式运行建议使用带 CUDA 的环境。当前默认配置 `configs/baseline_caa.json` 设置了：

```json
{
  "require_cuda": true
}
```

这是为了避免误在 CPU 上运行 Qwen3-4B 级别模型。

## 模型配置

比赛模型为 `Qwen/Qwen3-4B-Instruct-2507`。如果本地已经下载模型，建议把 `configs/baseline_caa.json` 中的路径改成本地模型目录：

```json
{
  "model_name_or_path": "path/to/Qwen3-4B-Instruct-2507"
}
```

使用本地模型路径更利于复现，也能避免 Hugging Face 网络波动。

## 数据检查

检查训练集和验证集字段、规模、domain 分布和 concept 分布：

```powershell
python scripts/inspect_data.py --train train.json --valid valid.json --out runs/data_report.json
```

当前数据规模：

- `train.json`：1680 条
- `valid.json`：120 条
- domain：`personality`
- concept 数量：24
- 每个 concept 训练 70 条、验证 5 条

## 环境检查

检查 PyTorch、Transformers、CUDA 和本地模型缓存：

```powershell
python scripts/check_environment.py --config configs/baseline_caa.json --out runs/environment_report.json
```

如果 `cuda_available=false`，正式 Qwen baseline 不应继续运行。

## 训练 Steering 向量

```powershell
python scripts/train_vectors.py --config configs/baseline_caa.json
```

输出目录：

```text
runs/baseline_caa/vectors/
```

每个层会保存一个 `.pt` 文件，内部按 `concept_id` 存储向量。

## 生成验证集答案

```powershell
python scripts/generate.py --config configs/baseline_caa.json
```

默认输出：

```text
runs/baseline_caa/predictions.json
```

可临时覆盖层数和强度：

```powershell
python scripts/generate.py --config configs/baseline_caa.json --layer 24 --strength 1.5
```

## 本地代理评测

```powershell
python scripts/local_eval.py --gold valid.json --pred runs/baseline_caa/predictions.json --out runs/baseline_caa/local_eval.json
```

注意：本地代理分数只用于调试，不等价于天池官方 LLM judge 分数。

## 生成提交文件

```powershell
python scripts/make_submission.py --pred runs/baseline_caa/predictions.json --out-dir runs/baseline_caa/submission
```

脚本会生成：

- `submission.json`
- `submission.jsonl`
- `submission.csv`

最终应以天池平台要求的提交格式为准。

## Smoke Test

如果当前机器没有 CUDA，可以用 tiny-gpt2 跑通完整代码链路：

```powershell
python scripts/train_vectors.py --config configs/smoke_tiny_gpt2.json --limit-per-concept 1
python scripts/generate.py --config configs/smoke_tiny_gpt2.json --limit-per-concept 1
python scripts/local_eval.py --gold valid.json --pred runs/smoke_tiny_gpt2/predictions.json --out runs/smoke_tiny_gpt2/local_eval.json --allow-partial
python scripts/make_submission.py --pred runs/smoke_tiny_gpt2/predictions.json --out-dir runs/smoke_tiny_gpt2/submission
```

Smoke test 只用于验证工程链路，不代表比赛效果。

## 防止验证集泄漏

`scripts/train_vectors.py` 只读取配置中的 `train_path`。`valid_path` 仅用于生成和评测脚本，避免训练阶段误用验证集。

## GitHub 推送说明

如果远端仓库创建时自动生成了 README 或 LICENSE，本地首次推送可能被拒绝。确认远端内容可以被覆盖后，可执行：

```powershell
git push -u origin main --force
```

如果需要保留远端已有内容，应先 fetch/merge 再 push。
