#!/usr/bin/env bash
# Install a "Claude" session-history view into Otty's Details panel.
#
#   bash install.sh [--id ID] [--title TITLE] [--days N] [--lang en|zh] [--dry-run]
#   bash install.sh --uninstall [--id ID] [--dry-run]
#
# All views share ONE code folder (~/.config/otty/views/claude-history) and differ only by the
# arguments in their details-view line, so re-running install updates every variant at once.
# Defaults: --id claude-history --title Claude, no day limit, language auto-detected at runtime
# (zh if LANG/AppleLanguages[0] is Chinese, else en). Example variant:
#   bash install.sh --id claude-7d --title "Claude 7天" --days 7
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODE="$HOME/.config/otty/views/claude-history"
VIEW_ID="claude-history"; TITLE="Claude"; DAYS=""; UILANG=""; dry=0; uninstall=0
while (( $# )); do
  case "$1" in
    --id) VIEW_ID="$2"; shift ;;
    --title) TITLE="$2"; shift ;;
    --days) DAYS="$2"; shift ;;
    --lang) UILANG="$2"; shift ;;
    --dry-run) dry=1 ;;
    --uninstall) uninstall=1 ;;
    *) echo "unknown arg $1" >&2; exit 2 ;;
  esac; shift
done
[[ "$VIEW_ID" =~ ^[A-Za-z0-9_-]+$ ]] || { echo "--id must be letters/digits/-/_" >&2; exit 2; }
[[ -z "$DAYS" || "$DAYS" =~ ^[0-9]+$ ]] || { echo "--days must be a whole number" >&2; exit 2; }
[[ -z "$UILANG" || "$UILANG" == en || "$UILANG" == zh ]] || { echo "--lang must be en or zh" >&2; exit 2; }
[[ "$TITLE" != *[\"\']* ]] || { echo "--title must not contain quotes" >&2; exit 2; }

OTTY="${OTTY_CLI:-}"
if [[ -z "$OTTY" ]]; then
  if [[ -x /Applications/Otty.app/Contents/MacOS/otty-cli ]]; then OTTY=/Applications/Otty.app/Contents/MacOS/otty-cli
  else OTTY="$(command -v otty || true)"; fi
fi
[[ -n "$OTTY" ]] || { echo "Otty CLI not found (is Otty installed?)" >&2; exit 1; }
CONFIG="$("$OTTY" config path 2>/dev/null || echo "$HOME/.config/otty/config.toml")"

# Otty runs `command` like a prompt command, so $HOME expands. ${cwd} is Otty's variable and must stay
# literal; \" is the TOML escape inside the single-quoted value.
ARGS='\"${cwd}\"'; [[ -n "$DAYS" ]] && ARGS="$ARGS $DAYS"; [[ -n "$UILANG" ]] && ARGS="--lang $UILANG $ARGS"
LINE='details-view = '\''id="'"$VIEW_ID"'" kind="tui" title="'"$TITLE"'" icon="claude" command="$HOME/.config/otty/views/claude-history/claude-history '"$ARGS"'" cwd="${cwd}"'\'

say() { if (( dry )); then echo "[dry-run] would $*"; else echo "$*"; fi; }
has_line() { grep -q "id=\"$VIEW_ID\"" "$CONFIG" 2>/dev/null; }
reload() { (( dry )) && return 0; "$OTTY" config validate; "$OTTY" config reload >/dev/null 2>&1 && echo "Otty config reloaded." || echo "(Otty not running — applies on next launch)"; }

if (( uninstall )); then
  if has_line; then
    say "back up $CONFIG → $CONFIG.bak-$VIEW_ID and remove the details-view id=\"$VIEW_ID\" line"
    if (( ! dry )); then cp "$CONFIG" "$CONFIG.bak-$VIEW_ID"; grep -v "id=\"$VIEW_ID\"" "$CONFIG.bak-$VIEW_ID" > "$CONFIG"; fi
  else
    echo "No details-view id=\"$VIEW_ID\" in $CONFIG."
  fi
  if grep -q 'views/claude-history/claude-history' "$CONFIG" 2>/dev/null && ! (( dry )); then
    echo "Other views still use $CODE — code and cache kept."
  else
    say "remove $CODE and ~/.cache/otty-session-browser (no view uses them any more)"
    (( dry )) || rm -rf "$CODE" "$HOME/.cache/otty-session-browser"
  fi
  reload; exit 0
fi

for dep in fzf python3; do command -v "$dep" >/dev/null || { echo "missing dependency: $dep (brew install $dep)" >&2; exit 1; }; done

say "copy sessions.py + claude-history → $CODE/"
if (( ! dry )); then mkdir -p "$CODE"; cp "$SRC/sessions.py" "$SRC/claude-history" "$CODE/"; chmod +x "$CODE/claude-history"; fi

if has_line; then
  echo "Config already has details-view id=\"$VIEW_ID\" — line left unchanged:"
  grep "id=\"$VIEW_ID\"" "$CONFIG" | sed 's/^/  /'
  [[ "$(grep "id=\"$VIEW_ID\"" "$CONFIG")" == "$LINE" ]] || echo "  (differs from what this run would write; --uninstall --id $VIEW_ID first to replace it)"
else
  say "back up $CONFIG → $CONFIG.bak-$VIEW_ID and append (line order = tab order in the panel):"
  echo "  $LINE"
  if (( ! dry )); then cp "$CONFIG" "$CONFIG.bak-$VIEW_ID"; printf '\n%s\n' "$LINE" >> "$CONFIG"; fi
fi

reload
if (( ! dry )); then
  CH_DAYS="$DAYS" python3 -I "$CODE/sessions.py" list --all | wc -l | xargs printf 'Indexed: %s sessions listed. '
  echo "Open the Details panel (⌘⇧R) → \"$TITLE\" tab."
else
  echo "[dry-run] nothing was changed."
fi
