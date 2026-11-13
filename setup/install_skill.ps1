# Install/update the anicraft-elite skill from GitHub into Claude Code skills + D:\youtube\anicraft\tools
param([string]$Branch = 'claude/intelligent-archimedes-68cftw')
$ErrorActionPreference = 'Stop'
$sha = (Invoke-RestMethod -UseBasicParsing "https://api.github.com/repos/dev091/AnicraftSkill/commits/$Branch").sha  # pinned: raw CDN caches branch URLs
$base = "https://raw.githubusercontent.com/dev091/AnicraftSkill/$sha/anicraft-elite"
$files = 'SKILL.md','references/recipes.md','references/commands-v0.2.1.md','references/moral-toon-bible.md','references/asset-spec.md','scripts/acsession.py','scripts/recipes.py',
         'scripts/lipsync.py','scripts/verify_frames.py','scripts/example_shot.py','scripts/selftest.py',
         'scripts/build_episode.py','scripts/make_demo_assets.py','scripts/rig.py','scripts/make_demo_puppet.py','scripts/walk_test.py'
$dst = Join-Path $env:USERPROFILE '.claude\skills\anicraft-elite'
foreach ($f in $files) {
  $p = Join-Path $dst $f; New-Item -ItemType Directory -Force (Split-Path $p) | Out-Null
  Invoke-WebRequest -UseBasicParsing "$base/$f" -OutFile $p
}
Copy-Item (Join-Path $dst 'scripts\*.py') 'D:\youtube\anicraft\tools\' -Force
"installed $($files.Count) files @ $($sha.Substring(0,7)) -> $dst"
