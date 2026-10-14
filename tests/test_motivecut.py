import subprocess
from pathlib import Path

import pytest

from motivecut.pipeline import FindSettings, find_clips, load_sources, pair_files, padded_bounds, render
from motivecut.selector import keyword_scores
from motivecut.subtitles import build_segments, load_cues, parse_ass, parse_srt_vtt
from motivecut.video import RenderOptions, ffmpeg_exe, probe

SRT = """1
00:00:01,000 --> 00:00:03,000
Привет, как дела?

2
00:00:04,000 --> 00:00:06,500
<i>Никогда не сдавайся.</i>

3
00:00:07,000 --> 00:00:09,000
Даже если ты упал —

4
00:00:09,200 --> 00:00:11,800
вставай и борись снова!

5
00:00:13,000 --> 00:00:15,000
Передай соль, пожалуйста.

6
00:00:16,000 --> 00:00:19,000
Боль временна, а победа навсегда!
"""


def test_parse_srt_and_vtt():
    cues = parse_srt_vtt(SRT)
    assert len(cues) == 6
    assert cues[1].text == "Никогда не сдавайся."
    assert cues[1].start == 4.0 and cues[1].end == 6.5
    vtt = "WEBVTT\n\n00:01.500 --> 00:03.000\n- Hello there\n"
    (c,) = parse_srt_vtt(vtt)
    assert (c.start, c.end, c.text) == (1.5, 3.0, "Hello there")


def test_parse_ass():
    ass = (
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        "Dialogue: 0,0:00:01.00,0:00:02.50,Default,,0,0,0,,{\\i1}Вставай,\\Nбоец{\\i0}\n"
    )
    (c,) = parse_ass(ass)
    assert c.text == "Вставай, боец" and c.end == 2.5


def test_cp1251_file(tmp_path):
    p = tmp_path / "film.srt"
    p.write_bytes(SRT.encode("cp1251", errors="replace"))
    assert load_cues(p)[1].text == "Никогда не сдавайся."


def test_segments_merge_unfinished_sentence():
    segs = build_segments(parse_srt_vtt(SRT))
    texts = [s.text for s in segs]
    assert "Даже если ты упал — вставай и борись снова!" in texts


def test_keyword_scores_prefer_motivation():
    segs = build_segments(parse_srt_vtt(SRT))
    scores = keyword_scores(segs, "никогда не сдавайся, борись")
    best = segs[max(range(len(segs)), key=scores.__getitem__)]
    assert "сдавайся" in best.text or "борись" in best.text
    salt = next(i for i, s in enumerate(segs) if "соль" in s.text)
    assert scores[salt] == 0


def test_pair_files():
    v = [Path("Rocky.mkv"), Path("Gladiator.mp4")]
    s = [Path("gladiator.ru.srt"), Path("rocky.srt")]
    assert pair_files(v, s) == [(v[0], s[1]), (v[1], s[0])]


@pytest.fixture(scope="module")
def sample(tmp_path_factory):
    d = tmp_path_factory.mktemp("media")
    video = d / "film.mp4"
    subprocess.run(
        [ffmpeg_exe(), "-y", "-loglevel", "error",
         "-f", "lavfi", "-i", "testsrc=size=640x360:rate=25:duration=20",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=20",
         "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-shortest", str(video)],
        check=True,
    )
    subs = d / "film.srt"
    subs.write_text(SRT, encoding="utf-8")
    return video, subs, d


def test_end_to_end(sample, tmp_path):
    video, subs, d = sample
    sources = load_sources([video], [subs], d)
    assert sources[0].info.has_audio and abs(sources[0].info.duration - 20) < 0.5
    _, clips = find_clips(sources, FindSettings(theme="никогда не сдавайся и борись", target_duration=12))
    assert clips and all("соль" not in c.text for c in clips)

    st, en = padded_bounds(sources[0], 4.0, 6.5, 0.5, 1.0)
    assert st == 3.5 and en == pytest.approx(6.95)  # не залезает на реплику в 7.0

    out = tmp_path / "out.mp4"
    for fmt in ("16:9 (YouTube)", "9:16 размытый фон (Shorts/Reels/TikTok)"):
        render(sources, clips, out, RenderOptions(format=fmt, burn_subs=True, preset="ultrafast"))
        info = probe(out)
        expected = sum(min(c.end + 0.6, 20) - c.start for c in clips)
        assert info.has_audio and abs(info.duration - expected) < 2.5
        assert (info.width, info.height) == ((1920, 1080) if fmt.startswith("16") else (1080, 1920))
