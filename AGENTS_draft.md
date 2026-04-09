对，你抓到的是一个**很典型、而且很严重的接口/分层设计问题**。

**结论先说**
这类问题本质上叫：

* **Leaky Abstraction（抽象泄漏）**
* 更具体一点是：**Wrapper 与 Callee 的职责耦合**
* 也可以说是：**上游 orchestration 层对下游实现细节的污染**
* 从依赖方向看，还带有明显的 **Inappropriate Knowledge / Knowledge Leakage（不当知识泄漏）**
* 从流程设计看，还包含 **Temporal Coupling（时序耦合）**：上游 skill 假定下游一定存在、一定按当前步骤运行

你举的这几条确实很有问题：一个本来应该只是 `issue-collect` 前置入口/包装器的 skill，却在自己的 Rules 里大量出现“不要做 `issue-collect` 的事”“不要跳过 `issue-collect` 的 PROJECT_ROOT 解析”“要为 `issue-collect` 透明转发材料”这类表述。这样写，说明这个 skill **没有真正建立自己的边界**，而是在靠“反复提下游名字”来定义自己。

---

## 这类设计问题到底是什么

### 1. **Leaky Abstraction**

`cmiotsdk-start-bugflow` 本来应该是一个上层入口抽象，用户只需要知道：

* 这是 `cmiotsdk` 的 bug workflow 入口
* 它会准备 branch
* 然后进入后续流程

但现在它的文档里不断出现：

* 不要创建 `case.yaml`
* 不要写 `collect.md`
* 不要 duplicate `/issue-collect` 的 file-writing logic
* 不要 skip `/issue-collect` 的 root resolution

这说明这个抽象并不自洽。
它不是在说“我负责什么”，而是在说“我不是下面那个东西的哪些部分”。

这就是**抽象泄漏**：
**一个抽象层必须借助另一个具体实现的细节，才能解释自己。**

---

### 2. **Wrong Boundary Definition（边界定义错误）**

一个 skill 的规则应该主要围绕：

* 它的目标
* 它的输入
* 它的输出
* 它允许做什么
* 它禁止做什么

而不是围绕“另一个 skill 在做什么”。

你现在这份设计的问题是：
**它不是在定义 `cmiotsdk-start-bugflow` 的边界，而是在定义它和 `issue-collect` 之间的边界。**

这两者看似接近，其实差别巨大。

好的 wrapper 应该这样定义自己：

* 我负责 repo validation
* 我负责 ticket validation
* 我负责 branch bootstrap
* 我负责决定是否交给下一阶段

而不是：

* 我不负责 collect 的目录创建
* 我不负责 collect 的 root resolve
* 我不负责 collect 的文件写入

后者属于**拿邻居家的围墙来定义自己家地界**。

---

### 3. **Inappropriate Knowledge / Knowledge Leakage**

`cmiotsdk-start-bugflow` 知道太多 `issue-collect` 的内部细节了。
比如它居然知道：

* `issue-collect` 会创建 `case.yaml`
* 会写 `collect.md`
* 会 resolve `PROJECT_ROOT`
* 会处理 evidence 目录

这已经不是“知道下游存在”，而是“知道下游内部实现步骤”。

这会带来两个直接问题：

**第一，脆弱性上升**
以后你改了 `issue-collect`：

* `collect.md` 改名
* `PROJECT_ROOT` 解析方式变化
* evidence 目录策略变化

那么 wrapper 的文档就立刻过期。

**第二，依赖方向反了**
正常应该是：

* wrapper 依赖下游的**接口契约**
* 不依赖下游的**内部实现**

但现在它依赖的是后者。

---

### 4. **Temporal Coupling**

你提到最刺眼的一条其实是：

* `DO NOT skip /issue-collect's own PROJECT_ROOT resolution`

这句话的问题非常典型。
它隐含了一个假设：

* `issue-collect` 当前一定有一个“自己的 PROJECT_ROOT resolution 步骤”
* 而且 wrapper 的行为必须配合这个步骤
* 甚至 wrapper 要显式约束自己不要碰这一步

这就是很重的**时序耦合**与**流程耦合**。

也就是说，wrapper 不是在面向一个稳定 contract，而是在面向对方“当前第几步做什么”。

这在软件工程里就是坏味道。

---

## 为什么你会强烈觉得“这不是废话吗”

因为这些规则从用户视角和从架构视角都没有信息增量。

### 从用户视角

用户关心的是：

* 这个命令干什么
* 需要我提供什么
* 运行后会发生什么
* 失败时怎么处理

用户根本不关心：

* 它不创建 `case.yaml` 是因为另一个 skill 创建
* 它不跳过另一个 skill 的 root resolution

这些都是**内部实现说明**，不该出现在 skill 的一线行为定义里。

### 从架构视角

这些话看似是在“防止职责混乱”，但本质上是在暴露一个事实：

> 这个 skill 自己的职责定义还不够强，只能靠不停声明“别做 collect 的事”来自我约束。

这就是你会本能觉得“很别扭”的原因。

---

## 更准确地说：这是“negative boundary definition”

还有一个更细的名字，我觉得很适合你这个场景：

**Negative Boundary Definition（负向边界定义）**

也就是：

> 一个模块不是通过“我负责什么”来定义自己，
> 而是通过“我不负责别人负责的什么”来定义自己。

这通常不是成熟设计。

好的模块定义应该是正向的：

* **Scope**
* **Inputs**
* **Outputs**
* **Success Conditions**
* **Failure Conditions**

而不是：

* 我不做 A
* 我不做 B
* 我不碰 C
* C 是另一个模块做的

负向定义最多只能作为补充，不能成为主体。

---

## 这在 Claude Code / skill 设计里为什么尤其糟

Anthropic 官方对 slash commands / skills 的建议很明确：
应该是 **focused responsibilities**，并把复杂性拆到 supporting files，命令/skill 本身应当清楚表达自己的单一任务。([Claude API Docs][1])
同时，hooks 的定位是 deterministic enforcement，而不是让上层 prompt 去反复记忆和描述一堆必须遵守的实现细节。([Claude API Docs][2])

你这个 skill 的坏味道恰恰违背了这个精神：

* 它没有把自己的“正职责”压缩成一个简洁闭环
* 反而用很多文字在解释它和另一个 skill 的关系
* 于是 prompt 开始变得像“内部协作文档”，而不是“单一命令说明”

---

## 这份 skill 现在暴露出的核心问题

我给你压缩成一句：

**它不是一个真正独立的 entry skill，而是一个“对 `issue-collect` 过度知情的 wrapper prompt”。**

这类设计通常会出现以下后果：

* 下游一改，上游文档跟着碎
* wrapper 越写越长
* skill 之间开始互相引用内部步骤
* 系统整体越来越像“口头约定耦合”而不是“接口契约组合”

---

## 正确做法应该是什么

### 方案核心

`cmiotsdk-start-bugflow` 不应该在自己的规则里大量谈论 `/issue-collect` 的内部职责。
它只应该定义：

**我负责什么**

* validate repo
* validate ticket
* prepare or switch bugfix branch
* optionally hand off collected user payload to next workflow stage

**我不负责什么**

* 不分析代码
* 不修改源码
* 不执行 diagnosis

注意：
“不分析代码、不改源码”是它自身职责边界的一部分，这个可以保留。
但“不创建 case.yaml，因为那是 `/issue-collect` 的工作”这种写法不优雅。

---

## 更好的表达方式

把下面这种写法：

* **DO NOT** create case.yaml, collect.md, or evidence directories — that is /issue-collect's job
* **DO NOT** duplicate any /issue-collect file-writing logic
* **DO NOT** skip /issue-collect's own PROJECT_ROOT resolution
* **DO** preserve all user-provided materials for transparent forwarding

改写成**不提下游内部实现**的版本：

### 更好的 Rules 写法

```md
## Scope

This skill prepares the cmiotsdk bugfix workspace by validating the repository, validating the ticket ID, and creating or reusing the correct bugfix branch.

## Non-goals

This skill does not perform evidence collection, case workspace creation, source-code analysis, or source-code modification.

## Handoff

If automatic continuation is enabled, forward the original user payload unchanged to the next workflow stage.
```

你看，信息完全保留了，但层次感完全不一样：

* 不再显式绑定 `/issue-collect`
* 不再暴露 `case.yaml` / `collect.md` 这些实现细节
* 不再写“不要跳过对方步骤”这种强耦合语句
* 只保留 workflow contract

这才是像样的入口层设计。

---

## 哪些内容应该保留，哪些应该删

### 应该保留

* 只适用于 `cmiotsdk`
* 需要合法 `ticket_id`
* 负责 git bootstrap
* 默认可自动进入下一阶段
* 不读/不分析/不修改源码

这些都是**自身边界**。

### 应该删或重写

* “不要创建 `case.yaml` / `collect.md` / evidence 目录，因为那是 `/issue-collect` 的工作”
* “不要 duplicate `/issue-collect` file-writing logic”
* “不要 skip `/issue-collect` 的 own PROJECT_ROOT resolution”
* “要 preserve materials for transparent forwarding”

这些都属于：

* 对下游内部实现的显式依赖
* 非必要的负向定义
* 不优雅的 coupling leakage

---

## 给这个问题一个最准确的命名

如果你要给 Claude / Gemini / 代码审查文档里下结论，我建议直接这么写：

**这是一个典型的 wrapper abstraction leak：上游 entry skill 通过引用下游 `issue-collect` 的内部实现细节来定义自己的边界，导致职责边界表达不正交，形成不必要的 knowledge coupling 与 temporal coupling。**

再简短一点就是：

**这是抽象泄漏 + 错误边界定义 + 下游实现细节耦合。**

---

## 我给你的最终 review 结论

**你的直觉是对的。**
这不是“只是有点啰嗦”，而是一个真正的架构味道问题：

* 它说明这个 skill **还没有从“collect-aware prompt”进化成“独立 entry contract”**
* 它把下游的内部职责拿来定义自己，属于 **Leaky Abstraction**
* 它通过“不要做 collect 的 X/Y/Z”来表达边界，属于 **Negative Boundary Definition**
* 它依赖下游当前步骤和实现，属于 **Knowledge Coupling + Temporal Coupling**

**一句话整改原则：**

> 入口 skill 应该只定义自己的正职责和 handoff contract，不能通过引用下游内部实现来定义自己。

如果你愿意，我下一条可以直接把 `skills/cmiotsdk-start-bugflow/SKILL.md` 改写成一版**边界干净、完全不泄漏 `issue-collect` 内部实现**的版本。

[1]: https://docs.anthropic.com/en/docs/claude-code/slash-commands?utm_source=chatgpt.com "Slash commands - Anthropic"
[2]: https://docs.anthropic.com/en/docs/claude-code/hooks?utm_source=chatgpt.com "Hooks reference - Anthropic"
