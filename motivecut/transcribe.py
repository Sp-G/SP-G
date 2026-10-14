"""Распознавание речи прямо из видео (Whisper) — когда субтитров нет или они не совпадают.

Результат сохраняется в кэш (.srt), поэтому один и тот же фильм распознаётся только один раз.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Callable

from .subtitles import Cue, write_srt

WHISPER_MODELS = {
    "small — баланс скорости и качества (~0.5 ГБ)": "small",
    "base — быстро, но с ошибками (~150 МБ)": "base",
    "medium — точнее, медленнее (~1.5 ГБ)": "medium",
    "large-v3-turbo — лучшее качество (~1.6 ГБ, лучше с видеокартой)": "large-v3-turbo",
}
LANGUAGES = {"Определить автоматически": None, "Русский": "ru", "Английский": "en", "Украинский": "uk"}

CACHE_DIR = Path(os.environ.get("MOTIVECUT_CACHE", Path.home() / ".motivecut" / "transcripts"))

_MODELS: dict[str, object] = {}


def available() -> bool:
    try:
        import faster_whisper  # noqa: F401
    except ImportError:
        return False
    return True


def cache_path(video: str | Path, model: str, language: str | None) -> Path:
    st = Path(video).stat()
    key = f"{Path(video).resolve()}|{st.st_size}|{int(st.st_mtime)}|{model}|{language}"
    h = hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
    return CACHE_DIR / f"{Path(video).stem}.{model}.{h}.srt"


def _gpu_count() -> int:
    try:
        import ctranslate2

        return ctranslate2.get_cuda_device_count()
    except Exception:  # noqa: BLE001
        return 0


def _load_model(name: str, gpu: bool):
    from faster_whisper import WhisperModel

    key = f"{name}|{gpu}"
    if key not in _MODELS:
        if gpu:
            _MODELS[key] = WhisperModel(name, device="cuda", compute_type="float16")
        else:
            _MODELS[key] = WhisperModel(name, device="cpu", compute_type="int8")
    return _MODELS[key]


def transcribe(
    video: str | Path,
    duration: float,
    model: str = "small",
    language: str | None = None,
    progress: Callable[[float, str], None] | None = None,
) -> Path:
    """Распознаёт речь и возвращает путь к .srt (из кэша, если уже распознавали)."""
    out = cache_path(video, model, language)
    if out.exists() and out.stat().st_size > 0:
        return out
    if not available():
        raise RuntimeError(
            "Для распознавания речи установите пакет: pip install faster-whisper "
            "(или запустите run.bat заново — он доустановит)"
        )
    name = Path(video).name
    if progress:
        progress(0.0, f"Загрузка модели распознавания «{model}» (при первом запуске скачивается)")

    def run(gpu: bool) -> list[Cue]:
        whisper = _load_model(model, gpu)
        segments, _info = whisper.transcribe(
            str(video),
            language=language,
            vad_filter=True,  # пропускает музыку и тишину — важно для фильмов
            vad_parameters={"min_silence_duration_ms": 500},
            beam_size=5,
            condition_on_previous_text=False,  # меньше «зацикливаний» на длинных фильмах
        )
        cues: list[Cue] = []
        for seg in segments:
            text = seg.text.strip()
            if text:
                cues.append(Cue(seg.start, seg.end, text))
            if progress and duration > 0:
                progress(min(seg.end / duration, 1.0),
                         f"Распознаю речь «{name}»: {int(seg.end // 60)} из {int(duration // 60)} мин")
        return cues

    if _gpu_count() > 0:
        try:
            cues = run(gpu=True)
        except Exception:  # noqa: BLE001  (нет библиотек CUDA — считаем на процессоре)
            cues = run(gpu=False)
    else:
        cues = run(gpu=False)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".part")
    write_srt(cues, tmp)
    tmp.replace(out)
    return out
