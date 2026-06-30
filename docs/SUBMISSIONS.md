# 提交文件索引（按实验阶段）

> 最后更新：2026-06-29  
> **官方最优**：根目录 `绝地邮兵_result.json`（Phase F · **0.6714** · 仅 L2_2）  
> 历史/实验提交已归档至 `archive/submissions/`，**勿误交** merged / pilot / phase_d / phase_e 文件。

---

> 归档内文件名均为 `绝地邮兵_result_<tag>.json`；下表 `<tag>` 列省略前缀便于阅读。

## 目录结构

```text
archive/submissions/
├── 00_current/          # 与根目录主提交同步的副本
├── 01_milestones/       # 已验证里程碑（含 Phase C、Phase F 0.6714）
├── 02_phase_f/          # Phase F 多 L2 合并试验（官方 0.6583，已回滚）
├── 02_phase_d/          # Phase D：L3 keyword 优化（官方失败）
├── 03_phase_e/          # Phase E：L2 mult 优化（官方失败）
├── 04_pilot/            # 降 mult / 重训等试点（多数未交官方）
└── 05_ablation/         # 对照实验：CAA/LoRA/matching_pick 等（勿提交）
```

重新整理归档：

```bash
bash scripts/organize_submissions.sh
```

---

## 一、当前正式提交

| 文件 | 阶段 | 官方分 | 说明 |
|------|------|--------|------|
| **`绝地邮兵_result.json`**（根目录） | **Phase F** | **0.6714** | ★ **唯一推荐提交** |
| `baseline/submission.json` | Phase F | 0.6714 | 与根目录文件内容一致 |
| `archive/submissions/00_current/绝地邮兵_result.json` | Phase F | 0.6714 | 归档副本 |
| `archive/submissions/01_milestones/绝地邮兵_result_phase_f_l2_2_retrain_0.6714.json` | Phase F | 0.6714 | 官方验证备份 |
| `archive/submissions/01_milestones/绝地邮兵_result_phase_c_l12.json` | Phase C | 0.5583 | 上一版最优 |

**配置**：`baseline/layers.json` + `baseline/multipliers.json`（L2_2 **m=3.5**）+ L2_2 重训向量 @ L18  
**复现**：`bash scripts/regen_from_baseline.sh 512`  
**重训脚本**：`bash scripts/run_pilot_retrain_l2_2.sh`

---

## 二、Phase F — L2_2 重训（01_milestones / 04_pilot）✅

| 文件 | 官方分 | 改动 | 结论 |
|------|--------|------|------|
| `pilot_retrain_L2_2.json` | — | 重训 L18 m=3.0 | ≈ Phase C |
| **`pilot_retrain_L2_2_m35.json`** | **0.6714** | 重训 L18 **m=3.5** | **★ 当前最优（仅 L2_2）** |
| `pilot_retrain_L2_2_m4.json` | — | 重训 L18 m=4.0 | Q4 过短 |

相对 Phase C：仅 L2_2 共 5 题变化；官方 **+0.1131（+20.3%）**。  
向量：`easyedit_reps/outputs/vectors/per_layer/L2_2/layer_18/`（来自 retrain_pilot）

---

## 二-b、Phase F 多 L2 合并（02_phase_f）❌

| 文件 | 官方分 | 改动 | 结论 |
|------|--------|------|------|
| `phase_f_merged.json` | — | L2_2+3+5+6+7 重训合并 | 本地肉眼 OK |
| **`phase_f_merged_0.6583.json`** | **0.6583** | 同上（已交官方） | **较 0.6714 −0.0131，已回滚** |

**教训**：L2 重训有效，但 **一次 merge 多个 concept 会拖累总分**；后续仅 **单 concept 官方 A/B**。

脚本：`scripts/merge_phase_f_all.sh` · 回滚：`scripts/rollback_to_phase_f_l2_2.sh`  
决策记录：`runs/phase_f_merge_decisions.md`

## 二-c、Phase F 单 L2 patch（02_phase_f）❌

| 文件 | 官方分 | 改动 | 结论 |
|------|--------|------|------|
| **`phase_f_L2_5_only_0.5006.json`** | **0.5006** | 0.6714 base + **仅 L2_5** 重训 L18 m=3.5 | **较 0.6714 −0.1708，勿再交** |
| `phase_f_L2_6_7_only_0.5433.json` | **0.5433** | 0.6714 base + L2_6+7 重训 | **已证伪**（若已归档） |

**教训**：L2_2 重训成功 **不可推广** 到其他 L2（即使单 concept、肉眼 OK）。Phase F `retrain_pilot` 向量除 L2_2 外 **全部冻结**。

脚本：`scripts/merge_retrain_submit.sh L2_5` · 归档：`archive/submissions/02_phase_f/`

### 5.3 批量 L2 重训（未 merge）

`scripts/run_phase_f_l2_batch.sh` 产出 L2_1–L2_8 重训候选于 `04_pilot/`；除 L2_2 外 **均未 merge 进主提交**。

---

## 三、里程碑阶段（01_milestones）

按时间线由低到高：

| 文件 | 阶段 | 官方分 | 关键改动 |
|------|------|--------|----------|
| `pre_optimize_long.json` | II-C reps_raw | **0.3817** | 512 token · layer18 统一 · raw |
| `regen_768.json` | III | 0.2967 | 768 token（有害） |
| `personality_trial.json` | III | 0.33 | L2_1↓ / L1_2↑ |
| `trunc_fix.json` | IV | 0.3633 | 截断修复后处理 |
| `weak8_layer.json` | V weak8 | **0.385** | 8 concept 逐层选层 |
| `weak8_l3_mult.json` | VI | — | weak8 + L3 mult 扫参 |
| `best_merge.json` | VI | **0.4517** | weak8_l3_mult + round2 选层 merge |
| `round2.json` / `round2_L3_6.json` | VI | — | L1/L2 选层 pilot |
| `round3_l3_partial.json` | VI | — | L3_1/2/6 mult 局部扫参 |
| `round3_pos_only.json` | VI | — | L3_3/5 pos_only 重训（未超越） |
| `submit1_l3*.json` | IV | 0.2583 等 | 早期 L3 mult / 后处理试验 |
| `layer20.json` | VI | 未提交 | 全量 layer20（本地更差） |
| `combo.json` / `l2_up.json` | — | 未提交 | 组合试验 |
| `phase_c_l12.json` | **VII Phase C** | **0.5583** | L2_1/3/6 mult↑ + L1_4/5/6 换层 |
| `phase_f_l2_2_retrain_0.6714.json` | **VIII Phase F** | **0.6714** | L2_2 重训 + m=3.5 |
| `best.json` | — | 0.5583 | 与 phase_c 重复备份 |

**Phase C 相对 best_merge 的主要 diff**：L2_1 m→3.5，L2_3 m→2.0，L2_6 m→4.0；L1_4/L1_6→L16，L1_5→L20。

---

## 三、Phase D — L3 keyword 优化（02_phase_d）❌

| 文件 | 官方分 | 改动 | 结论 |
|------|--------|------|------|
| `phase_d_l3_6.json` | — | 仅 L3_6 扫参候选 | 本地 kw +1 |
| `phase_d.json` | — | L3_1 + L3_6 merge 候选 | 本地 proxy +0.054 |
| **`phase_d_0.4383.json`** | **0.4383** | 同上（曾 merge 进主提交） | **官方 -0.12，已回滚** |

**教训**：L3 keyword / valid proxy ↑ 与官方 LLM 裁判 **反向**；L3_1/L3_6 **永久冻结**。

脚本：`scripts/run_phase_d_l3_6.sh`、`scripts/run_phase_d_l3_1.sh`  
日志：`archive/runs/phase_d_l3_*`

---

## 四、Phase E — L2 mult 优化（03_phase_e）❌

| 文件 | 官方分 | 改动 | 结论 |
|------|--------|------|------|
| `phase_e.json` | — | L2_2/5/8 layer×mult | 本地 proxy +0.054，L3 kw 不变 |
| `phase_e2.json` | — | + L2_1/6 微调（无增益） | 同 phase_e |
| **`phase_e_0.36.json`** | **0.36** | 同上 | **官方 -0.20，勿再交** |

配置快照：`baseline/archive/phase_e_config.json`  
脚本：`scripts/run_phase_e_l2_sweep.sh`  
日志：`archive/runs/phase_e/`

---

## 五、试点提交（04_pilot）

均未作为最终方案；肉眼 / 本地评估后 **不推荐** 替代 0.5583，除非单独官方 A/B。

### 5.1 降 mult 试点

| 文件 | 改动 | 肉眼结论 |
|------|------|----------|
| `pilot_L2_6_m3p5.json` | L2_6 m 4.0→3.5 | Q3 仍循环重复，无改善 |
| `pilot_L2_6_m3p0.json` | L2_6 m→3.0 | 出现 AI 免责声明，更差 |
| `pilot_L3_2_m4p5.json` | L3_2 m 5.0→4.5 | 丢失 verbatim 短语 |
| `pilot_L3_2_m4p0.json` | L3_2 m→4.0 | keyword 1/5 |

脚本：`scripts/run_pilot_lower_mult.sh`、`scripts/run_pilot_lower_mult_l3_2.sh`

### 5.2 重训 L2_2 试点

| 文件 | 改动 | 说明 |
|------|------|------|
| `pilot_retrain_L2_2.json` | 重训向量 L18 m=3.0 | ≈ baseline |
| **`pilot_retrain_L2_2_m35.json`** | 重训 L18 **m=3.5** | **官方 0.6714，当前 baseline** |
| `pilot_retrain_L2_2_m4.json` | 重训 L18 m=4.0 | Q4 过短 |

向量：`easyedit_reps/outputs/vectors/retrain_pilot/L2_2/`  
脚本：`scripts/run_pilot_retrain_l2_2.sh`  
日志：`archive/runs/pilot_retrain_l2_2/`

---

## 六、对照 / 证伪实验（05_ablation）— 勿提交

| 文件 | 实验 | 结论 |
|------|------|------|
| `phase_b_l3_3_lora.json` | L3_3 RePS-LoRA | kw 仍 0/5 |
| `l3_caa_hybrid.json` / `l3_3_caa_hybrid.json` | L3 CAA hybrid | 本地 L3 更差 |
| `l3_word_answer_caa_hybrid.json` | answer-level CAA | kw 0/5 |
| `l3_token_direction_hybrid.json` | unembedding 方向向量 | kw 0/5 |
| `l1_1_caa_hybrid.json` / `l1_1_reps_l12_hybrid.json` | L1_1 专项 | CS=0 顽固 |
| `matching_pick.json` | 4 候选 train margin | 风险大，未交 |
| `pos_aware.json` | pos-aware 生成 | 未超越 |
| `round5_step1.json` | L1_2/3 + L2_2/5/8 grid | 未完成 / 无 merge |
| `round5_step2.json` | L1_1 matching_pick + local_weight | proxy↑ 官方风险高 |
| `round5_step2_l1_1_only.json` | 仅 L1_1 子集 | 同上 |

---

## 七、冻结与禁区

**顽固 concept（任何新 merge 均禁止）**：L1_1、L1_8、L3_3、L3_5  

**已证伪路线（勿再 merge 到主提交）**：
- L3 keyword / mult 扫参（Phase D）
- 0.5583 基础上 L2 mult↑（Phase E）
- **Phase F 多 L2 重训一次合并**（0.6583 < 0.6714）
- **Phase F 单 L2 重训 patch**（L2_5 **0.5006**、L2_6+7 **0.5433**；除 L2_2 外 retrain_pilot 勿 merge）
- 后处理插词、768 token、local_weight、全量 CAA hybrid

**L2 重训规则**：**仅 L2_2** 已官方验证有效；其他 L2 的 retrain_pilot **禁止 merge**。若再实验，换 **L1 族** 或 **L2_2 推理侧微调**（同向量扫 m），勿用 Phase F 批量重训向量。

**valid proxy / 肉眼检查在 0.5583 之后不可信**；以 **天池官方分** 为唯一 merge 依据。

---

## 八、相关文档

| 文档 | 内容 |
|------|------|
| [EXPERIMENT_LOG.md](EXPERIMENT_LOG.md) | 完整实验时间线 |
| [../baseline/README.md](../baseline/README.md) | 当前 baseline 配置 |
| [../archive/README.md](../archive/README.md) | 归档目录总览 |
