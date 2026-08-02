from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


class FFmpegError(RuntimeError):
    pass


def run_ffmpeg(args: list[str]) -> None:
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise FFmpegError(f"ffmpeg failed: {' '.join(cmd)}\n{result.stderr}")


def write_drawtext_file(text: str) -> Path:
    """ffmpeg's drawtext escaping is fiendish; textfile= sidesteps it entirely."""
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    )
    tmp.write(text)
    tmp.close()
    return Path(tmp.name)


def build_audio_track(
    voiceover_path: Path | None,
    bg_music_path: Path | None,
    first_input_index: int,
) -> tuple[list[str], str, str]:
    """Returns (extra ffmpeg -i args, filter_complex fragment, output pad name)
    for a voiceover + background music mix, one of them, or silence.
    `first_input_index` is the next free ffmpeg input index to use.
    """
    i = first_input_index
    if voiceover_path and bg_music_path:
        extra_inputs = ["-i", str(voiceover_path), "-stream_loop", "-1", "-i", str(bg_music_path)]
        filt = f"[{i + 1}:a]volume=0.25[bg];[{i}:a][bg]amix=inputs=2:duration=first[a]"
        return extra_inputs, filt, "[a]"
    if voiceover_path:
        extra_inputs = ["-i", str(voiceover_path)]
        return extra_inputs, f"[{i}:a]apad[a]", "[a]"
    if bg_music_path:
        extra_inputs = ["-stream_loop", "-1", "-i", str(bg_music_path)]
        return extra_inputs, f"[{i}:a]volume=0.5[a]", "[a]"
    extra_inputs = ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
    return extra_inputs, "", f"{i}:a"
