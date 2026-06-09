# Smoke Test 报告

本报告用于说明当前项目在本机 CPU 环境下完成的轻量链路测试。Smoke test 不用于证明比赛效果，只用于证明工程流程可以正常运行。

## 测试目的

由于本机没有 NVIDIA CUDA 环境，无法正式运行 `Qwen/Qwen3-4B-Instruct-2507`。因此使用小模型 `sshleifer/tiny-gpt2` 做轻量测试，验证以下环节：

- 数据读取与字段检查
- no-steering 生成
- CAA steering 向量训练
- steering hook 注入生成
- 本地代理评测
- no-steering 与 CAA 结果对比
- layer/strength sweep 流程

## 数据检查结果

命令：

```powershell
.venv\Scripts\python.exe scripts\inspect_data.py --train train.json --valid valid.json --out runs\data_report.json
```

输出摘要：

```text
Wrote runs/data_report.json
train: rows=1680 domains={'personality': 1680} concepts=24
valid: rows=120 domains={'personality': 120} concepts=24
```

报告文件：

```text
runs/data_report.json
```

## 环境检查结果

命令：

```powershell
.venv\Scripts\python.exe scripts\check_environment.py --config configs\baseline_caa.json --out runs\environment_report.json
```

输出摘要：

```text
Wrote runs/environment_report.json
torch=2.12.0+cpu cuda=False transformers=5.10.2
model_config_cached=False
```

说明：

- 当前本机 PyTorch 是 CPU 版。
- 当前本机无 CUDA。
- 当前本机没有缓存正式 Qwen3-4B 模型。

报告文件：

```text
runs/environment_report.json
```

## no-steering Smoke Test

命令：

```powershell
.venv\Scripts\python.exe scripts\generate_no_steering.py --config configs\smoke_no_steering_tiny_gpt2.json --limit-per-concept 1
.venv\Scripts\python.exe scripts\local_eval.py --gold valid.json --pred runs\smoke_no_steering_tiny_gpt2\predictions.json --out runs\smoke_no_steering_tiny_gpt2\local_eval.json --allow-partial
```

输出摘要：

```text
Wrote runs\smoke_no_steering_tiny_gpt2\predictions.json
{"records": 24, "mode": "no_steering"}

Wrote runs/smoke_no_steering_tiny_gpt2/local_eval.json
Wrote runs\smoke_no_steering_tiny_gpt2\local_eval.csv
mean_hm_proxy=3.0000
```

产物文件：

```text
runs/smoke_no_steering_tiny_gpt2/predictions.json
runs/smoke_no_steering_tiny_gpt2/local_eval.json
runs/smoke_no_steering_tiny_gpt2/local_eval.csv
```

## CAA Steering Smoke Test

命令：

```powershell
.venv\Scripts\python.exe scripts\train_vectors.py --config configs\smoke_tiny_gpt2.json --limit-per-concept 1
.venv\Scripts\python.exe scripts\generate.py --config configs\smoke_tiny_gpt2.json --limit-per-concept 1
.venv\Scripts\python.exe scripts\local_eval.py --gold valid.json --pred runs\smoke_tiny_gpt2\predictions.json --out runs\smoke_tiny_gpt2\local_eval.json --allow-partial
```

输出摘要：

```text
Wrote vectors to runs\smoke_tiny_gpt2\vectors
{"layers": [0, 1], "concepts": 24}

Wrote runs\smoke_tiny_gpt2\predictions.json
{"records": 24, "layer": 1, "strength": 1.0}

Wrote runs/smoke_tiny_gpt2/local_eval.json
Wrote runs\smoke_tiny_gpt2\local_eval.csv
mean_hm_proxy=3.0000
```

产物文件：

```text
runs/smoke_tiny_gpt2/vectors/layer_0.pt
runs/smoke_tiny_gpt2/vectors/layer_1.pt
runs/smoke_tiny_gpt2/vector_metadata.json
runs/smoke_tiny_gpt2/predictions.json
runs/smoke_tiny_gpt2/local_eval.json
runs/smoke_tiny_gpt2/local_eval.csv
```

## Sweep Smoke Test

命令：

```powershell
.venv\Scripts\python.exe scripts\sweep_generate.py --config configs\smoke_tiny_gpt2.json --layers 1 --strengths 0.5 --out-dir runs\sweeps\smoke_tiny_gpt2 --limit-per-concept 1 --allow-partial-eval --overwrite
```

输出摘要：

```text
Wrote runs\sweeps\smoke_tiny_gpt2\layer_1_strength_0.5\predictions.json
{"records": 24, "layer": 1, "strength": 0.5}

Wrote runs\sweeps\smoke_tiny_gpt2\layer_1_strength_0.5\local_eval.json
Wrote runs\sweeps\smoke_tiny_gpt2\layer_1_strength_0.5\local_eval.csv
mean_hm_proxy=3.0000

Wrote runs\sweeps\smoke_tiny_gpt2\summary.json
{"best": {"layer": 1, "strength": 0.5, "predictions": "runs\\sweeps\\smoke_tiny_gpt2\\layer_1_strength_0.5\\predictions.json", "local_eval": "runs\\sweeps\\smoke_tiny_gpt2\\layer_1_strength_0.5\\local_eval.json", "mean_hm_proxy": 3.0}}
```

产物文件：

```text
runs/sweeps/smoke_tiny_gpt2/summary.json
runs/sweeps/smoke_tiny_gpt2/layer_1_strength_0.5/predictions.json
runs/sweeps/smoke_tiny_gpt2/layer_1_strength_0.5/local_eval.json
runs/sweeps/smoke_tiny_gpt2/layer_1_strength_0.5/local_eval.csv
```

## no-steering 与 CAA 对比

命令：

```powershell
.venv\Scripts\python.exe scripts\compare_predictions.py --gold valid.json --baseline runs\smoke_no_steering_tiny_gpt2\predictions.json --candidate runs\sweeps\smoke_tiny_gpt2\layer_1_strength_0.5\predictions.json --out runs\compare_smoke_no_steering_vs_caa.json --allow-partial
```

输出摘要：

```text
Wrote runs/compare_smoke_no_steering_vs_caa.json
Wrote runs\compare_smoke_no_steering_vs_caa.csv
delta_mean_hm_proxy=0.0000
```

产物文件：

```text
runs/compare_smoke_no_steering_vs_caa.json
runs/compare_smoke_no_steering_vs_caa.csv
```

## 结论

本机 smoke test 已验证项目工程链路可运行：

- no-steering baseline 脚本可运行。
- CAA steering 向量训练脚本可运行。
- steering hook 生成脚本可运行。
- 本地代理评测脚本可运行。
- sweep 与对比脚本可运行。

需要强调：上述分数基于 `tiny-gpt2` 和每个 concept 1 条样本，仅用于工程验证，不代表正式比赛效果。正式实验需要在 CUDA GPU 环境下运行 `Qwen/Qwen3-4B-Instruct-2507`。
