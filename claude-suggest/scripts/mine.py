#!/usr/bin/env python3
"""Extract typed prompts from Claude Code transcripts and surface repeat signals.

Transcripts live at ~/.claude/projects/<slug>/<session>.jsonl, one JSON object
per line. Records are filtered on their own `cwd` field rather than on the
directory slug, because the slug encoding is not documented and guessing it
silently returns zero results.
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Injected by the harness and wrapped around, or prepended to, real prompt text.
# Stripped rather than used to reject the record: a genuine prompt very often
# arrives with a system-reminder or ide_opened_file block glued to the front.
INJECTED_TAGS = [
    "system-reminder",
    "ide_opened_file",
    "ide_selection",
    "command-name",
    "command-message",
    "command-args",
    "local-command-stdout",
]

# Whole-message artifacts that are not something the user typed at the prompt.
ARTIFACT_PREFIXES = (
    "Base directory for this skill:",
    "[Request interrupted by user",
    "This session is being continued from a p",
    "Continue from where you left off.",
    "The session was unintentionally disconne",
    "Caveat: The messages below were generated",
)

# Repairing something Claude already did. Only meaningful mid-session.
CORRECTION_PATTERNS = re.compile(
    r"\b(no,|nope|stop|actually|instead|revert|undo|rollback|"
    r"i said|i asked|you (didn't|did not|were|forgot|missed|shouldn't)|"
    r"that's (wrong|not)|not what i|why did you|again,|still (broken|wrong|failing)|"
    r"remove the|put back|as i mentioned|like i said)\b",
    re.I,
)

# Standing instructions the user types pre-emptively. These matter as much as
# corrections and are far more common here: a constraint restated across
# sessions is one CLAUDE.md should be carrying instead of the user.
DIRECTIVE_PATTERNS = re.compile(
    r"\b(don't|do not|never|always|make sure|be sure|ensure|keep it|keep the|"
    r"avoid|prefer|only use|use \w+ instead|no need to|skip the|worry about|"
    r"remember to|must|should always|should never)\b",
    re.I,
)

STOPWORDS = frozenset(
    """a an and are as at be but by for from has have i if in is it its me my not of on
    or so that the this to up use used using want was we what when with you your don't
    please make sure just also need needs should would could can will do does did get
    got let like too very only into out over then than them they there here how all any
    each more most other some such no nor own same our us""".split()
)


def load_records(root: Path):
    for path in sorted(root.rglob("*.jsonl")):
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue  # partially written line at the tail of a live session


def message_text(rec):
    content = rec.get("message", {}).get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            b.get("text", "")
            for b in content
            if isinstance(b, dict) and b.get("type") == "text"
        )
    return ""


def clean(text):
    for tag in INJECTED_TAGS:
        text = re.sub(rf"<{tag}>.*?</{tag}>", "", text, flags=re.S)
        text = re.sub(rf"<{tag}>.*", "", text, flags=re.S)  # unclosed
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def is_human_prompt(rec):
    return (
        rec.get("type") == "user"
        and not rec.get("toolUseResult")
        and not rec.get("isSidechain")
        and not rec.get("isMeta")
    )


def collect(root, scope_cwd, since_days):
    cutoff = None
    if since_days:
        cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)

    prompts = []
    for rec in load_records(root):
        if not is_human_prompt(rec):
            continue
        cwd = rec.get("cwd", "")
        if scope_cwd and not (cwd == scope_cwd or cwd.startswith(scope_cwd + "/")):
            continue
        ts = rec.get("timestamp", "")
        if cutoff and ts:
            try:
                if datetime.fromisoformat(ts.replace("Z", "+00:00")) < cutoff:
                    continue
            except ValueError:
                pass
        text = clean(message_text(rec))
        if not text or text.startswith(ARTIFACT_PREFIXES):
            continue
        prompts.append(
            {
                "session": rec.get("sessionId", ""),
                "ts": ts,
                "cwd": cwd,
                "text": text,
            }
        )
    prompts.sort(key=lambda p: p["ts"])
    return prompts


def classify(prompts):
    """Split prompts into mid-session repairs and pre-emptive standing orders.

    Most sessions here are a single turn, so gating on "not the first turn"
    alone finds almost nothing. Directives are therefore matched anywhere,
    corrections only after the opening turn where the word implies a repair.
    """
    seen_session = set()
    corrections, directives = [], []
    for p in prompts:
        first = p["session"] not in seen_session
        seen_session.add(p["session"])
        head = p["text"][:400]
        if not first and CORRECTION_PATTERNS.search(head):
            corrections.append(p)
        if DIRECTIVE_PATTERNS.search(head):
            m = DIRECTIVE_PATTERNS.search(head)
            directives.append({**p, "trigger": m.group(0).lower()})
    return corrections, directives


def find_themes(prompts, min_sessions=2):
    """Word shingles recurring across distinct sessions.

    Cross-session repetition is the signal worth acting on: something restated
    in three separate sessions is a standing preference that belongs in
    CLAUDE.md, whereas repetition inside one session is just that task.
    """
    shingle_sessions = defaultdict(set)
    shingle_example = {}
    for p in prompts:
        words = [w for w in re.findall(r"[a-z0-9$_.'-]+", p["text"].lower())]
        kept = [w for w in words if w not in STOPWORDS and len(w) > 2]
        for n in (2, 3, 4):
            for i in range(len(kept) - n + 1):
                sh = " ".join(kept[i : i + n])
                shingle_sessions[sh].add(p["session"])
                shingle_example.setdefault(sh, p["text"][:160])

    themes = [
        {
            "phrase": sh,
            "sessions": len(sess),
            "signature": frozenset(sess),
            "example": shingle_example[sh],
        }
        for sh, sess in shingle_sessions.items()
        if len(sess) >= min_sessions
    ]
    # Prefer longer phrases at equal support; they are more specific.
    themes.sort(key=lambda t: (-t["sessions"], -len(t["phrase"].split())))

    # One repeated sentence emits a whole sliding window of overlapping
    # n-grams, all backed by exactly the same sessions. Substring checks miss
    # them because the windows are offset, so collapse on the session set
    # itself and keep the two longest phrases as representatives.
    per_signature, kept = Counter(), []
    for t in themes:
        sig = t["signature"]
        if per_signature[sig] >= 2:
            continue
        per_signature[sig] += 1
        kept.append({k: v for k, v in t.items() if k != "signature"})
    return kept


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--scope",
        choices=("global", "project"),
        default="project",
        help="global = every project's transcripts; project = this repo only",
    )
    ap.add_argument(
        "--project",
        default=str(Path.cwd()),
        help="project root for --scope project (default: cwd)",
    )
    ap.add_argument("--since", type=int, default=0, help="only the last N days")
    ap.add_argument(
        "--root",
        default=str(Path.home() / ".claude" / "projects"),
        help="transcript store",
    )
    ap.add_argument("--max-themes", type=int, default=25)
    ap.add_argument("--text", action="store_true", help="human-readable output")
    args = ap.parse_args()

    root = Path(args.root).expanduser()
    if not root.is_dir():
        sys.exit(f"no transcript store at {root}")

    scope_cwd = None if args.scope == "global" else str(Path(args.project).resolve())
    prompts = collect(root, scope_cwd, args.since)
    corrections, directives = classify(prompts)
    themes = find_themes(prompts)[: args.max_themes]

    result = {
        "scope": args.scope,
        "project": scope_cwd,
        "since_days": args.since or None,
        "counts": {
            "prompts": len(prompts),
            "sessions": len({p["session"] for p in prompts}),
            "projects": len({p["cwd"] for p in prompts}),
            "corrections": len(corrections),
            "directives": len(directives),
        },
        "corrections": corrections,
        "directives": directives,
        "directive_triggers": Counter(d["trigger"] for d in directives).most_common(),
        "themes": themes,
        "prompts": prompts,
    }

    if not args.text:
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return

    c = result["counts"]
    print(
        f"{c['prompts']} prompts / {c['sessions']} sessions / {c['projects']} dirs / "
        f"{c['corrections']} corrections / {c['directives']} directives"
    )
    print(f"\n--- corrections ({len(corrections)}) ---")
    for p in corrections:
        print(f"[{p['ts'][:10]}] {' '.join(p['text'].split())[:180]}")
    print(f"\n--- directives ({len(directives)}) ---")
    for d in directives:
        print(f"[{d['trigger']:<12}] {' '.join(d['text'].split())[:160]}")
    print(f"\n--- recurring phrases ({len(themes)}) ---")
    for t in themes:
        print(f"{t['sessions']:>3} sessions  {t['phrase']}")


if __name__ == "__main__":
    main()
