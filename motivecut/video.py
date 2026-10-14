"""Нарезка и склейка видео через ffmpeg."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .subtitles import Cue, write_srt

FORMATS = {
    "16:9 (YouTube)": (1920, 1080, "pad"),
    "9:16 размытый фон (Shorts/Reels/TikTok)": (1080, 1920, "blur"),
    "9:16 обрезка по центру": (1080, 1920, "crop"),
    "1:1 квадрат": (1080, 1080, "crop"),
}


@lru_cache(maxsize=1)
def ffmpeg_exe() -> str:
    env = os.environ.get("FFMPEG")
    if env:
        return env
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(
            "Не найден ffmpeg. Установите его (https://ffmpeg.org) или выполните: pip install imageio-ffmpeg"
        ) from e


@lru_cache(maxsize=1)
def has_subtitles_filter() -> bool:
    out = subprocess.run([ffmpeg_exe(), "-hide_banner", "-filters"], capture_output=True, text=True)
    return " subtitles " in out.stdout


@dataclass
class MediaInfo:
    duration: float
    has_audio: bool
    width: int
    height: int
    subtitle_streams: int


def probe(path: str | Path) -> MediaInfo:
    """Читает параметры файла из вывода `ffmpeg -i` (ffprobe не нужен)."""
    out = subprocess.run(
        [ffmpeg_exe(), "-hide_banner", "-i", str(path)], capture_output=True, text=True, errors="replace"
    ).stderr
    m = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", out)
    if not m:
        raise RuntimeError(f"Не удалось прочитать видео: {path}")
    duration = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
    vm = re.search(r"Stream #.*Video:.*?(\d{2,5})x(\d{2,5})", out)
    w, h = (int(vm[1]), int(vm[2])) if vm else (0, 0)
    return MediaInfo(
        duration=duration,
        has_audio=bool(re.search(r"Stream #.*Audio:", out)),
        width=w,
        height=h,
        subtitle_streams=len(re.findall(r"Stream #.*Subtitle:", out)),
    )


def extract_subtitles(video: str | Path, out_srt: str | Path) -> bool:
    """Достаёт первую дорожку субтитров из контейнера (mkv/mp4)."""
    r = subprocess.run(
        [ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error", "-i", str(video), "-map", "0:s:0", str(out_srt)],
        capture_output=True,
        text=True,
    )
    return r.returncode == 0 and Path(out_srt).exists() and Path(out_srt).stat().st_size > 0


@dataclass
class RenderOptions:
    format: str = "16:9 (YouTube)"
    fps: int = 30
    crf: int = 20
    preset: str = "medium"
    fade: float = 0.25
    burn_subs: bool = False
    sub_font_size: int = 0  # 0 = подобрать автоматически
    normalize_audio: bool = True


def _video_filter(opts: RenderOptions, dur: float, srt_name: str | None) -> str:
    w, h, mode = FORMATS[opts.format]
    if mode == "pad":
        chain = (
            f"[0:v]scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,setsar=1"
        )
    elif mode == "crop":
        chain = f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1"
    else:  # blur
        chain = (
            f"[0:v]split=2[bg0][fg0];"
            f"[bg0]scale={w // 4}:{h // 4}:force_original_aspect_ratio=increase,crop={w // 4}:{h // 4},"
            f"boxblur=10:2,scale={w}:{h}[bg];"
            f"[fg0]scale={w}:{h}:force_original_aspect_ratio=decrease[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1"
        )
    chain += f",fps={opts.fps}"
    if srt_name:
        size = opts.sub_font_size or (11 if h > w else 16)
        margin = 70 if h > w else 25
        style = f"FontName=Arial,FontSize={size},Bold=1,Outline=2,Shadow=0,MarginV={margin},Alignment=2"
        chain += f",subtitles={srt_name}:force_style='{style}'"
    if opts.fade > 0 and dur > 2 * opts.fade:
        chain += f",fade=t=in:st=0:d={opts.fade},fade=t=out:st={dur - opts.fade:.3f}:d={opts.fade}"
    return chain + ",format=yuv420p[v]"


def _audio_filter(opts: RenderOptions, dur: float, input_idx: int) -> str:
    chain = f"[{input_idx}:a]aresample=48000"
    if opts.normalize_audio:
        chain += ",loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000"
    if opts.fade > 0 and dur > 2 * opts.fade:
        chain += f",afade=t=in:st=0:d={opts.fade},afade=t=out:st={dur - opts.fade:.3f}:d={opts.fade}"
    return chain + ",aformat=channel_layouts=stereo[a]"


def render_clip(
    src: str | Path,
    start: float,
    end: float,
    out: str | Path,
    opts: RenderOptions,
    has_audio: bool = True,
    cues: list[Cue] | None = None,
) -> None:
    out = Path(out)
    dur = end - start
    srt_name = None
    if opts.burn_subs and cues and has_subtitles_filter():
        srt_path = out.with_suffix(".srt")
        if write_srt(cues, srt_path, offset=start, limit=dur):
            srt_name = srt_path.name  # относительный путь: ffmpeg запускается из папки клипа

    cmd = [ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
           "-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", str(Path(src).resolve())]
    audio_idx = 0
    if not has_audio:
        cmd += ["-f", "lavfi", "-t", f"{dur:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
        audio_idx = 1
    fc = _video_filter(opts, dur, srt_name) + ";" + _audio_filter(opts, dur, audio_idx)
    cmd += [
        "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", opts.preset, "-crf", str(opts.crf), "-r", str(opts.fps),
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-t", f"{dur:.3f}", "-movflags", "+faststart", out.name,
    ]
    r = subprocess.run(cmd, cwd=out.parent, capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg не смог вырезать клип {start:.1f}–{end:.1f} c:\n{r.stderr[-2000:]}")


def concat(clips: list[Path], out: str | Path) -> None:
    out = Path(out).resolve()
    workdir = clips[0].parent
    lst = workdir / "concat.txt"
    lst.write_text("".join(f"file '{c.name}'\n" for c in clips), encoding="utf-8")
    r = subprocess.run(
        [ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", lst.name, "-c", "copy", "-movflags", "+faststart", str(out)],
        cwd=workdir, capture_output=True, text=True, errors="replace",
    )
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg не смог склеить клипы:\n{r.stderr[-2000:]}")


def add_music(video: str | Path, music: str | Path, out: str | Path, volume: float = 0.25) -> None:
    """Подмешивает фоновую музыку под диалоги (музыка зацикливается и затухает в конце)."""
    dur = probe(video).duration
    fade_st = max(dur - 2.0, 0)
    fc = (
        f"[1:a]aresample=48000,volume={volume},afade=t=in:st=0:d=1,afade=t=out:st={fade_st:.3f}:d=2[m];"
        f"[0:a][m]amix=inputs=2:duration=first:normalize=0,aformat=channel_layouts=stereo[a]"
    )
    r = subprocess.run(
        [ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error", "-i", str(video),
         "-stream_loop", "-1", "-i", str(music), "-filter_complex", fc,
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-t", f"{dur:.3f}", "-movflags", "+faststart", str(out)],
        capture_output=True, text=True, errors="replace",
    )
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg не смог добавить музыку:\n{r.stderr[-2000:]}")
