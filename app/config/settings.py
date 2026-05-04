import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "model"

DATABASE_PATH = MODEL_DIR / "titanic.db"
TRAIN_DATA_PATH = DATA_DIR / "train.csv"
TEST_DATA_PATH = DATA_DIR / "test.csv"
TRAINED_MODEL_PATH = MODEL_DIR / "titanic_model.pkl"

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
