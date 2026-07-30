// Runs on extension uninstall, outside VS Code, with no access to the extension API.
// It removes only the skill directories recorded in the manifest that extension.js wrote,
// so a skill the user authored or installed elsewhere survives.

const fs = require('fs');
const os = require('os');
const path = require('path');

const MANIFEST = path.join(os.homedir(), '.copilot', '.daodan-installed.json');

try {
  const manifest = JSON.parse(fs.readFileSync(MANIFEST, 'utf8'));
  const location = manifest.location || path.join(os.homedir(), '.copilot', 'skills');
  for (const name of manifest.skills || []) {
    fs.rmSync(path.join(location, name), { recursive: true, force: true });
  }
  fs.rmSync(MANIFEST, { force: true });
} catch {
  // No manifest means nothing was installed, or a previous uninstall already cleaned up.
}
