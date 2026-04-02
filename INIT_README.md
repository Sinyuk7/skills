# Skills Init Script

同步当前项目的 skills 到各种 AI agent 的用户目录。

## 🎯 核心改进

这个脚本解决了原始版本的 **6 个关键问题**：

### ✅ 问题 1：正确的目录路径
- ✓ 使用 `~/.codex/skills` 而不是 `~/codex/skills`
- ✓ 添加 `~/.agents/skills` 作为 canonical user-level store（符合 Codex/open-agent-skills 标准）
- ✓ 支持 `.claude`, `.codex`, `.agents`, `.codemaker`, `.cursor` 等

### ✅ 问题 2：修复 `set -e` 陷阱
- ✓ 使用 `created=$((created + 1))` 而不是 `((created++))`
- ✓ 避免算术表达式返回 0 导致脚本退出的问题

### ✅ 问题 3：准确的跨平台说明
- ✓ 明确标注：macOS / Linux / Windows (Git Bash/WSL with Developer Mode)
- ✓ Windows 下失败时提示需要 Developer Mode 或 admin 权限
- ✓ 不夸大为"完全兼容 Windows"

### ✅ 问题 4：使用绝对路径
- ✓ `ln -s "$source" "$target"` 使用绝对路径
- ✓ 避免当目标目录本身是 symlink 时的相对路径解析问题

### ✅ 问题 5：智能冲突检测
- ✓ 检查已存在的 symlink 是否指向正确位置
- ✓ 区分 symlink / 真实目录 / 文件
- ✓ 提供详细的冲突信息

### ✅ 问题 6：完全可配置化
- ✓ 支持 `--claude`, `--codex`, `--agents` 等参数选择目标 agent
- ✓ 支持 `--all` 同步到所有已知 agent
- ✓ 支持 `--dry-run` 预览模式
- ✓ 支持 `--force` 强制覆盖冲突
- ✓ 内置可扩展的 agent 目录映射表

## 🚀 使用方法

### 基本用法

```bash
# 同步到默认 agents (.agents, .claude, .codex)
./init.sh

# 只同步到 Claude
./init.sh --claude

# 只同步到 Codex
./init.sh --codex

# 同步到 canonical store
./init.sh --agents

# 同步到所有已知 agents
./init.sh --all

# 组合使用
./init.sh --claude --codex
```

### 高级选项

```bash
# 预览模式（不实际创建链接）
./init.sh --dry-run

# 强制覆盖已存在的目录/链接
./init.sh --force

# 预览强制模式
./init.sh --dry-run --force

# 组合使用
./init.sh --claude --codex --force
```

### 查看帮助

```bash
./init.sh --help
```

## 📋 支持的 Agents

| Agent | 目录 | 说明 |
|-------|------|------|
| `agents` | `~/.agents/skills` | Canonical user-level store (Codex/open-agent-skills 标准) |
| `claude` | `~/.claude/skills` | Claude Code |
| `codex` | `~/.codex/skills` | Codex |
| `codemaker` | `~/.codemaker/skills` | CodeMaker |
| `cursor` | `~/.cursor/skills` | Cursor |

**默认 agents**：`.agents`, `.claude`, `.codex`

## 🔍 工作原理

1. 扫描 `./skills/` 目录下的所有子目录（跳过隐藏目录）
2. 为每个 skill 在目标 agent 目录创建**绝对路径**符号链接
3. 智能处理冲突：
   - ✅ 如果 symlink 已存在且指向正确，跳过
   - ⚠️ 如果 symlink 指向其他位置，显示警告（`--force` 可覆盖）
   - ⚠️ 如果存在真实目录/文件，显示警告（`--force` 可覆盖）
4. 输出详细的统计信息

## ⚠️ Agent 缓存注意事项

`init.sh` 的职责只是把 skill 同步到目标目录。它**不会**：

- 热更新已经在 agent 会话里激活过的 skill 指令
- 清理 agent 自己的 skill 缓存或索引
- 改变 agent 运行时使用的工作目录（cwd）

这点对 `CodeMaker` 尤其重要：

- 已经激活过的 skill，通常会在激活时把 `SKILL.md` 内容快照进当前会话
- 即使你随后重新执行 `./init.sh --codemaker`，当前会话也可能继续使用旧快照
- 某次运行里的相对路径解析，仍然取决于 CodeMaker 当前打开的工程 / 会话 cwd，不取决于 `init.sh`

推荐做法：

```bash
# 1. 同步磁盘上的 skill
./init.sh --codemaker

# 2. 然后新开一个聊天，必要时重启 CodeMaker
```

如果你刚修改了 `SKILL.md`、workflow 或 template，看到行为没变，优先怀疑是 agent 会话缓存，而不是 symlink 没更新。

## 📊 输出示例

```bash
$ ./init.sh --claude --dry-run

[INFO] ======================================
[INFO] Skills Sync Script
[INFO] ======================================
[DRY-RUN] Running in DRY-RUN mode (no changes will be made)

[INFO] User Home: /Users/shenyeke01
[INFO] Source: /Users/shenyeke01/Documents/Workspace/skills/skills
[INFO] Target Agents: claude

[INFO] Found 16 skill(s):
  - brand-guidelines
  - claude-api
  - doc-coauthoring
  ...

[INFO] Processing: claude (/Users/shenyeke01/.claude/skills)
[DRY-RUN] Would create: brand-guidelines -> /Users/.../skills/brand-guidelines
[DRY-RUN] Would create: claude-api -> /Users/.../skills/claude-api
...

[INFO] Summary for claude:
[✓]   Created/OK: 16

[INFO] ======================================
[INFO] Overall Summary
[INFO] ======================================
[✓] Created/OK: 16

[INFO] This was a dry-run. Run without --dry-run to apply changes.
```

## 🛡️ 安全特性

- **默认跳过冲突**：不会意外覆盖已存在的文件/目录
- **Dry-run 模式**：可以先预览再执行
- **详细日志**：清晰显示每个操作的结果
- **绝对路径**：避免 symlink 解析问题
- **退出状态**：失败时返回非零退出码

## 💡 最佳实践

### 推荐工作流

```bash
# 1. 先预览
./init.sh --dry-run

# 2. 确认无误后执行
./init.sh

# 3. 如果有冲突需要覆盖
./init.sh --force
```

### 添加新的 Agent

编辑 `init.sh` 中的 `KNOWN_AGENTS` 配置：

```bash
declare -A KNOWN_AGENTS=(
    ["agents"]=".agents/skills"
    ["claude"]=".claude/skills"
    ["codex"]=".codex/skills"
    ["myagent"]=".myagent/skills"  # 添加新 agent
)
```

然后使用：

```bash
./init.sh --myagent
```

## 🔧 故障排查

### Windows 下创建 symlink 失败

**原因**：Windows 需要 Developer Mode 或管理员权限

**解决方案**：
1. 启用 Developer Mode：设置 → 更新和安全 → 开发者选项 → 开发人员模式
2. 或以管理员身份运行 Git Bash

### 链接已存在但指向错误位置

**现象**：
```
[!] Conflict: skill-name points to /other/path (use --force to override)
```

**解决方案**：
```bash
./init.sh --force
```

## 📚 设计理念

遵循 **open-agent-skills** 和 **Codex** 生态的最佳实践：

1. **Canonical Store 优先**：支持 `~/.agents/skills` 作为标准存储位置
2. **绝对路径 Symlink**：避免相对路径在嵌套 symlink 场景下的解析问题
3. **用户友好**：默认安全（跳过冲突），提供 `--force` 选项
4. **可观测性**：详细的日志和统计信息
5. **可扩展性**：易于添加新的 agent 支持

## 📝 技术说明

- **Bash 版本**：需要 Bash 4.0+ (支持关联数组)
- **依赖**：`find`, `ln`, `readlink`, `mkdir` (标准 Unix 工具)
- **测试环境**：macOS, Linux, Windows Git Bash

## 🙏 致谢

设计灵感来自：
- Vercel skills CLI 的 `--global`, `--agent`, `--copy` 设计
- Codex 的用户级 skills 发现机制
- open-agent-skills 的 canonical store 理念
