# WorkBuddy Skill 安装脚本
# 用法：在仓库根目录运行 .\install.ps1
# 功能：将 skill 文件复制到 WorkBuddy skills 目录

$skillName = "feynman-tutor"
$workbuddySkillsDir = Join-Path $env:USERPROFILE ".workbuddy\skills"
$targetDir = Join-Path $workbuddySkillsDir $skillName

Write-Host "=== 费曼学习法 · 真懂教练 安装脚本 ===" -ForegroundColor Cyan
Write-Host ""

# 检查 WorkBuddy skills 目录是否存在
if (-not (Test-Path $workbuddySkillsDir)) {
    Write-Host "[!] 未找到 WorkBuddy skills 目录: $workbuddySkillsDir" -ForegroundColor Yellow
    Write-Host "    请确认 WorkBuddy 已安装并至少运行过一次。" -ForegroundColor Yellow
    exit 1
}

# 如果目标目录已存在，提示更新
if (Test-Path $targetDir) {
    Write-Host "[*] 检测到已有安装，将更新到最新版本..." -ForegroundColor Yellow
    Remove-Item -Path $targetDir -Recurse -Force
}

# 创建目标目录
New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $targetDir "references") -Force | Out-Null

# 复制 SKILL.md
Copy-Item -Path ".\SKILL.md" -Destination $targetDir -Force
Write-Host "[OK] SKILL.md" -ForegroundColor Green

# 复制 references
$refFiles = Get-ChildItem -Path ".\references" -Filter "*.md"
foreach ($file in $refFiles) {
    Copy-Item -Path $file.FullName -Destination (Join-Path $targetDir "references") -Force
    Write-Host "[OK] references/$($file.Name)" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== 安装完成 ===" -ForegroundColor Cyan
Write-Host "Skill 已安装到: $targetDir" -ForegroundColor Gray
Write-Host "在 WorkBuddy 对话中说「教我 X」或「我想学 X」即可触发。" -ForegroundColor Gray
