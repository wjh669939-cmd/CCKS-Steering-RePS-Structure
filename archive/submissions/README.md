# 提交归档

文件名统一前缀：`绝地邮兵_result_<tag>.json`（根目录主提交无后缀）。

| 子目录 | 含义 |
|--------|------|
| `00_current/` | 与根目录 `绝地邮兵_result.json` 同步（**0.6714**） |
| `01_milestones/` | 历史里程碑 → Phase F **0.6714** |
| `02_phase_f/` | 多 L2 合并失败（官方 **0.6583**，勿提交） |
| `02_phase_d/` | L3 keyword 优化（官方 0.4383） |
| `03_phase_e/` | L2 mult 优化（官方 0.36） |
| `04_pilot/` | 降 mult / 重训试点 |
| `05_ablation/` | CAA/LoRA/matching 等对照，**勿提交** |

**完整索引**：[docs/SUBMISSIONS.md](../../docs/SUBMISSIONS.md)

```bash
bash scripts/organize_submissions.sh
bash scripts/rollback_to_phase_f_l2_2.sh   # 恢复 0.6714
```
