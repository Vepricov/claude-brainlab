# backup-for-migration.ps1 -- collect everything a new machine cannot rebuild.
#
# NOTE: keep this file ASCII-only -- PS 5.1 reads BOM-less files as ANSI and
# multi-byte punctuation (em dash, smart quotes) corrupts the parse.
#
#   powershell -ExecutionPolicy Bypass -File install\backup-for-migration.ps1 -Destination E:\claude-migration
#
# The claude-brainlab repo rebuilds the harness itself (setup-windows.ps1).
# This script collects the things that exist ONLY on this laptop:
#
#   .mempalace/            the memory palace (drawers, embeddings)
#   .claude/projects/*/memory/   per-project memory files
#   .ssh/                  config + private keys
#   Zotero/                literature library
#   <vault>/               Obsidian vault (path read from .env)
#   .env                   gitignored; holds the Zotero API key
#   unversioned projects   any project folder with no git remote
#   graphify-out/          graph.json + report only (cache/ is regenerable)
#
# It also AUDITS every git project and reports uncommitted or unpushed work,
# which a fresh clone on the new machine would not have.
#
# Switches:
#   -IncludeTranscripts  also copy ~/.claude/projects session transcripts (~100 MB)
#   -AuditOnly           report what would be copied, copy nothing
#
# Full guide: docs/MIGRATION.md

param(
    [Parameter(Mandatory = $true)]
    [string]$Destination,
    [switch]$IncludeTranscripts,
    [switch]$AuditOnly
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path $PSScriptRoot -Parent
$Home_    = $env:USERPROFILE
$Manifest = New-Object System.Collections.Generic.List[string]
$Warnings = New-Object System.Collections.Generic.List[string]

function Say($m)  { Write-Host "  $m" }
function Warn($m) { Write-Host "  ! $m" -ForegroundColor Yellow; $Warnings.Add($m) }

function Get-SizeMB($path) {
    if (-not (Test-Path $path)) { return 0 }
    $item = Get-Item $path
    if (-not $item.PSIsContainer) { return [math]::Round($item.Length / 1MB, 1) }
    $b = (Get-ChildItem $path -Recurse -File -ErrorAction SilentlyContinue |
          Measure-Object -Property Length -Sum).Sum
    return [math]::Round($b / 1MB, 1)
}

# Copy $src into $Destination\$rel, optionally skipping directories by name.
function Copy-Asset($src, $rel, $label, $excludeDirs) {
    if (-not (Test-Path $src)) { Warn "skip $label (not found: $src)"; return }
    $mb = Get-SizeMB $src
    if ($AuditOnly) { Say ("would copy {0,-28} {1,8} MB" -f $label, $mb); $Manifest.Add("$label`t$mb MB`t$src"); return }

    $dst = Join-Path $Destination $rel
    New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null

    if ((Get-Item $src).PSIsContainer) {
        # robocopy: resilient on long paths, and /XD prunes regenerable caches.
        $args = @($src, $dst, '/E', '/NFL', '/NDL', '/NJH', '/NJS', '/NP', '/R:1', '/W:1')
        if ($excludeDirs) { $args += '/XD'; $args += $excludeDirs }
        robocopy @args | Out-Null
        # robocopy exit codes 0-7 are success; 8+ is a real failure.
        if ($LASTEXITCODE -ge 8) { Warn "robocopy reported errors for $label (code $LASTEXITCODE)" }
        $global:LASTEXITCODE = 0
    } else {
        Copy-Item $src $dst -Force
    }
    Say ("copied {0,-28} {1,8} MB" -f $label, $mb)
    $Manifest.Add("$label`t$mb MB`t$src")
}

Write-Host "-> Collecting laptop-only assets into $Destination"
if ($AuditOnly) { Write-Host "   (audit only - nothing will be copied)" }
if (-not $AuditOnly) { New-Item -ItemType Directory -Force -Path $Destination | Out-Null }

# --- 1. Memory, keys, libraries ---------------------------------------------
Copy-Asset (Join-Path $Home_ '.mempalace') 'mempalace' 'mempalace (memory)' @('locks')
Copy-Asset (Join-Path $Home_ '.ssh')       'ssh'       'ssh (config + keys)' $null
Copy-Asset (Join-Path $Home_ 'Zotero')     'Zotero'    'Zotero library'      $null

# .env is gitignored and holds the Zotero API key.
Copy-Asset (Join-Path $RepoRoot '.env') 'claude-brainlab.env' 'repo .env (secrets)' $null

# --- 2. Obsidian vault (path from .env) -------------------------------------
$vault = $null
$envFile = Join-Path $RepoRoot '.env'
if (Test-Path $envFile) {
    foreach ($line in Get-Content $envFile -Encoding UTF8) {
        if ($line -match '^\s*OBSIDIAN_VAULT\s*=\s*(.+)$') { $vault = $matches[1].Trim().Trim('"') }
    }
}
if ($vault) { Copy-Asset $vault 'vault' "Obsidian vault" @('.trash') }
else        { Warn 'OBSIDIAN_VAULT not set in .env - vault not copied' }

# --- 3. Per-project Claude memory -------------------------------------------
# These are keyed by project path (C--Users-<user>-<project>). If the new
# machine uses a different username or project root, the keys must be renamed
# or the memory silently stops loading. See docs/MIGRATION.md.
$projects = Join-Path $Home_ '.claude\projects'
if (Test-Path $projects) {
    if ($IncludeTranscripts) {
        Copy-Asset $projects 'claude-projects' 'claude projects (+transcripts)' $null
    } else {
        $n = 0
        foreach ($d in Get-ChildItem $projects -Directory) {
            $mem = Join-Path $d.FullName 'memory'
            if (-not (Test-Path $mem)) { continue }
            if (-not $AuditOnly) {
                $dst = Join-Path $Destination "claude-projects\$($d.Name)\memory"
                New-Item -ItemType Directory -Force -Path $dst | Out-Null
                robocopy $mem $dst '/E' '/NFL' '/NDL' '/NJH' '/NJS' '/NP' '/R:1' '/W:1' | Out-Null
                $global:LASTEXITCODE = 0
            }
            $n++
        }
        Say "copied project memory dirs        $n dirs"
        $Manifest.Add("claude project memory`t$n dirs`t$projects")
    }
}

# --- 4. Project folders: audit git state, carry the unversioned -------------
Write-Host "-> Auditing project folders in $Home_"
foreach ($d in Get-ChildItem $Home_ -Directory -ErrorAction SilentlyContinue) {
    $p = $d.FullName
    # Only look at folders that Claude Code has actually been used in.
    $hasClaude = Test-Path (Join-Path $p '.claude')
    $hasGit    = Test-Path (Join-Path $p '.git')
    if (-not $hasClaude -and -not $hasGit) { continue }

    if (-not $hasGit) {
        # A folder with no files left in it is not worth carrying or warning about.
        if ((Get-SizeMB $p) -eq 0) { continue }
        Warn "$($d.Name): NOT under version control - exists only on this laptop"
        Copy-Asset $p "unversioned\$($d.Name)" "  $($d.Name)" @('graphify-out', '__pycache__', '.venv')
        continue
    }

    Push-Location $p
    try {
        $dirty   = @(git status --porcelain 2>$null) |
                   Where-Object { $_ -notmatch '^\?\? (\.claude|graphify-out)/' }
        $unpush  = @(git log --oneline '@{u}..' 2>$null)
        $stash   = @(git stash list 2>$null)
        $remote  = git remote get-url origin 2>$null
        if (-not $remote)        { Warn "$($d.Name): git repo with NO remote" }
        if ($dirty.Count  -gt 0) { Warn "$($d.Name): $($dirty.Count) uncommitted change(s) - not on any remote" }
        if ($unpush.Count -gt 0) { Warn "$($d.Name): $($unpush.Count) unpushed commit(s)" }
        if ($stash.Count  -gt 0) { Warn "$($d.Name): $($stash.Count) stash entr(ies) - never leave the laptop" }
    } finally { Pop-Location }

    # Knowledge graphs: the JSON and report are expensive to rebuild, cache/ is not.
    $g = Join-Path $p 'graphify-out'
    if (Test-Path $g) {
        foreach ($f in @('graph.json', 'GRAPH_REPORT.md', 'manifest.json', 'cost.json')) {
            $src = Join-Path $g $f
            if (Test-Path $src) { Copy-Asset $src "graphify\$($d.Name)\$f" "  graph: $($d.Name)/$f" $null }
        }
    }
}

# --- 5. Manifest -------------------------------------------------------------
if (-not $AuditOnly) {
    $out = Join-Path $Destination 'MIGRATION-MANIFEST.txt'
    $header = @(
        "claude-brainlab migration payload",
        "created: $(Get-Date -Format s)",
        "source : $Home_",
        "",
        "asset`tsize`tsource"
    )
    ($header + $Manifest + @("", "WARNINGS:") + $Warnings) -join "`r`n" |
        Out-File -FilePath $out -Encoding utf8
    Say "wrote $out"
}

Write-Host ""
if ($Warnings.Count -gt 0) {
    Write-Host "$($Warnings.Count) warning(s) - review before wiping the old laptop:" -ForegroundColor Yellow
    foreach ($w in $Warnings) { Write-Host "  - $w" -ForegroundColor Yellow }
} else {
    Write-Host "No warnings: every project is committed and pushed."
}
Write-Host ""
Write-Host "Next: docs/MIGRATION.md, section 'On the new laptop'."
