#!/usr/bin/env node
/**
 * SessionStart Hook: Compact startup banner
 */

const path = require('path');
const os = require('os');
const common = require('./hook-common');

let input = {};
try {
  const stdinData = require('fs').readFileSync(0, 'utf8');
  if (stdinData.trim()) input = JSON.parse(stdinData);
} catch { }

const cwd = input.cwd || process.cwd();
const homeDir = os.homedir();
const shortCwd = cwd.startsWith(homeDir) ? '~' + cwd.slice(homeDir.length) : cwd;

const gitInfo = common.getGitInfo(cwd);

let gitLine = '';
if (gitInfo.is_repo) {
  if (gitInfo.has_changes) {
    gitLine = `  git  ${gitInfo.branch}  (${gitInfo.changes_count} changed)\n`;
  } else {
    gitLine = `  git  ${gitInfo.branch}\n`;
  }
}

const now = new Date();
const timeStr = now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });

const output = `${shortCwd}  ${timeStr}\n${gitLine}`;

console.log(JSON.stringify({ continue: true, systemMessage: output }));
process.exit(0);
