from __future__ import annotations

import csv
import queue
import threading
import time
import tkinter as tk
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import filedialog, ttk

from mensagens_saboritas.automation.whatsapp import collect_contacts, forward_last_message
from mensagens_saboritas.config import AppConfig, MAX_BATCH_SIZE, load_config


@dataclass(slots=True)
class WorkerState:
    thread: threading.Thread | None = None
    stop_event: threading.Event = field(default_factory=threading.Event)
    pause_event: threading.Event = field(default_factory=threading.Event)
    active: bool = False

    def reset_flags(self) -> None:
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()


class AppUI:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.root = tk.Tk()
        self.root.title("Mensagens Saboritas")
        self.root.geometry("880x620")
        self.root.minsize(780, 560)

        self.ui_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.scrape_state = WorkerState()
        self.send_state = WorkerState()

        self.status_var = tk.StringVar(value="Pronto.")
        self.scrape_count_var = tk.StringVar(value="0 contatos encontrados")
        self.file_var = tk.StringVar(value="Nenhum CSV selecionado")
        self.file_count_var = tk.StringVar(value="0 contatos carregados")
        self.output_name_var = tk.StringVar(value="contatos")
        self.source_contact_var = tk.StringVar()
        self.batch_size_var = tk.IntVar(value=self.config.default_batch_size)
        self.send_elapsed_var = tk.StringVar(value="Tempo decorrido: 00:00")
        self.send_remaining_var = tk.StringVar(value="Tempo restante estimado: --:--")
        self.send_progress_value = tk.DoubleVar(value=0.0)
        self.send_started_at: float | None = None

        self.selected_file: Path | None = None
        self._build()
        self.root.after(100, self._process_queue)

    def _build(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        header = ttk.Frame(self.root, padding=(20, 20, 20, 10))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="Mensagens Saboritas", font=("Segoe UI", 22, "bold")).grid(
            row=0,
            column=0,
            sticky="w",
        )
        ttk.Label(
            header,
            text="Colete contatos do WhatsApp Business e encaminhe a ultima mensagem com mais seguranca.",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        notebook = ttk.Notebook(self.root)
        notebook.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        collect_tab = ttk.Frame(notebook, padding=20)
        send_tab = ttk.Frame(notebook, padding=20)
        notebook.add(collect_tab, text="Coletar Contatos")
        notebook.add(send_tab, text="Enviar Mensagens")

        self._build_collect_tab(collect_tab)
        self._build_send_tab(send_tab)

        footer = ttk.Frame(self.root, padding=(20, 10, 20, 20))
        footer.grid(row=2, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        ttk.Label(footer, textvariable=self.status_var).grid(row=0, column=0, sticky="w")

    def _build_collect_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)

        form = ttk.LabelFrame(parent, text="Configuracoes da Coleta", padding=18)
        form.grid(row=0, column=0, columnspan=2, sticky="ew")
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Nome do arquivo de saida").grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.output_name_var).grid(row=0, column=1, sticky="ew", padx=(12, 0))

        ttk.Label(form, text="Contatos bloqueados").grid(row=1, column=0, sticky="nw", pady=(12, 0))
        blocked = tk.Text(form, height=6, width=40)
        blocked.grid(row=1, column=1, sticky="ew", padx=(12, 0), pady=(12, 0))
        blocked.insert("1.0", "\n".join(self.config.blocked_contacts))
        self.blocked_contacts_text = blocked

        progress = ttk.LabelFrame(parent, text="Progresso", padding=18)
        progress.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(18, 0))
        ttk.Label(progress, textvariable=self.scrape_count_var, font=("Segoe UI", 16, "bold")).grid(
            row=0,
            column=0,
            sticky="w",
        )
        ttk.Label(progress, text="Contatos unicos capturados ate agora").grid(
            row=1,
            column=0,
            sticky="w",
            pady=(8, 0),
        )
        ttk.Label(progress, text=f"Salvo em {self.config.output_dir}").grid(
            row=2,
            column=0,
            sticky="w",
            pady=(4, 0),
        )

        actions = ttk.Frame(parent)
        actions.grid(row=2, column=0, columnspan=2, sticky="e", pady=(18, 0))

        self.collect_start_btn = ttk.Button(actions, text="Iniciar", command=self.start_collect)
        self.collect_start_btn.grid(row=0, column=0, padx=(0, 8))
        self.collect_pause_btn = ttk.Button(actions, text="Pausar", command=self.pause_collect, state="disabled")
        self.collect_pause_btn.grid(row=0, column=1, padx=(0, 8))
        self.collect_cancel_btn = ttk.Button(actions, text="Cancelar", command=self.cancel_collect, state="disabled")
        self.collect_cancel_btn.grid(row=0, column=2)

    def _build_send_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(1, weight=1)

        settings = ttk.LabelFrame(parent, text="Configuracoes do Envio", padding=18)
        settings.grid(row=0, column=0, columnspan=2, sticky="ew")
        settings.columnconfigure(1, weight=1)

        ttk.Label(settings, text="CSV de contatos").grid(row=0, column=0, sticky="w")
        ttk.Label(settings, textvariable=self.file_var).grid(row=0, column=1, sticky="w", padx=(12, 12))
        ttk.Button(settings, text="Procurar", command=self.select_file).grid(row=0, column=2, sticky="e")

        ttk.Label(settings, text="Contato de origem").grid(row=1, column=0, sticky="w", pady=(12, 0))
        ttk.Entry(settings, textvariable=self.source_contact_var).grid(
            row=1,
            column=1,
            columnspan=2,
            sticky="ew",
            pady=(12, 0),
            padx=(12, 0),
        )

        ttk.Label(settings, text=f"Contatos por lote (maximo {MAX_BATCH_SIZE})").grid(
            row=2,
            column=0,
            sticky="w",
            pady=(12, 0),
        )
        ttk.Spinbox(settings, from_=1, to=MAX_BATCH_SIZE, textvariable=self.batch_size_var, width=8).grid(
            row=2,
            column=1,
            sticky="w",
            padx=(12, 0),
            pady=(12, 0),
        )

        summary = ttk.LabelFrame(parent, text="Arquivo Selecionado", padding=18)
        summary.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(18, 0))
        summary.columnconfigure(0, weight=1)
        ttk.Label(summary, textvariable=self.file_count_var, font=("Segoe UI", 16, "bold")).grid(
            row=0,
            column=0,
            sticky="w",
        )
        ttk.Label(
            summary,
            text="A ultima mensagem do contato de origem sera encaminhada em lotes.",
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))

        ttk.Label(
            summary,
            text=f"O tamanho do lote e limitado a {MAX_BATCH_SIZE} contatos para combinar com o fluxo de encaminhamento.",
        ).grid(row=2, column=0, sticky="w", pady=(8, 0))

        ttk.Progressbar(
            summary,
            variable=self.send_progress_value,
            maximum=100,
            mode="determinate",
        ).grid(row=3, column=0, sticky="ew", pady=(12, 0))
        ttk.Label(summary, textvariable=self.send_elapsed_var).grid(row=4, column=0, sticky="w", pady=(8, 0))
        ttk.Label(summary, textvariable=self.send_remaining_var).grid(row=5, column=0, sticky="w", pady=(4, 0))

        actions = ttk.Frame(parent)
        actions.grid(row=2, column=0, columnspan=2, sticky="e", pady=(18, 0))

        self.send_start_btn = ttk.Button(actions, text="Iniciar", command=self.start_send)
        self.send_start_btn.grid(row=0, column=0, padx=(0, 8))
        self.send_pause_btn = ttk.Button(actions, text="Pausar", command=self.pause_send, state="disabled")
        self.send_pause_btn.grid(row=0, column=1, padx=(0, 8))
        self.send_cancel_btn = ttk.Button(actions, text="Cancelar", command=self.cancel_send, state="disabled")
        self.send_cancel_btn.grid(row=0, column=2)

    def _process_queue(self) -> None:
        while True:
            try:
                action, payload = self.ui_queue.get_nowait()
            except queue.Empty:
                break

            if action == "status":
                self.status_var.set(str(payload))
            elif action == "scrape-progress":
                count = int(payload)
                self.scrape_count_var.set(f"{count} contatos encontrados")
            elif action == "send-progress":
                current, total = payload
                self.file_count_var.set(f"{current} de {total} contatos processados")
                self._update_send_progress(current, total)
            elif action == "collect-done":
                self._set_collect_idle()
            elif action == "send-done":
                self._set_send_idle()

        self.root.after(100, self._process_queue)

    def _run_worker(self, state: WorkerState, target) -> None:
        state.reset_flags()
        state.active = True
        state.thread = threading.Thread(target=target, daemon=True)
        state.thread.start()

    def _blocked_contacts(self) -> list[str]:
        raw = self.blocked_contacts_text.get("1.0", "end").strip()
        return [line.strip() for line in raw.splitlines() if line.strip()]

    def _format_duration(self, seconds: float) -> str:
        total_seconds = max(0, int(seconds))
        minutes, secs = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def _update_send_progress(self, current: int, total: int) -> None:
        if total <= 0:
            self.send_progress_value.set(0.0)
            self.send_elapsed_var.set("Tempo decorrido: 00:00")
            self.send_remaining_var.set("Tempo restante estimado: --:--")
            return

        self.send_progress_value.set((current / total) * 100)

        if self.send_started_at is None or current <= 0:
            self.send_elapsed_var.set("Tempo decorrido: 00:00")
            self.send_remaining_var.set("Tempo restante estimado: --:--")
            return

        elapsed = time.monotonic() - self.send_started_at
        self.send_elapsed_var.set(f"Tempo decorrido: {self._format_duration(elapsed)}")

        if current >= total:
            self.send_remaining_var.set("Tempo restante estimado: 00:00")
            return

        average_per_contact = elapsed / current
        remaining = average_per_contact * (total - current)
        self.send_remaining_var.set(
            f"Tempo restante estimado: {self._format_duration(remaining)}"
        )

    def start_collect(self) -> None:
        if self.scrape_state.active:
            return
        output_name = self.output_name_var.get().strip()
        if not output_name:
            self.status_var.set("O nome do arquivo de saida e obrigatorio.")
            return

        self.config.blocked_contacts = self._blocked_contacts()
        self.collect_start_btn.config(state="disabled")
        self.collect_pause_btn.config(state="normal", text="Pausar")
        self.collect_cancel_btn.config(state="normal")
        self.scrape_count_var.set("0 contatos encontrados")

        def worker() -> None:
            try:
                collect_contacts(
                    config=self.config,
                    output_name=output_name,
                    on_status=lambda message: self.ui_queue.put(("status", message)),
                    on_progress=lambda count, _total: self.ui_queue.put(("scrape-progress", count)),
                    is_paused=self.scrape_state.pause_event.is_set,
                    should_stop=self.scrape_state.stop_event.is_set,
                )
            except Exception as exc:
                self.ui_queue.put(("status", f"Falha na coleta: {exc}"))
            finally:
                self.ui_queue.put(("collect-done", None))

        self.status_var.set("Iniciando coleta de contatos...")
        self._run_worker(self.scrape_state, worker)

    def pause_collect(self) -> None:
        if not self.scrape_state.active:
            return
        if self.scrape_state.pause_event.is_set():
            self.scrape_state.pause_event.clear()
            self.collect_pause_btn.config(text="Pausar")
            self.status_var.set("Coleta retomada.")
        else:
            self.scrape_state.pause_event.set()
            self.collect_pause_btn.config(text="Continuar")
            self.status_var.set("Coleta pausada.")

    def cancel_collect(self) -> None:
        if self.scrape_state.active:
            self.scrape_state.stop_event.set()
            self.status_var.set("Cancelando coleta...")

    def start_send(self) -> None:
        if self.send_state.active:
            return
        if self.selected_file is None:
            self.status_var.set("Selecione um CSV de contatos antes de enviar.")
            return
        if not self.source_contact_var.get().strip():
            self.status_var.set("O contato de origem e obrigatorio.")
            return

        self.send_start_btn.config(state="disabled")
        self.send_pause_btn.config(state="normal", text="Pausar")
        self.send_cancel_btn.config(state="normal")
        self.send_started_at = time.monotonic()
        self.send_progress_value.set(0.0)
        self.send_elapsed_var.set("Tempo decorrido: 00:00")
        self.send_remaining_var.set("Tempo restante estimado: calculando...")

        def worker() -> None:
            try:
                forward_last_message(
                    config=self.config,
                    source_contact=self.source_contact_var.get().strip(),
                    contact_file=self.selected_file,
                    batch_size=max(1, min(MAX_BATCH_SIZE, int(self.batch_size_var.get()))),
                    on_status=lambda message: self.ui_queue.put(("status", message)),
                    on_progress=lambda current, total: self.ui_queue.put(("send-progress", (current, total))),
                    is_paused=self.send_state.pause_event.is_set,
                    should_stop=self.send_state.stop_event.is_set,
                )
            except Exception as exc:
                self.ui_queue.put(("status", f"Falha no envio: {exc}"))
            finally:
                self.ui_queue.put(("send-done", None))

        self.status_var.set("Iniciando encaminhamento de mensagens...")
        self._run_worker(self.send_state, worker)

    def pause_send(self) -> None:
        if not self.send_state.active:
            return
        if self.send_state.pause_event.is_set():
            self.send_state.pause_event.clear()
            self.send_pause_btn.config(text="Pausar")
            self.status_var.set("Envio retomado.")
        else:
            self.send_state.pause_event.set()
            self.send_pause_btn.config(text="Continuar")
            self.status_var.set("Envio pausado.")

    def cancel_send(self) -> None:
        if self.send_state.active:
            self.send_state.stop_event.set()
            self.status_var.set("Cancelando envio...")

    def select_file(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Selecione um arquivo CSV",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
            initialdir=str(self.config.output_dir),
        )
        if not file_path:
            return

        path = Path(file_path)
        with path.open("r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            count = sum(1 for row in reader if row and row[0].strip())

        self.selected_file = path
        self.file_var.set(str(path))
        self.file_count_var.set(f"{count} contatos carregados")
        self.status_var.set(f"Arquivo selecionado: {path.name}.")
        self.send_progress_value.set(0.0)
        self.send_elapsed_var.set("Tempo decorrido: 00:00")
        self.send_remaining_var.set("Tempo restante estimado: --:--")

    def _set_collect_idle(self) -> None:
        self.scrape_state.active = False
        self.collect_start_btn.config(state="normal")
        self.collect_pause_btn.config(state="disabled", text="Pausar")
        self.collect_cancel_btn.config(state="disabled")

    def _set_send_idle(self) -> None:
        self.send_state.active = False
        self.send_start_btn.config(state="normal")
        self.send_pause_btn.config(state="disabled", text="Pausar")
        self.send_cancel_btn.config(state="disabled")
        if self.send_started_at is not None and self.send_progress_value.get() >= 100:
            elapsed = time.monotonic() - self.send_started_at
            self.send_elapsed_var.set(f"Tempo decorrido: {self._format_duration(elapsed)}")
            self.send_remaining_var.set("Tempo restante estimado: 00:00")
        self.send_started_at = None

    def run(self) -> None:
        self.root.mainloop()


def run_gui(config: AppConfig | None = None) -> None:
    resolved_config = config or load_config(Path.cwd())
    app = AppUI(resolved_config)
    app.run()
