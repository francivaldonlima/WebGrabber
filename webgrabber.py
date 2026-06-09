#!/usr/bin/env python3
"""
WebGrabber - Downloader de Arquivos Web
Similar ao clássico WebReaper
Baixa PDFs, imagens, ZIPs e outros arquivos de páginas web
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote
import os
import re
import struct
import zlib
import base64
from pathlib import Path
from datetime import datetime
import queue


def _create_globe_icon():
    size = 32
    cx = cy = (size - 1) / 2.0
    r = cx - 0.5

    rows = []
    for y in range(size):
        row = bytearray()
        for x in range(size):
            dx = x - cx
            dy = y - cy
            dist = (dx * dx + dy * dy) ** 0.5

            if dist > r + 0.5:
                row += bytes([0, 0, 0, 0])
            elif dist > r - 0.5:
                alpha = int(255 * (r + 0.5 - dist))
                row += bytes([10, 50, 110, alpha])
            else:
                on_grid = (
                    abs(dy) < 1.0 or
                    abs(abs(dy) - r * 0.5) < 1.0 or
                    abs(dx) < 1.0 or
                    abs(abs(dx) - r * 0.55) < 1.0
                )
                if on_grid:
                    row += bytes([200, 225, 255, 210])
                else:
                    row += bytes([30, 100, 210, 255])
        rows.append(bytes(row))

    def make_chunk(ctype, data):
        crc = zlib.crc32(ctype + data) & 0xFFFFFFFF
        return struct.pack('>I', len(data)) + ctype + data + struct.pack('>I', crc)

    ihdr = struct.pack('>II', size, size) + bytes([8, 6, 0, 0, 0])
    idat = zlib.compress(b''.join(b'\x00' + row for row in rows), 6)

    png = (b'\x89PNG\r\n\x1a\n' +
           make_chunk(b'IHDR', ihdr) +
           make_chunk(b'IDAT', idat) +
           make_chunk(b'IEND', b''))

    return base64.b64encode(png).decode()

class WebGrabber:
    def __init__(self, root):
        self.root = root
        self.root.title("WebGrabber - Downloader de Arquivos Web")
        self.root.geometry("900x700")
        self.root.configure(bg="#1a1a2e")
        
        # Configurar estilo
        self.setup_styles()
        
        # Variáveis de controle
        self.is_downloading = False
        self.stop_flag = False
        self.download_queue = queue.Queue()
        self.found_files = []
        
        # Checkboxes variáveis
        self.var_pdf = tk.BooleanVar(value=True)
        self.var_images = tk.BooleanVar(value=True)
        self.var_zip = tk.BooleanVar(value=True)
        self.var_doc = tk.BooleanVar(value=False)
        self.var_xls = tk.BooleanVar(value=False)
        self.var_audio = tk.BooleanVar(value=False)
        self.var_video = tk.BooleanVar(value=False)
        self.var_exe = tk.BooleanVar(value=False)
        self.var_other = tk.BooleanVar(value=False)
        
        # Diretório de saída
        self.output_dir = tk.StringVar(value=str(Path.home() / "Downloads" / "WebGrabber"))
        
        # Criar interface
        self.create_ui()
        
    def setup_styles(self):
        """Configurar estilos personalizados"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Cores do tema
        self.colors = {
            'bg_dark': '#1a1a2e',
            'bg_medium': '#16213e',
            'bg_light': '#0f3460',
            'accent': '#e94560',
            'accent_hover': '#ff6b6b',
            'text': '#eaeaea',
            'text_dim': '#a0a0a0',
            'success': '#4ecca3',
            'warning': '#ffc107'
        }
        
        # Configurar estilos ttk
        style.configure('Main.TFrame', background=self.colors['bg_dark'])
        style.configure('Card.TFrame', background=self.colors['bg_medium'])
        style.configure('Title.TLabel', 
                       background=self.colors['bg_dark'],
                       foreground=self.colors['accent'],
                       font=('Segoe UI', 24, 'bold'))
        style.configure('Subtitle.TLabel',
                       background=self.colors['bg_dark'],
                       foreground=self.colors['text_dim'],
                       font=('Segoe UI', 10))
        style.configure('Section.TLabel',
                       background=self.colors['bg_medium'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 11, 'bold'))
        style.configure('Normal.TLabel',
                       background=self.colors['bg_medium'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 10))
        style.configure('Status.TLabel',
                       background=self.colors['bg_dark'],
                       foreground=self.colors['success'],
                       font=('Segoe UI', 10))
        
        # Checkbutton
        style.configure('Custom.TCheckbutton',
                       background=self.colors['bg_medium'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 10))
        style.map('Custom.TCheckbutton',
                 background=[('active', self.colors['bg_medium'])])
        
        # Entry
        style.configure('Custom.TEntry',
                       fieldbackground=self.colors['bg_light'],
                       foreground=self.colors['text'],
                       insertcolor=self.colors['text'])
        
        # Progressbar
        style.configure('Custom.Horizontal.TProgressbar',
                       background=self.colors['accent'],
                       troughcolor=self.colors['bg_light'])
        
    def create_ui(self):
        """Criar interface gráfica"""
        # Container principal
        main_frame = ttk.Frame(self.root, style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Cabeçalho
        header_frame = ttk.Frame(main_frame, style='Main.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(header_frame, text="🌐 WebGrabber", style='Title.TLabel')
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = ttk.Label(header_frame, 
                                   text="Downloader de Arquivos Web • Similar ao WebReaper",
                                   style='Subtitle.TLabel')
        subtitle_label.pack(side=tk.LEFT, padx=(15, 0), pady=(10, 0))
        
        # Card de URL
        url_card = self.create_card(main_frame, "🔗 URL da Página")
        url_card.pack(fill=tk.X, pady=(0, 15))
        
        url_inner = ttk.Frame(url_card, style='Card.TFrame')
        url_inner.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        self.url_entry = tk.Entry(url_inner, 
                                  font=('Consolas', 11),
                                  bg=self.colors['bg_light'],
                                  fg=self.colors['text'],
                                  insertbackground=self.colors['text'],
                                  relief=tk.FLAT,
                                  highlightthickness=2,
                                  highlightbackground=self.colors['bg_light'],
                                  highlightcolor=self.colors['accent'])
        self.url_entry.pack(fill=tk.X, ipady=8)
        self.url_entry.insert(0, "https://")
        
        # Card de Tipos de Arquivo
        types_card = self.create_card(main_frame, "📁 Tipos de Arquivo")
        types_card.pack(fill=tk.X, pady=(0, 15))
        
        types_inner = ttk.Frame(types_card, style='Card.TFrame')
        types_inner.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Grid de checkboxes
        checks_frame = ttk.Frame(types_inner, style='Card.TFrame')
        checks_frame.pack(fill=tk.X)
        
        checkboxes = [
            (self.var_pdf, "📄 PDF (.pdf)", 0, 0),
            (self.var_images, "🖼️ Imagens (.jpg, .png, .gif, .webp, .svg)", 0, 1),
            (self.var_zip, "📦 Compactados (.zip, .rar, .7z, .tar.gz)", 1, 0),
            (self.var_doc, "📝 Documentos (.doc, .docx, .odt, .txt)", 1, 1),
            (self.var_xls, "📊 Planilhas (.xls, .xlsx, .csv)", 2, 0),
            (self.var_audio, "🎵 Áudio (.mp3, .wav, .ogg, .flac)", 2, 1),
            (self.var_video, "🎬 Vídeo (.mp4, .avi, .mkv, .webm)", 3, 0),
            (self.var_exe, "⚙️ Executáveis (.exe, .msi, .deb, .rpm)", 3, 1),
            (self.var_other, "📎 Outros (extensões personalizadas)", 4, 0),
        ]
        
        for var, text, row, col in checkboxes:
            cb = ttk.Checkbutton(checks_frame, text=text, variable=var, 
                                style='Custom.TCheckbutton')
            cb.grid(row=row, column=col, sticky='w', padx=(0, 30), pady=5)
        
        # Campo para extensões personalizadas
        other_frame = ttk.Frame(types_inner, style='Card.TFrame')
        other_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(other_frame, text="Extensões extras (separadas por vírgula):",
                 style='Normal.TLabel').pack(side=tk.LEFT)
        
        self.other_ext_entry = tk.Entry(other_frame,
                                        font=('Consolas', 10),
                                        bg=self.colors['bg_light'],
                                        fg=self.colors['text'],
                                        insertbackground=self.colors['text'],
                                        relief=tk.FLAT,
                                        width=40)
        self.other_ext_entry.pack(side=tk.LEFT, padx=(10, 0), ipady=4)
        self.other_ext_entry.insert(0, ".bin, .iso")
        
        # Card de Diretório de Saída
        output_card = self.create_card(main_frame, "💾 Diretório de Saída")
        output_card.pack(fill=tk.X, pady=(0, 15))
        
        output_inner = ttk.Frame(output_card, style='Card.TFrame')
        output_inner.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        output_row = ttk.Frame(output_inner, style='Card.TFrame')
        output_row.pack(fill=tk.X)
        
        self.output_entry = tk.Entry(output_row,
                                     textvariable=self.output_dir,
                                     font=('Consolas', 10),
                                     bg=self.colors['bg_light'],
                                     fg=self.colors['text'],
                                     insertbackground=self.colors['text'],
                                     relief=tk.FLAT)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)
        
        browse_btn = tk.Button(output_row, text="Procurar...",
                              font=('Segoe UI', 9),
                              bg=self.colors['bg_light'],
                              fg=self.colors['text'],
                              activebackground=self.colors['accent'],
                              activeforeground='white',
                              relief=tk.FLAT,
                              cursor='hand2',
                              command=self.browse_output)
        browse_btn.pack(side=tk.RIGHT, padx=(10, 0), ipady=4, ipadx=10)
        
        # Botões de ação
        btn_frame = ttk.Frame(main_frame, style='Main.TFrame')
        btn_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.scan_btn = tk.Button(btn_frame, text="🔍 Escanear Página",
                                  font=('Segoe UI', 11, 'bold'),
                                  bg=self.colors['bg_light'],
                                  fg=self.colors['text'],
                                  activebackground=self.colors['accent'],
                                  activeforeground='white',
                                  relief=tk.FLAT,
                                  cursor='hand2',
                                  command=self.scan_page)
        self.scan_btn.pack(side=tk.LEFT, ipady=8, ipadx=20)
        
        self.download_btn = tk.Button(btn_frame, text="⬇️ Baixar Selecionados",
                                      font=('Segoe UI', 11, 'bold'),
                                      bg=self.colors['accent'],
                                      fg='white',
                                      activebackground=self.colors['accent_hover'],
                                      activeforeground='white',
                                      relief=tk.FLAT,
                                      cursor='hand2',
                                      state=tk.DISABLED,
                                      command=self.start_download)
        self.download_btn.pack(side=tk.LEFT, padx=(15, 0), ipady=8, ipadx=20)
        
        self.stop_btn = tk.Button(btn_frame, text="⏹️ Parar",
                                  font=('Segoe UI', 11, 'bold'),
                                  bg=self.colors['warning'],
                                  fg='black',
                                  activebackground='#ffca2c',
                                  activeforeground='black',
                                  relief=tk.FLAT,
                                  cursor='hand2',
                                  state=tk.DISABLED,
                                  command=self.stop_download)
        self.stop_btn.pack(side=tk.LEFT, padx=(15, 0), ipady=8, ipadx=20)
        
        # Seleção rápida
        select_frame = ttk.Frame(btn_frame, style='Main.TFrame')
        select_frame.pack(side=tk.RIGHT)
        
        select_all_btn = tk.Button(select_frame, text="Selecionar Todos",
                                   font=('Segoe UI', 9),
                                   bg=self.colors['bg_medium'],
                                   fg=self.colors['text'],
                                   activebackground=self.colors['accent'],
                                   activeforeground='white',
                                   relief=tk.FLAT,
                                   cursor='hand2',
                                   command=self.select_all_files)
        select_all_btn.pack(side=tk.LEFT, ipadx=10)
        
        select_none_btn = tk.Button(select_frame, text="Desmarcar Todos",
                                    font=('Segoe UI', 9),
                                    bg=self.colors['bg_medium'],
                                    fg=self.colors['text'],
                                    activebackground=self.colors['accent'],
                                    activeforeground='white',
                                    relief=tk.FLAT,
                                    cursor='hand2',
                                    command=self.deselect_all_files)
        select_none_btn.pack(side=tk.LEFT, padx=(10, 0), ipadx=10)
        
        # Barra de progresso
        progress_frame = ttk.Frame(main_frame, style='Main.TFrame')
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, 
                                           variable=self.progress_var,
                                           style='Custom.Horizontal.TProgressbar',
                                           mode='determinate')
        self.progress_bar.pack(fill=tk.X)
        
        self.status_label = ttk.Label(progress_frame, text="Pronto para escanear",
                                      style='Status.TLabel')
        self.status_label.pack(anchor='w', pady=(5, 0))
        
        # Lista de arquivos encontrados
        list_card = self.create_card(main_frame, "📋 Arquivos Encontrados")
        list_card.pack(fill=tk.BOTH, expand=True)
        
        list_inner = ttk.Frame(list_card, style='Card.TFrame')
        list_inner.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Frame para a lista com scrollbar
        list_container = ttk.Frame(list_inner, style='Card.TFrame')
        list_container.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Canvas para scrolling
        self.canvas = tk.Canvas(list_container,
                               bg=self.colors['bg_light'],
                               highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=self.canvas.yview)
        self.canvas.config(yscrollcommand=scrollbar.set)
        
        # Frame interno para os itens
        self.files_frame = ttk.Frame(self.canvas, style='Card.TFrame')
        self.canvas_window = self.canvas.create_window((0, 0), window=self.files_frame, anchor='nw')
        
        # Configurar scroll
        self.files_frame.bind('<Configure>', self.on_frame_configure)
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        self.canvas.bind_all('<MouseWheel>', self.on_mousewheel)
        
        # Dicionário para armazenar checkboxes dos arquivos
        self.file_checkboxes = {}
        
    def create_card(self, parent, title):
        """Criar card estilizado"""
        card = ttk.Frame(parent, style='Card.TFrame')
        
        # Título do card
        title_frame = ttk.Frame(card, style='Card.TFrame')
        title_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        ttk.Label(title_frame, text=title, style='Section.TLabel').pack(anchor='w')
        
        return card
    
    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
    
    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def browse_output(self):
        """Selecionar diretório de saída"""
        directory = filedialog.askdirectory(initialdir=self.output_dir.get())
        if directory:
            self.output_dir.set(directory)
            
    def get_extensions(self):
        """Obter lista de extensões selecionadas"""
        extensions = []
        
        if self.var_pdf.get():
            extensions.extend(['.pdf'])
        if self.var_images.get():
            extensions.extend(['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.ico', '.tiff'])
        if self.var_zip.get():
            extensions.extend(['.zip', '.rar', '.7z', '.tar', '.gz', '.tar.gz', '.tgz', '.bz2'])
        if self.var_doc.get():
            extensions.extend(['.doc', '.docx', '.odt', '.txt', '.rtf', '.pdf'])
        if self.var_xls.get():
            extensions.extend(['.xls', '.xlsx', '.csv', '.ods'])
        if self.var_audio.get():
            extensions.extend(['.mp3', '.wav', '.ogg', '.flac', '.aac', '.wma', '.m4a'])
        if self.var_video.get():
            extensions.extend(['.mp4', '.avi', '.mkv', '.webm', '.mov', '.wmv', '.flv', '.m4v'])
        if self.var_exe.get():
            extensions.extend(['.exe', '.msi', '.deb', '.rpm', '.dmg', '.appimage'])
        if self.var_other.get():
            other = self.other_ext_entry.get()
            for ext in other.split(','):
                ext = ext.strip()
                if ext and not ext.startswith('.'):
                    ext = '.' + ext
                if ext:
                    extensions.append(ext.lower())
        
        return list(set(extensions))
    
    def scan_page(self):
        """Escanear página em busca de arquivos"""
        url = self.url_entry.get().strip()
        
        if not url or url == "https://":
            messagebox.showwarning("Atenção", "Por favor, insira uma URL válida.")
            return
        
        # Verificar se tem extensões selecionadas
        extensions = self.get_extensions()
        if not extensions:
            messagebox.showwarning("Atenção", "Por favor, selecione pelo menos um tipo de arquivo.")
            return
        
        # Limpar lista anterior
        self.clear_file_list()
        self.found_files = []
        
        # Desabilitar botão durante scan
        self.scan_btn.config(state=tk.DISABLED, text="🔄 Escaneando...")
        self.status_label.config(text="Escaneando página...")
        self.progress_var.set(0)
        
        # Executar em thread separada
        thread = threading.Thread(target=self._scan_thread, args=(url, extensions))
        thread.daemon = True
        thread.start()
        
    def _scan_thread(self, url, extensions):
        """Thread para escanear página"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            found_urls = set()
            
            # Buscar em links <a>
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                found_urls.add(full_url)
            
            # Buscar em imagens <img>
            for img in soup.find_all('img', src=True):
                src = img['src']
                full_url = urljoin(url, src)
                found_urls.add(full_url)
            
            # Buscar em source <source>
            for source in soup.find_all('source', src=True):
                src = source['src']
                full_url = urljoin(url, src)
                found_urls.add(full_url)
            
            # Buscar em srcset
            for elem in soup.find_all(srcset=True):
                srcset = elem['srcset']
                for src in srcset.split(','):
                    src = src.strip().split()[0]
                    full_url = urljoin(url, src)
                    found_urls.add(full_url)
            
            # Buscar em data-src (lazy loading)
            for elem in soup.find_all(attrs={'data-src': True}):
                src = elem['data-src']
                full_url = urljoin(url, src)
                found_urls.add(full_url)
            
            # Filtrar por extensões
            files = []
            for file_url in found_urls:
                parsed = urlparse(file_url)
                path = unquote(parsed.path).lower()
                
                for ext in extensions:
                    if path.endswith(ext):
                        filename = os.path.basename(unquote(parsed.path))
                        if not filename:
                            filename = f"arquivo{ext}"
                        files.append({
                            'url': file_url,
                            'filename': filename,
                            'extension': ext
                        })
                        break
            
            # Atualizar UI
            self.root.after(0, lambda: self._update_file_list(files))
            
        except requests.RequestException as e:
            self.root.after(0, lambda: messagebox.showerror("Erro", f"Erro ao acessar a página:\n{str(e)}"))
            self.root.after(0, lambda: self.status_label.config(text="Erro ao escanear"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Erro", f"Erro inesperado:\n{str(e)}"))
            self.root.after(0, lambda: self.status_label.config(text="Erro ao escanear"))
        finally:
            self.root.after(0, lambda: self.scan_btn.config(state=tk.NORMAL, text="🔍 Escanear Página"))
    
    def _update_file_list(self, files):
        """Atualizar lista de arquivos na UI"""
        self.found_files = files
        
        if not files:
            self.status_label.config(text="Nenhum arquivo encontrado com as extensões selecionadas")
            self.download_btn.config(state=tk.DISABLED)
            return
        
        # Limpar frame
        for widget in self.files_frame.winfo_children():
            widget.destroy()
        self.file_checkboxes.clear()
        
        # Adicionar arquivos
        for i, file_info in enumerate(files):
            var = tk.BooleanVar(value=True)
            self.file_checkboxes[i] = var
            
            frame = tk.Frame(self.files_frame, bg=self.colors['bg_light'])
            frame.pack(fill=tk.X, pady=1)
            
            cb = tk.Checkbutton(frame, 
                               variable=var,
                               bg=self.colors['bg_light'],
                               activebackground=self.colors['bg_light'],
                               selectcolor=self.colors['bg_medium'])
            cb.pack(side=tk.LEFT, padx=(5, 0))
            
            # Ícone baseado na extensão
            ext = file_info['extension'].lower()
            if ext == '.pdf':
                icon = "📄"
            elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp']:
                icon = "🖼️"
            elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
                icon = "📦"
            elif ext in ['.doc', '.docx', '.odt', '.txt']:
                icon = "📝"
            elif ext in ['.xls', '.xlsx', '.csv']:
                icon = "📊"
            elif ext in ['.mp3', '.wav', '.ogg', '.flac']:
                icon = "🎵"
            elif ext in ['.mp4', '.avi', '.mkv', '.webm']:
                icon = "🎬"
            elif ext in ['.exe', '.msi', '.deb']:
                icon = "⚙️"
            else:
                icon = "📎"
            
            label = tk.Label(frame,
                           text=f"{icon} {file_info['filename']}",
                           bg=self.colors['bg_light'],
                           fg=self.colors['text'],
                           font=('Consolas', 9),
                           anchor='w')
            label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 10))
            
            # Tooltip com URL completa
            label.bind('<Enter>', lambda e, url=file_info['url']: self.status_label.config(text=url))
            label.bind('<Leave>', lambda e: self.status_label.config(text=f"{len(files)} arquivos encontrados"))
        
        self.status_label.config(text=f"{len(files)} arquivos encontrados")
        self.download_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)
    
    def clear_file_list(self):
        """Limpar lista de arquivos"""
        for widget in self.files_frame.winfo_children():
            widget.destroy()
        self.file_checkboxes.clear()
        
    def select_all_files(self):
        """Selecionar todos os arquivos"""
        for var in self.file_checkboxes.values():
            var.set(True)
            
    def deselect_all_files(self):
        """Desmarcar todos os arquivos"""
        for var in self.file_checkboxes.values():
            var.set(False)
    
    def start_download(self):
        """Iniciar download dos arquivos selecionados"""
        # Verificar arquivos selecionados
        selected = [(i, self.found_files[i]) for i, var in self.file_checkboxes.items() if var.get()]
        
        if not selected:
            messagebox.showwarning("Atenção", "Por favor, selecione pelo menos um arquivo para baixar.")
            return
        
        # Criar diretório de saída
        output_dir = self.output_dir.get()
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível criar o diretório:\n{str(e)}")
            return
        
        # Preparar para download
        self.is_downloading = True
        self.stop_flag = False
        self.scan_btn.config(state=tk.DISABLED)
        self.download_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)
        
        # Iniciar thread de download
        thread = threading.Thread(target=self._download_thread, args=(selected, output_dir))
        thread.daemon = True
        thread.start()
    
    def _download_thread(self, files, output_dir):
        """Thread para download dos arquivos"""
        total = len(files)
        downloaded = 0
        errors = 0
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        for idx, (i, file_info) in enumerate(files):
            if self.stop_flag:
                break
            
            url = file_info['url']
            filename = file_info['filename']
            
            # Garantir nome único
            filepath = os.path.join(output_dir, filename)
            counter = 1
            base, ext = os.path.splitext(filename)
            while os.path.exists(filepath):
                filepath = os.path.join(output_dir, f"{base}_{counter}{ext}")
                counter += 1
            
            self.root.after(0, lambda f=filename: self.status_label.config(text=f"Baixando: {f}"))
            
            try:
                response = requests.get(url, headers=headers, timeout=60, stream=True)
                response.raise_for_status()
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if self.stop_flag:
                            break
                        f.write(chunk)
                
                if not self.stop_flag:
                    downloaded += 1
                    
            except Exception as e:
                errors += 1
                print(f"Erro ao baixar {url}: {e}")
            
            # Atualizar progresso
            progress = ((idx + 1) / total) * 100
            self.root.after(0, lambda p=progress: self.progress_var.set(p))
        
        # Finalizar
        self.root.after(0, lambda: self._download_complete(downloaded, errors, total))
    
    def _download_complete(self, downloaded, errors, total):
        """Callback quando download termina"""
        self.is_downloading = False
        self.scan_btn.config(state=tk.NORMAL)
        self.download_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        if self.stop_flag:
            self.status_label.config(text=f"Download interrompido. {downloaded}/{total} arquivos baixados.")
            messagebox.showinfo("Download Interrompido", 
                              f"Download interrompido pelo usuário.\n\n"
                              f"Arquivos baixados: {downloaded}/{total}")
        else:
            self.status_label.config(text=f"Concluído! {downloaded}/{total} arquivos baixados.")
            msg = f"Download concluído!\n\nArquivos baixados: {downloaded}/{total}"
            if errors > 0:
                msg += f"\nErros: {errors}"
            msg += f"\n\nSalvo em: {self.output_dir.get()}"
            messagebox.showinfo("Download Concluído", msg)
    
    def stop_download(self):
        """Parar download"""
        self.stop_flag = True
        self.status_label.config(text="Parando download...")


def main():
    root = tk.Tk()
    root.minsize(800, 600)
    
    # Centralizar janela
    root.update_idletasks()
    width = 900
    height = 700
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    try:
        icon = tk.PhotoImage(data=_create_globe_icon())
        root._icon = icon
        root.iconphoto(True, icon)
    except Exception:
        pass

    app = WebGrabber(root)
    root.mainloop()


if __name__ == "__main__":
    main()