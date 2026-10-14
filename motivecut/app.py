"""Локальный интерфейс (открывается в браузере, всё работает на вашем ПК)."""
from __future__ import annotations

import os
import re
import tempfile
import time
from pathlib import Path

import gradio as gr

from .pipeline import SUB_EXT, VIDEO_EXT, FindSettings, Source, find_clips, load_sources, render
from .selector import Clip
from .transcribe import CACHE_DIR, LANGUAGES, WHISPER_MODELS
from .video import FORMATS, RenderOptions

OUTPUT_DIR = Path(os.environ.get("MOTIVECUT_OUTPUT", "output")).resolve()
HEADERS = ["Взять", "Порядок", "Фильм", "Начало", "Конец", "Текст", "Почему выбран"]
METHODS = {
    "Ключевые слова (быстро, офлайн)": "keywords",
    "Смысловой поиск (офлайн, нужен sentence-transformers)": "embeddings",
    "Claude AI (лучшее качество, нужен API-ключ)": "claude",
}
SPEECH = {
    "Субтитры из файла, а если их нет — распознать речь": "auto",
    "Распознать речь из видео (если субтитры не совпадают или их нет)": "always",
}
ORDERS = {
    "Как в фильме (хронологически)": "chronological",
    "По нарастанию силы": "crescendo",
    "Как предложил ИИ / по рейтингу": "as_is",
}


def fmt_time(t: float) -> str:
    m, s = divmod(t, 60)
    h, m = divmod(int(m), 60)
    return f"{h}:{m:02}:{s:04.1f}" if h else f"{m}:{s:04.1f}"


def parse_time(v) -> float:
    if isinstance(v, (int, float)):
        return float(v)
    parts = [float(p) for p in re.split(r"[:]", str(v).strip().replace(",", "."))]
    t = 0.0
    for p in parts:
        t = t * 60 + p
    return t


def _paths(files, text: str, exts: set[str]) -> list[Path]:
    out: list[Path] = []
    for f in files or []:
        out.append(Path(f if isinstance(f, str) else f.name))
    for line in (text or "").splitlines():
        line = line.strip().strip('"').strip("'")
        if not line:
            continue
        p = Path(line)
        if p.is_dir():
            out += sorted(x for x in p.iterdir() if x.suffix.lower() in exts)
        elif p.exists():
            out.append(p)
        else:
            raise gr.Error(f"Файл не найден: {line}")
    return [p for p in out if p.suffix.lower() in exts]


def _table(sources: list[Source], clips: list[Clip]) -> list[list]:
    return [
        [True, i + 1, sources[c.source].name, fmt_time(c.start), fmt_time(c.end), c.text, c.reason]
        for i, c in enumerate(clips)
    ]


def _rows(table) -> list[list]:
    if table is None:
        return []
    if hasattr(table, "values"):  # pandas.DataFrame
        return table.values.tolist()
    if isinstance(table, dict):
        return table.get("data", [])
    return list(table)


def on_find(video_files, video_paths, sub_files, sub_paths, speech, whisper_model, language, theme, method,
            duration, max_clip, order, api_key, model, progress=gr.Progress()):
    videos = _paths(video_files, video_paths, VIDEO_EXT)
    subs = _paths(sub_files, sub_paths, SUB_EXT | VIDEO_EXT)
    subs = [s for s in subs if s.suffix.lower() in SUB_EXT]
    if not videos:
        raise gr.Error("Добавьте видео (загрузкой или путём к файлу).")
    progress(0.1, desc="Читаю субтитры и видео")
    try:
        sources = load_sources(
            videos, subs, Path(tempfile.mkdtemp(prefix="motivecut_subs_")), max_clip,
            speech=SPEECH[speech], whisper_model=WHISPER_MODELS[whisper_model], language=LANGUAGES[language],
            progress=lambda f, m: progress(0.1 + 0.7 * f, desc=m),
        )
        progress(0.85, desc="Ищу подходящие фрагменты")
        title, clips = find_clips(
            sources,
            FindSettings(theme=theme, method=METHODS[method], target_duration=duration, max_clip=max_clip,
                         order=ORDERS[order], api_key=api_key or None, model=model or "claude-opus-5-5"),
        )
    except Exception as e:  # noqa: BLE001
        raise gr.Error(str(e)) from e
    total = sum(c.duration for c in clips)
    pairs = "; ".join(f"{s.video.name} ← {s.subtitles.name}" for s in sources)
    srt_files = [str(s.subtitles) for s in sources]
    status = (
        (f"### {title}\n" if title else "")
        + f"Найдено фрагментов: **{len(clips)}**, общая длина ≈ **{total:.0f} c**.  \n"
        + f"Источники: {pairs}  \n"
        + "Снимите галочки с лишнего, поправьте время или порядок — и жмите «Собрать видео»."
    )
    if not clips:
        status = "Ничего не найдено. Попробуйте описать смысл другими словами или выбрать другой способ поиска."
    return sources, _table(sources, clips), status, srt_files


def on_render(sources, table, fmt, burn_subs, fade, normalize, snap, pad_before, pad_after, music, music_volume,
              progress=gr.Progress()):
    if not sources:
        raise gr.Error("Сначала нажмите «Найти фрагменты».")
    names = {s.name: i for i, s in enumerate(sources)}
    picked = []
    for row in _rows(table):
        take, order, film, start, end, text = row[:6]
        if not (take is True or str(take).lower() in ("true", "1", "да", "✓")):
            continue
        if film not in names:
            raise gr.Error(f"Неизвестный фильм в таблице: {film}")
        st, en = parse_time(start), parse_time(end)
        if en <= st:
            raise gr.Error(f"Конец раньше начала в строке «{text[:40]}…»")
        picked.append((float(order or 0), Clip(names[film], st, en, str(text))))
    picked.sort(key=lambda x: x[0])
    clips = [c for _, c in picked]
    opts = RenderOptions(format=fmt, burn_subs=burn_subs, fade=fade, normalize_audio=normalize)
    out = OUTPUT_DIR / f"motivation_{time.strftime('%Y%m%d_%H%M%S')}.mp4"
    try:
        render(sources, clips, out, opts, pad_before=pad_before, pad_after=pad_after,
               music=music or None, music_volume=music_volume, snap_scenes=snap,
               progress=lambda f, m: progress(f, desc=m))
    except Exception as e:  # noqa: BLE001
        raise gr.Error(str(e)) from e
    return str(out), str(out), f"Сохранено: `{out}`"


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="MotiveCut — мотивационные нарезки") as ui:
        sources_state = gr.State([])
        gr.Markdown("# 🎬 MotiveCut\nЗагрузите фильм и субтитры, опишите смысл ролика — программа сама найдёт, нарежет и склеит фрагменты.")

        with gr.Row():
            with gr.Column():
                gr.Markdown("### 1. Видео")
                video_files = gr.File(label="Видеофайлы", file_count="multiple", type="filepath")
                video_paths = gr.Textbox(
                    label="…или пути к файлам/папкам (по одному в строке) — быстрее для больших фильмов",
                    lines=2, placeholder=r"D:\Фильмы\Rocky.mkv",
                )
            with gr.Column():
                gr.Markdown("### 2. Субтитры")
                sub_files = gr.File(label="Субтитры (.srt, .vtt, .ass)", file_count="multiple", type="filepath")
                sub_paths = gr.Textbox(
                    label="…или пути. Можно не указывать — тогда речь будет распознана из видео",
                    lines=2, placeholder=r"D:\Фильмы\Rocky.srt",
                )
        with gr.Group():
            speech = gr.Radio(list(SPEECH), value=list(SPEECH)[0], label="Откуда брать текст фраз")
            with gr.Row():
                whisper_model = gr.Dropdown(list(WHISPER_MODELS), value=list(WHISPER_MODELS)[0],
                                            label="Модель распознавания речи")
                language = gr.Dropdown(list(LANGUAGES), value=list(LANGUAGES)[0], label="Язык фильма")
            gr.Markdown("Распознавание идёт на вашем ПК: фильм 2 часа — примерно 15–40 минут (с видеокартой NVIDIA — "
                        "в разы быстрее). Результат запоминается, повторно тот же фильм распознаётся мгновенно.")

        gr.Markdown("### 3. Смысл ролика")
        theme = gr.Textbox(
            label="Общий смысл / идея",
            lines=3,
            placeholder="Например: никогда не сдавайся, даже когда весь мир против тебя. Боль временна, а победа остаётся навсегда.",
        )
        with gr.Row():
            method = gr.Radio(list(METHODS), value=list(METHODS)[0], label="Как искать фрагменты")
            order = gr.Radio(list(ORDERS), value=list(ORDERS)[0], label="Порядок клипов")
        with gr.Row():
            duration = gr.Slider(15, 300, value=60, step=5, label="Длительность ролика, сек")
            max_clip = gr.Slider(4, 40, value=15, step=1, label="Макс. длина одного клипа, сек")
        with gr.Accordion("Настройки Claude AI", open=False):
            api_key = gr.Textbox(label="ANTHROPIC_API_KEY (можно не вводить, если задан в системе)", type="password")
            model = gr.Textbox(label="Модель", value="claude-opus-5-5")

        find_btn = gr.Button("🔍 Найти фрагменты", variant="primary")
        status = gr.Markdown()
        srt_out = gr.File(label="Распознанные/использованные субтитры", file_count="multiple")
        table = gr.Dataframe(
            headers=HEADERS,
            datatype=["bool", "number", "str", "str", "str", "str", "str"],
            interactive=True,
            wrap=True,
            label="Найденные фрагменты (можно редактировать)",
        )

        gr.Markdown("### 4. Сборка")
        with gr.Row():
            fmt = gr.Dropdown(list(FORMATS), value=list(FORMATS)[0], label="Формат")
            burn_subs = gr.Checkbox(value=True, label="Вшить субтитры в видео")
            normalize = gr.Checkbox(value=True, label="Выровнять громкость")
            snap = gr.Checkbox(value=True, label="Резать по смене кадра")
        with gr.Row():
            fade = gr.Slider(0, 1, value=0.25, step=0.05, label="Плавный переход (затемнение), сек")
            pad_before = gr.Slider(0, 2, value=0.25, step=0.05, label="Запас до фразы, сек")
            pad_after = gr.Slider(0, 3, value=0.6, step=0.05, label="Запас после фразы, сек")
        with gr.Row():
            music = gr.File(label="Фоновая музыка (необязательно)", type="filepath", file_types=["audio"])
            music_volume = gr.Slider(0, 1, value=0.25, step=0.05, label="Громкость музыки")

        render_btn = gr.Button("🎞 Собрать видео", variant="primary")
        result_status = gr.Markdown()
        result_video = gr.Video(label="Результат")
        result_file = gr.File(label="Скачать")

        find_btn.click(
            on_find,
            [video_files, video_paths, sub_files, sub_paths, speech, whisper_model, language, theme, method,
             duration, max_clip, order, api_key, model],
            [sources_state, table, status, srt_out],
        )
        render_btn.click(
            on_render,
            [sources_state, table, fmt, burn_subs, fade, normalize, snap, pad_before, pad_after, music, music_volume],
            [result_video, result_file, result_status],
        )
    return ui


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    build_ui().queue().launch(inbrowser=True, server_name="127.0.0.1", allowed_paths=[str(OUTPUT_DIR), str(CACHE_DIR)])


if __name__ == "__main__":
    main()
