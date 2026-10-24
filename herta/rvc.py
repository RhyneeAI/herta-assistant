"""
RVC v2 (Retrieval-based Voice Conversion) inference module.
Converts base TTS audio into authentic Yamazaki Haruka (山崎はるか / Herta) voice.
"""

import os
import sys
import warnings

# Suppress PyTorch internal deprecation notices
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

from herta.config import TMP_DIR, load_config

_loader_instance = None
_loader_failed = False


def get_rvc_loader():
    """Retrieve or initialize singleton RVC inference loader."""
    global _loader_instance, _loader_failed

    if _loader_failed:
        return None
    if _loader_instance is not None:
        return _loader_instance

    cfg = load_config()
    model_path = cfg.get("rvc_model_path", "")
    index_path = cfg.get("rvc_index_path", "")

    if not model_path or not os.path.exists(model_path):
        return None

    try:
        from infer_rvc_python import BaseLoader
        loader = BaseLoader(only_cpu=True)
        loader.apply_conf(
            tag="herta",
            file_model=model_path,
            file_index=index_path if os.path.exists(index_path) else "",
            pitch_algo="pm",
            pitch_lvl=0,
            index_influence=0.75,
        )
        _loader_instance = loader
        return _loader_instance
    except Exception as exc:
        sys.stderr.write(f"RVC loader initialization error: {exc}\n")
        _loader_failed = True
        return None


def convert_voice(source_audio_path: str, output_path: str = None) -> str:
    """
    Transform source audio into Yamazaki Haruka voice using RVC v2.
    If RVC is unavailable or disabled, returns the source audio path.
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

    try:
        import soundfile as sf
        audio_data, sr = loader.generate_from_cache(audio_data=source_audio_path, tag="herta")
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass
        sf.write(output_path, audio_data, sr)
        return output_path
    except Exception as exc:
        sys.stderr.write(f"RVC voice conversion error: {exc}\n")
        return source_audio_path
