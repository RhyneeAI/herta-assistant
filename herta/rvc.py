"""
RVC v2 (Retrieval-based Voice Conversion) inference module.
Converts base TTS audio into authentic Yamazaki Haruka (山崎はるか / Herta) voice.
Enhanced with PyTorch multi-threading, dynamic index weighting, phrase caching,
and background model pre-warming.
"""

import hashlib
import os
import shutil
import sys
import threading
import warnings

# Suppress PyTorch internal deprecation notices
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

from herta.config import CACHE_DIR, TMP_DIR, load_config

_loader_instance = None
_loader_failed = False
_loader_lock = threading.Lock()
_prewarmed = False

RVC_CACHE_DIR = os.path.join(CACHE_DIR, "rvc_cache")
os.makedirs(RVC_CACHE_DIR, exist_ok=True)


def optimize_torch_cpu_threads():
    """Configure PyTorch CPU thread count to maximize multi-core performance."""
    try:
        import torch
        cores = os.cpu_count() or 4
        # Allocate optimal thread pool for modern multi-core CPUs (e.g. Ryzen 8c/16t)
        optimal_threads = min(12, max(4, cores - 2))
        torch.set_num_threads(optimal_threads)
    except Exception:
        pass


def get_rvc_loader():
    """Retrieve or initialize singleton RVC inference loader."""
    global _loader_instance, _loader_failed
    with _loader_lock:
        if _loader_failed:
            return None
        if _loader_instance is not None:
            return _loader_instance

        cfg = load_config()
        model_path = cfg.get("rvc_model_path", "")
        index_path = cfg.get("rvc_index_path", "")
        index_influence = float(cfg.get("rvc_index_influence", 0.3))

        if not model_path or not os.path.exists(model_path):
            return None

        optimize_torch_cpu_threads()

        try:
            from infer_rvc_python import BaseLoader
            loader = BaseLoader(only_cpu=True)
            # Use index only if influence > 0 and file exists
            use_index = index_path if (index_influence > 0 and os.path.exists(index_path)) else ""
            loader.apply_conf(
                tag="herta",
                file_model=model_path,
                file_index=use_index,
                pitch_algo="pm",
                pitch_lvl=0,
                index_influence=index_influence,
            )
            _loader_instance = loader
            return _loader_instance
        except Exception as exc:
            sys.stderr.write(f"RVC loader initialization error: {exc}\n")
            _loader_failed = True
            return None


def preload_rvc_in_background():
    """Pre-warm RVC model asynchronously in background to eliminate first-turn lag."""
    global _prewarmed
    if _prewarmed:
        return
    _prewarmed = True

    def _worker():
        get_rvc_loader()

    threading.Thread(target=_worker, daemon=True).start()


def _get_audio_file_hash(filepath: str) -> str:
    """Calculate fast hash of source audio file for caching."""
    hasher = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return ""


def convert_voice(source_audio_path: str, output_path: str = None) -> str:
    """
    Transform source audio into Yamazaki Haruka voice using RVC v2.
    Enhanced with automatic audio phrase caching for instant turnaround.
    """
    cfg = load_config()
    if not cfg.get("rvc_enabled", True):
        return source_audio_path

    if not os.path.exists(source_audio_path):
        return source_audio_path

    loader = get_rvc_loader()
    if not loader:
        return source_audio_path

    if output_path is None:
        output_path = os.path.join(TMP_DIR, "rvc_herta_output.wav")

    # 1. Fast Cache Check: if exact source audio was converted previously
    audio_hash = _get_audio_file_hash(source_audio_path)
    if audio_hash:
        cached_file = os.path.join(RVC_CACHE_DIR, f"{audio_hash}.wav")
        if os.path.exists(cached_file) and os.path.getsize(cached_file) > 1000:
            shutil.copyfile(cached_file, output_path)
            return output_path

    try:
        import soundfile as sf
        audio_data, sr = loader.generate_from_cache(audio_data=source_audio_path, tag="herta")
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass
        sf.write(output_path, audio_data, sr)

        # Save to phrase cache for subsequent instant playback
        if audio_hash:
            try:
                shutil.copyfile(output_path, os.path.join(RVC_CACHE_DIR, f"{audio_hash}.wav"))
            except Exception:
                pass

        return output_path
    except Exception as exc:
        sys.stderr.write(f"RVC voice conversion error: {exc}\n")
        return source_audio_path
