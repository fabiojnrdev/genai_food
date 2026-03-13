"""
Configuração global do pytest.

Garante que a raiz do projeto esteja no sys.path,
permitindo imports absolutos como `from api.main import app`
independentemente de onde o pytest é invocado.
"""
import sys
from pathlib import Path

# Insere a raiz do projeto no início do path se ainda não estiver
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))