const fs = require('fs');
const os = require('os');
const path = require('path');
const vscode = require('vscode');

// Agents and prompts reach Copilot through the chatAgents and chatPromptFiles contribution
// points in package.json. Skills cannot: 50 of the 71 carry supporting files under
// references/, scripts/ and assets/, and a contributed skill loads only its SKILL.md
// (microsoft/vscode#304721). So whole skill directories are copied into the personal skills
// location instead, which VS Code reads in every workspace.

const MANIFEST = path.join(os.homedir(), '.copilot', '.daodan-installed.json');

function defaultLocation() {
  return path.join(os.homedir(), '.copilot', 'skills');
}

function targetLocation() {
  const configured = vscode.workspace.getConfiguration('daodan').get('skillsLocation', '').trim();
  if (!configured) return defaultLocation();
  if (configured.startsWith('~')) return path.join(os.homedir(), configured.slice(1));
  return path.resolve(configured);
}

function readManifest() {
  try {
    return JSON.parse(fs.readFileSync(MANIFEST, 'utf8'));
  } catch {
    return { version: null, location: null, skills: [] };
  }
}

function writeManifest(data) {
  fs.mkdirSync(path.dirname(MANIFEST), { recursive: true });
  fs.writeFileSync(MANIFEST, JSON.stringify(data, null, 2) + '\n', 'utf8');
}

// Every <bundle>/.github/skills/<name>/ directory shipped inside the extension.
function bundledSkills(root) {
  const found = [];
  for (const bundle of fs.readdirSync(root, { withFileTypes: true })) {
    if (!bundle.isDirectory()) continue;
    const dir = path.join(root, bundle.name, '.github', 'skills');
    if (!fs.existsSync(dir)) continue;
    for (const skill of fs.readdirSync(dir, { withFileTypes: true })) {
      if (!skill.isDirectory()) continue;
      if (!fs.existsSync(path.join(dir, skill.name, 'SKILL.md'))) continue;
      found.push({ name: skill.name, source: path.join(dir, skill.name) });
    }
  }
  return found.sort((a, b) => a.name.localeCompare(b.name));
}

function upToDate(version, location, skills) {
  const previous = readManifest();
  if (previous.version !== version || previous.location !== location) return false;
  return skills.every((s) => fs.existsSync(path.join(location, s.name, 'SKILL.md')));
}

// A directory we did not install is someone else's skill. Leave it alone and report it.
function sync(root, version) {
  const location = targetLocation();
  const skills = bundledSkills(root);
  const owned = new Set(readManifest().skills || []);
  const installed = [];
  const conflicts = [];

  fs.mkdirSync(location, { recursive: true });

  for (const skill of skills) {
    const dest = path.join(location, skill.name);
    if (fs.existsSync(dest) && !owned.has(skill.name)) {
      conflicts.push(skill.name);
      continue;
    }
    fs.rmSync(dest, { recursive: true, force: true });
    fs.cpSync(skill.source, dest, { recursive: true });
    installed.push(skill.name);
  }

  // Drop what we installed previously and no longer ship.
  const current = new Set(installed);
  for (const stale of owned) {
    if (current.has(stale) || conflicts.includes(stale)) continue;
    fs.rmSync(path.join(location, stale), { recursive: true, force: true });
  }

  writeManifest({ version, location, skills: installed });
  return { location, installed, conflicts };
}

function remove() {
  const manifest = readManifest();
  const location = manifest.location || defaultLocation();
  for (const name of manifest.skills || []) {
    fs.rmSync(path.join(location, name), { recursive: true, force: true });
  }
  fs.rmSync(MANIFEST, { force: true });
  return { location, removed: (manifest.skills || []).length };
}

function report({ location, installed, conflicts }, { silent }) {
  if (conflicts.length) {
    vscode.window.showWarningMessage(
      `Daodan: installed ${installed.length} skills into ${location}. ` +
        `Skipped ${conflicts.length} already present and not installed by this extension: ` +
        conflicts.join(', ')
    );
    return;
  }
  if (silent) return;
  vscode.window.showInformationMessage(
    `Daodan: ${installed.length} skills available in every workspace, from ${location}.`
  );
}

function activate(context) {
  const root = context.extensionPath;
  const version = context.extension.packageJSON.version;

  const run = (silent) => {
    try {
      report(sync(root, version), { silent });
    } catch (error) {
      vscode.window.showErrorMessage(`Daodan: could not install skills. ${error.message}`);
    }
  };

  context.subscriptions.push(
    vscode.commands.registerCommand('daodan.syncSkills', () => run(false)),
    vscode.commands.registerCommand('daodan.removeSkills', () => {
      try {
        const { location, removed } = remove();
        vscode.window.showInformationMessage(`Daodan: removed ${removed} skills from ${location}.`);
      } catch (error) {
        vscode.window.showErrorMessage(`Daodan: could not remove skills. ${error.message}`);
      }
    }),
    vscode.commands.registerCommand('daodan.openSkillsFolder', () =>
      vscode.commands.executeCommand('revealFileInOS', vscode.Uri.file(targetLocation()))
    )
  );

  if (!vscode.workspace.getConfiguration('daodan').get('autoSync', true)) return;

  const location = targetLocation();
  const firstRun = readManifest().version === null;
  if (upToDate(version, location, bundledSkills(root))) return;
  run(!firstRun);
}

function deactivate() {}

module.exports = { activate, deactivate };
