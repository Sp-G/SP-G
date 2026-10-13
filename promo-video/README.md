# Coffee Pass — рекламный ролик (Reels / TikTok / Shorts)

Вертикальное видео 1080×1920, 30 fps, ~31 с, русская озвучка, субтитры, фоновая музыка и инфографика.
Собрано на [Remotion](https://www.remotion.dev) (React → видео).

## Сценарий (~31 с)

Хук «Стоп!» → бренд → 3 шага (подписка · еда от 1 000 ₸ · скан чека = кофе бесплатно) → монеты и бонусы за друзей → цена и призыв.
Тексты фраз и субтитров — `LINES` в `scripts/voiceover.py`. Субтитры подсвечиваются по словам синхронно с голосом.

## Как пересобрать

```bash
npm i

# 1. Озвучка → public/vo/*.mp3, src/vo-timings.json, src/vo-captions.json
pip install edge-tts
python3 scripts/voiceover.py --engine edge --voice ru-RU-SvetlanaNeural   # естественный женский голос
# или ElevenLabs:  ELEVENLABS_API_KEY=... python3 scripts/voiceover.py --engine eleven
# или офлайн:      python3 scripts/voiceover.py --engine piper --model ./ru-irinia-medium.onnx

# 2. Музыка и звуки (синтез, без лицензий):
python3 scripts/music.py                               # → public/music.mp3, public/sfx/*.wav

# 3. Превью и рендер
npx remotion studio
npx remotion render CoffeePassPromo out/coffeepass-promo.mp4 --crf=18
```

Тексты озвучки — в `scripts/voiceover.py`. Длительность сцен подстраивается под длину фраз автоматически.


Скриншоты приложения — `public/screens/` (вырезаны из записей экрана).
