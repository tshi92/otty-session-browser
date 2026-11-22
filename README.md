# otty-session-browser

A Claude Code plugin that adds a **Claude** tab to the [Otty](https://otty.sh) terminal's Details panel (`⌘⇧R`). The tab lists your past Claude Code sessions with fzf, shows a preview of each, and opens the one you double-click in a terminal tab that you left waiting.

Otty's left sidebar can only hold tabs, so the session list goes in the Details panel instead.

```
  ⏎/dbl-click open  ^O resume here  ^Y copy id
  ^A here/all  ^R refresh
Here>                                         11/11
───────────────────────────────────────────────────
▌ 1m ago   Fix flaky upload test (18)
▌ 3h ago   Refactor auth middleware (7)
───────────────────────────────────────────────────
Fix flaky upload test
Dir   ~/Git/app  main
Time  2026-11-18 15:57 → 1m ago   Prompts 18
▍ First prompt
…
```

## Requirements

- macOS (the copy keys use `pbcopy`)
- Otty 1.6 or later, with Claude Code enabled under Settings ▸ Agents
- `fzf` and `python3` (`brew install fzf`); tested with fzf 0.70

## Install

```bash
/plugin marketplace add tshi92/otty-session-browser   # or a local path to this folder
/plugin install otty-session-browser@otty-session-browser
```

Then ask Claude something like *"add my Claude session history to Otty"*. The skill shows you a dry run first and installs once you confirm.

You can also run the installer yourself:

```bash
bash skills/otty-session-browser/scripts/install.sh --dry-run
bash skills/otty-session-browser/scripts/install.sh [--lang en|zh] [--days N] [--id ID --title TITLE]
bash skills/otty-session-browser/scripts/install.sh --uninstall [--id ID]
```

## Open in a normal terminal

Otty doesn't let a panel view create tabs, or type into other terminals unless you turn on `ipc-allow-send-keys`. This plugin doesn't bypass either rule and doesn't need that setting. Instead, a terminal opts in. Run this in an ordinary tab and leave it there:

```bash
~/.config/otty/views/claude-history/claude-history --wait     # add --lang zh for Chinese
```

Then double-click a session (or press `⏎`) in the panel:

| Situation | What happens |
|---|---|
| The session is already open in Otty | switches to it |
| A terminal is waiting | switches to it, then runs `cd <dir>` and `claude --resume <id>` there |
| No terminal is waiting | copies that command to the clipboard |

When Claude exits, the tab waits again. For several sessions at once, leave several tabs waiting. The panel hands over a session id only, never a command. Sessions start with your default Claude Code permission mode.

## Keys

Click the panel first so it has focus. `^` means Control.

| Key | Action |
|---|---|
| type | fuzzy filter |
| double-click / `⏎` | open in a waiting terminal (see above) |
| `^O` | resume inside the panel |
| `^Y` | copy the session id |
| `^A` | switch between this folder and all projects |
| `^R` | refresh |

## Update

```bash
claude plugin marketplace update otty-session-browser
claude plugin update otty-session-browser@otty-session-browser
```

Then, in a new session, ask Claude to *"update my Otty session panel"* (it re-runs the installer) and restart Otty.

## Language

- `--lang en` or `--lang zh` fixes the UI language.
- Without `--lang`, Chinese is used when `LANG` or the first entry of macOS AppleLanguages starts with `zh`; otherwise English.
- `CH_LANG=en|zh` in the environment also sets it.

## Changelog

### 1.1.0

- Double-click or `⏎` opens the session in a waiting terminal (`--wait`), or switches to it if it's already open.
- Fixed: double-click could pick the row above the one clicked.
- Fixed: prompts that start with pasted text were dropped.
- Fixed: "copied" was shown when nothing was selected.
- Fixed: concurrent index rebuilds could fail.
- Fixed: `--uninstall --dry-run` said shared code would be removed while another view used it.

## License

MIT
