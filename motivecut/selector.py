"""Поиск подходящих по смыслу фрагментов.

Три способа:
  * keywords   — офлайн, без зависимостей: совпадение слов темы + словарь мотивации;
  * embeddings — офлайн, семантический поиск (нужен пакет sentence-transformers);
  * claude     — Claude сам выбирает фразы и выстраивает из них историю (нужен API-ключ).
"""
from __future__ import annotations

import json
import math
import os
import re
from dataclasses import dataclass

from .subtitles import Segment


@dataclass
class Clip:
    source: int
    start: float
    end: float
    text: str
    score: float = 0.0
    reason: str = ""
    segment_ids: tuple[int, ...] = ()

    @property
    def duration(self) -> float:
        return self.end - self.start


MOTIVATION_WORDS = """
никогда сдавайся сдаваться сдамся борись бороться борьба сражайся драться победа победить побеждать
сила сильный сильнее воля мечта мечтать цель верь вера поверь смелость страх боишься бояться
вставай встань поднимись падать упал падение боль терпеть больно путь выбор жизнь живи
шанс должен можешь сможешь способен возможно невозможно лучший величие великий герой
дух сердце честь гордость трудно тяжело работа трудись успех добиться вперёд вперед
пытайся попробуй продолжай идти держись выжить сражение время сейчас никто никому никогда
never give up quit fight fighting win winner victory strong stronger strength will dream dreams goal
believe faith courage fear afraid rise stand fall fail failure pain hurt path choice life live
chance must can could able impossible possible best great greatness hero spirit heart honor pride
hard work success keep going hold survive battle now nobody anyone champion
"""

STOPWORDS = set(
    """и в во не что он на я с со как а то все она так его но да ты к у же вы за бы по только ее мне было
    вот от меня еще нет о из ему теперь когда даже ну вдруг ли если уже или ни быть был него до вас нибудь
    опять уж вам ведь там потом себя ничего ей может они тут где есть надо ней для мы тебя их чем была сам
    чтоб без будто чего раз тоже себе под будет ж тогда кто этот того потому этого какой совсем ним здесь
    этом один почти мой тем чтобы нее кажется сейчас были куда зачем всех можно при наконец два об другой
    хоть после над больше тот через эти нас про всего них какая много разве три эту моя впрочем хорошо
    свою этой перед иногда лучше чуть том нельзя такой им более всегда конечно всю между это видео ролик
    нарезка нарезку про о об мотивация мотивационный мотивационная мотивационную фильм фильма
    the a an and or but if of to in on at by for with about as is are was were be been it this that
    you he she we they i me my your his her our their what which who whom video clip about""".split()
)


def _stem(word: str) -> str:
    word = word.lower().replace("ё", "е")
    return word[:5] if len(word) > 5 else word


def tokenize(text: str) -> list[str]:
    return [w for w in re.findall(r"[\w']+", text.lower()) if len(w) > 1]


def theme_stems(theme: str) -> set[str]:
    return {_stem(w) for w in tokenize(theme) if w not in STOPWORDS and len(w) > 2}


_MOTIVATION_STEMS = {_stem(w) for w in MOTIVATION_WORDS.split()}


def keyword_scores(segments: list[Segment], theme: str) -> list[float]:
    stems = theme_stems(theme)
    scores = []
    for seg in segments:
        words = tokenize(seg.text)
        if not words:
            scores.append(0.0)
            continue
        seg_stems = [_stem(w) for w in words]
        theme_hits = sum(1 for s in seg_stems if s in stems)
        motiv_hits = sum(1 for s in seg_stems if s in _MOTIVATION_STEMS)
        score = (3.0 * theme_hits + 1.0 * motiv_hits) / math.sqrt(len(words))
        score += 0.3 * seg.text.count("!")
        if seg.duration < 1.5:
            score *= 0.5
        scores.append(score)
    return scores


_EMBED_MODEL = None


def embedding_scores(segments: list[Segment], theme: str) -> list[float]:
    global _EMBED_MODEL
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        raise RuntimeError(
            "Для режима «embeddings» установите пакет: pip install sentence-transformers"
        ) from e
    if _EMBED_MODEL is None:
        _EMBED_MODEL = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    texts = [s.text for s in segments]
    vecs = _EMBED_MODEL.encode([theme] + texts, normalize_embeddings=True, batch_size=64)
    q = vecs[0]
    kw = keyword_scores(segments, theme)
    top_kw = max(kw) or 1.0
    return [float(v @ q) + 0.15 * (k / top_kw) for v, k in zip(vecs[1:], kw)]


def _clip_from(segs: list[Segment], score: float = 0.0, reason: str = "") -> Clip:
    return Clip(
        source=segs[0].source,
        start=segs[0].start,
        end=segs[-1].end,
        text=" ".join(s.text for s in segs),
        score=score,
        reason=reason,
        segment_ids=tuple(s.id for s in segs),
    )


def pick_by_score(
    segments: list[Segment],
    scores: list[float],
    target_duration: float,
    min_clip: float = 1.5,
    max_clip: float = 15.0,
    order: str = "chronological",
) -> list[Clip]:
    """Жадно берёт лучшие сегменты, пока не наберётся нужная длительность."""
    ranked = sorted(range(len(segments)), key=lambda i: scores[i], reverse=True)
    chosen: list[int] = []
    total = 0.0
    for i in ranked:
        seg = segments[i]
        if scores[i] <= 0 or total >= target_duration:
            break
        if seg.duration < min_clip or seg.duration > max_clip:
            continue
        chosen.append(i)
        total += seg.duration
    clips = [_clip_from([segments[i]], scores[i]) for i in chosen]
    if order == "chronological":
        clips.sort(key=lambda c: (c.source, c.start))
    elif order == "crescendo":
        clips.sort(key=lambda c: c.score)
    return clips


CLAUDE_SYSTEM = """Ты — монтажёр мотивационных роликов. Тебе дают субтитры одного или нескольких фильмов,
разбитые на пронумерованные фрагменты речи с таймкодами, и тему ролика от автора.

Твоя задача — выбрать фрагменты, из которых сложится цельный, сильный мотивационный ролик на заданную тему:
- выбирай реплики, которые звучат мощно и понятно вне контекста фильма (без имён, сюжетных деталей, «он», «она» без ясного смысла);
- клип может состоять из нескольких подряд идущих фрагментов одного фильма (start_id..end_id), если мысль идёт через них;
- расставь клипы в таком порядке, чтобы получилась история: завязка (проблема / боль / сомнение) → перелом → сильная кульминация;
- уложись примерно в целевую длительность (±20%);
- не выбирай один и тот же фрагмент дважды."""

_CLAUDE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Короткое название ролика"},
        "clips": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "start_id": {"type": "integer"},
                    "end_id": {"type": "integer"},
                    "reason": {"type": "string", "description": "Почему этот фрагмент и его роль в истории"},
                },
                "required": ["start_id", "end_id", "reason"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["title", "clips"],
    "additionalProperties": False,
}


def _fmt_time(t: float) -> str:
    m, s = divmod(int(t), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02}:{s:02}" if h else f"{m}:{s:02}"


def claude_pick(
    segments: list[Segment],
    source_names: list[str],
    theme: str,
    target_duration: float,
    max_clip: float = 20.0,
    api_key: str | None = None,
    model: str = "claude-opus-5-5",
) -> tuple[str, list[Clip]]:
    try:
        import anthropic
    except ImportError as e:
        raise RuntimeError("Для режима «claude» установите пакет: pip install anthropic") from e

    lines = []
    for src_idx, name in enumerate(source_names):
        lines.append(f"\n=== Фильм {src_idx + 1}: {name} ===")
        for s in segments:
            if s.source == src_idx:
                lines.append(f"[{s.id}] ({_fmt_time(s.start)}, {s.duration:.1f}с) {s.text}")
    user = (
        f"Тема ролика: {theme}\n"
        f"Целевая длительность: около {int(target_duration)} секунд.\n"
        f"Максимальная длина одного клипа: {int(max_clip)} секунд.\n"
        f"\nФрагменты:\n" + "\n".join(lines)
    )

    client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY") or None)
    with client.beta.messages.stream(
        model=model,
        max_tokens=32000,
        system=CLAUDE_SYSTEM,
        messages=[{"role": "user", "content": user}],
        output_config={"effort": "high", "format": {"type": "json_schema", "schema": _CLAUDE_SCHEMA}},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    ) as stream:
        response = stream.get_final_message()

    if response.stop_reason == "refusal":
        raise RuntimeError("Claude отказался обрабатывать запрос. Попробуйте другую тему или способ поиска.")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("Ответ Claude оборвался (max_tokens). Попробуйте уменьшить длительность ролика.")
    text = "".join(b.text for b in response.content if b.type == "text")
    data = json.loads(text)

    by_id = {s.id: s for s in segments}
    clips: list[Clip] = []
    used: set[int] = set()
    for item in data.get("clips", []):
        a, b = sorted((int(item["start_id"]), int(item["end_id"])))
        if a not in by_id or b not in by_id or by_id[a].source != by_id[b].source:
            continue
        segs = [by_id[i] for i in range(a, b + 1) if i in by_id and i not in used]
        if not segs:
            continue
        # Не даём клипу разрастись больше лимита
        while len(segs) > 1 and segs[-1].end - segs[0].start > max_clip:
            segs.pop()
        used.update(s.id for s in segs)
        clips.append(_clip_from(segs, reason=item.get("reason", "")))
    return data.get("title", ""), clips
