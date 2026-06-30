# BA-BoN 官方 A/B 记录

> 更新：2026-06-30

| 提交 | concept | 改动 | 官方分 | vs 0.6714 | 结论 |
|------|---------|------|--------|-----------|------|
| `绝地邮兵_result_ba_bon_L1_8_submit.json` | L1_8 | 4/5 | **0.5183** | −0.1531 | ❌ 证伪 |
| L3_3 / L3_5 | — | 0/5 | — | — | 本地 0 改，未交 |
| `绝地邮兵_result_ba_bon_L1_1_submit.json` | L1_1 | 4/5 | — | — | **禁止提交** |

## 教训

- BA-BoN 本地 antagonistic proxy（长度 + CS）与官方评分**负相关**；L1_8 本地「4/5 更优」→ 官方大跌
- L1_8 已归入 `PATCH_FORBIDDEN`；正式仍交 `绝地邮兵_result.json`（0.6714）
- 归档：`archive/submissions/06_ba_bon/绝地邮兵_result_ba_bon_L1_8_submit_0.5183.json`
