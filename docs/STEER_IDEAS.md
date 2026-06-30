# 新 Steer 方法 brainstorm（2026-06-30）

> **现状**：官方 **0.6714**（L2_2 重训 L18 m=3.5 唯一大赢）  
> **停止**：BA-BoN mult 扫参、L1 antagonistic patch、多 concept merge、本地 proxy 驱动提交  
> **目标**：在**不动 11 个已锁 concept** 前提下，找 1–2 个可验证的新干预形态

---

## 已从实验得到的约束

| 事实 | 含义 |
|------|------|
| 仅 L2_2 重训有效 | 「换向量」不是通用解；需 concept 级假设 |
| L3 keyword 在词表 rank 15 万+ | 现有 RePS 向量**推不动目标 token** |
| L1_7/L1_8 patch 大跌 | 够好的 L1 **减损 > 增益**；L1 主攻方向存疑 |
| 512 raw > 后处理 | 任何答案级 hack 风险极高 |
| per-concept layer 有效 | 层选择是真实自由度 |

---

## 方向 A：分阶段 multiplier（Decay Steer）— 优先试

**假设**：L2_2 成功因「强 steer 开头、弱 steer 收尾」；高 mult 全程注入破坏流畅度。

**做法**：
- 生成前 `k` 个 token：`mult = m_high`（如 3.5）
- 之后线性衰减到 `m_low`（如 1.0）或第 2 段起 `mult=0`
- **仅对 STUBBORN / 已证伪可重试的 L2 类 concept** 在 train 上扫 `(k, m_high, decay)`

**合规**：仍是 RePS 向量，无 prompt 注入。  
**成本**：改 EasyEdit applier hook（按 step 改 mult），单 concept 官方 A/B。  
**ROI**：中—复用 L2_2 向量，不碰 locked concept。

**借鉴论文**：
- [Steering Vector Fields (SVF)](https://arxiv.org/html/2602.01654v1) — 长文生成中静态向量会 misalign，需按解码步刷新方向
- [Why Steering Works](https://arxiv.org/html/2602.02343v2) — validity decay：\|m\| 越大，激活越偏离 manifold，能力/流畅度下降
- [Inference-time Alignment via Sparse Junction Steering (SIA)](https://arxiv.org/html/2602.21215v1) — 仅在高熵/关键 junction token 干预，非全程均匀 steer

---

## 方向 B：pos_only 子集 RePS（L3 keyword 专用）

**假设**：L3_3/5 失败因 neg 样本「太像 pos」，向量方向模糊（对比对不够「硬」）。

**做法**：
- 仅用 train 中 **pos 含目标词 / neg 不含** 的子集训 RePS
- 合成 neg：同题 paraphrase 去掉 keyword（合规，只用 train）
- 层：在 L3_4/7/8 成功层（16/18）附近扫，**不**用 valid 选层

**与 CAA 区别**：仍走 [RePS](https://arxiv.org/html/2505.20809v1) pipeline，避免 hybrid 换法全盘翻车。  
**验证**：本地只看 **logit rank 是否进 top-1k** + keyword 0/5→?；**不信 HM proxy**。  
**ROI**：高（L3 是 0.6714 里 HM 最高档）— 但 Phase D 曾 0.4383，需极保守单 concept。

**借鉴论文**：
- [CAA](https://arxiv.org/html/2312.06681v4) — 对比激活差分；本项目 L3 hybrid 已证伪，但 **pos/neg 构造**可借鉴
- [BiPO](https://arxiv.org/abs/2406.00045) — 偏好优化让向量直接推高目标回复概率（RePS 的理论前置）
- [RepE](https://arxiv.org/html/2310.01405v4) — Representation Reading + Control 两阶段范式

---

## 方向 C：正交化向量（Orthogonal RePS）

**假设**：steer 向量与「helpfulness / 长回答」方向共线，导致 L1 patch 时 IS 崩。

**做法**：
- 在 train 上估计全局「helpful 方向」\(h\)（如 pos−neg 均值）
- 对每个 concept 向量 \(v\)：\(v' = v - \mathrm{proj}_h(v)\)，再归一化
- 仅对 **新训向量** 使用；**不**改 0.6714 已有 per_layer 向量

**合规**：训练期变换，推理仍 RePS。  
**ROI**：低—实现简单但缺乏 L2_2 级先验，适合作为 B 的预处理。

**借鉴论文**：
- [Conceptors](https://arxiv.org/html/2410.16314v2) — 用椭球投影矩阵替代向量相加，Boolean AND/OR 组合多 concept、减轻干扰
- [RepE Survey (Wehner et al.)](https://arxiv.org/html/2502.19649v3) — 多向量组合干扰是 RepE 核心挑战

---

## 方向 D：层间组合（同一 concept 双点注入）

**假设**：L2_2 在 L18 有效，但部分 L2 在 L16 更稳；单点不够。

**做法**：
- 同 concept 在 **两层** 各训一向量，推理时 `mult_1 * v_L16 + mult_2 * v_L18`（权重和 ≤ 当前单点 mult）
- **仅 1 个 STUBBORN concept** 试点，总干预强度不超过 baseline 单点

**风险**：EasyEdit 默认单层；需小改 applier。  
**ROI**：中低—复杂度高，优先 A/B。

**借鉴论文**：
- [RepE Survey](https://arxiv.org/html/2502.17601v1) — 多层/多位置干预综述
- [EasyEdit2](https://arxiv.org/html/2504.15133v1) — 模块化 vector applier，支持组合干预

---

## 方向 E：生成后验约束（Inference-Time Accept-Reject）

**与 BA-BoN 区别**：不用本地 personality proxy，只用**硬规则**：

- L3：无 keyword → 拒绝，回退 baseline 答案（不是 mult 候选里挑）
- 长度：超过 baseline ×1.3 → 拒绝
- 免责声明模式 → 拒绝

**本质**：对 baseline 做 guard，不是 steer 新方法；官方分上限 = 0.6714。  
**用途**：防止未来实验误提交，**不作为涨分路径**。

**借鉴论文**：
- [When is Your LLM Steerable?](https://arxiv.org/html/2606.11599) — 用早期 hidden state 预测 steer 成败，避免无效 rollout

---

## 建议执行顺序

```text
1. 工作区冻结 0.6714，不再官方 A/B 除非有新机制
2. 实现 Decay Steer hook → 仅在 L2_2 上复现是否 ≥0.6714（sanity）
3. pos_only L3_2（4/5 keyword，差 1 题）训向量 + logit audit
4. 若 rank 进 top-500 → 单 concept 官方；否则停 L3 keyword 线
5. L1 全线降为「观察」：不 patch，除非官方披露 rubric
```

---

## 明确不做

- 多 concept merge、全量 layer 替换、768 token、后处理插词
- BA-BoN + 本地 antagonistic/keyword proxy 驱动提交
- L1_1/L1_8/L1_7 类「够好或已跌」concept 的任何 patch
- 用 valid 调参或选层

---

## 相关文件

| 文件 | 用途 |
|------|------|
| `baseline/concept_lock.json` | 11 concept 冻结 |
| `runs/baseline_concept_audit.json` | 逐 concept proxy（仅参考） |
| `docs/ba_bon_official.md` | BA-BoN 证伪记录 |
| `docs/EXPERIMENT_LOG.md` | 全量历史 + 论文附录 |

---

## 方法论文献速查

| 方法 | 链接 |
|------|------|
| RePS（当前主方法） | https://arxiv.org/html/2505.20809v1 |
| EasyEdit2（工程框架） | https://arxiv.org/html/2504.15133v1 |
| RepE | https://arxiv.org/html/2310.01405v4 |
| ActAdd | https://arxiv.org/html/2308.10248v4 |
| CAA | https://arxiv.org/html/2312.06681v4 |
| BiPO | https://arxiv.org/abs/2406.00045 |
| Conceptors | https://arxiv.org/html/2410.16314v2 |
| RepE Taxonomy Survey | https://arxiv.org/html/2502.19649v3 |
| SVF | https://arxiv.org/html/2602.01654v1 |
| Validity decay | https://arxiv.org/html/2602.02343v2 |
| Sparse junction (SIA) | https://arxiv.org/html/2602.21215v1 |
| Steerability prediction | https://arxiv.org/html/2606.11599 |
