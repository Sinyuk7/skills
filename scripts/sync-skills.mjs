#!/usr/bin/env node

import { promises as fs } from "node:fs";
import { existsSync } from "node:fs";
import crypto from "node:crypto";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const STATE_FILE = ".skills-sync-state.json";
export const MANAGER = "skills-sync";

const SCRIPT_PATH = fileURLToPath(import.meta.url);
const REPO_ROOT = path.resolve(path.dirname(SCRIPT_PATH), "..");

const KNOWN_AGENTS = [
  { name: "agents", rootDir: ".agents" },
  { name: "claude", rootDir: ".claude" },
  { name: "codemaker", rootDir: ".codemaker" },
  { name: "codex", rootDir: ".codex" },
  { name: "gemini", rootDir: ".gemini" },
  { name: "opencode", rootDir: ".opencode" },
  { name: "cursor", rootDir: ".cursor" }
];

const LEGACY_AGENT_FLAGS = new Map(
  KNOWN_AGENTS.map((agent) => [`--${agent.name}`, agent.name])
);

function usage() {
  return `Skills Sync

USAGE:
  node scripts/sync-skills.mjs sync [options]
  npm run sync -- [options]

OPTIONS:
  --dry-run              Print planned actions without writing files
  --agent <name>         Sync only one target agent; can be repeated
  --replace-managed      Recreate conflicting entries already recorded in state
  --adopt-links          Adopt existing links/junctions that point at this repo
  --prune <mode>         managed (default), report, or off
  --skill <name>         Sync only one source skill; can be repeated
  --home <path>          Override HOME for testing
  --source-root <path>   Override source skills directory for testing
  --help                 Show this help

KNOWN AGENTS:
  ${KNOWN_AGENTS.map((agent) => agent.name).join(", ")}
`;
}

export function parseArgs(argv) {
  const args = [...argv];
  const options = {
    command: "sync",
    dryRun: false,
    selectedAgents: [],
    replaceManaged: false,
    adoptLinks: false,
    pruneMode: "managed",
    homeDir: os.homedir(),
    sourceRoot: path.join(REPO_ROOT, "skills"),
    skillFilters: [],
    allExistingAgents: false,
    help: false
  };

  if (args[0] === "sync") {
    args.shift();
  } else if (args[0] && !args[0].startsWith("-")) {
    throw new Error(`Unknown command: ${args[0]}`);
  }

  while (args.length > 0) {
    const arg = args.shift();

    if (arg === "--help" || arg === "-h") {
      options.help = true;
      continue;
    }

    if (arg === "--dry-run") {
      options.dryRun = true;
      continue;
    }

    if (arg === "--replace-managed") {
      options.replaceManaged = true;
      continue;
    }

    if (arg === "--adopt-links") {
      options.adoptLinks = true;
      continue;
    }

    if (arg === "--all") {
      options.allExistingAgents = true;
      continue;
    }

    if (LEGACY_AGENT_FLAGS.has(arg)) {
      options.selectedAgents.push(LEGACY_AGENT_FLAGS.get(arg));
      continue;
    }

    if (arg === "--agent") {
      const value = args.shift();
      if (!value || value.startsWith("-")) {
        throw new Error("--agent requires a value");
      }
      options.selectedAgents.push(value);
      continue;
    }

    if (arg?.startsWith("--agent=")) {
      const value = arg.slice("--agent=".length);
      if (!value) {
        throw new Error("--agent requires a value");
      }
      options.selectedAgents.push(value);
      continue;
    }

    if (arg === "--skill") {
      const value = args.shift();
      if (!value || value.startsWith("-")) {
        throw new Error("--skill requires a value");
      }
      options.skillFilters.push(value);
      continue;
    }

    if (arg?.startsWith("--skill=")) {
      const value = arg.slice("--skill=".length);
      if (!value) {
        throw new Error("--skill requires a value");
      }
      options.skillFilters.push(value);
      continue;
    }

    if (arg === "--prune") {
      const value = args.shift();
      if (!value || value.startsWith("-")) {
        throw new Error("--prune requires managed, report, or off");
      }
      options.pruneMode = parsePruneMode(value);
      continue;
    }

    if (arg?.startsWith("--prune=")) {
      options.pruneMode = parsePruneMode(arg.slice("--prune=".length));
      continue;
    }

    if (arg === "--home") {
      const value = args.shift();
      if (!value || value.startsWith("-")) {
        throw new Error("--home requires a path");
      }
      options.homeDir = value;
      continue;
    }

    if (arg?.startsWith("--home=")) {
      options.homeDir = arg.slice("--home=".length);
      continue;
    }

    if (arg === "--source-root") {
      const value = args.shift();
      if (!value || value.startsWith("-")) {
        throw new Error("--source-root requires a path");
      }
      options.sourceRoot = value;
      continue;
    }

    if (arg?.startsWith("--source-root=")) {
      options.sourceRoot = arg.slice("--source-root=".length);
      continue;
    }

    throw new Error(`Unknown option: ${arg}`);
  }

  options.homeDir = path.resolve(options.homeDir);
  options.sourceRoot = path.resolve(options.sourceRoot);
  options.selectedAgents = dedupe(options.selectedAgents);
  options.skillFilters = dedupe(options.skillFilters);
  return options;
}

function parsePruneMode(value) {
  if (!["managed", "report", "off"].includes(value)) {
    throw new Error("--prune must be managed, report, or off");
  }
  return value;
}

function dedupe(values) {
  return [...new Set(values)];
}

export function normalizeForCompare(value, platform = process.platform) {
  if (platform === "win32") {
    return path.win32.normalize(value).replaceAll("/", "\\").toLowerCase();
  }
  return path.posix.normalize(value.replaceAll("\\", "/"));
}

function samePath(left, right) {
  return normalizeForCompare(left) === normalizeForCompare(right);
}

async function pathExists(value) {
  try {
    await fs.lstat(value);
    return true;
  } catch (error) {
    if (error.code === "ENOENT") {
      return false;
    }
    throw error;
  }
}

async function realpathOrResolve(value) {
  try {
    return await fs.realpath(value);
  } catch {
    return path.resolve(value);
  }
}

async function sameRealPath(left, right) {
  const [leftReal, rightReal] = await Promise.all([
    realpathOrResolve(left),
    realpathOrResolve(right)
  ]);
  return samePath(leftReal, rightReal);
}

function isWithin(child, parent) {
  const relative = path.relative(parent, child);
  return relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative));
}

function linkModeForPlatform(platform = process.platform) {
  return platform === "win32" ? "junction" : "dir";
}

async function hashTree(rootDir) {
  const hash = crypto.createHash("sha256");

  async function walk(currentDir, relativeDir) {
    const entries = await fs.readdir(currentDir, { withFileTypes: true });
    entries.sort((left, right) => left.name.localeCompare(right.name));

    for (const entry of entries) {
      const absolutePath = path.join(currentDir, entry.name);
      const relativePath = path.join(relativeDir, entry.name).replaceAll("\\", "/");

      if (entry.isDirectory()) {
        hash.update(`dir\0${relativePath}\0`);
        await walk(absolutePath, relativePath);
      } else if (entry.isSymbolicLink()) {
        const target = await fs.readlink(absolutePath);
        hash.update(`link\0${relativePath}\0${target}\0`);
      } else if (entry.isFile()) {
        const content = await fs.readFile(absolutePath);
        hash.update(`file\0${relativePath}\0`);
        hash.update(content);
        hash.update("\0");
      }
    }
  }

  await walk(rootDir, "");
  return hash.digest("hex");
}

async function scanSkills(sourceRoot, skillFilters = []) {
  if (!(await pathExists(sourceRoot))) {
    throw new Error(`Source skills directory does not exist: ${sourceRoot}`);
  }

  const filterSet = new Set(skillFilters);
  const entries = await fs.readdir(sourceRoot, { withFileTypes: true });
  entries.sort((left, right) => left.name.localeCompare(right.name));

  const skills = [];
  const skipped = [];
  const seen = new Set();

  for (const entry of entries) {
    const name = entry.name;
    if (name.startsWith(".")) {
      continue;
    }

    const absolutePath = path.join(sourceRoot, name);
    let stat;
    try {
      stat = await fs.stat(absolutePath);
    } catch {
      skipped.push({ name, reason: "unreadable" });
      continue;
    }

    if (!stat.isDirectory()) {
      continue;
    }

    seen.add(name);
    if (filterSet.size > 0 && !filterSet.has(name)) {
      continue;
    }

    const skillFile = path.join(absolutePath, "SKILL.md");
    if (!(await pathExists(skillFile))) {
      skipped.push({ name, reason: "missing SKILL.md" });
      continue;
    }

    skills.push({
      name,
      sourcePath: path.resolve(absolutePath),
      treeHash: await hashTree(absolutePath)
    });
  }

  const missingRequested = skillFilters.filter((name) => !seen.has(name));
  if (missingRequested.length > 0) {
    throw new Error(`Requested skill(s) not found: ${missingRequested.join(", ")}`);
  }

  return { skills, skipped };
}

function knownAgentByName(name) {
  return KNOWN_AGENTS.find((agent) => agent.name === name);
}

async function discoverTargets(options) {
  const selected = options.selectedAgents;
  const targets = [];

  if (selected.length > 0) {
    for (const name of selected) {
      const agent = knownAgentByName(name);
      if (!agent) {
        throw new Error(`Unknown agent: ${name}`);
      }
      targets.push(buildTarget(options.homeDir, agent, true));
    }
    return targets;
  }

  for (const agent of KNOWN_AGENTS) {
    const root = path.join(options.homeDir, agent.rootDir);
    if (existsSync(root)) {
      targets.push(buildTarget(options.homeDir, agent, false));
    }
  }

  return targets;
}

function buildTarget(homeDir, agent, explicit) {
  const root = path.join(homeDir, agent.rootDir);
  return {
    name: agent.name,
    explicit,
    root,
    skillsRoot: path.join(root, "skills"),
    statePath: path.join(root, "skills", STATE_FILE)
  };
}

function initialState(sourceRoot) {
  return {
    version: 1,
    manager: MANAGER,
    sourceRoot,
    entries: {}
  };
}

async function readState(target, sourceRoot) {
  if (!(await pathExists(target.statePath))) {
    return initialState(sourceRoot);
  }

  const raw = await fs.readFile(target.statePath, "utf8");
  let state;
  try {
    state = JSON.parse(raw);
  } catch (error) {
    throw new Error(`Invalid state JSON at ${target.statePath}: ${error.message}`);
  }

  if (state.manager !== MANAGER || state.version !== 1 || typeof state.entries !== "object") {
    throw new Error(`Unsupported state file at ${target.statePath}`);
  }

  if (!samePath(path.resolve(state.sourceRoot), sourceRoot)) {
    throw new Error(
      `State file at ${target.statePath} belongs to a different source root: ${state.sourceRoot}`
    );
  }

  return state;
}

function canonicalState(state) {
  const entries = {};
  for (const name of Object.keys(state.entries).sort()) {
    const entry = state.entries[name];
    entries[name] = {
      source: entry.source,
      target: entry.target,
      mode: entry.mode,
      treeHash: entry.treeHash
    };
  }

  return {
    version: 1,
    manager: MANAGER,
    sourceRoot: state.sourceRoot,
    entries
  };
}

async function writeStateIfChanged(target, state, dryRun) {
  const canonical = canonicalState(state);
  const next = `${JSON.stringify(canonical, null, 2)}\n`;
  let previous = null;

  if (await pathExists(target.statePath)) {
    previous = await fs.readFile(target.statePath, "utf8");
  }

  if (previous === next) {
    return false;
  }

  if (!dryRun) {
    await fs.mkdir(target.skillsRoot, { recursive: true });
    await fs.writeFile(target.statePath, next, "utf8");
  }

  return true;
}

async function inspectTarget(targetPath) {
  try {
    const stat = await fs.lstat(targetPath);
    return {
      exists: true,
      isLink: stat.isSymbolicLink(),
      isDirectory: stat.isDirectory(),
      isFile: stat.isFile()
    };
  } catch (error) {
    if (error.code === "ENOENT") {
      return { exists: false };
    }
    throw error;
  }
}

async function isLinkToSource(targetPath, sourcePath) {
  return (await pathExists(targetPath)) && (await sameRealPath(targetPath, sourcePath));
}

async function createSkillLink(sourcePath, targetPath, mode) {
  await fs.mkdir(path.dirname(targetPath), { recursive: true });
  await fs.symlink(sourcePath, targetPath, mode);
}

async function removeLinkOrManagedTarget(targetPath, allowDirectory) {
  const info = await inspectTarget(targetPath);
  if (!info.exists) {
    return;
  }

  if (info.isLink) {
    await fs.unlink(targetPath);
    return;
  }

  if (allowDirectory) {
    await fs.rm(targetPath, { recursive: true, force: true });
    return;
  }

  throw new Error(`Refusing to remove non-link target: ${targetPath}`);
}

function desiredStateEntry(skill, targetPath, mode) {
  return {
    source: skill.sourcePath,
    target: targetPath,
    mode,
    treeHash: skill.treeHash
  };
}

function stateEntryMatches(entry, desired) {
  return (
    entry &&
    samePath(entry.source, desired.source) &&
    samePath(entry.target, desired.target) &&
    entry.mode === desired.mode &&
    entry.treeHash === desired.treeHash
  );
}

function makeReport(options, sourceRoot) {
  return {
    dryRun: options.dryRun,
    sourceRoot,
    skippedSourceDirs: [],
    targets: [],
    actions: [],
    summary: {
      validSkills: 0,
      skippedSources: 0,
      targets: 0,
      created: 0,
      recreated: 0,
      alreadyOk: 0,
      adopted: 0,
      adoptable: 0,
      pruned: 0,
      pruneReported: 0,
      conflicts: 0,
      stateUpdated: 0,
      failed: 0,
      noTargets: 0
    },
    exitCode: 0
  };
}

function addAction(report, action) {
  report.actions.push(action);

  switch (action.action) {
    case "create":
      report.summary.created += 1;
      break;
    case "recreate":
      report.summary.recreated += 1;
      break;
    case "already-ok":
      report.summary.alreadyOk += 1;
      break;
    case "adopted":
      report.summary.adopted += 1;
      break;
    case "adoptable":
      report.summary.adoptable += 1;
      break;
    case "prune":
      report.summary.pruned += 1;
      break;
    case "prune-report":
      report.summary.pruneReported += 1;
      break;
    case "conflict":
      report.summary.conflicts += 1;
      break;
    case "state-update":
      report.summary.stateUpdated += 1;
      break;
    case "failed":
      report.summary.failed += 1;
      report.exitCode = 1;
      break;
  }
}

export async function syncSkills(rawOptions = {}) {
  const options = {
    dryRun: false,
    selectedAgents: [],
    replaceManaged: false,
    adoptLinks: false,
    pruneMode: "managed",
    homeDir: os.homedir(),
    sourceRoot: path.join(REPO_ROOT, "skills"),
    skillFilters: [],
    ...rawOptions
  };

  options.homeDir = path.resolve(options.homeDir);
  options.sourceRoot = path.resolve(options.sourceRoot);

  const sourceRoot = await realpathOrResolve(options.sourceRoot);
  const report = makeReport(options, sourceRoot);
  const { skills, skipped } = await scanSkills(sourceRoot, options.skillFilters);
  const skillMap = new Map(skills.map((skill) => [skill.name, skill]));
  const targets = await discoverTargets(options);

  report.skippedSourceDirs = skipped;
  report.summary.validSkills = skills.length;
  report.summary.skippedSources = skipped.length;
  report.targets = targets.map((target) => ({
    name: target.name,
    root: target.root,
    skillsRoot: target.skillsRoot
  }));
  report.summary.targets = targets.length;

  if (targets.length === 0) {
    report.summary.noTargets = 1;
    addAction(report, {
      action: "no-targets",
      reason: "No known agent roots found under HOME"
    });
    return report;
  }

  for (const target of targets) {
    await syncTarget({ options, sourceRoot, skills, skillMap, target, report });
  }

  return report;
}

async function syncTarget({ options, sourceRoot, skills, skillMap, target, report }) {
  if (!(await pathExists(target.skillsRoot))) {
    addAction(report, {
      action: "ensure-target",
      agent: target.name,
      targetRoot: target.skillsRoot,
      dryRun: options.dryRun
    });

    if (!options.dryRun) {
      await fs.mkdir(target.skillsRoot, { recursive: true });
    }
  }

  const state = await readState(target, sourceRoot);
  const mode = linkModeForPlatform();
  let stateTouched = false;

  for (const name of Object.keys(state.entries).sort()) {
    if (skillMap.has(name)) {
      continue;
    }

    const entry = state.entries[name];
    const targetPath = path.resolve(entry.target);

    if (!isWithin(targetPath, target.skillsRoot)) {
      addAction(report, {
        action: "conflict",
        agent: target.name,
        skill: name,
        target: targetPath,
        reason: "Managed state target is outside target root"
      });
      continue;
    }

    if (options.pruneMode === "off") {
      continue;
    }

    if (options.pruneMode === "report") {
      addAction(report, {
        action: "prune-report",
        agent: target.name,
        skill: name,
        target: targetPath,
        reason: "Source skill no longer exists"
      });
      continue;
    }

    try {
      if (!options.dryRun) {
        await removeLinkOrManagedTarget(targetPath, false);
      }
      delete state.entries[name];
      stateTouched = true;
      addAction(report, {
        action: "prune",
        agent: target.name,
        skill: name,
        target: targetPath,
        reason: "Source skill no longer exists"
      });
    } catch (error) {
      addAction(report, {
        action: "failed",
        agent: target.name,
        skill: name,
        target: targetPath,
        reason: error.message
      });
    }
  }

  for (const skill of skills) {
    const targetPath = path.join(target.skillsRoot, skill.name);
    const desired = desiredStateEntry(skill, targetPath, mode);
    const existing = await inspectTarget(targetPath);
    const managedEntry = state.entries[skill.name];

    if (!existing.exists) {
      if (!options.dryRun) {
        try {
          await createSkillLink(skill.sourcePath, targetPath, mode);
        } catch (error) {
          addAction(report, {
            action: "failed",
            agent: target.name,
            skill: skill.name,
            target: targetPath,
            reason: `Failed to create ${mode}: ${error.message}`
          });
          continue;
        }
      }

      state.entries[skill.name] = desired;
      stateTouched = true;
      addAction(report, {
        action: "create",
        agent: target.name,
        skill: skill.name,
        target: targetPath,
        source: skill.sourcePath,
        mode
      });
      continue;
    }

    if (managedEntry) {
      if (await isLinkToSource(targetPath, skill.sourcePath)) {
        if (!stateEntryMatches(managedEntry, desired)) {
          state.entries[skill.name] = desired;
          stateTouched = true;
          addAction(report, {
            action: "state-update",
            agent: target.name,
            skill: skill.name,
            target: targetPath,
            reason: "Managed link is correct but state metadata changed"
          });
        } else {
          addAction(report, {
            action: "already-ok",
            agent: target.name,
            skill: skill.name,
            target: targetPath
          });
        }
        continue;
      }

      if (options.replaceManaged) {
        if (!options.dryRun) {
          try {
            await removeLinkOrManagedTarget(targetPath, true);
            await createSkillLink(skill.sourcePath, targetPath, mode);
          } catch (error) {
            addAction(report, {
              action: "failed",
              agent: target.name,
              skill: skill.name,
              target: targetPath,
              reason: `Failed to recreate managed target: ${error.message}`
            });
            continue;
          }
        }

        state.entries[skill.name] = desired;
        stateTouched = true;
        addAction(report, {
          action: "recreate",
          agent: target.name,
          skill: skill.name,
          target: targetPath,
          source: skill.sourcePath,
          mode
        });
      } else {
        addAction(report, {
          action: "conflict",
          agent: target.name,
          skill: skill.name,
          target: targetPath,
          reason: "Managed target no longer points to expected source; use --replace-managed"
        });
      }
      continue;
    }

    if (existing.isLink && (await isLinkToSource(targetPath, skill.sourcePath))) {
      if (options.adoptLinks) {
        state.entries[skill.name] = desired;
        stateTouched = true;
        addAction(report, {
          action: "adopted",
          agent: target.name,
          skill: skill.name,
          target: targetPath,
          source: skill.sourcePath,
          mode
        });
      } else {
        addAction(report, {
          action: "adoptable",
          agent: target.name,
          skill: skill.name,
          target: targetPath,
          reason: "Existing link points to this repo; rerun with --adopt-links to manage it"
        });
      }
      continue;
    }

    addAction(report, {
      action: "conflict",
      agent: target.name,
      skill: skill.name,
      target: targetPath,
      reason: existing.isLink
        ? "Existing link points somewhere else"
        : "Existing non-managed directory or file"
    });
  }

  const wroteState = await writeStateIfChanged(target, state, options.dryRun);
  if (wroteState || stateTouched) {
    addAction(report, {
      action: "state-written",
      agent: target.name,
      target: target.statePath,
      dryRun: options.dryRun
    });
  }
}

function printReport(report) {
  console.log("");
  console.log("Skills Sync");
  console.log(`  Source: ${report.sourceRoot}`);
  console.log(`  Mode: ${report.dryRun ? "dry-run" : "apply"}`);
  console.log(`  Valid skills: ${report.summary.validSkills}`);

  if (report.skippedSourceDirs.length > 0) {
    console.log("  Skipped source dirs:");
    for (const skipped of report.skippedSourceDirs) {
      console.log(`    - ${skipped.name}: ${skipped.reason}`);
    }
  }

  if (report.targets.length === 0) {
    console.log("  Targets: none");
  } else {
    console.log("  Targets:");
    for (const target of report.targets) {
      console.log(`    - ${target.name}: ${target.skillsRoot}`);
    }
  }

  console.log("");
  for (const action of report.actions) {
    console.log(formatAction(action));
  }

  console.log("");
  console.log(
    [
      `created=${report.summary.created}`,
      `recreated=${report.summary.recreated}`,
      `alreadyOk=${report.summary.alreadyOk}`,
      `adopted=${report.summary.adopted}`,
      `adoptable=${report.summary.adoptable}`,
      `pruned=${report.summary.pruned}`,
      `pruneReported=${report.summary.pruneReported}`,
      `conflicts=${report.summary.conflicts}`,
      `stateUpdated=${report.summary.stateUpdated}`,
      `failed=${report.summary.failed}`
    ].join(" ")
  );
  console.log("");
}

function formatAction(action) {
  const agent = action.agent ? `[${action.agent}] ` : "";
  const skill = action.skill ? `${action.skill}: ` : "";

  switch (action.action) {
    case "ensure-target":
      return `${agent}ensure target ${action.targetRoot}${action.dryRun ? " (dry-run)" : ""}`;
    case "create":
      return `${agent}${skill}create ${action.mode} -> ${action.target}`;
    case "recreate":
      return `${agent}${skill}recreate managed ${action.mode} -> ${action.target}`;
    case "already-ok":
      return `${agent}${skill}already ok`;
    case "adopted":
      return `${agent}${skill}adopt existing link`;
    case "adoptable":
      return `${agent}${skill}adoptable - ${action.reason}`;
    case "prune":
      return `${agent}${skill}prune stale managed target`;
    case "prune-report":
      return `${agent}${skill}would prune stale managed target`;
    case "state-update":
      return `${agent}${skill}update state metadata`;
    case "state-written":
      return `${agent}write state ${action.target}${action.dryRun ? " (dry-run)" : ""}`;
    case "conflict":
      return `${agent}${skill}conflict - ${action.reason}: ${action.target}`;
    case "failed":
      return `${agent}${skill}failed - ${action.reason}`;
    case "no-targets":
      return `no targets found - ${action.reason}`;
    default:
      return JSON.stringify(action);
  }
}

export async function main(argv = process.argv.slice(2)) {
  const options = parseArgs(argv);
  if (options.help) {
    console.log(usage());
    return 0;
  }

  const report = await syncSkills(options);
  printReport(report);
  return report.exitCode;
}

if (process.argv[1] && samePath(fileURLToPath(import.meta.url), path.resolve(process.argv[1]))) {
  main()
    .then((exitCode) => {
      process.exitCode = exitCode;
    })
    .catch((error) => {
      console.error(`skills-sync: ${error.message}`);
      process.exitCode = 1;
    });
}

export const __test = {
  KNOWN_AGENTS,
  linkModeForPlatform,
  hashTree,
  scanSkills,
  discoverTargets
};
