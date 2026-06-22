# RePS Baseline v1（reps_raw_v1）

> 天池官方分 **0.3817** | 512 token | raw 生成 | 无后处理

## 内容

| 文件 | 说明 |
|------|------|
| `baseline_manifest.json` | 完整配置快照（模型、层、生成参数、官方分） |
| `multipliers.json` | 24 concept 分档最优 multiplier（L3 + L1/L2 扫参合并） |
| `submission.json` | 冻结提交文件（等同 `绝地邮兵_result_pre_optimize_long.json`） |

## 复现 baseline 生成

```bash
bash scripts/regen_from_baseline.sh 512
# 输出: 绝地邮兵_result_regen_512.json
```

## 从 baseline 做实验变体

```bash
# 768 token（Round 1 优化）
bash scripts/regen_from_baseline.sh 768
# 输出: 绝地邮兵_result_regen_768.json
```

multiplier 固定读 `baseline/multipliers.json`，仅改 `--max-new-tokens` 即可做 controlled ablation。

## 关键参数

- 模型：Qwen3-4B-Instruct-2507，layer **18**
- `max_new_tokens`: **512**
- `temperature`: 0，`do_sample`: false
- `system_prompt`: 空
- 后处理：**无**
