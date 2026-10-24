"""
Model Downloader for Madam Herta RVC v2 Weights.
Downloads Herta JP model weights (model.pth and model.index) from Hugging Face.
"""

import os
import shutil
import sys
import urllib.request
import zipfile

from herta.config import CONFIG_DIR, IS_WINDOWS

MODEL_DIR = os.path.join(CONFIG_DIR, "models")
MODEL_ZIP_URL = "https://huggingface.co/Thereallo/RVCModels/resolve/main/HertaJP.zip"


def download_and_setup_models():
    """Download Herta JP model weights if not present."""
    os.makedirs(MODEL_DIR, exist_ok=True)
    pth_dest = os.path.join(MODEL_DIR, "model.pth")
    index_dest = os.path.join(MODEL_DIR, "model.index")

    if os.path.exists(pth_dest) and os.path.exists(index_dest):
        print(f"Herta JP models already exist in: {MODEL_DIR}")
        return

    # Check if local files exist on Linux (/mnt/games/rvc_models)
    local_source = "/mnt/games/rvc_models"
    if not IS_WINDOWS and os.path.exists(os.path.join(local_source, "model.pth")):
        print(f"Linking existing models from {local_source}...")
        try:
            if not os.path.exists(pth_dest):
                os.symlink(os.path.join(local_source, "model.pth"), pth_dest)
            if not os.path.exists(index_dest):
                os.symlink(os.path.join(local_source, "model.index"), index_dest)
            print("Successfully linked local models.")
            return
        except Exception:
            pass

    print(f"Downloading Herta JP RVC model from Hugging Face...")
    zip_dest = os.path.join(MODEL_DIR, "HertaJP.zip")

    try:
        urllib.request.urlretrieve(MODEL_ZIP_URL, zip_dest)
        print("Extracting archive...")
        with zipfile.ZipFile(zip_dest, "r") as z:
            z.extractall(MODEL_DIR)

        # Rename extracted files to standardized names
        for root, _, files in os.walk(MODEL_DIR):
            for file in files:
                if file.endswith(".pth") and file != "model.pth":
                    shutil.move(os.path.join(root, file), pth_dest)
                elif file.endswith(".index") and file != "model.index":
                    shutil.move(os.path.join(root, file), index_dest)

        if os.path.exists(zip_dest):
            os.remove(zip_dest)

        print(f"Model installation complete! Models stored in {MODEL_DIR}")
    except Exception as exc:
        sys.stderr.write(f"Download failed: {exc}\n")
        print("You can manually place model.pth and model.index into: " + MODEL_DIR)


if __name__ == "__main__":
    download_and_setup_models()
