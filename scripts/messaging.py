from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mensagens_saboritas.automation.whatsapp import (
    collect_contacts,
    forward_last_message,
    load_contacts_from_csv,
    save_contacts_to_csv,
)


__all__ = [
    "collect_contacts",
    "forward_last_message",
    "load_contacts_from_csv",
    "save_contacts_to_csv",
]
