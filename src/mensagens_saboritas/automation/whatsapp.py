from __future__ import annotations

import csv
import time
from pathlib import Path
from typing import Callable

import emoji
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy

from mensagens_saboritas.config import AppConfig


StatusCallback = Callable[[str], None]
ProgressCallback = Callable[[int, int], None]
PauseCheck = Callable[[], bool]
StopCheck = Callable[[], bool]


def remove_emojis(text: str) -> str:
    return "".join(char for char in text if char not in emoji.EMOJI_DATA)


def save_contacts_to_csv(contacts: list[str], filename: Path) -> None:
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        for contact in contacts:
            writer.writerow([contact])


def load_contacts_from_csv(filename: Path) -> list[str]:
    with filename.open("r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        return [row[0].strip() for row in reader if row and row[0].strip()]


def _wait_if_paused(is_paused: PauseCheck, should_stop: StopCheck) -> None:
    while is_paused() and not should_stop():
        time.sleep(0.2)


def _driver(config: AppConfig):
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.device_name = config.device_name
    options.app_package = config.whatsapp_package
    options.app_activity = config.whatsapp_activity
    options.no_reset = True
    options.full_reset = False
    options.set_capability("forceAppLaunch", True)

    driver = webdriver.Remote(
        command_executor=config.appium_url,
        options=options,
    )
    time.sleep(3)
    return driver


def _safe_back(driver, label: str, attempts: int = 3) -> None:
    for _ in range(attempts):
        try:
            driver.find_element(AppiumBy.ACCESSIBILITY_ID, label).click()
            time.sleep(0.1)
        except Exception:
            return


def _enter_visible_chat(driver, contact: str) -> None:
    try:
        chat_list_view = driver.find_element(AppiumBy.ID, "android:id/list")
        rows = chat_list_view.find_elements(AppiumBy.ID, "com.whatsapp.w4b:id/contact_row_container")
    except Exception as exc:
        raise RuntimeError("Não foi possível ler a lista de conversas do WhatsApp.") from exc

    for row in rows:
        try:
            name = row.find_element(AppiumBy.ID, "com.whatsapp.w4b:id/conversations_row_contact_name")
        except Exception:
            continue
        if name.text.strip() == contact:
            row.click()
            time.sleep(0.4)
            return
    raise RuntimeError(
        f'O contato de origem "{contact}" não está visível na lista atual de conversas. '
        "Abra o WhatsApp Business e deixe essa conversa na tela antes de iniciar."
    )


def forward_last_message(
    *,
    config: AppConfig,
    source_contact: str,
    contact_file: Path,
    batch_size: int,
    on_status: StatusCallback,
    on_progress: ProgressCallback,
    is_paused: PauseCheck,
    should_stop: StopCheck,
) -> None:
    if not source_contact.strip():
        raise RuntimeError("O contato de origem é obrigatório.")

    contact_list = load_contacts_from_csv(contact_file)
    if not contact_list:
        raise RuntimeError("O arquivo CSV selecionado não contém contatos.")

    driver = None
    contacts_found: list[str] = []
    contacts_not_found: list[str] = []
    labels = config.labels

    try:
        driver = _driver(config)
        total = len(contact_list)
        on_status(f"Enviando para {total} contatos a partir de {contact_file.name}.")

        for start in range(0, total, batch_size):
            if should_stop():
                break
            _wait_if_paused(is_paused, should_stop)
            if should_stop():
                break

            _enter_visible_chat(driver, source_contact)

            messages = driver.find_elements(AppiumBy.ID, "com.whatsapp.w4b:id/main_layout")
            if not messages:
                raise RuntimeError("Nenhuma mensagem foi encontrada na conversa de origem.")

            driver.execute_script(
                "mobile: longClickGesture",
                {"elementId": messages[-1].id, "duration": 1000},
            )
            time.sleep(0.1)

            driver.find_element(AppiumBy.ACCESSIBILITY_ID, labels["forward"]).click()
            time.sleep(0.1)
            driver.find_element(AppiumBy.ACCESSIBILITY_ID, labels["search"]).click()
            time.sleep(0.1)
            search_input = driver.find_element(AppiumBy.ID, "com.whatsapp.w4b:id/search_src_text")

            any_contact_found = False
            for offset in range(batch_size):
                index = start + offset
                if index >= total or should_stop():
                    break

                _wait_if_paused(is_paused, should_stop)
                contact_name = contact_list[index]

                search_input.clear()
                search_input.send_keys(contact_name)
                time.sleep(1.0)
                results = driver.find_elements(AppiumBy.ID, "com.whatsapp.w4b:id/contactpicker_row_name")
                if results and '"' not in results[-1].text:
                    results[-1].click()
                    contacts_found.append(contact_name)
                    any_contact_found = True
                else:
                    contacts_not_found.append(contact_name)

                on_progress(min(index + 1, total), total)
                time.sleep(0.1)

            if any_contact_found and not should_stop():
                driver.find_element(AppiumBy.ACCESSIBILITY_ID, labels["send"]).click()
                on_status(f"Lote enviado. Sucesso: {len(contacts_found)} | Não encontrados: {len(contacts_not_found)}")
            else:
                _safe_back(driver, labels["back"], attempts=3)

            try:
                driver.find_element(AppiumBy.ID, "com.whatsapp.w4b:id/whatsapp_toolbar_home").click()
            except Exception:
                pass
            time.sleep(0.1)

        if should_stop():
            on_status("Envio cancelado.")
        else:
            on_status(
                f"Envio concluído. Sucesso: {len(contacts_found)} | Não encontrados: {len(contacts_not_found)}"
            )
    finally:
        if driver is not None:
            driver.quit()


def collect_contacts(
    *,
    config: AppConfig,
    output_name: str,
    on_status: StatusCallback,
    on_progress: ProgressCallback,
    is_paused: PauseCheck,
    should_stop: StopCheck,
) -> Path:
    normalized_name = output_name.strip()
    if not normalized_name:
        raise RuntimeError("O nome do arquivo de saída não pode ficar vazio.")

    if not normalized_name.lower().endswith(".csv"):
        normalized_name += ".csv"

    output_path = config.output_dir / normalized_name
    driver = None

    try:
        driver = _driver(config)
        collected_titles: set[str] = set()
        new_titles_found = True

        try:
            chat_list_view = driver.find_element(AppiumBy.ID, "android:id/list")
        except Exception as exc:
            raise RuntimeError("Não foi possível encontrar a lista de conversas do WhatsApp.") from exc

        on_status(f"Coletando contatos em {output_path.name}.")
        while new_titles_found and not should_stop():
            _wait_if_paused(is_paused, should_stop)
            new_titles_found = False
            rows = chat_list_view.find_elements(AppiumBy.ID, "com.whatsapp.w4b:id/contact_row_container")

            for row in rows:
                if should_stop():
                    break
                try:
                    name_elem = row.find_element(
                        AppiumBy.ID,
                        "com.whatsapp.w4b:id/conversations_row_contact_name",
                    )
                    title = remove_emojis(name_elem.text.strip().replace("\u200d", ""))
                except Exception:
                    continue

                if title and title not in config.blocked_contacts and title not in collected_titles:
                    collected_titles.add(title)
                    new_titles_found = True
                    on_progress(len(collected_titles), len(collected_titles))

            if not should_stop():
                driver.swipe(start_x=500, start_y=1100, end_x=500, end_y=400, duration=500)
                time.sleep(0.3)

        contacts = sorted(collected_titles, key=str.casefold)
        if contacts:
            save_contacts_to_csv(contacts, output_path)
            on_status(f"{len(contacts)} contatos salvos em {output_path.name}.")
            return output_path
        raise RuntimeError("Nenhum contato foi encontrado.")
    finally:
        if driver is not None:
            driver.quit()
