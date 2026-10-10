"""Download the pinned public model during build, rather than during a request."""
import ssl
from pathlib import Path
from urllib.request import urlopen

from backend.vision import MODEL_ID, MODEL_REVISION


def main():
    target = Path(__file__).resolve().parents[1] / "models" / "buildings"
    target.mkdir(parents=True, exist_ok=True)
    for name in ("config.json", "preprocessor_config.json", "model.safetensors"):
        path = target / name
        if path.exists():
            continue
        url = f"https://huggingface.co/{MODEL_ID}/resolve/{MODEL_REVISION}/{name}"
        with urlopen(url, context=ssl.create_default_context(), timeout=180) as source:
            with path.open("wb") as output:
                while chunk := source.read(1024 * 1024):
                    output.write(chunk)
        print(f"Bundled pretrained model file: {name} ({path.stat().st_size} bytes)", flush=True)
    (target / "provenance.txt").write_text(
        f"{MODEL_ID}\nrevision={MODEL_REVISION}\nApache-2.0\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
