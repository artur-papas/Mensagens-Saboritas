from __future__ import annotations

import subprocess
import time

from .config import AppConfig


class AppiumServerManager:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._process: subprocess.Popen | None = None

    def start(self) -> None:
        if not self.config.manage_appium_server:
            return
        if not self.config.appium_command:
            raise RuntimeError(
                "O gerenciamento automático do Appium está ativado, mas nenhum comando do Appium foi configurado."
            )
        if self._process is not None:
            return
        self._process = subprocess.Popen(
            self.config.appium_command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        time.sleep(3)

    def stop(self) -> None:
        if self._process is None:
            return
        self._process.terminate()
        self._process.wait(timeout=10)
        self._process = None
