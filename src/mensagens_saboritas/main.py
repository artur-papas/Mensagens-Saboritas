from __future__ import annotations

import argparse
from pathlib import Path

from mensagens_saboritas.config import load_config
from mensagens_saboritas.runtime import AppiumServerManager


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mensagens Saboritas launcher")
    parser.add_argument(
        "--manage-appium",
        action="store_true",
        help="Start and stop the local Appium server automatically.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root that contains mensagens_saboritas.json.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(args.project_root)
    if args.manage_appium:
        config.manage_appium_server = True

    manager = AppiumServerManager(config)
    manager.start()
    try:
        from mensagens_saboritas.ui.app import run_gui

        run_gui(config)
    finally:
        manager.stop()
    return 0
