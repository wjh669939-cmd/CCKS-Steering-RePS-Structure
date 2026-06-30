# 归档目录

历史实验产物，不影响当前 baseline 复现与后续训练。需要时可从此处找回。

## 结构

| 路径 | 内容 |
|------|------|
| [`submissions/`](submissions/) | 历史提交 JSON，按阶段分子目录（见 [SUBMISSIONS.md](../docs/SUBMISSIONS.md)） |
| `runs/` | 实验运行日志（phase_d/e、pilot、round5、CAA 等） |
| `outputs/` | 中间生成结果、失败向量（layer20、LoRA、CAA、pos_only） |
| `scripts/` | 已结案的一键脚本（round2、weak8、submit 系列等） |
| `baseline/` | 过时 manifest / round3 partial mult |
| `external/` | 与 CCKS 无关的资料（大创等） |

### submissions 子目录

| 目录 | 说明 |
|------|------|
| `00_current/` | 主提交副本（0.6714） |
| `01_milestones/` | pre_optimize → weak8 → best_merge → phase_c → **phase_f 0.6714** |
| `02_phase_f/` | L2 多 concept 合并（官方 0.6583，已回滚） |
| `02_phase_d/` | L3_1/L3_6 扫参（官方 0.4383） |
| `03_phase_e/` | L2 mult 扫参（官方 0.36） |
| `04_pilot/` | 降 mult、L1/L2 重训试点 |
| `05_ablation/` | CAA/LoRA/matching_pick 等证伪实验 |
| `06_ba_bon/` | BA-BoN 候选（L1_8 官方 **0.5183**） |

### runs 近期归档

`phase_d_l3_*`、`phase_e*`、`pilot_*`、`ba_bon_*`、`round5_*`、`l1_1_caa`、`l3_*_caa` 等已移入 `archive/runs/`。  
活跃日志仍保留在根目录 `runs/`（`phase_a`、`phase_c`、`ba_bon_official.md`、`baseline_concept_audit.json`）。

## 当前活跃文件（勿删）

- 提交：`../绝地邮兵_result.json`（**0.6714**）
- 配置：`../baseline/{layers.json,multipliers.json,submission.json}`
- 向量：`../easyedit_reps/outputs/vectors/per_layer/`、`ccks_baseline_reps/`
- 复现：`bash ../scripts/regen_from_baseline.sh 512`

## 重新整理

```bash
bash scripts/organize_submissions.sh   # 提交 JSON 分类
bash scripts/workspace_cleanup.sh       # 全量工作区清理（若存在）
```
