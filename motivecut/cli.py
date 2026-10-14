"""Запуск из командной строки:

python -m motivecut.cli --video film.mkv --subs film.srt --theme "никогда не сдавайся" -o out.mp4
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from .pipeline import FindSettings, find_clips, load_sources, render
from .video import FORMATS, RenderOptions


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Автоматическая мотивационная нарезка из фильмов")
    p.add_argument("--video", nargs="+", required=True, help="видеофайлы")
    p.add_argument("--subs", nargs="*", default=[], help="файлы субтитров (.srt/.vtt/.ass)")
    p.add_argument("--theme", required=True, help="общий смысл ролика")
    p.add_argument("-o", "--out", default="output/motivation.mp4")
    p.add_argument("--method", choices=["keywords", "embeddings", "claude"], default="keywords")
    p.add_argument("--duration", type=float, default=60, help="целевая длительность, сек")
    p.add_argument("--max-clip", type=float, default=15)
    p.add_argument("--order", choices=["chronological", "crescendo", "as_is"], default="chronological")
    p.add_argument("--format", choices=list(FORMATS), default="16:9 (YouTube)")
    p.add_argument("--burn-subs", action="store_true", help="вшить субтитры в видео")
    p.add_argument("--music", help="фоновая музыка")
    p.add_argument("--music-volume", type=float, default=0.25)
    p.add_argument("--dry-run", action="store_true", help="только показать найденные фрагменты")
    a = p.parse_args(argv)

    workdir = Path(tempfile.mkdtemp(prefix="motivecut_subs_"))
    sources = load_sources([Path(v) for v in a.video], [Path(s) for s in a.subs], workdir, a.max_clip)
    title, clips = find_clips(
        sources,
        FindSettings(theme=a.theme, method=a.method, target_duration=a.duration, max_clip=a.max_clip, order=a.order),
    )
    if title:
        print(f"Название: {title}")
    total = 0.0
    for i, c in enumerate(clips, 1):
        total += c.duration
        print(f"{i:2}. [{sources[c.source].name} {c.start:7.1f}-{c.end:7.1f}] {c.text}")
        if c.reason:
            print(f"     → {c.reason}")
    print(f"Всего фрагментов: {len(clips)}, ~{total:.0f} c")
    if a.dry_run or not clips:
        return
    opts = RenderOptions(format=a.format, burn_subs=a.burn_subs)
    out = render(sources, clips, a.out, opts, music=a.music, music_volume=a.music_volume,
                 progress=lambda f, m: print(f"[{f * 100:3.0f}%] {m}"))
    print(f"Готово: {out.resolve()}")


if __name__ == "__main__":
    main()
