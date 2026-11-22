---
name: otty-session-browser
description: Use when the user wants past Claude Code sessions (history, resume list, session browser) visible inside the Otty terminal — "add Claude history to Otty's sidebar/panel", "browse ~/.claude/projects sessions", "otty details-view for claude --resume" — or when updating that panel, opening its sessions in a terminal tab, or adding any custom tui/web view to Otty's Details panel.
---

# Claude session history in Otty

## Overview

Otty's **left sidebar only holds tabs** (optionally grouped into Spaces) — there is no config key to put anything else there. The persistent place for a custom list is the **right-hand Details panel** (`⌘⇧R`), which accepts custom views. This skill installs a `Claude` Details view: an fzf browser over `~/.claude/projects/*/*.jsonl` with preview, double-click to open in a waiting terminal, and resume-in-place.

Tell the user this up front — then offer both the built-in route and the custom view.

## Built-in alternative (no install)

Needs Otty's Claude integration (Settings ▸ Agents ▸ Claude Code; it writes `otty-hook.sh` hooks into `~/.claude/settings.json`):
- `⌘⇧O` (Open Quickly) → `⌘G` switches to the **Agents** filter → type → `↩` resumes (jumps to the live tab if running). `⌘K` there: fork in new tab / View Session History.
- Claude Code itself: `claude --resume` → `^A` lists all projects on the machine; choosing one from another project copies a `cd … && claude --resume <id>` command. The panel's advantage is staying visible beside a running session, not access to other projects.
- History view: Command Palette or titlebar dropdown — transcript, search, Resume.

## Install the custom view

```bash
I="<this skill's base directory>/scripts/install.sh"   # base dir is printed when the skill loads
bash "$I" --dry-run          # always show the user this first; it prints the exact config line
bash "$I"                  # idempotent; backs up config.toml; validates + reloads Otty
bash "$I" --lang zh                                    # pin UI language (en|zh); omit = auto-detect
bash "$I" --id claude-7d --title "Claude 7d" --days 7  # a variant view (own id ⇒ own tab)
bash "$I" --uninstall [--id claude-7d]                      # removes that view's line only
```

- All views share **one** code folder `~/.config/otty/views/claude-history/`; variants differ only by args in their `details-view` line (`claude-history [--lang en|zh] "${cwd}" [DAYS]`). Re-running `install.sh` updates every variant — never fork the scripts into a second folder.
- Every view needs a **distinct `id`**; line order in config.toml = tab order in the panel. An existing line with the same id is left untouched (it says so); to change it, `--uninstall --id X` then reinstall.
- `--days N` = sessions whose **last activity** (file mtime) is within N days. `sessions.py` reads it from env `CH_DAYS`; "auto-switch to all projects when this folder is empty" still applies within the window.
- `--uninstall` deletes code + `~/.cache/otty-session-browser` only when no remaining view references the code folder.
- Requires `fzf`, `python3`, macOS `pbcopy`. Otty runs `command=` like a prompt command (shell expands `$HOME`); the script also appends `/opt/homebrew/bin`, `/usr/local/bin`, `~/.local/bin` to PATH in case the GUI environment lacks them.
- **Language**: without `--lang`, the UI is zh if `LANG` or macOS `AppleLanguages[0]` starts with `zh`, else en. Many Chinese users have `en-CN` first — ask which language they want and pass `--lang` explicitly. Reply to the user in their language either way.
- Changing config needs the user's go-ahead: show the dry-run, then install.
- **After installing, give the user the `--wait` command** the installer prints, and say it belongs in an ordinary terminal tab. Without it, double-click only copies the command.
- **Updating**: re-run `install.sh` (same code folder), then have the user restart Otty. Open panels keep the script they started with.

Verify without the GUI by driving it in tmux (zsh: wrap tmux in a function, `T="tmux -L x"; $T …` does not word-split):
```bash
T(){ tmux -L chtest "$@"; }; T new-session -d -x 70 -y 40 "$HOME/.config/otty/views/claude-history/claude-history '$PWD'"
sleep 3; T capture-pane -p; T send-keys C-a; sleep 1; T capture-pane -p; T kill-server
```
Enter/double-click can start a real session or overwrite the clipboard. When testing, use a fake `HOME`, plus fake `claude` and `pbcopy` first in PATH.

## Keys (tell the user `^A` means Control+A, and to click the panel first)

| Key | Action |
|---|---|
| type | fuzzy filter titles |
| double-click / `⏎` | already open → focus it; a `--wait` terminal → resume there; neither → copy `cd '<dir>' && claude --resume <id>` |
| `^O` | resume inside the panel; back to list when claude exits |
| `^Y` | copy session id |
| `^A` | toggle this folder ↔ all projects (auto "all" if folder has none) |
| `^R` | refresh |

## Otty Details-view reference

```toml
details-view = 'id="info"'                      # built-ins: info outline git files
details-view = 'id="x" kind="tui" title="X" icon="claude" command="prog \"${cwd}\"" cwd="${cwd}"'
details-view = 'id="y" kind="web" url="http://localhost:3000"'
```
- `kind`: `builtin` | `tui` (embedded terminal) | `web`. Listing any view still appends unlisted built-ins.
- Variables: `${cwd} ${folder} ${file} ${pid} ${command} ${branch} ${host} ${user} ${agent} ${shell}`. Inner `"` must be `\"` (TOML single-quoted value).
- A tui view runs with `OTTY_NO_NEW_PANE=1`: it **cannot open tabs/panes** — and Otty also checks by pane identity. `pane run`/`send-text` need `ipc-allow-send-keys` (off by default). Don't bypass either (clearing the variable, AppleScript, a helper that creates tabs) and don't turn that setting on for the user. `pane focus` and `pane list` work, hence the design: an ordinary terminal opts in with `claude-history --wait`, receives a session id, and runs claude itself.
- Same command+folder ⇒ shared process; ≤6 kept alive. Icons: `/Applications/Otty.app/Contents/Resources/view-icons/*.svg`.
- Discover more: `otty config schema --json`, `otty skill show`, docs https://doc.otty.sh/user-interface/details-panel.

## Claude session JSONL facts (for adapting sessions.py)

- Top-level `~/.claude/projects/<dir-slug>/<session-id>.jsonl` only; subdirectories hold subagent transcripts — skip them.
- Title: `{"type":"custom-title","customTitle":…}` (user rename, prefer) > `{"type":"ai-title","aiTitle":…}` (last one wins) > first prompt.
- Real prompts: `type=user`, not `isMeta`/`isSidechain`, content a string or `text` parts, not starting with `<` (command wrappers/reminders) once `<pasted_content>` tags are stripped. `tool_result`-only content is not a prompt.
- Files can be hundreds of MB total: prefix-check raw lines (`{"type":"ai-title"`) before `json.loads`, and cache per file by mtime+size.
- Group by the **first** `cwd` (launch dir). `claude --resume <id>` finds the id from any directory but then runs in the current one, so `cd` to the launch dir first; a mid-session `cd` changes later records' `cwd`.

## Common mistakes

| Mistake | Fix |
|---|---|
| Promising to add items to the left sidebar | Not supported; use Details panel |
| `printf %q` for paths (bash 3.2 on macOS) | Mangles CJK into `$'\255…'`; use single-quote escaping (`squote` in script) |
| Nested parens in fzf binds, e.g. `transform(… reload(…))` or `reload($(…))` | fzf ends the action at first `)`. Use `transform:` colon form, and move logic into a helper subcommand (`claude-history __list` reads `$FZF_PROMPT`) |
| Using last `cwd` of a session | Use first `cwd` |
| Parsing every line with json.loads | Prefix-filter + cache; first index ≈2s for 1 GB, cached ≈0.03s |
| fzf header changing height on click | Rows move between the two clicks and the wrong one is picked. Keep every header two lines |
| `otty tab close -y` to clean up a test tab | Doesn't close a busy tab: use `--force`, only on ids you created, and verify with `tab list` |
| fzf exiting leaves an empty panel | Wrap fzf in `while true` loop |
| Copying scripts into a new folder for a variant | Use `install.sh --id … --days …`; one shared code folder |
| New variant filter as a new script flag only in fzf wrapper | Pass via env (`CH_DAYS`) so `__list` reloads and `^A` inherit it |
