# Skills Sync

这个仓库使用 Node-first 同步器把 `./skills` 下的有效 skill 同步到本机已存在的 agent 用户目录。主入口是：

```bash
npm run sync
```

`init.sh` 只保留为兼容 wrapper，内部调用同一个 Node 同步器，不再包含 Bash 版同步、删除或杀进程逻辑。

## 默认行为

- 自动扫描 `$HOME` 下已存在的 agent 根目录：`.agents`、`.claude`、`.codemaker`、`.codex`、`.gemini`、`.opencode`、`.cursor`。
- 为每个已存在的 agent 根目录创建 `<agent>/skills` 子目录。
- 只同步包含 `SKILL.md` 的目录；没有 `SKILL.md` 的目录会被跳过并报告。
- Windows 使用 directory junction，macOS/Linux 使用 directory symlink。
- 每个目标 `skills` 目录写入 `.skills-sync-state.json`，记录本仓库托管的 skill。
- 默认只删除 state 中证明由本仓库托管、但源仓库已删除的 stale skill。
- 未托管的同名目录、文件或指向其他位置的链接默认只报告 conflict，不覆盖、不删除。
- 已存在且指向本仓库的旧链接默认报告为 adoptable；传 `--adopt-links` 后才纳入 state。

Codex/OpenAI 生态的主目标是 `~/.agents/skills`；如果 `~/.codex` 已存在，同步器会把 `~/.codex/skills` 作为兼容目标处理。

## 常用命令

```bash
# 同步到自动发现的已有 agent 目标
npm run sync

# 预览，不写文件
npm run sync:dry-run
npm run sync -- --dry-run

# 只同步到指定 agent
npm run sync -- --agent agents
npm run sync -- --agent claude --agent agents

# 只同步指定 skill
npm run sync -- --skill skill-creator

# 认领已经指向本仓库的旧 symlink/junction
npm run sync -- --adopt-links

# 只报告 stale managed skill，不删除
npm run sync -- --prune report

# 重建 state 中已托管但目标异常的条目
npm run sync -- --replace-managed

# 运行测试
npm test
```

`init.sh` 仍可用于旧习惯：

```bash
./init.sh --dry-run
./init.sh --agent agents
```

## 安全模型

同步器只会自动删除满足全部条件的目标：

1. 目标记录在 `.skills-sync-state.json` 中。
2. state 的 `sourceRoot` 是当前仓库的 `skills` 目录。
3. 源仓库中对应 skill 已不存在。
4. 目标路径位于当前 agent 的 `skills` 目录下。
5. 目标是 symlink/junction，而不是真实目录。

真实目录或未知链接不会被默认删除。需要修复托管项时使用 `--replace-managed`；非托管冲突需要人工处理。

## Agent 缓存限制

同步器只更新磁盘文件，不会热更新已经激活的 agent 会话：

- 已激活 skill 的说明可能已被 agent 快照到当前会话。
- 修改 `SKILL.md` 后，如果行为没变，优先新开会话或重启对应 agent。
- 同步器不会 kill CodeMaker、Qzhddr 或其他后台进程。

## 设计说明

旧 Bash 脚本依赖 `ln -s`、Git Bash/WSL 或管理员权限，在 Windows 上很容易失效。新同步器把跨平台路径、junction/symlink、状态文件、managed prune 和 dry-run 都放到 Node CLI 中，保证一个入口在 Windows 和 macOS 上保持一致。
