# Scheduled commit and push (the "watcher")

Every 4 hours a launchd job on this Mac runs `_scripts/autopush.sh`:

1. If the working tree is clean, it pushes any local commits that are not on GitHub yet and stops.
2. Otherwise it runs `python3 _scripts/validate.py`. If validation fails, nothing is committed; the log says why and the changes stay in the tree for you to fix.
3. If validation passes, it commits everything (`auto: scheduled commit <date> (<n> paths changed, validated)`), rebases on `origin/main`, and pushes. GitHub Actions then renders and deploys the site (about 4 minutes).

Log: `~/Library/Logs/perovskite-atlas-autopush.log`.
Job: `~/Library/LaunchAgents/eus.igartua.perovskite-atlas.autopush.plist` (StartInterval 14400 s).

Notes
- launchd interval jobs do not run while the Mac sleeps; a missed pass runs shortly after wake.
- To run a pass now: `launchctl kickstart -k gui/$(id -u)/eus.igartua.perovskite-atlas.autopush`
- To pause: `launchctl bootout gui/$(id -u)/eus.igartua.perovskite-atlas.autopush`; to resume: `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/eus.igartua.perovskite-atlas.autopush.plist`
- Commit yourself whenever you want a meaningful message; the watcher only sweeps up what is left.
