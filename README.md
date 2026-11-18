# otty-session-browser

A Claude Code plugin that adds a **Claude** tab to the [Otty](https://otty.sh) terminal's Details panel (`⌘⇧R`). The tab lists your past Claude Code sessions with fzf, shows a preview of each, and lets you resume one.

Otty's left sidebar can only hold tabs, so the session list goes in the Details panel instead.

```
  ⏎ copy resume cmd  ^O resume here  ^Y copy id
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
- `fzf` and `python3` (`brew install fzf`)

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

## Keys

Click the panel first so it has focus. `^` means Control.

| Key | Action |
|---|---|
| type | fuzzy filter |
| `⏎` | copy `cd '<dir>' && claude --resume <id>` |
| `^O` | resume inside the panel |
| `^Y` | copy the session id |
| `^A` | switch between this folder and all projects |
| `^R` | refresh |

## Language

- `--lang en` or `--lang zh` fixes the UI language.
- Without `--lang`, Chinese is used when `LANG` or the first entry of macOS AppleLanguages starts with `zh`; otherwise English.
- `CH_LANG=en|zh` in the environment also sets it.

## License

MIT
