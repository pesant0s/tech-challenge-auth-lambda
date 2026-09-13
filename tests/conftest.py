import os
import sys
from pathlib import Path

# Espelha o runtime da Lambda, que importa a partir da raiz do zip.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ.setdefault("SECRET_KEY", "chave-de-teste-com-mais-de-32-caracteres-ok")
