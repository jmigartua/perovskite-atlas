#!/bin/bash
# Scheduled commit-and-push for the Perovskite Atlas (every 4 h via launchd, see docs/AUTOPUSH.md).
# Gate: nothing is committed unless `make validate` passes, so a half-edited record never reaches the site.
set -u
REPO="$HOME/Claude/Projects/igartua/perovskite-atlas"
LOG="$HOME/Library/Logs/perovskite-atlas-autopush.log"
export PATH="$HOME/anaconda3/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin"
stamp() { date "+%Y-%m-%d %H:%M:%S"; }
log() { echo "$(stamp) $*" >> "$LOG"; }

cd "$REPO" || { log "repo not found"; exit 0; }
if [ -f .git/index.lock ]; then log "git busy (index.lock present), skipped"; exit 0; fi

# 1. anything to commit?
if [ -z "$(git status --porcelain)" ]; then
  # still push anything committed by hand but not yet pushed
  if [ -n "$(git log origin/main..main --oneline 2>/dev/null)" ]; then
    git push -q origin main >> "$LOG" 2>&1 && log "pushed local commits (tree was clean)" || log "push failed"
  else
    log "clean, nothing to do"
  fi
  exit 0
fi

# 2. validate before committing
if ! python3 _scripts/validate.py >> "$LOG" 2>&1; then
  log "VALIDATION FAILED: changes left uncommitted (fix the records; see lines above)"
  exit 0
fi

# 3. commit
N=$(git status --porcelain | wc -l | tr -d ' ')
git add -A
git commit -q -m "auto: scheduled commit $(date '+%Y-%m-%d %H:%M') ($N path(s) changed, validated)" >> "$LOG" 2>&1 || { log "commit failed"; exit 0; }

# 4. push (rebase first in case something was pushed from elsewhere)
git pull -q --rebase --autostash origin main >> "$LOG" 2>&1 || log "pull --rebase reported a problem; attempting push anyway"
if git push -q origin main >> "$LOG" 2>&1; then
  log "committed and pushed ($N path(s)); GitHub Actions will validate, render and deploy"
else
  log "PUSH FAILED (commit kept locally)"
fi
