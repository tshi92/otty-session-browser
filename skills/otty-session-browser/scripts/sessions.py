#!/usr/bin/env python3
"""Index Claude Code sessions in ~/.claude/projects for the Otty "Claude" details view.

  sessions.py list [--all] [DIR]   tab-separated rows for fzf: id, cwd, display
                                   (env CH_DAYS=N: only sessions active in the last N days)
  sessions.py preview ID           human-readable summary of one session
  sessions.py cwd ID               print the session's working directory

Results are cached per file (keyed by mtime + size) in ~/.cache/otty-session-browser.
"""
import json
import os
import re
import sys
import time
import unicodedata

PROJECTS = os.path.expanduser(os.environ.get("CLAUDE_CONFIG_DIR", "~/.claude")) + "/projects"
CACHE_DIR = os.path.expanduser("~/.cache/otty-session-browser")
CACHE = os.path.join(CACHE_DIR, "index.json")
VERSION = 4

LANG = "zh" if os.environ.get("CH_LANG") == "zh" else "en"
STR = {
    "zh": {"min": "{}分钟前", "hour": "{}小时前", "day": "{}天前", "notfound": "找不到这个会话",
           "untitled": "(无标题)", "dir": "目录", "time": "时间", "prompts": "提问", "unit": " 条",
           "first": "第一条", "recent": "最近的提问", "w": 9},
    "en": {"min": "{}m ago", "hour": "{}h ago", "day": "{}d ago", "notfound": "Session not found",
           "untitled": "(untitled)", "dir": "Dir ", "time": "Time", "prompts": "Prompts", "unit": "",
           "first": "First prompt", "recent": "Recent prompts", "w": 8},
}[LANG]

# ANSI colours for fzf (--ansi)
DIM, CYAN, YEL, MAG, RST = "\033[2m", "\033[36m", "\033[33m", "\033[35m", "\033[0m"


def clean(text, limit=None):
    text = " ".join(str(text).split())
    if limit and len(text) > limit:
        text = text[: limit - 1] + "…"
    return text


def user_text(msg):
    """Return the typed prompt of a user record, or None for tool results / meta records."""
    content = (msg.get("message") or {}).get("content")
    if isinstance(content, list):
        parts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
        if not parts:
            return None  # tool_result etc.
        content = "\n".join(parts)
    if not isinstance(content, str):
        return None
    # Pasted text is still something the user sent: keep it, drop only the wrapper tags.
    s = re.sub(r"</?pasted_content\b[^>]*>", "", content).strip()
    if not s or s.startswith("<") or s.startswith("Caveat:") or s.startswith("[Request interrupted"):
        return None  # command wrappers, system reminders, interrupts
    return s


def scan(path):
    info = {"title": "", "custom": "", "first": "", "last": "", "prompts": 0,
            "cwd": "", "branch": "", "start": "", "end": "", "recent": []}
    with open(path, "rb") as fh:
        for raw in fh:
            head = raw[:400]
            if head.startswith(b'{"type":"ai-title"'):
                try:
                    info["title"] = json.loads(raw).get("aiTitle", "") or info["title"]
                except ValueError:
                    pass
                continue
            if head.startswith(b'{"type":"custom-title"'):
                try:
                    info["custom"] = json.loads(raw).get("customTitle", "") or info["custom"]
                except ValueError:
                    pass
                continue
            if b'"type":"user"' not in head and b'"type":"assistant"' not in head:
                continue
            is_user = b'"type":"user"' in head
            # Assistant lines are only needed for cwd/timestamps; skip the big ones once known.
            if not is_user and info["cwd"] and len(raw) > 4000:
                continue
            try:
                o = json.loads(raw)
            except ValueError:
                continue
            if o.get("isSidechain"):
                continue
            ts = o.get("timestamp") or ""
            if ts:
                info["start"] = info["start"] or ts
                info["end"] = ts
            info["cwd"] = info["cwd"] or o.get("cwd") or ""  # launch dir: what --resume needs
            info["branch"] = o.get("gitBranch") or info["branch"]
            if is_user and not o.get("isMeta"):
                t = user_text(o)
                if t:
                    info["prompts"] += 1
                    info["first"] = info["first"] or clean(t, 300)
                    info["last"] = clean(t, 300)
                    info["recent"] = (info["recent"] + [clean(t, 400)])[-6:]
    return info


def load_index():
    try:
        with open(CACHE) as fh:
            data = json.load(fh)
        if data.get("version") == VERSION:
            return data["files"]
    except (OSError, ValueError, KeyError):
        pass
    return {}


def build_index():
    cache = load_index()
    fresh = {}
    changed = False
    try:
        projects = os.listdir(PROJECTS)
    except OSError:
        projects = []
    for proj in projects:
        pdir = os.path.join(PROJECTS, proj)
        try:
            names = os.listdir(pdir)
        except OSError:
            continue
        for name in names:
            if not name.endswith(".jsonl"):
                continue
            path = os.path.join(pdir, name)
            try:
                st = os.stat(path)
            except OSError:
                continue
            key = f"{st.st_mtime_ns}:{st.st_size}"
            old = cache.get(path)
            if old and old.get("key") == key:
                fresh[path] = old
                continue
            try:
                info = scan(path)
            except OSError:
                continue
            info.update(key=key, id=name[:-6], mtime=st.st_mtime)
            fresh[path] = info
            changed = True
    if changed or len(fresh) != len(cache):
        os.makedirs(CACHE_DIR, exist_ok=True)
        tmp = f"{CACHE}.{os.getpid()}.tmp"  # panel and waiting terminals index concurrently
        with open(tmp, "w") as fh:
            json.dump({"version": VERSION, "files": fresh}, fh, ensure_ascii=False)
        os.replace(tmp, CACHE)
    return [s for s in fresh.values() if s["prompts"] > 0]


def ago(mtime):
    d = time.time() - mtime
    if d < 3600:
        return STR["min"].format(max(1, int(d // 60)))
    if d < 86400:
        return STR["hour"].format(int(d // 3600))
    if d < 86400 * 30:
        return STR["day"].format(int(d // 86400))
    return time.strftime("%Y-%m-%d", time.localtime(mtime))


def width(s):
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def pad(s, n):
    return s + " " * max(0, n - width(s))


def short_path(p):
    home = os.path.expanduser("~")
    return "~" + p[len(home):] if p.startswith(home) else p


def under(path, root):
    root = root.rstrip("/") or "/"
    return path == root or path.startswith(root + "/")


def cmd_list(args):
    show_all = "--all" in args
    rest = [a for a in args if a != "--all"]
    root = os.path.realpath(rest[0]) if rest else ""
    # CH_DAYS=N keeps sessions whose last activity (file mtime) is within N days; empty/0 = no limit.
    try:
        days = float(os.environ.get("CH_DAYS") or 0)
    except ValueError:
        days = 0
    cutoff = time.time() - days * 86400 if days > 0 else 0
    rows = sorted(build_index(), key=lambda s: s["mtime"], reverse=True)
    for s in rows:
        if s["mtime"] < cutoff:
            break  # newest first

        cwd = s["cwd"]
        if not show_all and root and not (under(cwd, root) or under(os.path.realpath(cwd), root)):
            continue
        title = clean(s["custom"] or s["title"] or s["first"], 60)
        when = pad(ago(s["mtime"]), STR["w"])
        extra = f" {MAG}{os.path.basename(cwd.rstrip('/')) or cwd}{RST}" if show_all or cwd != root else ""
        line = f"{DIM}{when}{RST} {title}{extra} {DIM}({s['prompts']}){RST}"
        print(f"{s['id']}\t{cwd}\t{line}")


def find(sid):
    for s in build_index():
        if s["id"] == sid:
            return s
    return None


def cmd_preview(args):
    s = find(args[0]) if args else None
    if not s:
        print(STR["notfound"])
        return
    title = s["custom"] or s["title"] or STR["untitled"]
    print(f"{YEL}{title}{RST}")
    print(f"{DIM}{STR['dir']}{RST}  {short_path(s['cwd'])}" + (f"  {CYAN}{s['branch']}{RST}" if s["branch"] else ""))
    start = s["start"][:16].replace("T", " ")
    try:
        from datetime import datetime
        start = datetime.fromisoformat(s["start"].replace("Z", "+00:00")).astimezone().strftime("%Y-%m-%d %H:%M")
    except ValueError:
        pass
    print(f"{DIM}{STR['time']}{RST}  {start} → {ago(s['mtime'])}   {DIM}{STR['prompts']}{RST} {s['prompts']}{STR['unit']}")
    print(f"{DIM}ID{RST}    {s['id']}")
    print()
    print(f"{CYAN}▍ {STR['first']}{RST}")
    print(s["first"])
    recent = [r for r in s["recent"] if r]
    if s["prompts"] > 1 and recent:
        print()
        print(f"{CYAN}▍ {STR['recent']}{RST}")
        for r in recent[-5:]:
            print(f"• {r}")


def cmd_cwd(args):
    s = find(args[0]) if args else None
    if s:
        print(s["cwd"])


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    cmd, args = sys.argv[1], sys.argv[2:]
    {"list": cmd_list, "preview": cmd_preview, "cwd": cmd_cwd}.get(cmd, lambda a: print(__doc__))(args)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        pass
