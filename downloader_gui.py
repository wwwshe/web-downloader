import re
import json
import threading
import queue
from pathlib import Path
from urllib.parse import urljoin, urlparse
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
from bs4 import BeautifulSoup

INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

def safe_name(name):
    return (INVALID.sub('_', name.strip()).rstrip(' .')[:180] or 'download')

class App:
    def __init__(self, root):
        self.root = root
        root.title('링크 텍스트 파일 다운로더')
        root.geometry('760x520')
        self.settings_path = Path(__file__).resolve().with_name('downloader_settings.json')
        settings = self.load_settings()
        self.url = tk.StringVar()
        self.ext = tk.StringVar(value='')
        self.folder = tk.StringVar(value=settings.get('folder', str(Path.home() / 'Downloads')))
        root.protocol('WM_DELETE_WINDOW', self.on_close)
        self.files = []
        self.busy = False
        self.events = queue.Queue()
        frame = ttk.Frame(root, padding=14)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='웹페이지 URL').grid(row=0, column=0, sticky='w')
        ttk.Entry(frame, textvariable=self.url).grid(row=0, column=1, columnspan=3, sticky='ew', padx=8, pady=5)
        ttk.Label(frame, text='확장자').grid(row=1, column=0, sticky='w')
        ttk.Entry(frame, textvariable=self.ext, width=10).grid(row=1, column=1, sticky='w', padx=8, pady=5)
        ttk.Label(frame, text='저장 폴더').grid(row=2, column=0, sticky='w')
        ttk.Entry(frame, textvariable=self.folder).grid(row=2, column=1, columnspan=2, sticky='ew', padx=8, pady=5)
        ttk.Button(frame, text='찾아보기', command=self.choose_folder).grid(row=2, column=3)
        buttons = ttk.Frame(frame)
        buttons.grid(row=3, column=0, columnspan=4, sticky='w', pady=10)
        self.scan_button = ttk.Button(buttons, text='링크 검색', command=self.scan)
        self.scan_button.pack(side='left', padx=(0, 8))
        self.download_button = ttk.Button(buttons, text='전체 다운로드', command=self.download, state='disabled')
        self.download_button.pack(side='left', padx=(0, 8))
        self.selected_button = ttk.Button(buttons, text='선택 다운로드', command=self.download_selected, state='disabled')
        self.selected_button.pack(side='left')
        self.status = tk.StringVar(value='URL을 입력하고 링크 검색을 누르세요.')
        ttk.Label(frame, textvariable=self.status).grid(row=4, column=0, columnspan=4, sticky='w', pady=(0, 8))
        self.table = ttk.Treeview(frame, columns=('name', 'url'), show='headings', selectmode='extended')
        self.table.bind('<<TreeviewSelect>>', lambda event: self.update_selected_button())
        self.table.heading('name', text='저장 파일명')
        self.table.heading('url', text='다운로드 URL')
        self.table.column('name', width=220, stretch=False)
        self.table.column('url', width=450)
        self.table.grid(row=5, column=0, columnspan=4, sticky='nsew')
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=self.table.yview)
        scrollbar.grid(row=5, column=4, sticky='ns')
        self.table.configure(yscrollcommand=scrollbar.set)
        self.log = tk.Text(frame, height=7, state='disabled')
        self.log.grid(row=6, column=0, columnspan=4, sticky='ew', pady=(10, 0))
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)
        frame.rowconfigure(5, weight=1)
        root.after(100, self.poll)

    def load_settings(self):
        try:
            data = json.loads(self.settings_path.read_text(encoding='utf-8'))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def save_settings(self):
        data = {'extension': self.ext.get().strip(), 'folder': self.folder.get().strip()}
        try:
            self.settings_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        except OSError as exc:
            messagebox.showwarning('설정 저장 실패', str(exc))

    def on_close(self):
        self.save_settings()
        self.root.destroy()

    def choose_folder(self):
        value = filedialog.askdirectory(initialdir=self.folder.get())
        if value:
            self.folder.set(value)

    def update_selected_button(self):
        self.selected_button.config(state='normal' if not self.busy and self.table.selection() else 'disabled')

    def set_busy(self, busy):
        self.busy = busy
        self.scan_button.config(state='disabled' if busy else 'normal')
        self.update_selected_button()
        self.download_button.config(state='disabled' if busy or not self.files else 'normal')

    def write(self, message):
        self.log.config(state='normal')
        self.log.insert('end', message + '\n')
        self.log.see('end')
        self.log.config(state='disabled')

    def scan(self):
        url = self.url.get().strip()
        if urlparse(url).scheme not in ('http', 'https'):
            messagebox.showerror('URL 오류', 'http:// 또는 https://로 시작하는 URL을 입력하세요.')
            return
        ext = self.ext.get().strip().lower().lstrip('.')
        if ext and not re.fullmatch(r'[a-z0-9]+', ext):
            messagebox.showerror('확장자 오류', 'egg, zip, pdf처럼 확장자를 입력하세요.')
            return
        self.save_settings()
        self.files = []
        for item in self.table.get_children():
            self.table.delete(item)
        self.set_busy(True)
        self.status.set('링크 검색 중...')
        threading.Thread(target=self.scan_worker, args=(url, '.' + ext if ext else ''), daemon=True).start()

    def scan_worker(self, url, ext):
        try:
            response = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            found, seen = [], set()
            for a in soup.select('a[href]'):
                name = a.get_text(' ', strip=True)
                name = re.sub(r'\s+\d+(?:\.\d+)?\s*(?:B|KB|MB|GB|TB)$', '', name, flags=re.IGNORECASE)
                href = a.get('href', '').strip()
                if not href or (ext and not name.lower().endswith(ext)):
                    continue
                link = urljoin(url, href)
                if urlparse(link).scheme not in ('http', 'https'):
                    continue
                pair = (safe_name(name), link)
                if pair not in seen:
                    found.append(pair)
                    seen.add(pair)
            self.events.put(('found', found))
        except Exception as exc:
            self.events.put(('error', str(exc)))

    def download(self):
        self.start_download(list(self.files))

    def download_selected(self):
        selected = [tuple(self.table.item(item, 'values')) for item in self.table.selection()]
        if not selected:
            messagebox.showinfo('선택 다운로드', '파일 목록에서 다운로드할 항목을 선택하세요.')
            return
        self.start_download(selected)

    def start_download(self, files):
        if self.busy or not files:
            return
        self.save_settings()
        folder = Path(self.folder.get()).expanduser()
        self.set_busy(True)
        self.status.set('다운로드 중...')
        threading.Thread(target=self.download_worker, args=(files, folder, self.url.get().strip()), daemon=True).start()

    def download_worker(self, files, folder, referer):
        try:
            folder.mkdir(parents=True, exist_ok=True)
            session = requests.Session()
            session.headers.update({'User-Agent': 'Mozilla/5.0', 'Referer': referer})
            for i, (name, url) in enumerate(files, 1):
                target = folder / name
                if target.exists():
                    self.events.put(('log', f'[{i}/{len(files)}] 기존 파일 건너뜀: {name}'))
                    continue
                temp = folder / (name + '.part')
                try:
                    with session.get(url, stream=True, timeout=90) as response:
                        response.raise_for_status()
                        if 'text/html' in response.headers.get('Content-Type', '').lower():
                            raise ValueError('파일 대신 HTML 응답이 반환됨')
                        with temp.open('wb') as output:
                            for chunk in response.iter_content(262144):
                                if chunk:
                                    output.write(chunk)
                        temp.replace(target)
                    self.events.put(('log', f'[{i}/{len(files)}] 완료: {name}'))
                except Exception as exc:
                    self.events.put(('log', f'[{i}/{len(files)}] 실패: {name} ({exc})'))
                    temp.unlink(missing_ok=True)
            self.events.put(('done', str(folder)))
        except Exception as exc:
            self.events.put(('error', str(exc)))

    def poll(self):
        try:
            while True:
                event, payload = self.events.get_nowait()
                if event == 'found':
                    self.files = payload
                    for name, url in payload:
                        self.table.insert('', 'end', values=(name, url))
                    self.status.set(f'{len(payload)}개 파일 발견')
                    self.set_busy(False)
                elif event == 'log':
                    self.write(payload)
                elif event == 'done':
                    self.status.set('다운로드 작업 완료 (실패 여부는 로그 확인)')
                    self.set_busy(False)
                    self.write(f'저장 위치: {payload}')
                elif event == 'error':
                    self.status.set('오류 발생')
                    self.set_busy(False)
                    messagebox.showerror('오류', payload)
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()
