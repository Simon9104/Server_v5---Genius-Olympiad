import os
import sys
import socket
import subprocess
import threading
import tkinter as tk
from tkinter import scrolledtext, font, ttk
import datetime

# ── Resolve paths ─────────────────────────────────────────────────────────────
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
SERVER_DIR      = os.path.abspath(os.path.join(BASE_DIR, '..', 'server'))
SERVER_WIFI_PY  = os.path.join(SERVER_DIR, 'server.py')
SERVER_SERIAL_PY= os.path.join(SERVER_DIR, 'serial_server.py')

# ── Colours ───────────────────────────────────────────────────────────────────
BG    = '#0f0f1a'
CARD  = '#1e1e2e'
BORDER= '#2a2a3e'
GREEN = '#4ade80'
RED   = '#f87171'
YELLOW= '#facc15'
CYAN  = '#60a5fa'
PURPLE= '#a78bfa'
TEXT  = '#e2e8f0'
MUTED = '#64748b'

def local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

def list_com_ports():
    try:
        import serial.tools.list_ports
        return [p.device for p in serial.tools.list_ports.comports()] or ['(none)']
    except ImportError:
        return ['pyserial not installed']

class GreenIOTApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('GreenIOT — Server Launcher')
        self.geometry('860x660')
        self.minsize(700, 520)
        self.configure(bg=BG)
        self.resizable(True, True)

        self._proc: subprocess.Popen | None = None
        self._running = False
        self._mode = tk.StringVar(value='wifi')   # 'wifi' | 'serial'

        self._build_ui()
        self._on_mode_change()
        self.protocol('WM_DELETE_WINDOW', self._on_close)

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        title_font = font.Font(family='Segoe UI', size=18, weight='bold')
        label_font = font.Font(family='Segoe UI', size=9)
        small_font = font.Font(family='Segoe UI', size=8)
        btn_font   = font.Font(family='Segoe UI', size=10, weight='bold')
        mono_font  = font.Font(family='Consolas', size=9)

        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=CARD, pady=12, padx=20)
        hdr.pack(fill='x')
        tk.Label(hdr, text='GreenIOT', font=title_font, fg=GREEN, bg=CARD).pack(side='left')
        tk.Label(hdr, text=' Server Launcher', font=title_font, fg=TEXT, bg=CARD).pack(side='left')
        self._status_dot = tk.Label(hdr, text='●', fg=MUTED, bg=CARD,
                                    font=font.Font(size=14))
        self._status_dot.pack(side='right', padx=(0, 8))
        self._status_lbl = tk.Label(hdr, text='Stopped', fg=MUTED, bg=CARD, font=label_font)
        self._status_lbl.pack(side='right')

        # ── Mode selector ─────────────────────────────────────────────────────
        mode_frame = tk.Frame(self, bg=BG, pady=10, padx=20)
        mode_frame.pack(fill='x')

        tk.Label(mode_frame, text='Mode:', fg=MUTED, bg=BG, font=label_font).pack(side='left', padx=(0,10))

        tk.Radiobutton(mode_frame, text='📶  WiFi Network', variable=self._mode,
                       value='wifi', fg=TEXT, bg=BG, selectcolor=CARD,
                       activebackground=BG, activeforeground=GREEN,
                       font=label_font, command=self._on_mode_change).pack(side='left', padx=(0,20))

        tk.Radiobutton(mode_frame, text='🔌  USB Serial (demo mode)', variable=self._mode,
                       value='serial', fg=TEXT, bg=BG, selectcolor=CARD,
                       activebackground=BG, activeforeground=PURPLE,
                       font=label_font, command=self._on_mode_change).pack(side='left')

        # ── Info bar (dynamic) ────────────────────────────────────────────────
        self._info_frame = tk.Frame(self, bg=BORDER, pady=10, padx=20)
        self._info_frame.pack(fill='x')

        # WiFi info
        self._wifi_info = tk.Frame(self._info_frame, bg=BORDER)
        ip = local_ip()
        tk.Label(self._wifi_info, text=f'Local IP:  {ip}', fg=CYAN, bg=BORDER,
                 font=label_font).pack(side='left', padx=(0, 24))
        tk.Label(self._wifi_info, text='TCP :9991   API :8080', fg=MUTED, bg=BORDER,
                 font=label_font).pack(side='left')
        tk.Label(self._wifi_info, text=f'Dashboard → http://{ip}:8080/data',
                 fg=MUTED, bg=BORDER, font=label_font).pack(side='right')

        # Serial info
        self._serial_info = tk.Frame(self._info_frame, bg=BORDER)
        tk.Label(self._serial_info, text='COM Port:', fg=MUTED, bg=BORDER,
                 font=label_font).pack(side='left', padx=(0, 6))
        self._port_var = tk.StringVar()
        self._port_cb = ttk.Combobox(self._serial_info, textvariable=self._port_var,
                                     width=12, state='readonly',
                                     font=label_font)
        self._port_cb.pack(side='left', padx=(0, 8))
        tk.Button(self._serial_info, text='↻ Refresh', font=small_font,
                  bg=CARD, fg=TEXT, relief='flat', padx=8, pady=3,
                  cursor='hand2', command=self._refresh_ports).pack(side='left', padx=(0,20))
        ip2 = local_ip()
        tk.Label(self._serial_info, text=f'API :8080   Dashboard → http://{ip2}:8080/data',
                 fg=MUTED, bg=BORDER, font=label_font).pack(side='left')
        self._refresh_ports()

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_row = tk.Frame(self, bg=BG, pady=8, padx=20)
        btn_row.pack(fill='x')

        self._btn_start = tk.Button(
            btn_row, text='▶  Start Server', font=btn_font,
            bg=GREEN, fg=BG, activebackground='#22c55e', activeforeground=BG,
            relief='flat', padx=18, pady=8, cursor='hand2', command=self._start)
        self._btn_start.pack(side='left', padx=(0, 10))

        self._btn_stop = tk.Button(
            btn_row, text='■  Stop Server', font=btn_font,
            bg=BORDER, fg=MUTED, activebackground=RED, activeforeground=BG,
            relief='flat', padx=18, pady=8, cursor='hand2',
            state='disabled', command=self._stop)
        self._btn_stop.pack(side='left', padx=(0, 10))

        tk.Button(btn_row, text='🗑  Clear Log', font=btn_font,
                  bg=BORDER, fg=TEXT, activebackground='#3a3a5e', activeforeground=TEXT,
                  relief='flat', padx=12, pady=8, cursor='hand2',
                  command=self._clear_log).pack(side='left')

        # mode badge on right
        self._mode_badge = tk.Label(btn_row, text='', fg=BG, bg=GREEN,
                                    font=font.Font(family='Segoe UI', size=8, weight='bold'),
                                    padx=8, pady=4)
        self._mode_badge.pack(side='right')

        # ── Log area ──────────────────────────────────────────────────────────
        log_frame = tk.Frame(self, bg=BG, padx=20)
        log_frame.pack(fill='both', expand=True, pady=(0, 16))

        tk.Label(log_frame, text='Server Output', fg=MUTED, bg=BG,
                 font=label_font).pack(anchor='w', pady=(0, 4))

        self._log = scrolledtext.ScrolledText(
            log_frame, bg=CARD, fg=TEXT, font=mono_font,
            relief='flat', bd=0, insertbackground=TEXT,
            selectbackground=BORDER, wrap='word', state='disabled')
        self._log.pack(fill='both', expand=True)

        self._log.tag_config('info', foreground=TEXT)
        self._log.tag_config('ok',   foreground=GREEN)
        self._log.tag_config('warn', foreground=YELLOW)
        self._log.tag_config('err',  foreground=RED)
        self._log.tag_config('ts',   foreground=MUTED)

    def _on_mode_change(self):
        mode = self._mode.get()
        for w in self._wifi_info.winfo_children():
            pass
        if mode == 'wifi':
            self._serial_info.pack_forget()
            self._wifi_info.pack(fill='x')
            self._mode_badge.config(text='WiFi Mode', bg=CYAN, fg=BG)
        else:
            self._wifi_info.pack_forget()
            self._serial_info.pack(fill='x')
            self._mode_badge.config(text='Serial Mode', bg=PURPLE, fg=BG)

    def _refresh_ports(self):
        ports = list_com_ports()
        self._port_cb['values'] = ports
        if ports:
            self._port_var.set(ports[0])

    # ── Log helpers ───────────────────────────────────────────────────────────
    def _append(self, text: str, tag: str = 'info'):
        self._log.configure(state='normal')
        ts = datetime.datetime.now().strftime('%H:%M:%S')
        self._log.insert('end', f'[{ts}] ', 'ts')
        self._log.insert('end', text + '\n', tag)
        self._log.see('end')
        self._log.configure(state='disabled')

    def _clear_log(self):
        self._log.configure(state='normal')
        self._log.delete('1.0', 'end')
        self._log.configure(state='disabled')

    # ── Process control ───────────────────────────────────────────────────────
    def _start(self):
        if self._running:
            return
        mode = self._mode.get()
        script = SERVER_WIFI_PY if mode == 'wifi' else SERVER_SERIAL_PY

        if not os.path.isfile(script):
            self._append(f'Script not found: {script}', 'err')
            return

        cmd = [sys.executable, script]
        if mode == 'serial':
            port = self._port_var.get()
            if port and port not in ('(none)', 'pyserial not installed'):
                cmd.append(port)

        self._append(f'Starting in {mode.upper()} mode…', 'ok')
        if mode == 'serial' and len(cmd) > 2:
            self._append(f'COM port: {cmd[2]}', 'ok')

        try:
            self._proc = subprocess.Popen(
                cmd,
                cwd=SERVER_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
            )
        except Exception as e:
            self._append(f'Failed to start: {e}', 'err')
            return

        self._running = True
        self._btn_start.config(state='disabled', bg=BORDER, fg=MUTED)
        self._btn_stop.config(state='normal',   bg=RED,    fg=BG)
        self._status_dot.config(fg=GREEN)
        self._status_lbl.config(text='Running', fg=GREEN)
        threading.Thread(target=self._read_output, daemon=True).start()

    def _stop(self):
        if self._proc:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()
            self._proc = None
        self._running = False
        self._btn_start.config(state='normal',  bg=GREEN,  fg=BG)
        self._btn_stop.config(state='disabled', bg=BORDER, fg=MUTED)
        self._status_dot.config(fg=RED)
        self._status_lbl.config(text='Stopped', fg=RED)
        self._append('Server stopped.', 'warn')

    def _read_output(self):
        for line in self._proc.stdout:
            line = line.rstrip()
            if not line:
                continue
            tag = 'info'
            lo = line.lower()
            if any(w in lo for w in ('error', 'failed', 'exception', 'traceback')):
                tag = 'err'
            elif any(w in lo for w in ('warning', 'warn')):
                tag = 'warn'
            elif any(w in lo for w in ('started', 'running', 'sent', 'saved',
                                        'online', 'connected', 'ok')):
                tag = 'ok'
            self.after(0, self._append, line, tag)
        if self._running:
            self.after(0, self._on_proc_died)

    def _on_proc_died(self):
        self._running = False
        self._proc = None
        self._btn_start.config(state='normal',  bg=GREEN,  fg=BG)
        self._btn_stop.config(state='disabled', bg=BORDER, fg=MUTED)
        self._status_dot.config(fg=RED)
        self._status_lbl.config(text='Crashed', fg=RED)
        self._append('Server process exited unexpectedly.', 'err')

    def _on_close(self):
        if self._running:
            self._stop()
        self.destroy()


if __name__ == '__main__':
    app = GreenIOTApp()
    app.mainloop()
