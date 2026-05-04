/**
 *
 * @module utils
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync, spawnSync } = require('child_process');

const isWindows = process.platform === 'win32';
const isMacOS = process.platform === 'darwin';
const isLinux = process.platform === 'linux';

/**
 */
function getHomeDir() {
  return os.homedir();
}

/**
 */
function ensureDir(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
  return dirPath;
}

/**
 */
function commandExists(cmd) {
  if (!/^[a-zA-Z0-9_.-]+$/.test(cmd)) {
    return false;
  }

  try {
    if (isWindows) {
      const result = spawnSync('where', [cmd], { stdio: 'pipe' });
      return result.status === 0;
    } else {
      const result = spawnSync('which', [cmd], { stdio: 'pipe' });
      return result.status === 0;
    }
  } catch {
    return false;
  }
}

/**
 */
function runCommand(cmd, options = {}) {
  try {
    const result = execSync(cmd, {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
      ...options
    });
    return { success: true, output: result.trim() };
  } catch (err) {
    return {
      success: false,
      output: err.stdout || '',
      error: err.stderr || err.message
    };
  }
}

/**
 */
function getClaudeConfigDir() {
  const homeDir = getHomeDir();
  return path.join(homeDir, '.claude');
}

/**
 */
function getProjectRoot(startDir = process.cwd()) {
  let currentDir = startDir;

  while (currentDir !== path.parse(currentDir).root) {
    const pluginDir = path.join(currentDir, '.claude-plugin');
    if (fs.existsSync(pluginDir)) {
      return currentDir;
    }

    const packageJson = path.join(currentDir, 'package.json');
    if (fs.existsSync(packageJson)) {
      return currentDir;
    }

    currentDir = path.dirname(currentDir);
  }

  return null;
}

/**
 */
function joinPath(...paths) {
  return path.join(...paths);
}

/**
 */
function resolvePath(...paths) {
  return path.resolve(...paths);
}

/**
 */
function normalizePath(filePath) {
  return path.normalize(filePath);
}

/**
 */
function readJSON(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    return JSON.parse(content);
  } catch {
    return null;
  }
}

/**
 */
function writeJSON(filePath, data, space = 2) {
  try {
    ensureDir(path.dirname(filePath));
    fs.writeFileSync(filePath, JSON.stringify(data, null, space), 'utf8');
    return true;
  } catch {
    return false;
  }
}

/**
 */
function copyFile(src, dest) {
  try {
    ensureDir(path.dirname(dest));
    fs.copyFileSync(src, dest);
    return true;
  } catch {
    return false;
  }
}

/**
 */
function getPlatformInfo() {
  return {
    platform: process.platform,
    isWindows,
    isMacOS,
    isLinux,
    arch: process.arch,
    nodeVersion: process.version,
    homeDir: getHomeDir(),
    tempDir: os.tmpdir()
  };
}

module.exports = {
  isWindows,
  isMacOS,
  isLinux,
  getHomeDir,
  ensureDir,
  commandExists,
  runCommand,
  getClaudeConfigDir,
  getProjectRoot,
  joinPath,
  resolvePath,
  normalizePath,
  readJSON,
  writeJSON,
  copyFile,
  getPlatformInfo
};
