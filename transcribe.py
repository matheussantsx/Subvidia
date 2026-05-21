#!/usr/bin/env python3
"""
Faster-Whisper Transcriber
Extrai áudio de vídeos (.mp4, .mkv) e transcreve com faster-whisper (GPU).
Salva .srt (legendas com timestamps) e .txt (transcrição plana) em /subtitles.
"""

import json
import sys
import subprocess
import tempfile
import argparse
import threading
import time
from pathlib import Path

# ─── Cores ────────────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def log(msg, color=RESET):  print(f"{color}{msg}{RESET}", flush=True)
def warn(msg):              log(f"  ⚠ {msg}", YELLOW)
def err(msg):               log(f"  ✗ {msg}", RED)
def info(msg):              log(f"  → {msg}", CYAN)


# ─── Barra de progresso ───────────────────────────────────────────────────────
class ProgressBar:
    WIDTH = 38

    def __init__(self, label: str):
        self._label = f"{label:<22}"
        self._value = 0.0
        self._render()

    def update(self, pct: float):
        self._value = max(0.0, min(pct, 100.0))
        self._render()

    def _render(self, color=CYAN):
        filled = int(self.WIDTH * self._value / 100)
        bar = "█" * filled + "░" * (self.WIDTH - filled)
        print(f"\r  {color}{self._label}{RESET} [{color}{bar}{RESET}] {self._value:5.1f}%",
              end="", flush=True)

    def done(self):
        self._value = 100.0
        self._render(GREEN)
        print(flush=True)

    def fail(self):
        self._render(RED)
        print(flush=True)


# ─── Spinner (para etapas sem duração conhecida) ──────────────────────────────
class Spinner:
    FRAMES = ["|", "/", "-", "\\"]

    def __init__(self, label: str):
        self._label = f"{label:<22}"
        self._stop  = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        i = 0
        while not self._stop.is_set():
            print(f"\r  {CYAN}{self._label}{RESET} {self.FRAMES[i % 4]}",
                  end="", flush=True)
            i += 1
            time.sleep(0.1)

    def start(self):
        self._thread.start()
        return self

    def done(self):
        self._stop.set()
        self._thread.join()
        width = ProgressBar.WIDTH
        bar = "█" * width
        print(f"\r  {GREEN}{self._label}{RESET} [{GREEN}{bar}{RESET}] 100.0%",
              flush=True)

    def fail(self):
        self._stop.set()
        self._thread.join()
        print(f"\r  {RED}{self._label}{RESET} ✗", flush=True)


# ─── Duração do vídeo via ffprobe ─────────────────────────────────────────────
def get_duration(path: Path) -> float:
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
        return float(json.loads(r.stdout).get("format", {}).get("duration", 0))
    except Exception:
        return 0.0


# ─── Carrega modelo ───────────────────────────────────────────────────────────
def load_model(model_size: str):
    spinner = Spinner(f"Carregando {model_size}").start()
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel(model_size, device="cuda", compute_type="float16")
        spinner.done()
        return model
    except Exception as e:
        spinner.fail()
        err(f"Falha ao carregar modelo: {e}")
        sys.exit(1)


# ─── Extrai áudio com FFmpeg + progresso ─────────────────────────────────────
def extract_audio(video_path: Path, output_wav: Path, duration: float):
    bar = ProgressBar("Extração de áudio")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        "-progress", "pipe:1", "-nostats",
        str(output_wav)
    ]

    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        text=True, encoding="utf-8", errors="ignore"
    )

    for line in proc.stdout:
        line = line.strip()
        if line.startswith("out_time_us=") and duration > 0:
            try:
                secs = int(line.split("=")[1]) / 1_000_000
                bar.update(secs / duration * 100)
            except (ValueError, IndexError):
                pass

    proc.wait()

    if proc.returncode != 0:
        bar.fail()
        raise RuntimeError("FFmpeg falhou na extração de áudio.")
    bar.done()


# ─── Transcreve com progresso ─────────────────────────────────────────────────
def transcribe_audio(model, wav_path: Path, language: str):
    segments_gen, meta = model.transcribe(
        str(wav_path),
        language=language if language != "auto" else None,
        word_timestamps=True,
        beam_size=5,
    )

    total = meta.duration or 1.0
    bar   = ProgressBar("Transcrição")

    text_parts, word_ts = [], []

    for seg in segments_gen:
        text_parts.append(seg.text.strip())
        if seg.words:
            for w in seg.words:
                word_ts.append({"word": w.word, "start": w.start, "end": w.end})
        bar.update(min(seg.end / total * 100, 99.5))

    bar.done()
    return " ".join(text_parts), word_ts


# ─── Converte segundos → SRT ──────────────────────────────────────────────────
def to_srt_time(s: float) -> str:
    ms = int((s % 1) * 1000)
    return f"{int(s)//3600:02d}:{int(s)//60%60:02d}:{int(s)%60:02d},{ms:03d}"


# ─── Agrupa palavras em blocos de legenda ─────────────────────────────────────
def words_to_blocks(words: list, max_words=8, max_dur=4.0) -> list:
    blocks, buf, buf_start, buf_end = [], [], None, 0.0
    for w in words:
        word, start, end = w["word"].strip(), w["start"], w["end"]
        if not word:
            continue
        if buf_start is None:
            buf_start = start
        buf.append(word)
        buf_end = end
        if len(buf) >= max_words or (buf_end - buf_start) >= max_dur or word[-1] in ".!?,":
            blocks.append({"start": buf_start, "end": buf_end, "text": " ".join(buf)})
            buf, buf_start = [], None
    if buf and buf_start is not None:
        blocks.append({"start": buf_start, "end": buf_end, "text": " ".join(buf)})
    return blocks


def build_srt(blocks: list) -> str:
    lines = []
    for i, b in enumerate(blocks, 1):
        lines += [str(i), f"{to_srt_time(b['start'])} --> {to_srt_time(b['end'])}", b["text"], ""]
    return "\n".join(lines)


# ─── Formata segundos em mm:ss ou hh:mm:ss ───────────────────────────────────
def fmt_time(secs: float) -> str:
    s = int(secs)
    h, m, s = s // 3600, s % 3600 // 60, s % 60
    return f"{h}h {m}m {s}s" if h else f"{m}m {s}s"


# ─── Processa um vídeo ────────────────────────────────────────────────────────
def process_video(model, video_path: Path, subtitles_dir: Path, max_words: int, language: str):
    stem     = video_path.stem
    srt_path = subtitles_dir / f"{stem}.srt"
    txt_path = subtitles_dir / f"{stem}.txt"

    if srt_path.exists() and txt_path.exists():
        warn(f"Já processado, pulando: {video_path.name}")
        return

    log(f"\n{'─'*60}", CYAN)
    log(f"  {BOLD}{video_path.name}{RESET}", CYAN)
    log(f"{'─'*60}", CYAN)

    t0       = time.time()
    duration = get_duration(video_path)

    with tempfile.TemporaryDirectory() as tmp:
        wav_path = Path(tmp) / "audio.wav"

        try:
            extract_audio(video_path, wav_path, duration)
        except RuntimeError as e:
            err(str(e))
            return

        try:
            full_text, word_ts = transcribe_audio(model, wav_path, language)
        except Exception as e:
            err(f"Falha na transcrição: {e}")
            return

    # ─── Salva resultados ─────────────────────────────────────────────────────
    spinner = Spinner("Salvando arquivos").start()
    txt_path.write_text(full_text, encoding="utf-8")

    if word_ts:
        blocks = words_to_blocks(word_ts, max_words=max_words)
        srt_path.write_text(build_srt(blocks), encoding="utf-8")
        spinner.done()
        log(f"  {GREEN}✓{RESET} {srt_path.name}  ({len(blocks)} blocos)")
    else:
        srt_path.write_text("", encoding="utf-8")
        spinner.done()
        warn("Sem word-timestamps — apenas .txt gerado.")

    log(f"  {GREEN}✓{RESET} {txt_path.name}")
    log(f"  {CYAN}Tempo do vídeo: {fmt_time(time.time() - t0)}{RESET}")


# ─── Entry point ──────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Transcreve vídeos com faster-whisper (GPU)")
    parser.add_argument("--data",      default="./data")
    parser.add_argument("--subtitles", default="./subtitles")
    parser.add_argument("--max-words", type=int, default=8)
    parser.add_argument("--ext",       nargs="+", default=["mp4", "mkv"])
    parser.add_argument("--model",     default="large-v3",
                        help="Modelo Whisper: tiny/base/small/medium/large-v3 (default: large-v3)")
    parser.add_argument("--language",  default="auto",
                        help="Idioma do áudio: pt, en, es... (default: auto-detect)")
    args = parser.parse_args()

    data_dir      = Path(args.data).resolve()
    subtitles_dir = Path(args.subtitles).resolve()
    extensions    = {f".{e.lstrip('.')}" for e in args.ext}

    if not data_dir.exists():
        err(f"Pasta de dados não encontrada: {data_dir}")
        sys.exit(1)

    subtitles_dir.mkdir(parents=True, exist_ok=True)

    videos = sorted([f for f in data_dir.iterdir()
                     if f.is_file() and f.suffix.lower() in extensions])

    if not videos:
        warn(f"Nenhum vídeo encontrado em {data_dir}")
        sys.exit(0)

    t_total = time.time()

    log(f"\n{'═'*60}", BOLD)
    log(f"  Faster-Whisper Transcriber", BOLD)
    log(f"{'═'*60}", BOLD)
    info(f"Vídeos  : {len(videos)}")
    info(f"Modelo  : {args.model}  |  Idioma: {args.language}")
    print()

    model = load_model(args.model)

    for i, video in enumerate(videos, 1):
        log(f"\n[{i}/{len(videos)}]", BOLD)
        process_video(model, video, subtitles_dir, args.max_words, args.language)

    log(f"\n{'═'*60}", GREEN)
    log(f"  Concluído! Legendas em: {subtitles_dir}", GREEN)
    log(f"  Tempo total: {fmt_time(time.time() - t_total)}", GREEN)
    log(f"{'═'*60}", GREEN)


if __name__ == "__main__":
    main()
