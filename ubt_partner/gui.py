from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

from .config import WorkspacePaths
from .providers import ProviderConfig, ProviderRegistry
from .reference_map import build_reference_map
from .sessions import SessionNode, SessionStore
from .ubt import UBTExecutor
from .watcher import scan_file_state, diff_states


class UBTPartnerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("UBT Coding Partner")
        self.root.geometry("1100x760")

        self.repo_var = tk.StringVar(value=str(Path.cwd()))
        self.target_var = tk.StringVar(value="MyProjectEditor")
        self.platform_var = tk.StringVar(value="Win64")
        self.config_var = tk.StringVar(value="Development")

        self.current_state: dict[str, float] = {}
        self.paths = WorkspacePaths(Path(self.repo_var.get()).resolve())
        self.session_store = SessionStore(self.paths.sessions)
        self.ubt = UBTExecutor(self.paths.logs)
        self.providers = ProviderRegistry(self.paths.providers)

        self.current_session = SessionNode.create("main")
        self.session_store.save(self.current_session)

        self._build_ui()

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")

        ttk.Label(top, text="Repo Path").pack(side="left")
        ttk.Entry(top, textvariable=self.repo_var, width=70).pack(side="left", padx=6)
        ttk.Button(top, text="Start Tracking", command=self.start_tracking).pack(side="left")

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        build_tab = ttk.Frame(notebook)
        sessions_tab = ttk.Frame(notebook)
        refs_tab = ttk.Frame(notebook)
        providers_tab = ttk.Frame(notebook)

        notebook.add(build_tab, text="UBT")
        notebook.add(sessions_tab, text="Sessions")
        notebook.add(refs_tab, text="Reference Map")
        notebook.add(providers_tab, text="AI Providers")

        self._build_build_tab(build_tab)
        self._build_sessions_tab(sessions_tab)
        self._build_refs_tab(refs_tab)
        self._build_providers_tab(providers_tab)

    def refresh_paths(self) -> None:
        self.paths = WorkspacePaths(Path(self.repo_var.get()).resolve())
        self.paths.logs.mkdir(parents=True, exist_ok=True)
        self.paths.sessions.mkdir(parents=True, exist_ok=True)
        self.paths.config.mkdir(parents=True, exist_ok=True)
        self.session_store = SessionStore(self.paths.sessions)
        self.ubt = UBTExecutor(self.paths.logs)
        self.providers = ProviderRegistry(self.paths.providers)

    def start_tracking(self) -> None:
        self.refresh_paths()
        repo = Path(self.repo_var.get()).resolve()
        if not repo.exists():
            messagebox.showerror("Error", "Repo path does not exist")
            return
        self.current_state = scan_file_state(repo)
        self.log_text.insert("end", f"Tracking started: {len(self.current_state)} files\n")

    def _build_build_tab(self, tab: ttk.Frame) -> None:
        controls = ttk.Frame(tab, padding=8)
        controls.pack(fill="x")

        ttk.Label(controls, text="Target").grid(row=0, column=0, sticky="w")
        ttk.Entry(controls, textvariable=self.target_var, width=30).grid(row=0, column=1, padx=4)
        ttk.Label(controls, text="Platform").grid(row=0, column=2, sticky="w")
        ttk.Entry(controls, textvariable=self.platform_var, width=20).grid(row=0, column=3, padx=4)
        ttk.Label(controls, text="Config").grid(row=0, column=4, sticky="w")
        ttk.Entry(controls, textvariable=self.config_var, width=20).grid(row=0, column=5, padx=4)

        ttk.Button(controls, text="Run Build", command=self.run_build).grid(row=1, column=0, pady=8, sticky="w")
        ttk.Button(controls, text="Save Snapshot", command=self.save_snapshot).grid(row=1, column=1, pady=8, sticky="w")

        self.log_text = tk.Text(tab, wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=8, pady=8)

    def run_build(self) -> None:
        repo = Path(self.repo_var.get()).resolve()
        ubt_command = (
            f"Engine/Build/BatchFiles/Build.bat {self.target_var.get()} "
            f"{self.platform_var.get()} {self.config_var.get()}"
        )
        result = self.ubt.run(ubt_command, cwd=repo)

        self.current_session.last_build_log = str(result.log_path)
        self.session_store.save(self.current_session)

        self.log_text.insert("end", f"\n[BUILD] {result.command}\n")
        self.log_text.insert("end", f"Return code: {result.return_code}\n")
        self.log_text.insert("end", f"Log: {result.log_path}\n")
        self.log_text.insert("end", "Errors:\n")
        if result.error_lines:
            for line in result.error_lines:
                self.log_text.insert("end", f" - {line}\n")
        else:
            self.log_text.insert("end", " - no explicit error lines detected\n")

    def save_snapshot(self) -> None:
        repo = Path(self.repo_var.get()).resolve()
        latest = scan_file_state(repo)
        changed = diff_states(self.current_state, latest)
        self.current_state = latest

        self.current_session.changed_files = changed
        self.current_session.reference_map = build_reference_map(repo)
        self.session_store.save(self.current_session)

        self.log_text.insert("end", f"\n[SNAPSHOT] changed files: {len(changed)}\n")
        for path in changed[:200]:
            self.log_text.insert("end", f" * {path}\n")

    def _build_sessions_tab(self, tab: ttk.Frame) -> None:
        frame = ttk.Frame(tab, padding=8)
        frame.pack(fill="both", expand=True)

        self.session_list = tk.Listbox(frame)
        self.session_list.pack(side="left", fill="both", expand=True)

        side = ttk.Frame(frame)
        side.pack(side="left", fill="y", padx=8)
        ttk.Button(side, text="Refresh", command=self.refresh_sessions).pack(fill="x")
        ttk.Button(side, text="Create Branch Session", command=self.create_branch).pack(fill="x", pady=6)

        self.refresh_sessions()

    def refresh_sessions(self) -> None:
        self.session_list.delete(0, "end")
        for session in self.session_store.list_all():
            parent = session.parent_id[:8] if session.parent_id else "root"
            self.session_list.insert("end", f"{session.name} ({session.id[:8]}) <- {parent}")

    def create_branch(self) -> None:
        branched = SessionNode.create(
            name=f"branch-{self.current_session.id[:4]}",
            parent_id=self.current_session.id,
        )
        branched.changed_files = list(self.current_session.changed_files)
        branched.reference_map = dict(self.current_session.reference_map)
        branched.last_build_log = self.current_session.last_build_log
        self.session_store.save(branched)
        self.current_session = branched
        self.refresh_sessions()
        self.log_text.insert("end", f"\n[SESSION] branched to {branched.id}\n")

    def _build_refs_tab(self, tab: ttk.Frame) -> None:
        frame = ttk.Frame(tab, padding=8)
        frame.pack(fill="both", expand=True)

        ttk.Button(frame, text="Regenerate Map", command=self.regen_map).pack(anchor="w")
        self.refs_text = tk.Text(frame, wrap="none")
        self.refs_text.pack(fill="both", expand=True, pady=8)

    def regen_map(self) -> None:
        repo = Path(self.repo_var.get()).resolve()
        graph = build_reference_map(repo)
        self.current_session.reference_map = graph
        self.session_store.save(self.current_session)

        self.refs_text.delete("1.0", "end")
        for file, refs in sorted(graph.items()):
            self.refs_text.insert("end", f"{file}\n")
            for ref in refs[:20]:
                self.refs_text.insert("end", f"  -> {ref}\n")

    def _build_providers_tab(self, tab: ttk.Frame) -> None:
        frame = ttk.Frame(tab, padding=8)
        frame.pack(fill="both", expand=True)

        self.provider_name = tk.StringVar()
        self.provider_endpoint = tk.StringVar(value="https://api.openai.com/v1/chat/completions")
        self.provider_api_key = tk.StringVar()
        self.provider_model = tk.StringVar(value="gpt-4o-mini")

        ttk.Label(frame, text="Name").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.provider_name, width=24).grid(row=0, column=1, sticky="w")
        ttk.Label(frame, text="Endpoint").grid(row=1, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.provider_endpoint, width=72).grid(row=1, column=1, sticky="w")
        ttk.Label(frame, text="API Key").grid(row=2, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.provider_api_key, width=72, show="*").grid(row=2, column=1, sticky="w")
        ttk.Label(frame, text="Model").grid(row=3, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.provider_model, width=24).grid(row=3, column=1, sticky="w")

        ttk.Button(frame, text="Save Provider", command=self.save_provider).grid(row=4, column=1, sticky="w", pady=8)

        self.provider_list = tk.Listbox(frame, height=12)
        self.provider_list.grid(row=5, column=0, columnspan=2, sticky="nsew")
        frame.rowconfigure(5, weight=1)
        frame.columnconfigure(1, weight=1)

        self.refresh_providers()

    def save_provider(self) -> None:
        name = self.provider_name.get().strip()
        if not name:
            messagebox.showerror("Error", "Provider name is required")
            return

        provider = ProviderConfig(
            name=name,
            endpoint=self.provider_endpoint.get().strip(),
            api_key=self.provider_api_key.get().strip(),
            model=self.provider_model.get().strip(),
        )
        self.providers.upsert(provider)
        self.refresh_providers()

    def refresh_providers(self) -> None:
        self.provider_list.delete(0, "end")
        for p in self.providers.list_all():
            self.provider_list.insert("end", f"{p.name} | {p.model} | {p.endpoint}")


def launch() -> None:
    root = tk.Tk()
    app = UBTPartnerApp(root)
    app.start_tracking()
    root.mainloop()
