import test from "node:test";
import assert from "node:assert/strict";
import { promises as fs } from "node:fs";
import os from "node:os";
import path from "node:path";

import {
  STATE_FILE,
  __test,
  normalizeForCompare,
  syncSkills
} from "../scripts/sync-skills.mjs";

async function makeFixture() {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "skills sync test "));
  const sourceRoot = path.join(root, "repo with spaces", "skills");
  const homeDir = path.join(root, "home with spaces");
  await fs.mkdir(sourceRoot, { recursive: true });
  await fs.mkdir(homeDir, { recursive: true });

  return {
    root,
    sourceRoot,
    homeDir,
    async cleanup() {
      await fs.rm(root, { recursive: true, force: true });
    }
  };
}

async function makeSkill(sourceRoot, name, body = "") {
  const dir = path.join(sourceRoot, name);
  await fs.mkdir(dir, { recursive: true });
  await fs.writeFile(
    path.join(dir, "SKILL.md"),
    `---\nname: ${name}\ndescription: test skill\n---\n\n# ${name}\n${body}\n`,
    "utf8"
  );
  return dir;
}

async function makeNonSkill(sourceRoot, name) {
  const dir = path.join(sourceRoot, name);
  await fs.mkdir(dir, { recursive: true });
  await fs.writeFile(path.join(dir, "README.md"), "not a skill\n", "utf8");
  return dir;
}

async function exists(value) {
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

async function readState(homeDir, agent = "agents") {
  const statePath = path.join(homeDir, `.${agent}`, "skills", STATE_FILE);
  return JSON.parse(await fs.readFile(statePath, "utf8"));
}

async function createAgentRoot(homeDir, agent = "agents") {
  const root = path.join(homeDir, `.${agent}`);
  await fs.mkdir(root, { recursive: true });
  return root;
}

async function createAgentSkillsRoot(homeDir, agent = "agents") {
  const skillsRoot = path.join(await createAgentRoot(homeDir, agent), "skills");
  await fs.mkdir(skillsRoot, { recursive: true });
  return skillsRoot;
}

async function removeTarget(targetPath) {
  const stat = await fs.lstat(targetPath);
  if (stat.isSymbolicLink()) {
    await fs.unlink(targetPath);
  } else {
    await fs.rm(targetPath, { recursive: true, force: true });
  }
}

async function createSkillLink(sourcePath, targetPath) {
  await fs.symlink(sourcePath, targetPath, __test.linkModeForPlatform());
}

test("dry-run lists creates and does not write target directories or state", async () => {
  const fixture = await makeFixture();
  try {
    await createAgentRoot(fixture.homeDir, "agents");
    await makeSkill(fixture.sourceRoot, "alpha");
    await makeSkill(fixture.sourceRoot, "beta");
    await makeNonSkill(fixture.sourceRoot, "notes");

    const report = await syncSkills({
      homeDir: fixture.homeDir,
      sourceRoot: fixture.sourceRoot,
      dryRun: true
    });

    assert.equal(report.summary.validSkills, 2);
    assert.equal(report.summary.skippedSources, 1);
    assert.equal(report.summary.created, 2);
    assert.equal(await exists(path.join(fixture.homeDir, ".agents", "skills")), false);
  } finally {
    await fixture.cleanup();
  }
});

test("sync creates links, writes state, and is idempotent", async () => {
  const fixture = await makeFixture();
  try {
    await createAgentRoot(fixture.homeDir, "agents");
    await makeSkill(fixture.sourceRoot, "alpha");
    await makeSkill(fixture.sourceRoot, "beta");

    const first = await syncSkills({
      homeDir: fixture.homeDir,
      sourceRoot: fixture.sourceRoot
    });

    assert.equal(first.summary.created, 2);
    assert.equal(await exists(path.join(fixture.homeDir, ".agents", "skills", "alpha")), true);
    assert.equal(await exists(path.join(fixture.homeDir, ".agents", "skills", "beta")), true);

    const statePath = path.join(fixture.homeDir, ".agents", "skills", STATE_FILE);
    const stateText = await fs.readFile(statePath, "utf8");
    const state = JSON.parse(stateText);
    assert.deepEqual(Object.keys(state.entries), ["alpha", "beta"]);

    const second = await syncSkills({
      homeDir: fixture.homeDir,
      sourceRoot: fixture.sourceRoot
    });
    const stateTextAfter = await fs.readFile(statePath, "utf8");

    assert.equal(second.summary.created, 0);
    assert.equal(second.summary.alreadyOk, 2);
    assert.equal(stateTextAfter, stateText);
  } finally {
    await fixture.cleanup();
  }
});

test("managed stale skills are pruned when source skill is deleted", async () => {
  const fixture = await makeFixture();
  try {
    await createAgentRoot(fixture.homeDir, "agents");
    const alpha = await makeSkill(fixture.sourceRoot, "alpha");
    await makeSkill(fixture.sourceRoot, "beta");
    await syncSkills({ homeDir: fixture.homeDir, sourceRoot: fixture.sourceRoot });

    await fs.rm(alpha, { recursive: true, force: true });
    const report = await syncSkills({ homeDir: fixture.homeDir, sourceRoot: fixture.sourceRoot });
    const state = await readState(fixture.homeDir);

    assert.equal(report.summary.pruned, 1);
    assert.equal(await exists(path.join(fixture.homeDir, ".agents", "skills", "alpha")), false);
    assert.deepEqual(Object.keys(state.entries), ["beta"]);
  } finally {
    await fixture.cleanup();
  }
});

test("missing SKILL.md source directories are skipped", async () => {
  const fixture = await makeFixture();
  try {
    await createAgentRoot(fixture.homeDir, "agents");
    await makeSkill(fixture.sourceRoot, "alpha");
    await makeNonSkill(fixture.sourceRoot, "not-a-skill");

    const report = await syncSkills({ homeDir: fixture.homeDir, sourceRoot: fixture.sourceRoot });
    const state = await readState(fixture.homeDir);

    assert.equal(report.summary.skippedSources, 1);
    assert.equal(await exists(path.join(fixture.homeDir, ".agents", "skills", "not-a-skill")), false);
    assert.deepEqual(Object.keys(state.entries), ["alpha"]);
  } finally {
    await fixture.cleanup();
  }
});

test("unknown real target directory is reported as conflict and not replaced", async () => {
  const fixture = await makeFixture();
  try {
    const skillsRoot = await createAgentSkillsRoot(fixture.homeDir, "agents");
    await makeSkill(fixture.sourceRoot, "alpha");
    const target = path.join(skillsRoot, "alpha");
    await fs.mkdir(target, { recursive: true });
    await fs.writeFile(path.join(target, "local.txt"), "keep me\n", "utf8");

    const report = await syncSkills({ homeDir: fixture.homeDir, sourceRoot: fixture.sourceRoot });
    const state = await readState(fixture.homeDir);

    assert.equal(report.summary.conflicts, 1);
    assert.equal(await fs.readFile(path.join(target, "local.txt"), "utf8"), "keep me\n");
    assert.deepEqual(Object.keys(state.entries), []);
  } finally {
    await fixture.cleanup();
  }
});

test("existing links to this repo are adoptable by default and adopted with flag", async () => {
  const fixture = await makeFixture();
  try {
    const skillsRoot = await createAgentSkillsRoot(fixture.homeDir, "agents");
    const source = await makeSkill(fixture.sourceRoot, "alpha");
    const target = path.join(skillsRoot, "alpha");
    await createSkillLink(source, target);

    const first = await syncSkills({ homeDir: fixture.homeDir, sourceRoot: fixture.sourceRoot });
    let state = await readState(fixture.homeDir);

    assert.equal(first.summary.adoptable, 1);
    assert.deepEqual(Object.keys(state.entries), []);

    const second = await syncSkills({
      homeDir: fixture.homeDir,
      sourceRoot: fixture.sourceRoot,
      adoptLinks: true
    });
    state = await readState(fixture.homeDir);

    assert.equal(second.summary.adopted, 1);
    assert.deepEqual(Object.keys(state.entries), ["alpha"]);
  } finally {
    await fixture.cleanup();
  }
});

test("missing managed target is recreated and state is repaired", async () => {
  const fixture = await makeFixture();
  try {
    await createAgentRoot(fixture.homeDir, "agents");
    await makeSkill(fixture.sourceRoot, "alpha");
    await syncSkills({ homeDir: fixture.homeDir, sourceRoot: fixture.sourceRoot });

    const target = path.join(fixture.homeDir, ".agents", "skills", "alpha");
    await removeTarget(target);

    const report = await syncSkills({ homeDir: fixture.homeDir, sourceRoot: fixture.sourceRoot });

    assert.equal(report.summary.created, 1);
    assert.equal(await exists(target), true);
  } finally {
    await fixture.cleanup();
  }
});

test("no known agent roots exits cleanly without writes", async () => {
  const fixture = await makeFixture();
  try {
    await makeSkill(fixture.sourceRoot, "alpha");

    const report = await syncSkills({ homeDir: fixture.homeDir, sourceRoot: fixture.sourceRoot });

    assert.equal(report.summary.noTargets, 1);
    assert.equal(report.targets.length, 0);
    assert.equal(report.exitCode, 0);
  } finally {
    await fixture.cleanup();
  }
});

test("path normalization handles Windows case and spaces predictably", () => {
  assert.equal(
    normalizeForCompare("C:/Temp/Foo Bar/Skill", "win32"),
    normalizeForCompare("c:\\temp\\foo bar\\skill", "win32")
  );
  assert.notEqual(
    normalizeForCompare("/Tmp/Foo Bar/Skill", "linux"),
    normalizeForCompare("/tmp/foo bar/skill", "linux")
  );
});

test("init.sh is a Node wrapper with a clear missing-node guard", async () => {
  const init = await fs.readFile(path.resolve("init.sh"), "utf8");

  assert.match(init, /command -v node/);
  assert.match(init, /Node\.js is required/);
  assert.doesNotMatch(init, /rm\s+-rf/);
  assert.doesNotMatch(init, /\bkill\b/);
});
