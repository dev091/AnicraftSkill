# Install/update the anicraft-elite skill from GitHub into Claude Code skills + D:\youtube\anicraft\tools
param([string]$Branch = 'claude/intelligent-archimedes-68cftw')
$ErrorActionPreference = 'Stop'
$base = "https://raw.githubusercontent.com/dev091/AnicraftSkill/$Branch/anicraft-elite"
$files = 'SKILL.md','references/recipes.md','references/commands-v0.2.1.md','scripts/acsession.py','scripts/recipes.py',
         'scripts/lipsync.py','scripts/verify_frames.py','scripts/example_shot.py','scripts/selftest.py',
         'scripts/build_episode.py','scripts/make_demo_assets.py'
$dst = Join-Path $env:USERPROFILE '.claude\skills\anicraft-elite'
foreach ($f in $files) {
  $p = Join-Path $dst $f; New-Item -ItemType Directory -Force (Split-Path $p) | Out-Null
  Invoke-WebRequest -UseBasicParsing "$base/$f`?t=$(Get-Date -UFormat %s)" -OutFile $p
}
Copy-Item (Join-Path $dst 'scripts\*.py') 'D:\youtube\anicraft\tools\' -Force
"installed $($files.Count) files -> $dst"
