/**
 *
 * @module package-manager
 */

const fs = require('fs');
const path = require('path');
const { commandExists, readJSON, getProjectRoot, getClaudeConfigDir, isWindows } = require('./utils');

const PACKAGE_MANAGERS = {
  npm: {
    name: 'npm',
    lockFile: 'package-lock.json',
    installCmd: 'npm install',
    runCmd: 'npm run',
    execCmd: 'npx',
    globalFlag: '--global'
  },
  pnpm: {
    name: 'pnpm',
    lockFile: 'pnpm-lock.yaml',
    installCmd: 'pnpm install',
    runCmd: 'pnpm',
    execCmd: 'pnpm dlx',
    globalFlag: '--global'
  },
  yarn: {
    name: 'yarn',
    lockFile: 'yarn.lock',
    installCmd: 'yarn install',
    runCmd: 'yarn',
    execCmd: 'yarn dlx',
    globalFlag: 'global'
  },
  bun: {
    name: 'bun',
    lockFile: 'bun.lockb',
    installCmd: 'bun install',
    runCmd: 'bun run',
    execCmd: 'bun x',
    globalFlag: '--global'
  }
};

const DETECTION_PRIORITY = ['pnpm', 'bun', 'yarn', 'npm'];

/**
 */
function getProjectConfigPath() {
  const projectRoot = getProjectRoot();
  if (projectRoot) {
    return path.join(projectRoot, '.claude', 'package-manager.json');
  }
  return null;
}

/**
 */
function getGlobalConfigPath() {
  return path.join(getClaudeConfigDir(), 'package-manager.json');
}

/**
 */
function detectFromEnvironment() {
  const envPm = process.env.CLAUDE_PACKAGE_MANAGER;
  if (envPm && PACKAGE_MANAGERS[envPm]) {
    return envPm;
  }
  return null;
}

/**
 */
function detectFromProjectConfig() {
  const configPath = getProjectConfigPath();
  if (configPath && fs.existsSync(configPath)) {
    const config = readJSON(configPath);
    if (config && config.packageManager && PACKAGE_MANAGERS[config.packageManager]) {
      return config.packageManager;
    }
  }
  return null;
}

/**
 */
function detectFromGlobalConfig() {
  const configPath = getGlobalConfigPath();
  if (configPath && fs.existsSync(configPath)) {
    const config = readJSON(configPath);
    if (config && config.packageManager && PACKAGE_MANAGERS[config.packageManager]) {
      return config.packageManager;
    }
  }
  return null;
}

/**
 */
function detectFromPackageJson() {
  const projectRoot = getProjectRoot();
  if (!projectRoot) {
    return null;
  }

  const packageJsonPath = path.join(projectRoot, 'package.json');
  if (!fs.existsSync(packageJsonPath)) {
    return null;
  }

  const packageJson = readJSON(packageJsonPath);
  if (!packageJson) {
    return null;
  }

  if (packageJson.packageManager) {
    const match = packageJson.packageManager.match(/^([a-zA-Z]+)@/);
    if (match && PACKAGE_MANAGERS[match[1]]) {
      return match[1];
    }
  }

  return null;
}

/**
 */
function detectFromLockFile() {
  const projectRoot = getProjectRoot();
  if (!projectRoot) {
    return null;
  }

  for (const pm of DETECTION_PRIORITY) {
    const lockFile = path.join(projectRoot, PACKAGE_MANAGERS[pm].lockFile);
    if (fs.existsSync(lockFile)) {
      return pm;
    }
  }

  return null;
}

/**
 */
function detectFromAvailableCommands() {
  for (const pm of DETECTION_PRIORITY) {
    if (commandExists(pm)) {
      return pm;
    }
  }
  return 'npm';
}

/**
 */
function getPackageManager(options = {}) {
  const {
    skipEnvironment = false,
    skipProjectConfig = false,
    skipGlobalConfig = false,
    skipPackageJson = false,
    skipLockFile = false,
    skipAvailable = false
  } = options;

  const detectors = [
    !skipEnvironment && { detector: detectFromEnvironment, source: 'environment' },
    !skipProjectConfig && { detector: detectFromProjectConfig, source: 'project-config' },
    !skipPackageJson && { detector: detectFromPackageJson, source: 'package.json' },
    !skipLockFile && { detector: detectFromLockFile, source: 'lock-file' },
    !skipGlobalConfig && { detector: detectFromGlobalConfig, source: 'global-config' },
    !skipAvailable && { detector: detectFromAvailableCommands, source: 'available' }
  ].filter(Boolean);

  for (const { detector, source } of detectors) {
    const pm = detector();
    if (pm && PACKAGE_MANAGERS[pm]) {
      return {
        name: pm,
        source,
        config: PACKAGE_MANAGERS[pm]
      };
    }
  }

  return {
    name: 'npm',
    source: 'default',
    config: PACKAGE_MANAGERS.npm
  };
}

/**
 */
function setProjectPackageManager(packageManager) {
  if (!PACKAGE_MANAGERS[packageManager]) {
    return false;
  }

  const configPath = getProjectConfigPath();
  if (!configPath) {
    return false;
  }

  const configDir = path.dirname(configPath);
  if (!fs.existsSync(configDir)) {
    fs.mkdirSync(configDir, { recursive: true });
  }

  try {
    fs.writeFileSync(
      configPath,
      JSON.stringify({ packageManager }, null, 2),
      'utf8'
    );
    return true;
  } catch (err) {
    return false;
  }
}

/**
 */
function setGlobalPackageManager(packageManager) {
  if (!PACKAGE_MANAGERS[packageManager]) {
    return false;
  }

  const configPath = getGlobalConfigPath();
  const configDir = path.dirname(configPath);

  if (!fs.existsSync(configDir)) {
    fs.mkdirSync(configDir, { recursive: true });
  }

  try {
    fs.writeFileSync(
      configPath,
      JSON.stringify({ packageManager }, null, 2),
      'utf8'
    );
    return true;
  } catch (err) {
    return false;
  }
}

/**
 */
function buildCommand(commandType, options = {}) {
  const pm = getPackageManager();
  const config = pm.config;

  switch (commandType) {
    case 'install':
      return config.installCmd;
    case 'run':
      return `${config.runCmd} ${options.script || ''}`;
    case 'exec':
      return `${config.execCmd} ${options.package || ''}`;
    default:
      return config.installCmd;
  }
}

/**
 */
function getAvailablePackageManagers() {
  return Object.keys(PACKAGE_MANAGERS).map(name => ({
    name,
    available: commandExists(name)
  }));
}

/**
 */
function printPackageManagerInfo() {
  const pm = getPackageManager();
}

module.exports = {
  PACKAGE_MANAGERS,
  DETECTION_PRIORITY,
  getPackageManager,
  setProjectPackageManager,
  setGlobalPackageManager,
  buildCommand,
  getAvailablePackageManagers,
  printPackageManagerInfo,
  getProjectConfigPath,
  getGlobalConfigPath,
  setPreferredPackageManager: setGlobalPackageManager,
  detectFromLockFile,
  detectFromPackageJson,
  getSelectionPrompt: () => {
  }
};
