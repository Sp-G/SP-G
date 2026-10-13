"""Generate the voiceover + per-word timings for Remotion captions.

Engines:
  edge   — Microsoft neural voices (ru-RU-SvetlanaNeural / ru-RU-DariyaNeural), very natural.
           Needs network access to speech.platform.bing.com.  pip install edge-tts
  eleven — ElevenLabs (best quality). Needs ELEVENLABS_API_KEY and access to api.elevenlabs.io.
           Optional ELEVENLABS_VOICE_ID.
  piper  — offline fallback (ru_RU irina). pip install piper-tts; pass --model path/to/ru-irinia-medium.onnx

Usage:
  python3 scripts/voiceover.py --engine edge
  python3 scripts/voiceover.py --engine piper --model ./ru-irinia-medium.onnx
"""
import argparse
import asyncio
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "vo"

# Each line is a list of segments. A plain string is one spoken word shown as-is.
# A (display, spoken) tuple shows `display` on screen while the voice reads `spoken`.
BRAND = ("Coffee Pass", "Кофи Пасс")
LINES = {
    "hook": ["Стоп!", "Ты", "всё", "ещё", "платишь", "за", "каждую", "чашку", "кофе?"],
    "intro": ["Тогда", "тебе", "нужен", BRAND, "—", "кофе", "по", "подписке."],
    "step1": ["Раз", "—", "оформи", "подписку."],
    "step2": ["Два", "—", "закажи", "еду", "от", ("1 000 ₸", "тысячи тенге"), "в", "кофейне."],
    "step3": ["Три", "—", "сканируй", "чек,", "и", "кофе", "—", "бесплатно!"],
    "perks": ["А", "ещё", "монеты", "за", "визиты", "и", "до", ("100%", "ста процентов"), "бонусов", "за", "друзей!"],
    "cta": ["Всего", ("1 490 ₸", "тысяча четыреста девяносто тенге"), "в", "месяц.", BRAND, "—", "подключайся!"],
}


def segments(line):
    """-> list of (display, spoken_word_count, spoken_text)"""
    out = []
    for seg in line:
        disp, spoken = (seg, seg) if isinstance(seg, str) else seg
        n = len([w for w in spoken.split() if re.search(r"\w", w)])
        out.append((disp, n, spoken))
    return out


def spoken_text(line):
    return " ".join(s for _, _, s in segments(line))


def to_mp3(src, dst):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af",
                    "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                    "silenceremove=start_periods=1:start_threshold=-45dB,areverse",
                    "-b:a", "192k", "-ar", "44100", str(dst)], check=True)


def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout)


def estimate_words(text, total):
    """Spread word timings proportionally to length (+pauses at punctuation)."""
    words = text.split()
    weights = [len(w) + (6 if w[-1] in ".,!?—" else 1.5) for w in words]
    t, res, k = 0.0, [], total / sum(weights)
    for w, wt in zip(words, weights):
        res.append((w, t, t + (len(w) + 1.5) * k))
        t += wt * k
    return [x for x in res if re.search(r"\w", x[0])]


async def edge_line(text, voice, rate, pitch, mp3):
    import edge_tts
    comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, boundary="WordBoundary")
    words = []
    with open(mp3, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                s = chunk["offset"] / 1e7
                words.append((chunk["text"], s, s + chunk["duration"] / 1e7))
    return words


def eleven_line(text, mp3):
    key = os.environ["ELEVENLABS_API_KEY"]
    voice = os.environ.get("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnJSxMxa")
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps",
        data=json.dumps({"text": text, "model_id": "eleven_multilingual_v2",
                         "voice_settings": {"stability": 0.35, "similarity_boost": 0.8, "style": 0.45}}).encode(),
        headers={"xi-api-key": key, "Content-Type": "application/json"})
    data = json.load(urllib.request.urlopen(req))
    Path(mp3).write_bytes(base64.b64decode(data["audio_base64"]))
    al = data["alignment"]
    words, cur, start = [], "", None
    for ch, s, e in zip(al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]):
        if ch.isspace():
            if cur: words.append((cur, start, end)); cur = ""
            continue
        if not cur: start = s
        cur += ch; end = e
    if cur: words.append((cur, start, end))
    return [w for w in words if re.search(r"\w", w[0])]


def piper_line(text, model, wav):
    subprocess.run([sys.executable, "-m", "piper", "-m", model, "-f", str(wav), "--length-scale", "0.9",
                    "--noise-scale", "0.75", "--noise-w-scale", "0.9", "--sentence-silence", "0.15"],
                   input=text.encode(), check=True, capture_output=True)
    with wave.open(str(wav)) as w:
        total = w.getnframes() / w.getframerate()
    return estimate_words(text, total)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["edge", "eleven", "piper"], default="edge")
    ap.add_argument("--voice", default="ru-RU-SvetlanaNeural")
    ap.add_argument("--rate", default="+8%")
    ap.add_argument("--pitch", default="+0Hz")
    ap.add_argument("--model")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    timings, captions = {}, {}
    with tempfile.TemporaryDirectory() as tmp:
        for key, line in LINES.items():
            text = spoken_text(line)
            raw = Path(tmp) / f"{key}.raw"
            if a.engine == "edge":
                words = asyncio.run(edge_line(text, a.voice, a.rate, a.pitch, raw))
            elif a.engine == "eleven":
                words = eleven_line(text, raw)
            else:
                raw = raw.with_suffix(".wav")
                words = piper_line(text, a.model, raw)
            # leading silence is trimmed in to_mp3 -> shift word times accordingly
            lead = words[0][1] if words else 0.0
            mp3 = OUT / f"{key}.mp3"
            to_mp3(raw, mp3)
            timings[key] = round(duration(mp3), 3)
            # map engine words back onto display segments
            caps, i = [], 0
            for disp, n, _ in segments(line):
                if n == 0:  # punctuation-only segment, glue to previous word
                    if caps: caps[-1]["text"] += " " + disp
                    continue
                chunk = words[i:i + n] or words[-1:]
                i += n
                caps.append({"text": disp, "start": round(max(0, chunk[0][1] - lead), 3),
                             "end": round(max(0, chunk[-1][2] - lead), 3)})
            captions[key] = caps
            print(f"{key}: {timings[key]}s  {text}")
    (ROOT / "src" / "vo-timings.json").write_text(json.dumps(timings, indent=2, ensure_ascii=False) + "\n")
    (ROOT / "src" / "vo-captions.json").write_text(json.dumps(captions, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
