#!/usr/bin/env node
/**
 * UserPromptSubmit Hook: Forced skill activation flow (cross-platform version)
 *
 * Event: UserPromptSubmit
 * Function: Force AI to evaluate available skills and begin implementation after activation
 */

const path = require('path');
const fs = require('fs');
const os = require('os');
const common = require('./hook-common');

// Read stdin input
let input = {};
try {
  const stdinData = require('fs').readFileSync(0, 'utf8');
  if (stdinData.trim()) {
    input = JSON.parse(stdinData);
  }
} catch {
  // Use default empty object
}

const userPrompt = input.user_prompt || '';
const cwd = input.cwd || process.cwd();

// Check if it is a slash command (escape)
if (userPrompt.startsWith('/')) {
  // Distinguish commands from paths:
  // - Commands: /commit, /update-github (no second slash after the first)
  // - Paths: /Users/xxx, /path/to/file (contains path separators)
  const rest = userPrompt.substring(1);
  if (rest.includes('/')) {
    // This is a path, continue with skill scanning
  } else {
    // This is a command, skip skill evaluation
    console.log(JSON.stringify({ continue: true }));
    process.exit(0);
  }
}

const homeDir = os.homedir();

// Dynamically collect skill list
function collectSkills() {
  const skills = [];
  const skillsDir = path.join(homeDir, '.claude', 'skills');

  // 1. Collect local skills
  if (fs.existsSync(skillsDir)) {
    const skillDirs = fs.readdirSync(skillsDir, { withFileTypes: true })
      .filter(d => d.isDirectory())
      .map(d => d.name);

    for (const skillName of skillDirs) {
      skills.push(skillName);
    }
  }

  // 2. Collect plugin skills
  const pluginsCache = path.join(homeDir, '.claude', 'plugins', 'cache');

  if (fs.existsSync(pluginsCache)) {
    const marketplaces = fs.readdirSync(pluginsCache, { withFileTypes: true })
      .filter(d => d.isDirectory())
      .map(d => d.name);

    for (const marketplace of marketplaces) {
      const marketplacePath = path.join(pluginsCache, marketplace);
      const plugins = fs.readdirSync(marketplacePath, { withFileTypes: true })
        .filter(d => d.isDirectory() && !d.name.startsWith('.'))
        .map(d => d.name);

      for (const plugin of plugins) {
        const pluginPath = path.join(marketplacePath, plugin);
        const versions = fs.readdirSync(pluginPath, { withFileTypes: true })
          .filter(d => d.isDirectory())
          .map(d => d.name)
          .sort()
          .reverse();

        if (versions.length > 0) {
          const latestVersion = versions[0];
          const skillsDirPath = path.join(pluginPath, latestVersion, 'skills');

          if (fs.existsSync(skillsDirPath)) {
            const skillDirs = fs.readdirSync(skillsDirPath, { withFileTypes: true })
              .filter(d => d.isDirectory())
              .map(d => d.name);

            for (const skillName of skillDirs) {
              skills.push(`${plugin}:${skillName}`);
            }
          }
        }
      }
    }
  }

  // Deduplicate
  return [...new Set(skills)].sort();
}

// Categorize skills into groups
function categorizeSkills(skills) {
  const categories = {
    'Research & Writing': /research|paper|writing|citation|review-response|rebuttal|post-acceptance|doc-coauthoring|latex|daily-paper|ml-paper|results-analysis|results-report|brainstorm/,
    'Development': /coding|git|code-review|bug|architecture|verification|tdd|uv-package|webapp-testing|kaggle|driven-development|development-branch|planning|dispatching|executing|using-superpowers/,
    'Plugin Dev': /skill-|command-|hook-|mcp-|agent-identifier|plugin-structure/,
    'Design & UI': /frontend|ui-ux|web-design|canvas|brand|theme|algorithmic-art|slack-gif|figma/,
    'Documents': /docx|xlsx|pptx|pdf|internal-comms|web-artifacts/,
  };

  const grouped = {};
  for (const cat of Object.keys(categories)) {
    grouped[cat] = [];
  }
  grouped['Other'] = [];

  for (const skill of skills) {
    let matched = false;
    for (const [cat, regex] of Object.entries(categories)) {
      if (regex.test(skill)) {
        grouped[cat].push(skill);
        matched = true;
        break;
      }
    }
    if (!matched) {
      grouped['Other'].push(skill);
    }
  }

  return grouped;
}

// Keyword-to-skill mapping for pre-matching
// Note: \b doesn't work with CJK characters, so we use separate patterns
const KEYWORD_SKILL_MAP = [
  { keywords: /\b(git|github|commit|push|pull|merge|rebase|branch|tag|stash|cherry.?pick|develop|master|main)\b/i, skills: ['git-workflow'] },
  { keywords: /\b(debug|bug|error|broken|failing|traceback|exception)\b/i, skills: ['bug-detective'] },
  { keywords: /\b(tdd|test.?driven)\b/i, skills: ['superpowers:test-driven-development'] },
  { keywords: /\b(code.?review|review code)\b/i, skills: ['code-review-excellence'] },
  { keywords: /\b(paper|manuscript|draft)\b/i, skills: ['ml-paper-writing'] },
  { keywords: /\b(research|idea|brainstorm)\b/i, skills: ['research-ideation'] },
  { keywords: /\b(rebuttal|reviewer|response to reviewer)\b/i, skills: ['review-response'] },
  { keywords: /\b(frontend|landing.?page|dashboard)\b/i, skills: ['frontend-design'] },
  { keywords: /\b(create|write|develop|improve).*skill\b/i, skills: ['skill-development'] },
  { keywords: /\b(create|write|develop).*hook\b/i, skills: ['hook-development'] },
  { keywords: /\b(create|write|develop).*command|slash.*command\b/i, skills: ['command-development'] },
  { keywords: /\b(create|write|develop).*agent\b/i, skills: ['agent-identifier'] },
  { keywords: /\b(mcp)\b|mcp.*server/i, skills: ['mcp-integration'] },
  { keywords: /\b(architecture|factory|registry)\b/i, skills: ['architecture-design'] },
  { keywords: /\b(uv|pip|package.*manager|venv)\b/i, skills: ['uv-package-manager'] },
  { keywords: /\b(kaggle|competition)\b/i, skills: ['kaggle-learner'] },
  { keywords: /\b(citation|reference.*check)\b/i, skills: ['citation-verification'] },
  { keywords: /\b(latex.*template|overleaf)\b/i, skills: ['latex-conference-template-organizer'] },
  { keywords: /\b(ablation|results.*analysis)\b/i, skills: ['results-analysis'] },
  { keywords: /\b(experiment.?report|results.?report|retrospective|wrap.?up)\b/i, skills: ['results-report'] },
  { keywords: /\b(poster|presentation|promote)\b/i, skills: ['post-acceptance'] },
  { keywords: /\b(plan|planning)\b/i, skills: ['planning-with-files'] },
  { keywords: /\b(verify|verification)\b/i, skills: ['verification-loop'] },
  { keywords: /\b(self.?review)\b/i, skills: ['paper-self-review'] },
  { keywords: /\b(anti.?ai|humanize)\b/i, skills: ['writing-anti-ai'] },
  { keywords: /\b(write|draft|rewrite|edit|polish)\b.*\b(text|paragraph|section|abstract|introduction|conclusion|email|letter|proposal|essay|summary)\b|\b(text|paragraph|section|abstract|introduction|conclusion|email|letter|proposal|essay|summary)\b.*\b(write|draft|rewrite|edit|polish)\b|\b(перепиши|отредактируй|улучши|сделай|напиши)\b.*\b(текст|абзац|раздел|секци|аннотац|введение|заключение|письмо|эссе|саммари|summary)\b/i, skills: ['writing-anti-ai'] },
  { keywords: /\b(implement|write code|add feature|modify|refactor)\b/i, skills: ['daily-coding'] },
];

// Pre-match user prompt against keyword map
function suggestSkills(prompt) {
  const suggested = new Set();
  for (const { keywords, skills } of KEYWORD_SKILL_MAP) {
    if (keywords.test(prompt)) {
      for (const s of skills) suggested.add(s);
    }
  }
  return [...suggested];
}

// Generate skill list
const SKILL_LIST = collectSkills();
const SKILL_GROUPS = categorizeSkills(SKILL_LIST);
const suggestedSkills = suggestSkills(userPrompt);
const binding = common.getProjectMemoryBinding(cwd);
const isResearchPrompt = common.promptLooksResearchRelated(userPrompt);

if (binding.bound && isResearchPrompt) {
  if (SKILL_LIST.includes('obsidian-project-memory')) {
    suggestedSkills.push('obsidian-project-memory');
  }
  if (/\b(zotero|collection|doi|arxiv|citation)\b/i.test(userPrompt) &&
      SKILL_LIST.includes('zotero-obsidian-bridge')) {
    suggestedSkills.push('zotero-obsidian-bridge');
  }
  if (/\b(paper|papers|literature|review|claim|method|evidence)\b/i.test(userPrompt) &&
      SKILL_LIST.includes('obsidian-literature-workflow')) {
    suggestedSkills.push('obsidian-literature-workflow');
  }
}

const dedupedSuggestedSkills = [...new Set(suggestedSkills)];

// Format grouped skills (skip empty groups)
const groupedDisplay = Object.entries(SKILL_GROUPS)
  .filter(([, skills]) => skills.length > 0)
  .map(([cat, skills]) => `[${cat}] ${skills.join(', ')}`)
  .join('\n');

// Build suggested skills hint
const suggestedHint = dedupedSuggestedSkills.length > 0
  ? `\n**Pre-matched skills (MUST activate these)**: ${dedupedSuggestedSkills.join(', ')}\nThese skills matched keywords in the user's prompt. You MUST activate them via Skill tool.\n`
  : '';

const boundRepoHint = binding.bound && isResearchPrompt
  ? `\n**Bound Obsidian repo detected**: ${binding.projectId || 'unknown-project'}\nUse lightweight curator behavior by default: keep \`Daily/YYYY-MM-DD.md\` and \`.claude/project-memory/<project_id>.md\` in sync when this turn changes research state, and touch \`00-Hub.md\` only when top-level project status really changes. Consider the \`research-knowledge-curator-obsidian\` agent when the task spans plans, papers, experiments, results, or writing.\n`
  : '';

// Generate output — show full skill list only when skills are pre-matched,
// otherwise emit a minimal reminder to keep token usage low.
let output;

if (dedupedSuggestedSkills.length > 0) {
  // Full list + pre-matched hint
  output = `## Skill Activation
Available skills:
${groupedDisplay}
**Pre-matched (MUST activate)**: ${dedupedSuggestedSkills.join(', ')}
Use Skill tool to activate, then implement.${boundRepoHint}`;
} else {
  // Minimal — no full list, just a quiet reminder
  output = `## Skill Activation
No pre-matched skills. If the request clearly fits a skill, activate it via Skill tool. Otherwise proceed directly.${boundRepoHint}`;
}

console.log(output);

process.exit(0);
