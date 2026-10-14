"""Чтение субтитров (SRT / VTT / ASS) и склейка реплик в смысловые сегменты."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Cue:
    start: float
    end: float
    text: str


@dataclass
class Segment:
    """Непрерывный кусок речи из одной или нескольких реплик."""

    id: int
    source: int
    start: float
    end: float
    cues: list[Cue] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(c.text for c in self.cues)

    @property
    def duration(self) -> float:
        return self.end - self.start


_TAG_RE = re.compile(r"<[^>]+>|\{[^}]*\}")
_TIME_RE = re.compile(
    r"(?:(\d+):)?(\d{1,2}):(\d{2})[,.](\d{1,3})\s*-->\s*(?:(\d+):)?(\d{1,2}):(\d{2})[,.](\d{1,3})"
)


def read_text(path: str | Path) -> str:
    data = Path(path).read_bytes()
    for enc in ("utf-8-sig", "utf-16", "cp1251"):
        try:
            text = data.decode(enc)
        except UnicodeDecodeError:
            continue
        if enc == "utf-16" and not data.startswith((b"\xff\xfe", b"\xfe\xff")):
            continue
        return text
    return data.decode("latin-1")


def _clean(text: str) -> str:
    text = _TAG_RE.sub("", text).replace("\\N", " ").replace("\\n", " ")
    text = re.sub(r"^\s*-\s*", "", text, flags=re.M)
    return re.sub(r"\s+", " ", text).strip()


def _secs(h, m, s, ms) -> float:
    return int(h or 0) * 3600 + int(m) * 60 + int(s) + int(ms.ljust(3, "0")) / 1000


def parse_srt_vtt(text: str) -> list[Cue]:
    cues: list[Cue] = []
    blocks = re.split(r"\r?\n\s*\r?\n", text.replace("\r\n", "\n"))
    for block in blocks:
        lines = block.strip().split("\n")
        for i, line in enumerate(lines):
            m = _TIME_RE.search(line)
            if not m:
                continue
            g = m.groups()
            body = _clean(" ".join(lines[i + 1 :]))
            if body:
                cues.append(Cue(_secs(*g[:4]), _secs(*g[4:]), body))
            break
    return cues


def _ass_time(t: str) -> float:
    h, m, s = t.strip().split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def parse_ass(text: str) -> list[Cue]:
    cues: list[Cue] = []
    fmt: list[str] | None = None
    in_events = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("["):
            in_events = s.lower() == "[events]"
            continue
        if not in_events:
            continue
        if s.lower().startswith("format:"):
            fmt = [f.strip().lower() for f in s[7:].split(",")]
        elif s.lower().startswith("dialogue:") and fmt:
            parts = s[9:].split(",", len(fmt) - 1)
            row = dict(zip(fmt, parts))
            body = _clean(row.get("text", ""))
            if body:
                cues.append(Cue(_ass_time(row["start"]), _ass_time(row["end"]), body))
    return cues


def load_cues(path: str | Path) -> list[Cue]:
    text = read_text(path)
    ext = Path(path).suffix.lower()
    cues = parse_ass(text) if ext in (".ass", ".ssa") else parse_srt_vtt(text)
    cues = [c for c in cues if c.end > c.start]
    cues.sort(key=lambda c: c.start)
    return cues


_SENTENCE_END = re.compile(r"[.!?…]['\"»)]*$")


def build_segments(
    cues: list[Cue],
    source: int = 0,
    start_id: int = 0,
    max_gap: float = 1.2,
    max_len: float = 15.0,
    min_len: float = 1.0,
) -> list[Segment]:
    """Склеивает соседние реплики в сегменты, стараясь резать по концу фразы."""
    segments: list[Segment] = []
    cur: Segment | None = None
    for cue in cues:
        if cur is not None:
            gap = cue.start - cur.end
            too_long = cue.end - cur.start > max_len
            sentence_done = bool(_SENTENCE_END.search(cur.cues[-1].text)) and cur.duration >= min_len
            if gap > max_gap or too_long or sentence_done:
                segments.append(cur)
                cur = None
        if cur is None:
            cur = Segment(start_id + len(segments), source, cue.start, cue.end, [cue])
        else:
            cur.cues.append(cue)
            cur.end = max(cur.end, cue.end)
    if cur is not None:
        segments.append(cur)
    return segments


def write_srt(cues: list[Cue], path: str | Path, offset: float = 0.0, limit: float | None = None) -> int:
    """Пишет SRT со сдвигом времени (для вшивания субтитров в отдельный клип)."""

    def fmt(t: float) -> str:
        ms = int(round(max(t, 0) * 1000))
        h, ms = divmod(ms, 3_600_000)
        m, ms = divmod(ms, 60_000)
        s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    out, n = [], 0
    for c in cues:
        st, en = c.start - offset, c.end - offset
        if en <= 0 or (limit is not None and st >= limit):
            continue
        st = max(st, 0)
        if limit is not None:
            en = min(en, limit)
        n += 1
        out.append(f"{n}\n{fmt(st)} --> {fmt(en)}\n{c.text}\n")
    Path(path).write_text("\n".join(out), encoding="utf-8")
    return n
