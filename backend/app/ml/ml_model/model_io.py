from pathlib import Path
import joblib
import json

BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"

MODEL_PATH = ARTIFACTS_DIR / "menu_model.joblib"
METADATA_PATH = ARTIFACTS_DIR / "menu_model_metadata.json"


def load_menu_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError("No existe el modelo entrenado")
    return joblib.load(MODEL_PATH)


def load_metadata():
    if not METADATA_PATH.exists():
        return {}
    return json.loads(METADATA_PATH.read_text())