# Issue Triage Handoff — TODO v2（最终版）

---

## P0 — 核心架构缺陷（必须优先解决）

---

## P0.1 引入「Triage Decision」分叉（避免强制 handoff）

**背景 / 触发**
测试用例中存在“问题已清晰，但仍被强制 handoff”的情况（如 case_02）。

**当前问题**

* 所有流程默认进入 handoff
* 没有“是否需要 handoff”的判断层
* 导致：

  * 输出冗余
  * agent 链路污染
  * 错误责任归属

**目标**
在 handoff 前增加一个**强制决策阶段**，决定流程走向。

**必须实现**

* [ ] 在所有 workflow 前新增阶段：

  ```
  D-1: triage_decision
  ```
* [ ] 输出结构：

  ```json
  {
    "status": "resolved | needs_handoff | needs_more_evidence | blocked",
    "confidence": "high|medium|low"
  }
  ```
* [ ] 行为约束：

  * `resolved` → 输出 `triage-summary.json`，禁止 handoff
  * `needs_handoff` → 进入 handoff pipeline
  * `needs_more_evidence` → 输出缺失项
  * `blocked` → 输出阻塞原因

**验收标准**

* case_02 不再生成 handoff
* 输出规模下降 ≥50%

---

## P0.2 输出结构重构（解决 300 行膨胀问题）

**背景 / 触发**
当前 handoff 输出约 300 行（case_02），远超合理规模。

**当前问题**

* evidence / timeline / facts 三重重复
* 原始日志内容直接嵌入
* 无信息压缩机制

**目标**
构建**双层输出结构**，压缩主输出体积。

---

### 新结构

#### A. 主输出（必须）

`handoff.summary.json`

仅包含：

* issue meta
* triage_decision
* top evidence（≤8）
* key findings（引用）
* minimal timeline（≤5）
* next steps
* gaps

👉 目标：≤120 行

---

#### B. 附属输出（可选）

`handoff.evidence.json`

* 全量 evidence（详细内容）
* 不参与默认消费

---

### 必须实现

* [ ] evidence.content ≤ 200 chars（超长用引用）
* [ ] 所有 fact 必须引用 evidence_id（禁止重复文本）
* [ ] 删除重复 timeline
* [ ] 删除低价值 code_mapping
* [ ] Top-K evidence（默认 5~8）

**验收标准**

* case_02 输出 ≤150 行
* 无重复字段内容

---

## P0.3 全量 Evidence Inventory（禁止漏扫）

**背景 / 触发**
用户明确要求：目录中的所有文件都是有效输入。

**当前问题**

* 当前为“抽样扫描”
* 部分文件（如视频）未被处理 

**目标**
建立**强制全量登记机制**。

---

### 新阶段

```
D0: build_evidence_inventory (MANDATORY)
```

---

### 必须实现

* [ ] 扫描目录下所有文件（禁止类型过滤）
* [ ] 每个文件必须进入 inventory：

  ```json
  {
    "file_path": "",
    "type": "",
    "size": "",
    "mtime": "",
    "status": "parsed|skipped|failed",
    "reason": ""
  }
  ```
* [ ] 未解析必须记录原因

**验收标准**

* 输入目录中所有文件均出现在 inventory
* 无 silent skip

---

## P0.4 多模态证据支持（image / video 一等公民）

**背景 / 触发**
测试中存在视频 / 截图，但 pipeline 未处理。

**当前问题**

* collect 脚本只处理日志
* workflow 无视觉解析
* schema 未定义视觉信息结构

**目标**
统一证据模型，支持多模态。

---

### 必须实现

* [ ] collect 支持：

  * `.png .jpg .jpeg .webp`
  * `.mp4 .mov`
* [ ] image/video 解析输出：

  * description（视觉描述）
  * OCR（可选）
  * visual_signals（关键UI/错误/状态）
* [ ] schema 扩展：

  ```json
  {
    "type": "image|video",
    "visual_signals": [],
    "ocr_text": "",
    "relevance": "direct|context|weak"
  }
  ```

**关键约束**
👉 inventory 全量，但 handoff 只保留 Top-K

**验收标准**

* case_02 中视频必须出现在 evidence 中

---

## P0.5 项目上下文注入（修复错误责任归属）

**背景 / 触发**
输出建议“让 SDK 团队排查”，但当前执行者本身就是 SDK 团队。

**当前问题**

* skill 不知道：

  * 当前项目是谁
  * 当前团队角色
  * ownership 边界
* 导致 handoff 建议错误

---

### 目标

为 synthesis 提供**稳定的项目身份锚点**。

---

### 必须实现

* [ ] 支持读取：

  ```
  triage/project-context.md
  ```
* [ ] 内容结构：

  ```yaml
  project_name:
  team_role: "provider|consumer|integration"
  ownership:
  issue_scope:
  forbidden_assumptions:
  ```
* [ ] 在 synthesis 阶段强制加载

---

### 行为约束

* provider → 禁止建议“本团队继续排查”
* 根据 ownership 调整 next steps

---

**验收标准**

* 不再出现“建议自己排查自己”

---

# P1 — 执行稳定性 & pipeline

---

## P1.1 Preflight（依赖检查）

**问题**

* 7z/unzip 缺失导致失败 

---

### 必须实现

* [ ] 新阶段：

  ```
  D-2: preflight_check
  ```
* [ ] 检查：

  * unzip / 7z / unar
  * python3
* [ ] missing → fail fast + install hint

---

## P1.2 工具失败控制（防卡死）

**问题**

* `process hasn't exited`
* 执行卡死 

---

### 必须实现

* [ ] timeout（30s）
* [ ] retry（≤2）
* [ ] fallback（rg → grep）
* [ ] fail 分类：

  * hard_fail / soft_fail / degraded

---

## P1.3 去重执行（缓存机制）

**问题**

* 重复 grep 20+ 次 

---

### 必须实现

* [ ] cache dir：`.triage_work/cache/`
* [ ] key：event + window + identifiers
* [ ] 重复任务直接复用

---

## P1.4 批量搜索（替代循环 grep）

**目标**
一次扫描，多结果输出

---

### 必须实现

* [ ] multi-pattern grep
* [ ] 单次 IO 扫描
* [ ] 中间索引缓存

---

## P1.5 归档处理（统一规范）

**问题**

* `.7z.001` 不支持 

---

### 必须实现

* [ ] 支持：

  * zip / tar / gz
  * 7z / 7z.001
  * rar
* [ ] 自动分卷识别
* [ ] 每 archive 独立目录

---

## P1.6 长路径处理（健壮性）

**问题**

* 长路径 + wildcard 风险 

---

### 必须实现

* [ ] >100 chars → hash rename
* [ ] 保留映射
* [ ] 禁止 wildcard unzip

---

# P2 — 认知与可扩展性

---

## P2.1 动态模板系统

**问题**

* 当前 handoff 模板固定

---

### 建议实现

* [ ] 支持 conditional fields
* [ ] 支持 repo-specific override
* [ ] 根据 triage_decision 输出不同结构

---

## P2.2 Evidence Ranking（可选优化）

* [ ] relevance scoring
* [ ] 自动 Top-K

---

---

# 🔥 最优执行顺序

1. P0.1（triage decision）
2. P0.2（输出瘦身）
3. P0.3（inventory）
4. P0.4（多模态）
5. P0.5（project context）
6. P1（稳定性）

---
