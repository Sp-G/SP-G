"""Generate voiceover lines with Piper (offline Russian TTS) and write timings for Remotion.

Usage: python3 scripts/voiceover.py /path/to/ru-irinia-medium.onnx
"""
import json, subprocess, sys, wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "vo"
MODEL = sys.argv[1]

# id -> text for TTS (brand name and numbers are spelled out so Piper reads them correctly)
LINES = {
    "hook": "Кофе каждый день — это дорого. А что, если платить за него один раз в месяц?",
    "intro": "Знакомься: Кофи Пасс. Подписка на кофе в кофейнях-партнёрах.",
    "step1": "Шаг первый. Оформи подписку — всего тысяча четыреста девяносто тенге в месяц.",
    "step2": "Шаг второй. Найди кофейню-партнёра на карте и закажи еду от тысячи тенге.",
    "step3": "Шаг третий. Отсканируй чек в приложении — и напиток получаешь бесплатно!",
    "coins": "За каждый визит начисляются монеты. Меняй их на заморозку подписки или участвуй в розыгрыше подписки на целый год.",
    "friends": "Зови друзей — и получай до ста процентов от цены подписки на бонусный баланс.",
    "savings": "А приложение само считает, сколько ты сэкономил. Подписка окупается уже за пару чашек.",
    "cta": "Кофи Пасс. Больше кофе — меньше трат. Подключайся уже сегодня!",
}

timings = {}
for key, text in LINES.items():
    wav = OUT / f"{key}.wav"
    subprocess.run(
        [sys.executable, "-m", "piper", "-m", MODEL, "-f", str(wav),
         "--length-scale", "0.92", "--sentence-silence", "0.25"],
        input=text.encode(), check=True, capture_output=True,
    )
    with wave.open(str(wav)) as w:
        timings[key] = round(w.getnframes() / w.getframerate(), 3)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-b:a", "160k",
                    str(wav.with_suffix(".mp3"))], check=True)
    wav.unlink()
    print(f"{key}: {timings[key]}s")

(ROOT / "src" / "vo-timings.json").write_text(json.dumps(timings, indent=2) + "\n")
