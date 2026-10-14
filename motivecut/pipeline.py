"""Связывает всё вместе: исходники → поиск фрагментов → нарезка → склейка."""
from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from . import selector
from .selector import Clip
from .subtitles import Cue, Segment, build_segments, load_cues
from . import transcribe as asr
from .video import MediaInfo, RenderOptions, add_music, concat, extract_subtitles, probe, render_clip, scene_cuts

VIDEO_EXT = {".mp4", ".mkv", ".avi", ".mov", ".m4v", ".webm", ".wmv", ".ts", ".flv", ".mpg", ".mpeg"}
SUB_EXT = {".srt", ".vtt", ".ass", ".ssa"}

Progress = Callable[[float, str], None]


def _noop(_: float, __: str) -> None:
    pass


@dataclass
class Source:
    video: Path
    subtitles: Path
    info: MediaInfo
    cues: list[Cue]
    segments: list[Segment] = field(default_factory=list)

    @property
    def name(self) -> str:
        return self.video.stem


def _norm(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())


def pair_files(videos: list[Path], subs: list[Path]) -> list[tuple[Path, Path | None]]:
    """Сопоставляет видео и субтитры по имени файла (film.mkv ↔ film.srt / film.ru.srt)."""
    if len(videos) == 1 and len(subs) == 1:
        return [(videos[0], subs[0])]
    pairs: list[tuple[Path, Path | None]] = []
    free = list(subs)
    for v in videos:
        key = _norm(v.stem)
        match = next((s for s in free if _norm(s.stem.split(".")[0]) == key or _norm(s.stem) == key), None)
        if match is None:
            match = next((s for s in free if _norm(s.stem).startswith(key) or key.startswith(_norm(s.stem))), None)
        if match is not None:
            free.remove(match)
        pairs.append((v, match))
    # Оставшиеся субтитры раздаём оставшимся видео по порядку
    for i, (v, s) in enumerate(pairs):
        if s is None and free:
            pairs[i] = (v, free.pop(0))
    return pairs


def load_sources(
    videos: list[Path],
    subs: list[Path],
    workdir: Path,
    max_clip: float = 15.0,
    speech: str = "auto",  # auto | always | never — распознавать ли речь из видео
    whisper_model: str = "small",
    language: str | None = None,
    progress: Progress = _noop,
) -> list[Source]:
    """speech="always": текст берётся из распознанной речи (субтитры не нужны и не мешают);
    speech="auto": субтитры из файла → встроенные в mkv → распознавание речи."""
    sources: list[Source] = []
    next_id = 0
    pairs = [(v, None) for v in videos] if speech == "always" else pair_files(videos, subs)
    for idx, (video, sub) in enumerate(pairs):
        info = probe(video)
        if sub is None and speech != "always" and info.subtitle_streams:
            extracted = workdir / f"{_norm(video.stem) or 'video'}_{idx}.srt"
            if extract_subtitles(video, extracted):
                sub = extracted
        if sub is None:
            if speech == "never":
                raise RuntimeError(f"Нет субтитров для «{video.name}» — загрузите .srt/.vtt/.ass файл "
                                   "или включите распознавание речи.")
            if not info.has_audio:
                raise RuntimeError(f"В «{video.name}» нет звуковой дорожки — распознавать нечего.")
            part = (idx / len(pairs), 1 / len(pairs))
            sub = asr.transcribe(video, info.duration, whisper_model, language,
                                 progress=lambda f, m: progress(part[0] + f * part[1], m))
        cues = load_cues(sub)
        if not cues:
            raise RuntimeError(f"В «{sub.name}» не найдено ни одной реплики.")
        segs = build_segments(cues, source=len(sources), start_id=next_id, max_len=max_clip)
        next_id += len(segs)
        sources.append(Source(video, sub, info, cues, segs))
    if not sources:
        raise RuntimeError("Загрузите хотя бы одно видео.")
    return sources


@dataclass
class FindSettings:
    theme: str
    method: str = "keywords"  # keywords | embeddings | claude
    target_duration: float = 60.0
    min_clip: float = 1.5
    max_clip: float = 15.0
    order: str = "chronological"  # chronological | crescendo | as_is
    api_key: str | None = None
    model: str = "claude-opus-5-5"


def find_clips(sources: list[Source], s: FindSettings) -> tuple[str, list[Clip]]:
    segments = [seg for src in sources for seg in src.segments]
    if not s.theme.strip():
        raise RuntimeError("Опишите общий смысл ролика.")
    if s.method == "claude":
        return selector.claude_pick(
            segments, [src.name for src in sources], s.theme, s.target_duration,
            max_clip=s.max_clip, api_key=s.api_key, model=s.model,
        )
    if s.method == "embeddings":
        scores = selector.embedding_scores(segments, s.theme)
    else:
        scores = selector.keyword_scores(segments, s.theme)
    clips = selector.pick_by_score(segments, scores, s.target_duration, s.min_clip, s.max_clip, s.order)
    return "", clips


def padded_bounds(src: Source, start: float, end: float, before: float, after: float) -> tuple[float, float]:
    """Добавляет «воздух» до и после фразы, не залезая на соседние реплики."""
    prev_end = max((c.end for c in src.cues if c.end <= start + 0.01), default=0.0)
    next_start = min((c.start for c in src.cues if c.start >= end - 0.01), default=src.info.duration)
    new_start = max(start - before, prev_end + 0.05, 0.0)
    new_end = min(end + after, next_start - 0.05, src.info.duration)
    return min(new_start, start), max(new_end, min(end, src.info.duration))


def snap_to_scenes(src: Source, start: float, end: float, text_start: float, text_end: float,
                   reach: float = 1.5) -> tuple[float, float]:
    """Двигает границы клипа к ближайшей смене кадра, если она рядом и не режет фразу/соседнюю реплику."""
    prev_end = max((c.end for c in src.cues if c.end <= text_start + 0.01), default=0.0)
    next_start = min((c.start for c in src.cues if c.start >= text_end - 0.01), default=src.info.duration)
    lo = max(text_start - reach, prev_end + 0.05, 0.0)
    hi = min(text_end + reach, next_start - 0.05, src.info.duration)
    cuts_before = [t for t in scene_cuts(src.video, lo, text_start) if lo <= t <= text_start]
    cuts_after = [t for t in scene_cuts(src.video, text_end, hi) if text_end <= t <= hi]
    if cuts_before:
        start = max(cuts_before)  # начинаем ровно с новой сцены
    if cuts_after:
        end = min(cuts_after) - 0.04  # заканчиваем за кадр до следующей сцены
    return start, max(end, text_end)


def render(
    sources: list[Source],
    clips: list[Clip],
    out_path: str | Path,
    opts: RenderOptions,
    pad_before: float = 0.25,
    pad_after: float = 0.6,
    music: str | Path | None = None,
    music_volume: float = 0.25,
    snap_scenes: bool = True,
    progress: Progress = _noop,
) -> Path:
    if not clips:
        raise RuntimeError("Нет выбранных фрагментов для сборки.")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="motivecut_"))
    try:
        parts: list[Path] = []
        for i, clip in enumerate(clips):
            progress(i / (len(clips) + 1), f"Нарезка клипа {i + 1} из {len(clips)}")
            src = sources[clip.source]
            st, en = padded_bounds(src, clip.start, clip.end, pad_before, pad_after)
            if snap_scenes:
                st, en = snap_to_scenes(src, st, en, clip.start, clip.end)
            part = tmp / f"clip_{i:03}.mp4"
            render_clip(src.video, st, en, part, opts, has_audio=src.info.has_audio, cues=src.cues)
            parts.append(part)
        progress(len(clips) / (len(clips) + 1), "Склейка")
        if music:
            joined = tmp / "joined.mp4"
            concat(parts, joined)
            progress(0.97, "Добавление музыки")
            add_music(joined, music, out_path, music_volume)
        else:
            concat(parts, out_path)
        progress(1.0, "Готово")
        return out_path
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
