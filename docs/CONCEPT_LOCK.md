# 概念锁定与顽固实验队列（0.6714）

> 更新：2026-06-30  
> 原则：**先锁够好的，只对顽固 concept 做实验**

## 四类划分（24 concept）

| 类别 | 数量 | 含义 | 实验 |
|------|------|------|------|
| **PROVEN** | 1 | 官方验证涨分 | 可微调 L2_2 mult，勿换向量 |
| **LOCKED** | 10 | 0.6714 里够好/稳定 | **禁止 merge patch** |
| **PATCH_FORBIDDEN** | 5 | 单 patch 官方已跌 | **禁止再实验**，保持 baseline |
| **STUBBORN** | 8 | 顽固，有改进空间 | **唯一允许专项实验** |

配置文件：`baseline/concept_lock.json`

---

## PROVEN（1）— 核心涨分

| ID | 配置 | 说明 |
|----|------|------|
| **L2_2** | L18 · m=3.5 · retrain_pilot | 0.5583→0.6714 的唯一大赢 |

---

## LOCKED 够好（10）— 禁止动

| ID | L / m | proxy HM | 备注 |
|----|-------|----------|------|
| L1_4 | 16 / 3.0 | 1.20 | 稳定 |
| L1_5 | 20 / 3.0 | 1.44 | 较好 |
| L1_6 | 16 / 3.0 | 1.44 | 较好 |
| L2_1 | 16 / 3.5 | 0.72 | Phase C 已调 |
| L2_3 | 16 / 2.0 | 0.72 | 勿用 retrain_pilot |
| L2_4 | 18 / 3.0 | 0.72 | 默认锁 |
| L2_8 | 16 / 2.5 | 0.54 | 无 patch 失败记录 |
| L3_4 | 16 / 3.0 | 1.44 | kw **5/5** |
| L3_7 | 18 / 3.0 | 1.44 | kw **5/5** |
| L3_8 | 18 / 4.5 | 1.44 | kw **5/5** |

---

## PATCH_FORBIDDEN（5）— 勿再 patch

| ID | 官方 patch 分 | 原因 |
|----|-------------|------|
| L1_7 | **0.55** | 基线已够好，m=3.5 过 steer |
| L1_8 | **0.5183** | BA-BoN 单 patch（4/5 改），本地 proxy 误判 |
| L2_5 | **0.5006** | retrain_pilot 证伪 |
| L2_6 | **0.5433** | retrain_pilot 证伪 |
| L2_7 | **0.5433** | retrain_pilot 证伪 |

---

## STUBBORN 实验队列（8）— 仅攻这些

**优先级**（建议顺序）：

1. **L3_1、L3_2、L3_6** — keyword 3–4/5，补全即可  
2. **L1_2、L1_3** — L1 proxy CS 弱  
3. ~~L3_3、L3_5~~ — BA-BoN mult 已 0/5 改，改走 CAA 重训  
4. ~~L1_1、L1_8~~ — L1_8 BA-BoN 官方 **0.5183** 证伪；**勿交 L1_1**  

| ID | 类型 | proxy | keyword |
|----|------|-------|-----------|
| L1_2 | personality | CS=0.2 | — |
| L1_3 | personality | CS=0.2 | — |
| L3_1 | keyword | HM=1.2 | **3/5** |
| L3_2 | keyword | HM=1.6 | **4/5** |
| L3_3 | keyword | HM=0 | **0/5**（BA-BoN mult 死路） |
| L3_5 | keyword | HM=0 | **0/5**（BA-BoN mult 死路） |
| L3_6 | keyword | HM=0.9 | **3/5** |
| L1_1 | antagonistic | HM=0 | —（本地 4/5 改，**禁止提交**） |

---

## 实验规则

```text
merge / 官方提交：
  ✅ 仅 patch STUBBORN 中 1 个 concept
  ❌ 不得 patch LOCKED / PROVEN / PATCH_FORBIDDEN
  ❌ 不得多 concept 一次 merge

下一方法：BA-BoN（baseline 锚定多候选），见 docs/NEXT_EXPERIMENTS.md
```

检查锁定：

```bash
python3 scripts/check_concept_lock.py L3_3   # exit 0 = 允许实验
python3 scripts/check_concept_lock.py L1_5   # exit 1 = 禁止 patch
```

复现审计：

```bash
python3 scripts/audit_official_proxy.py \
  --submission baseline/submission.json \
  --label baseline_0.6714 \
  --out runs/baseline_concept_audit.json
```
