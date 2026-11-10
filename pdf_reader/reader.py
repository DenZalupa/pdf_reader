import sys
import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageOps, ImageDraw

# Windows High-DPI support
try:
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

import pymupdf


class PDFReaderApp(tk.Tk):
    """
    Простая, быстрая и удобная читалка PDF файлов на Python.
    Поддерживает:
      - Навигацию по страницам (клавиатура, кнопки, ввод номера)
      - Плавное масштабирование (Ctrl + Колесико, кнопки, по ширине/странице)
      - Поиск текста по всему документу с подсветкой
      - Ночной режим чтения (инверсия цветов страниц)
      - Темную и светлую темы интерфейса
      - Поворот страниц на 90°
      - Запоминание последнего открытого файла и страницы
    """

    # Цветовые палитры
    THEMES = {
        "dark": {
            "bg": "#1e1e2e",
            "toolbar_bg": "#181825",
            "panel_bg": "#252538",
            "fg": "#cdd6f4",
            "accent": "#89b4fa",
            "accent_hover": "#b4befe",
            "btn_bg": "#313244",
            "btn_hover": "#45475a",
            "canvas_bg": "#11111b",
            "entry_bg": "#313244",
            "entry_fg": "#cdd6f4",
            "border": "#45475a",
            "search_bg": "#1e1e2e",
        },
        "light": {
            "bg": "#f3f4f6",
            "toolbar_bg": "#ffffff",
            "panel_bg": "#f9fafb",
            "fg": "#1f2937",
            "accent": "#2563eb",
            "accent_hover": "#1d4ed8",
            "btn_bg": "#e5e7eb",
            "btn_hover": "#d1d5db",
            "canvas_bg": "#cbd5e1",
            "entry_bg": "#ffffff",
            "entry_fg": "#111827",
            "border": "#d1d5db",
            "search_bg": "#f9fafb",
        }
    }

    ZOOM_LEVELS = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0]

    def __init__(self, initial_file=None):
        super().__init__()
        self.title("PDF Читалка")
        self.geometry("1100x800")
        self.minsize(640, 480)

        # Состояние приложения
        self.doc = None
        self.filepath = None
        self.current_page = 0
        self.total_pages = 0
        self.zoom = 1.0
        self.rotation = 0
        self.invert_colors = False
        self.current_theme = "dark"
        self.tk_image = None
        self.search_matches = []
        self.search_index = -1
        self.is_fullscreen = False

        # Установка иконки приложения
        self._set_window_icon()

        # Конфиг для сохранения состояния
        self.config_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.config_dir, ".reader_config.json")
        self.load_config()

        # Создание интерфейса
        self._init_ui()
        self._apply_theme()
        self._bind_events()

        # Загрузка файла (из аргументов или последнего)
        target = initial_file or (sys.argv[1] if len(sys.argv) > 1 else None)
        if target and os.path.isfile(target):
            self.open_pdf(target)
        elif self.last_file and os.path.isfile(self.last_file):
            self.open_pdf(self.last_file, page=self.last_page)
        else:
            self._show_welcome_screen()

    def _set_window_icon(self):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        ico_path = os.path.join(base_dir, "app.ico")
        png_path = os.path.join(base_dir, "app.png")
        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass
        if os.path.exists(png_path):
            try:
                self._app_icon_photo = ImageTk.PhotoImage(file=png_path)
                self.iconphoto(True, self._app_icon_photo)
            except Exception:
                pass

    # --- Конфигурация и сохранение ---
    def load_config(self):
        self.last_file = None
        self.last_page = 0
        self.invert_colors = False  # По умолчанию всегда выключен (обычный белый фон страниц)
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.last_file = data.get("last_file")
                    self.last_page = data.get("last_page", 0)
                    self.current_theme = data.get("theme", "dark")
            except Exception:
                pass

    def save_config(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump({
                    "last_file": self.filepath,
                    "last_page": self.current_page,
                    "theme": self.current_theme
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # --- Создание интерфейса ---
    def _init_ui(self):
        # Верхняя панель (Toolbar)
        self.toolbar = tk.Frame(self, relief="flat", bd=0, padx=8, pady=6)
        self.toolbar.pack(side="top", fill="x")

        # Кнопка «Открыть»
        self.btn_open = self._create_btn(self.toolbar, "📂 Открыть (Ctrl+O)", self.on_open_file)
        self.btn_open.pack(side="left", padx=(2, 8))

        # Разделитель
        self._create_separator(self.toolbar)

        # Навигация по страницам
        self.btn_first = self._create_btn(self.toolbar, "⏮", lambda: self.go_page(0), tooltip="Первая страница (Home)")
        self.btn_first.pack(side="left", padx=2)

        self.btn_prev = self._create_btn(self.toolbar, "◀ Назад", self.prev_page, tooltip="Предыдущая (←, PageUp)")
        self.btn_prev.pack(side="left", padx=2)

        self.page_frame = tk.Frame(self.toolbar)
        self.page_frame.pack(side="left", padx=4)

        self.page_entry = tk.Entry(self.page_frame, width=4, justify="center", font=("Segoe UI", 10, "bold"), bd=1, relief="solid")
        self.page_entry.pack(side="left")
        self.page_entry.bind("<Return>", self._on_page_entry_submit)

        self.lbl_total_pages = tk.Label(self.page_frame, text=" / 0", font=("Segoe UI", 10))
        self.lbl_total_pages.pack(side="left", padx=(2, 0))

        self.btn_next = self._create_btn(self.toolbar, "Вперед ▶", self.next_page, tooltip="Следующая (→, PageDown, Пробел)")
        self.btn_next.pack(side="left", padx=2)

        self.btn_last = self._create_btn(self.toolbar, "⏭", lambda: self.go_page(self.total_pages - 1), tooltip="Последняя страница (End)")
        self.btn_last.pack(side="left", padx=2)

        # Разделитель
        self._create_separator(self.toolbar)

        # Масштабирование
        self.btn_zoom_out = self._create_btn(self.toolbar, "🔍 -", self.zoom_out, tooltip="Уменьшить (Ctrl -)")
        self.btn_zoom_out.pack(side="left", padx=2)

        self.lbl_zoom = tk.Label(self.toolbar, text="100%", width=6, font=("Segoe UI", 9, "bold"))
        self.lbl_zoom.pack(side="left", padx=2)

        self.btn_zoom_in = self._create_btn(self.toolbar, "🔍 +", self.zoom_in, tooltip="Увеличить (Ctrl +)")
        self.btn_zoom_in.pack(side="left", padx=2)

        self.btn_fit_width = self._create_btn(self.toolbar, "↔ По ширине", self.fit_width, tooltip="Подогнать по ширине окна (Ctrl+W)")
        self.btn_fit_width.pack(side="left", padx=2)

        self.btn_fit_page = self._create_btn(self.toolbar, "↕ По странице", self.fit_page, tooltip="Подогнать по высоте окна (Ctrl+H)")
        self.btn_fit_page.pack(side="left", padx=2)

        # Разделитель
        self._create_separator(self.toolbar)

        # Поворот и инструменты чтения
        self.btn_rotate = self._create_btn(self.toolbar, "🔄 Поворот", self.rotate_page, tooltip="Повернуть на 90° (Ctrl+R)")
        self.btn_rotate.pack(side="left", padx=2)

        self.btn_night = self._create_btn(self.toolbar, "🌙 Ночной режим", self.toggle_invert, tooltip="Инвертировать цвета страниц (Ctrl+I)")
        self.btn_night.pack(side="left", padx=2)

        # Правая часть тулбара: Поиск и переключение темы
        self.btn_theme = self._create_btn(self.toolbar, "🌓 Тема", self.toggle_theme, tooltip="Переключить тему оформления")
        self.btn_theme.pack(side="right", padx=2)

        self.btn_search = self._create_btn(self.toolbar, "🔎 Поиск", self.toggle_search_panel, tooltip="Поиск по тексту (Ctrl+F)")
        self.btn_search.pack(side="right", padx=2)

        # Панель поиска (скрыта по умолчанию)
        self.search_panel = tk.Frame(self, padx=10, pady=5, bd=1, relief="solid")
        self.search_entry = tk.Entry(self.search_panel, width=28, font=("Segoe UI", 10), bd=1, relief="solid")
        self.search_entry.pack(side="left", padx=(0, 6))
        self.search_entry.bind("<Return>", lambda e: self.search_text(forward=True))

        self.btn_search_go = self._create_btn(self.search_panel, "Найти", lambda: self.search_text(forward=True))
        self.btn_search_go.pack(side="left", padx=2)

        self.btn_search_prev = self._create_btn(self.search_panel, "◀ Предыдущее", lambda: self.search_text(forward=False))
        self.btn_search_prev.pack(side="left", padx=2)

        self.btn_search_next = self._create_btn(self.search_panel, "Следующее ▶", lambda: self.search_text(forward=True))
        self.btn_search_next.pack(side="left", padx=2)

        self.lbl_search_status = tk.Label(self.search_panel, text="", font=("Segoe UI", 9))
        self.lbl_search_status.pack(side="left", padx=8)

        self.btn_close_search = self._create_btn(self.search_panel, "✕ Закрыть", self.toggle_search_panel)
        self.btn_close_search.pack(side="right", padx=2)

        # Рабочая область: холст (Canvas) + скроллбары
        self.view_container = tk.Frame(self)
        self.view_container.pack(side="top", fill="both", expand=True)

        self.v_scroll = tk.Scrollbar(self.view_container, orient="vertical")
        self.v_scroll.pack(side="right", fill="y")

        self.h_scroll = tk.Scrollbar(self.view_container, orient="horizontal")
        self.h_scroll.pack(side="bottom", fill="x")

        self.canvas = tk.Canvas(
            self.view_container,
            xscrollcommand=self.h_scroll.set,
            yscrollcommand=self.v_scroll.set,
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(side="left", fill="both", expand=True)

        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)

        # Нижняя статус-строка
        self.status_bar = tk.Frame(self, padx=8, pady=4)
        self.status_bar.pack(side="bottom", fill="x")

        self.lbl_status = tk.Label(self.status_bar, text="Готово", font=("Segoe UI", 9), anchor="w")
        self.lbl_status.pack(side="left", fill="x", expand=True)

        self.lbl_shortcuts = tk.Label(
            self.status_bar,
            text="Ctrl+O: Открыть | ←/→: Страницы | Ctrl+Колесико: Масштаб | F11: Во весь экран",
            font=("Segoe UI", 8),
            anchor="e"
        )
        self.lbl_shortcuts.pack(side="right")

    def _create_btn(self, parent, text, command, tooltip=None):
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 9),
            relief="flat",
            bd=0,
            padx=8,
            pady=4,
            cursor="hand2"
        )
        # Простая подсветка при наведении
        def on_enter(e):
            theme = self.THEMES[self.current_theme]
            btn.config(bg=theme["btn_hover"])
        def on_leave(e):
            theme = self.THEMES[self.current_theme]
            btn.config(bg=theme["btn_bg"])

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def _create_separator(self, parent):
        sep = tk.Frame(parent, width=1, height=22)
        sep.pack(side="left", padx=6)
        sep._is_separator = True
        return sep

    # --- Применение темы оформления ---
    def _apply_theme(self):
        t = self.THEMES[self.current_theme]

        self.config(bg=t["bg"])
        self.toolbar.config(bg=t["toolbar_bg"])
        self.page_frame.config(bg=t["toolbar_bg"])
        self.status_bar.config(bg=t["toolbar_bg"])
        self.search_panel.config(bg=t["search_bg"], highlightbackground=t["border"])
        self.view_container.config(bg=t["canvas_bg"])
        self.canvas.config(bg=t["canvas_bg"])

        # Обновление всех кнопок в тулбаре и панели поиска
        for parent in (self.toolbar, self.search_panel, self.page_frame):
            for child in parent.winfo_children():
                if isinstance(child, tk.Button):
                    child.config(bg=t["btn_bg"], fg=t["fg"], activebackground=t["btn_hover"], activeforeground=t["fg"])
                elif isinstance(child, tk.Label):
                    child.config(bg=t["toolbar_bg"], fg=t["fg"])
                elif isinstance(child, tk.Entry):
                    child.config(bg=t["entry_bg"], fg=t["entry_fg"], insertbackground=t["fg"], highlightbackground=t["border"])
                elif getattr(child, "_is_separator", False):
                    child.config(bg=t["border"])

        self.lbl_status.config(bg=t["toolbar_bg"], fg=t["fg"])
        self.lbl_shortcuts.config(bg=t["toolbar_bg"], fg=t["fg"])
        self.lbl_search_status.config(bg=t["search_bg"], fg=t["fg"])

        # Обновление статуса кнопки ночного режима
        if self.invert_colors:
            self.btn_night.config(
                text="☀️ Обычные цвета (Ctrl+I)",
                bg="#f59e0b",
                fg="#000000",
                activebackground="#d97706",
                activeforeground="#000000"
            )
        else:
            self.btn_night.config(
                text="🌙 Ночной режим (Ctrl+I)",
                bg=t["btn_bg"],
                fg=t["fg"],
                activebackground=t["btn_hover"],
                activeforeground=t["fg"]
            )

        # Если документ не открыт, перерисовать экран приветствия
        if not self.doc:
            self._show_welcome_screen()
        else:
            self.render_page()

    def toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self._apply_theme()
        self.save_config()

    def toggle_invert(self):
        self.invert_colors = not self.invert_colors
        self._apply_theme()
        if self.invert_colors:
            self._update_status("🌙 Ночной режим ВКЛЮЧЕН (цвета страниц инвертированы в темные)")
        else:
            self._update_status("☀️ Ночной режим ВЫКЛЮЧЕН (стандартный белый фон страниц)")

    # --- Экран приветствия ---
    def _show_welcome_screen(self):
        self.canvas.delete("all")
        t = self.THEMES[self.current_theme]
        w = max(self.canvas.winfo_width(), 800)
        h = max(self.canvas.winfo_height(), 600)

        cx, cy = w // 2, h // 2

        self.canvas.create_text(
            cx, cy - 60,
            text="📖 PDF Читалка",
            font=("Segoe UI", 26, "bold"),
            fill=t["accent"]
        )

        self.canvas.create_text(
            cx, cy - 10,
            text="Нажмите «Открыть» или перетащите PDF файл на значок программы",
            font=("Segoe UI", 12),
            fill=t["fg"]
        )

        self.canvas.create_text(
            cx, cy + 25,
            text="Горячие клавиши:  Ctrl+O — открыть  |  ← / → — страницы  |  Ctrl + Колесико — масштаб",
            font=("Segoe UI", 10),
            fill=t["border"]
        )

        # Кнопка по центру экрана
        open_box = self.canvas.create_rectangle(
            cx - 90, cy + 60, cx + 90, cy + 100,
            fill=t["accent"], outline="", width=0
        )
        open_txt = self.canvas.create_text(
            cx, cy + 80,
            text="Выбрать файл",
            font=("Segoe UI", 11, "bold"),
            fill="#ffffff"
        )
        self.canvas.tag_bind(open_box, "<Button-1>", lambda e: self.on_open_file())
        self.canvas.tag_bind(open_txt, "<Button-1>", lambda e: self.on_open_file())
        self.canvas.config(cursor="hand2")

    # --- Горячие клавиши и события ---
    def _bind_events(self):
        # Навигация клавишами
        self.bind("<Left>", lambda e: self.prev_page())
        self.bind("<Right>", lambda e: self.next_page())
        self.bind("<Prior>", lambda e: self.prev_page())   # PageUp
        self.bind("<Next>", lambda e: self.next_page())    # PageDown
        self.bind("<space>", lambda e: self.next_page())
        self.bind("<BackSpace>", lambda e: self.prev_page())
        self.bind("<Home>", lambda e: self.go_page(0))
        self.bind("<End>", lambda e: self.go_page(self.total_pages - 1))

        # Горячие комбинации Ctrl
        self.bind("<Control-o>", lambda e: self.on_open_file())
        self.bind("<Control-O>", lambda e: self.on_open_file())
        self.bind("<Control-plus>", lambda e: self.zoom_in())
        self.bind("<Control-equal>", lambda e: self.zoom_in())
        self.bind("<Control-minus>", lambda e: self.zoom_out())
        self.bind("<Control-0>", lambda e: self.set_zoom(1.0))
        self.bind("<Control-w>", lambda e: self.fit_width())
        self.bind("<Control-W>", lambda e: self.fit_width())
        self.bind("<Control-h>", lambda e: self.fit_page())
        self.bind("<Control-H>", lambda e: self.fit_page())
        self.bind("<Control-r>", lambda e: self.rotate_page())
        self.bind("<Control-R>", lambda e: self.rotate_page())
        self.bind("<Control-i>", lambda e: self.toggle_invert())
        self.bind("<Control-I>", lambda e: self.toggle_invert())
        self.bind("<Control-f>", lambda e: self.toggle_search_panel())
        self.bind("<Control-F>", lambda e: self.toggle_search_panel())
        self.bind("<Escape>", lambda e: self.close_search_panel())
        self.bind("<F11>", lambda e: self.toggle_fullscreen())

        # Колесико мыши (Windows)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Shift-MouseWheel>", self._on_shift_mousewheel)

        # Изменение размера окна
        self.canvas.bind("<Configure>", self._on_canvas_resize)

    def _on_mousewheel(self, event):
        # Если зажат Ctrl — масштабирование
        if event.state & 0x0004:
            if event.delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            # Обычная вертикальная прокрутка
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_shift_mousewheel(self, event):
        # Горизонтальная прокрутка
        self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_canvas_resize(self, event):
        if not self.doc:
            self._show_welcome_screen()
        else:
            self._center_image()

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        self.attributes("-fullscreen", self.is_fullscreen)

    # --- Работа с PDF ---
    def on_open_file(self):
        file = filedialog.askopenfilename(
            title="Выберите PDF документ",
            filetypes=[("PDF файлы (*.pdf)", "*.pdf"), ("Все файлы (*.*)", "*.*")]
        )
        if file:
            self.open_pdf(file)

    def open_pdf(self, path, page=0):
        try:
            self.doc = pymupdf.open(path)
            self.filepath = os.path.abspath(path)
            self.total_pages = len(self.doc)
            self.current_page = max(0, min(page, self.total_pages - 1))
            self.rotation = 0

            filename = os.path.basename(path)
            self.title(f"{filename} — PDF Читалка")
            self.lbl_total_pages.config(text=f" / {self.total_pages}")
            self.canvas.config(cursor="")

            self.render_page()
            self.save_config()
            self._update_status(f"Открыт: {filename} ({self.total_pages} стр.)")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть PDF файл:\n{e}")

    def render_page(self):
        if not self.doc or self.total_pages == 0:
            return

        try:
            page = self.doc[self.current_page]

            # Создание матрицы трансформации (масштаб + угол поворота)
            mat = pymupdf.Matrix(self.zoom, self.zoom).prerotate(self.rotation)
            # Рендерим с гарантированным белым фоном и цветовым пространством RGB
            pix = page.get_pixmap(matrix=mat, colorspace=pymupdf.csRGB, alpha=False)

            # Конвертация в PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Если включен ночной режим (инверсия страниц)
            if self.invert_colors:
                img = ImageOps.invert(img)

            # Если активен поиск по тексту, подсвечиваем найденное
            query = self.search_entry.get().strip()
            if query:
                rects = page.search_for(query)
                if rects:
                    draw = ImageDraw.Draw(img, "RGBA")
                    for r in rects:
                        # Преобразование координат в соответствии с матрицей
                        p1 = r.tl * mat
                        p2 = r.br * mat
                        draw.rectangle(
                            [min(p1.x, p2.x), min(p1.y, p2.y), max(p1.x, p2.x), max(p1.y, p2.y)],
                            fill=(255, 235, 59, 110),
                            outline=(245, 127, 23, 220),
                            width=2
                        )

            # Создание Tkinter-совместимого изображения
            self.tk_image = ImageTk.PhotoImage(img)

            self.canvas.delete("all")
            self.img_width = pix.width
            self.img_height = pix.height

            # Отрисовка по центру
            self._center_image()

            # Обновление полей ввода страниц и зума
            self.page_entry.delete(0, tk.END)
            self.page_entry.insert(0, str(self.current_page + 1))
            self.lbl_zoom.config(text=f"{int(self.zoom * 100)}%")

        except Exception as e:
            self._update_status(f"Ошибка рендеринга: {e}")

    def _center_image(self):
        if not self.tk_image:
            return

        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()

        margin = 15
        total_w = max(self.img_width + margin * 2, canvas_w)
        total_h = max(self.img_height + margin * 2, canvas_h)

        x = total_w // 2
        y = margin + (self.img_height // 2) if total_h > canvas_h else canvas_h // 2

        self.canvas.delete("pdf_page")
        self.canvas.delete("pdf_border")
        # Рамка вокруг страницы для четкого отделения от фона холста
        half_w = self.img_width // 2
        half_h = self.img_height // 2
        t = self.THEMES[self.current_theme]
        self.canvas.create_rectangle(
            x - half_w - 1, y - half_h - 1,
            x + half_w + 1, y + half_h + 1,
            outline=t["border"], width=1, tags="pdf_border"
        )
        self.canvas.create_image(x, y, image=self.tk_image, anchor="center", tags="pdf_page")
        self.canvas.config(scrollregion=(0, 0, total_w, total_h))

    # --- Навигация по страницам ---
    def prev_page(self):
        if self.doc and self.current_page > 0:
            self.go_page(self.current_page - 1)

    def next_page(self):
        if self.doc and self.current_page < self.total_pages - 1:
            self.go_page(self.current_page + 1)

    def go_page(self, index):
        if not self.doc:
            return
        index = max(0, min(index, self.total_pages - 1))
        if index != self.current_page:
            self.current_page = index
            self.render_page()
            self.canvas.yview_moveto(0)  # Скролл наверх новой страницы
            self.save_config()

    def _on_page_entry_submit(self, event=None):
        if not self.doc:
            return
        val = self.page_entry.get().strip()
        if val.isdigit():
            page_num = int(val) - 1
            self.go_page(page_num)

    # --- Масштабирование и поворот ---
    def zoom_in(self):
        for z in self.ZOOM_LEVELS:
            if z > self.zoom + 0.05:
                self.set_zoom(z)
                return
        self.set_zoom(min(self.zoom * 1.2, 5.0))

    def zoom_out(self):
        for z in reversed(self.ZOOM_LEVELS):
            if z < self.zoom - 0.05:
                self.set_zoom(z)
                return
        self.set_zoom(max(self.zoom / 1.2, 0.2))

    def set_zoom(self, zoom_val):
        self.zoom = round(max(0.2, min(zoom_val, 5.0)), 2)
        self.render_page()

    def fit_width(self):
        if not self.doc:
            return
        page = self.doc[self.current_page]
        rect = page.rect
        # Учитываем поворот
        w = rect.width if self.rotation in (0, 180) else rect.height
        canvas_w = max(self.canvas.winfo_width() - 40, 300)
        new_zoom = canvas_w / w
        self.set_zoom(new_zoom)

    def fit_page(self):
        if not self.doc:
            return
        page = self.doc[self.current_page]
        rect = page.rect
        h = rect.height if self.rotation in (0, 180) else rect.width
        canvas_h = max(self.canvas.winfo_height() - 40, 300)
        new_zoom = canvas_h / h
        self.set_zoom(new_zoom)

    def rotate_page(self):
        self.rotation = (self.rotation + 90) % 360
        self.render_page()

    # --- Поиск по тексту ---
    def toggle_search_panel(self):
        if self.search_panel.winfo_ismapped():
            self.close_search_panel()
        else:
            self.search_panel.pack(side="top", fill="x", before=self.view_container)
            self.search_entry.focus_set()
            self.search_entry.select_range(0, tk.END)

    def close_search_panel(self):
        if self.search_panel.winfo_ismapped():
            self.search_panel.pack_forget()
            self.lbl_search_status.config(text="")
            self.render_page()

    def search_text(self, forward=True):
        if not self.doc:
            return
        query = self.search_entry.get().strip()
        if not query:
            self.lbl_search_status.config(text="Введите слово для поиска")
            return

        # Ищем совпадения по всем страницам
        matches = []
        for p_idx in range(self.total_pages):
            page = self.doc[p_idx]
            rects = page.search_for(query)
            if rects:
                matches.append(p_idx)

        if not matches:
            self.lbl_search_status.config(text="Совпадений не найдено")
            return

        self.lbl_search_status.config(text=f"Найдено на {len(matches)} стр.")

        # Определение следующей страницы для перехода
        if forward:
            next_pages = [p for p in matches if p > self.current_page]
            target = next_pages[0] if next_pages else matches[0]
        else:
            prev_pages = [p for p in matches if p < self.current_page]
            target = prev_pages[-1] if prev_pages else matches[-1]

        self.go_page(target)

    # --- Вспомогательные методы ---
    def _update_status(self, text):
        self.lbl_status.config(text=text)


def main():
    initial = sys.argv[1] if len(sys.argv) > 1 else None
    app = PDFReaderApp(initial)
    app.mainloop()


if __name__ == "__main__":
    main()
