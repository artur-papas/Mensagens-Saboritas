from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_BLOCKED_CONTACTS = [
    "Service Notifications",
    "WhatsApp Support",
    "WhatsApp Business",
    "Payment Notifications",
    "System Notifications",
    "Marketing Group",
    "Broadcast List",
    "Group Announcements",
]
MAX_BATCH_SIZE = 5


@dataclass(slots=True)
class AppConfig:
    project_root: Path
    appium_url: str = "http://127.0.0.1:4723"
    appium_command: list[str] = field(default_factory=list)
    manage_appium_server: bool = False
    device_name: str = "Android"
    whatsapp_package: str = "com.whatsapp.w4b"
    whatsapp_activity: str = "com.whatsapp.home.ui.HomeActivity"
    default_batch_size: int = 1
    output_dir: Path = field(default_factory=Path)
    blocked_contacts: list[str] = field(default_factory=lambda: list(DEFAULT_BLOCKED_CONTACTS))
    labels: dict[str, str] = field(
        default_factory=lambda: {
            "forward": "Encaminhar",
            "search": "Pesquisar",
            "send": "Enviar",
            "back": "Voltar",
        }
    )

    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"

    def ensure_directories(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)


def _split_command(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [part.strip() for part in raw.split() if part.strip()]


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_config(project_root: Path | None = None) -> AppConfig:
    root = project_root or Path.cwd()
    config_path = root / "configuracao.json"
    if not config_path.is_file():
        config_path = root / "mensagens_saboritas.json"
    file_config = _load_json(config_path)

    output_dir = Path(
        os.getenv(
            "MENSAGENS_OUTPUT_DIR",
            file_config.get("output_dir", str(root / "outputs")),
        )
    )

    configured_command = file_config.get("appium_command")
    env_command = os.getenv("MENSAGENS_APPIUM_COMMAND")
    appium_command = _split_command(env_command) or list(configured_command or [])
    if not appium_command:
        discovered = shutil.which("appium")
        if discovered:
            appium_command = [discovered]

    config = AppConfig(
        project_root=root,
        appium_url=os.getenv("MENSAGENS_APPIUM_URL", file_config.get("appium_url", "http://127.0.0.1:4723")),
        appium_command=appium_command,
        manage_appium_server=bool(
            os.getenv("MENSAGENS_MANAGE_APPIUM", str(file_config.get("manage_appium_server", False))).lower()
            in {"1", "true", "yes", "on"}
        ),
        device_name=os.getenv("MENSAGENS_DEVICE_NAME", file_config.get("device_name", "Android")),
        whatsapp_package=file_config.get("whatsapp_package", "com.whatsapp.w4b"),
        whatsapp_activity=file_config.get("whatsapp_activity", "com.whatsapp.home.ui.HomeActivity"),
        default_batch_size=max(
            1,
            min(
                MAX_BATCH_SIZE,
                int(os.getenv("MENSAGENS_BATCH_SIZE", file_config.get("default_batch_size", 1))),
            ),
        ),
        output_dir=output_dir,
        blocked_contacts=list(file_config.get("blocked_contacts", DEFAULT_BLOCKED_CONTACTS)),
        labels=dict(
            {
                "forward": "Encaminhar",
                "search": "Pesquisar",
                "send": "Enviar",
                "back": "Voltar",
            }
            | dict(file_config.get("labels", {}))
        ),
    )
    config.ensure_directories()
    return config
