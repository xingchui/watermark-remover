# Requires -Version 5.1
param(
  [string]$Head = "feat/agents-ci",
  [string]$Base = "main",
  [string]$Title = "feat(agents-ci): add CI-based verification workflow for AGENTS.md",
  [string]$BodyFile = "PR_BODY.md",
  [string]$Remote = "origin",
  [switch]$OpenWeb = $false
)

$ErrorActionPreference = "Stop"

# 确认在仓库根目录
$repoRoot = & git rev-parse --show-toplevel 2>$null
if (-not $repoRoot) {
  Write-Error "当前目录不是一个 Git 仓库，请在仓库根目录中执行脚本。"
  exit 1
}
Set-Location $repoRoot

# gh 是否可用
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
  Write-Error "未找到 gh 命令，请先安装并登录 gh。"
  exit 2
}

# PR Body 文件检查
if (-not (Test-Path $BodyFile)) {
  Write-Warning "Body 文件不存在: $BodyFile。将使用默认 Body。"
}

# 1) 拉取并确保分支存在，且有差异
Write-Host "步骤 1/4：拉取并准备分支 $Head ..." -ForegroundColor Cyan
git fetch --all
$headRemoteInfo = (& git ls-remote --heads origin $Head 2>$null)
if ($headRemoteInfo) {
  # 远端存在该分支
  git checkout $Head
  git pull --ff-only
} else {
  # 远端不存在该分支，则从远端主分支创建，或直接创建新分支并推送
  if (git rev-parse --verify $Head 2>$null) {
    git checkout $Head
    git pull --ff-only
  } else {
    git checkout -b $Head
    git push -u $Remote $Head
  }
}
# 查看是否和基线存在差异
$diff = & git diff origin/$Base...origin/$Head --stat
if ([string]::IsNullOrWhiteSpace($diff)) {
  Write-Warning "当前分支 $Head 与 $Base 之间没有实际差异，PR 可能为空。请确保你已经提交并推送了改动。继续执行可能导致无实际变更的 PR。"
}

# 2) 构造 gh pr create 命令
Write-Host "步骤 2/4：尝试创建 PR ..." -ForegroundColor Cyan
$bodyArg = "--body-file `"$BodyFile`""
$cmd = "gh pr create --head `"$Head`" --base `"$Base`" --title `"$Title`" $bodyArg"
if ($OpenWeb.IsPresent) { $cmd += " --web" }

Write-Host "执行命令: $cmd" -ForegroundColor Green
try {
  Invoke-Expression $cmd
} catch {
  Write-Error "PR 创建失败，请检查 gh 输出的错误信息。"
  exit 3
}

# 3) 获取 PR URL（若创建成功，gh 通常会打印 URL；若未打开浏览器也可获取）
Write-Host "步骤 3/4：获取 PR URL ..." -ForegroundColor Cyan
try {
  $prUrl = & gh pr view --head $Head --base $Base --json url -q .url
  if ($prUrl) {
    Write-Host "PR 链接: $prUrl" -ForegroundColor Cyan
  } else {
    Write-Warning "未能获取 PR 链接。请在浏览器中打开 PR 页面查看链接。"
  }
} catch {
  Write-Warning "无法通过 gh 获取 PR 链接。请手动在浏览器中查看 PR。"
}

# 4) 结束
Write-Host "完成。若需要，你可以粘贴 PR 链接以用于后续验收证据整理。" -ForegroundColor Green
exit 0
