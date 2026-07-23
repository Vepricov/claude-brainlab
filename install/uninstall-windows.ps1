# uninstall-windows.ps1 -- roll back a claude-brainlab install on Windows.
#
# Mirror of install/uninstall.sh plus MCP de-registration. ASCII-only on
# purpose (PS 5.1 reads BOM-less files as ANSI; see setup-windows.ps1).
#
#   powershell -ExecutionPolicy Bypass -File install\uninstall-windows.ps1
#
# What it does:
#   1. Restores the most recent backup snapshot from
#      ~/.claude/.claude-brainlab-backups (created by setup-windows.ps1).
#   2. Removes components we installed fresh (per the install manifest).
#   3. Removes the CLAUDE.brainlab.md sidecar.
#   4. Unregisters the mempalace and zotero MCP servers
#      (`claude mcp remove -s user` -- edits ~/.claude.json only; the server
#      executables and your data (memory palace, Zotero library) are NOT touched).
#
# Backups themselves are never deleted.
#
# Switches:
#   -KeepMcp   leave MCP server registrations in place
#   -Yes       skip the confirmation prompt

param(
    [switch]$KeepMcp,
    [switch]$Yes
)

$ErrorActionPreference = 'Stop'
# CLAUDE_HOME env var overrides the default (parity with the bash scripts).
$ClaudeHome = $env:CLAUDE_HOME
if ([string]::IsNullOrWhiteSpace($ClaudeHome)) {
    $ClaudeHome = Join-Path $env:USERPROFILE '.claude'
}
$BackupRoot = Join-Path $ClaudeHome '.claude-brainlab-backups'
$Manifest   = Join-Path $ClaudeHome '.claude-brainlab-manifest.txt'

function Write-Step($msg) { Write-Host "  $msg" }

# --- 1. Locate the latest backup snapshot ------------------------------------
$latest = $null
if (Test-Path $BackupRoot) {
    $latest = Get-ChildItem $BackupRoot -Directory |
        Sort-Object Name | Select-Object -Last 1
}
if ($null -eq $latest) {
    Write-Host "No backups found at $BackupRoot - nothing to restore."
    Write-Host 'Will still remove the sidecar and MCP registrations (unless -KeepMcp).'
} else {
    Write-Host "Rolling back to: $($latest.FullName)"
}

if (-not $Yes) {
    $ans = Read-Host 'Continue? [y/N]'
    if ($ans -notmatch '^[yY]') { Write-Host 'Aborted.'; exit 0 }
}

# --- 2. Restore backed-up items ----------------------------------------------
if ($null -ne $latest) {
    foreach ($item in Get-ChildItem $latest.FullName -Force) {
        $target = Join-Path $ClaudeHome $item.Name
        Write-Step "restore $($item.Name)"
        if (Test-Path $target) { Remove-Item $target -Recurse -Force }
        Copy-Item $item.FullName $target -Recurse -Force
    }
}

# --- 3. Remove components we installed fresh (no prior backup) ---------------
if (Test-Path $Manifest) {
    $manifestPaths = Get-Content $Manifest -Encoding UTF8 |
        Where-Object { $_ -and $_ -notmatch '^\s*#' }
    foreach ($p in $manifestPaths) {
        $name = Split-Path $p -Leaf
        $inBackup = ($null -ne $latest) -and (Test-Path (Join-Path $latest.FullName $name))
        if ((Test-Path $p) -and (-not $inBackup)) {
            Write-Step "remove $name (was newly installed)"
            Remove-Item $p -Recurse -Force
        }
    }
    Remove-Item $Manifest -Force
} elseif ($null -eq $latest) {
    Write-Warning 'No manifest and no backup - installed files left as-is.'
}

# Sidecar: always remove on uninstall.
$sidecar = Join-Path $ClaudeHome 'CLAUDE.brainlab.md'
if (Test-Path $sidecar) { Remove-Item $sidecar -Force; Write-Step 'removed CLAUDE.brainlab.md' }

# --- 4. Unregister MCP servers ------------------------------------------------
if (-not $KeepMcp) {
    if (Get-Command claude -ErrorAction SilentlyContinue) {
        Write-Host '-> Unregistering MCP servers (user scope, ~/.claude.json)'
        foreach ($server in @('mempalace', 'zotero')) {
            cmd /c "claude mcp remove $server -s user >nul 2>&1"
            if ($LASTEXITCODE -eq 0) {
                Write-Step "removed $server"
            } else {
                Write-Step "[skip] $server (was not registered)"
            }
        }
    } else {
        Write-Step '[skip] MCP unregister (claude CLI not found)'
    }
}

Write-Host ''
Write-Host 'Rolled back.'
if ($null -ne $latest) { Write-Host "Backup snapshot preserved at: $($latest.FullName)" }
Write-Host 'Restart Claude Code to drop the removed servers from new sessions.'
Write-Host 'Note: mempalace/zotero executables and their data were not touched.'
