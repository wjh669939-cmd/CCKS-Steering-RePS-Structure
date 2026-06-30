# 后续实验计划（2026-06-30）

> **官方最优**：`绝地邮兵_result.json` · **0.6714**  
> **状态**：BA-BoN / L1 patch 已停；新方向见 **[STEER_IDEAS.md](STEER_IDEAS.md)**  
> 锁定策略：[CONCEPT_LOCK.md](CONCEPT_LOCK.md) · `baseline/concept_lock.json`

---

## 当前策略

- **不再**做 BA-BoN mult 扫参、L1 antagonistic patch、多 concept merge
- **冻结** 11 个 concept（1 PROVEN + 10 LOCKED + 5 PATCH_FORBIDDEN 含 L1_8）
- **下一优先**：Decay Steer（分阶段 mult）→ pos_only RePS（L3_2 试点）

详见 [STEER_IDEAS.md](STEER_IDEAS.md)。

---

## 已锁定（禁止 patch）

| 类别 | 数量 | concept |
|------|------|---------|
| PROVEN | 1 | L2_2 |
| LOCKED 够好 | 10 | L1_4–6, L2_1/3/4/8, L3_4/7/8 |
| PATCH_FORBIDDEN | 5 | L1_7/8, L2_5/6/7 |

---

## BA-BoN 官方结果（已结案）

| 提交 | 官方分 | 结论 |
|------|--------|------|
| L1_8 BA-BoN | **0.5183** | ❌ 归档 `archive/submissions/06_ba_bon/` |

---

## 工作区整理

```bash
bash scripts/workspace_cleanup.sh   # 根目录只留主提交 + 活跃配置
bash scripts/organize_submissions.sh
bash scripts/rollback_to_phase_f_l2_2.sh   # 回滚到 0.6714
```

---

## 相关脚本

| 脚本 | 用途 |
|------|------|
| `workspace_cleanup.sh` | 归档实验 JSON / runs |
| `rollback_to_phase_f_l2_2.sh` | 回滚到 0.6714 |
| `run_l2_2_mult_sweep.sh` | L2_2 只扫 mult（已验证路径） |
| `check_concept_lock.py` | 实验前检查是否允许 patch |
