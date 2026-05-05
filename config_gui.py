#!/usr/bin/env python3
"""
st_book 配置GUI - 可视化编辑 config.yaml
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import sys
import os
import subprocess
import threading
import shutil

try:
    from ruamel.yaml import YAML
    _ruamel = YAML()
    _ruamel.indent(mapping=2, sequence=4, offset=2)
    _ruamel.preserve_quotes = True
    HAVE_RUAMEL = True
except ImportError:
    HAVE_RUAMEL = False

try:
    import yaml
except ImportError:
    yaml = None


class ConfigGUI:
    """主配置界面"""

    def __init__(self, master):
        self.master = master
        master.title("st_book 配置管理")
        master.geometry("850x780")

        self.config_path = Path("config.yaml")
        self.data = {}  # 当前配置数据

        # 模式名 → 中文描述映射
        self._mode_names = {
            "full-auto": "一键全自动（角色卡+世界书）",
            "auto":  "角色全自动",
            "full":  "完整流程",
            "split": "文本分割",
            "extract": "角色提取",
            "merge": "角色合并",
            "filter": "角色筛选",
            "create": "制卡",
            "wb-auto": "世界书全自动",
            "wb-extract": "世界书提取",
            "wb-generate": "世界书生成",
            "status": "状态检查",
            "clean": "清理文件",
            "help": "帮助信息",
        }

        style = ttk.Style()
        style.configure("Title.TLabel", font=("微软雅黑", 10, "bold"))
        style.configure("Header.TLabel", font=("微软雅黑", 9, "bold"))

        self._build_ui()
        self.load_config()

    # ── UI 构建 ──────────────────────────────────────────────

    def _build_ui(self):
        """构建完整界面"""
        main_panel = ttk.PanedWindow(self.master, orient=tk.VERTICAL)
        main_panel.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # 顶部操作栏
        top_bar = ttk.Frame(main_panel)
        ttk.Button(top_bar, text="📂 加载配置", command=self.load_config).pack(side=tk.LEFT, padx=2)
        ttk.Button(top_bar, text="💾 保存配置", command=self.save_config).pack(side=tk.LEFT, padx=2)
        ttk.Button(top_bar, text="🔄 重新加载", command=self.reload_config).pack(side=tk.LEFT, padx=2)
        ttk.Separator(top_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=6, fill=tk.Y)
        ttk.Button(top_bar, text="帮助", command=self.show_help).pack(side=tk.LEFT, padx=2)
        self.status_label = ttk.Label(top_bar, text="就绪", foreground="gray", width=40, anchor=tk.E)
        self.status_label.pack(side=tk.RIGHT, padx=5, fill=tk.X, expand=True)
        main_panel.add(top_bar, weight=0)

        # ── Notebook 选项卡 ──
        self.notebook = ttk.Notebook(main_panel)
        main_panel.add(self.notebook, weight=1)

        self.tab_input = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_input, text=" 📖 加载小说 ")
        self._build_input_tab()

        self.tab_api = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_api, text=" API & 模型 ")
        self._build_api_tab()

        self.tab_params = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_params, text=" 模型参数 ")
        self._build_params_tab()

        self.tab_perf = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_perf, text=" 网络与性能 ")
        self._build_perf_tab()

        self.tab_cache = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_cache, text=" 缓存配置 ")
        self._build_cache_tab()

        self.tab_output = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_output, text=" 输出目录 ")
        self._build_output_tab()

        # ── 工作流工具栏 ──
        wf_bar = ttk.LabelFrame(main_panel, text="工作流快捷启动", padding=3)
        self._build_workflow_bar(wf_bar)
        main_panel.add(wf_bar, weight=0)

        # ── 日志区域 ──
        log_frame = ttk.LabelFrame(main_panel, text="日志", padding=4)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state=tk.DISABLED,
                                                    font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4",
                                                    insertbackground="white")
        self.log_text.pack(fill=tk.BOTH, expand=True)
        main_panel.add(log_frame, weight=1)

    # ── Tab: 加载小说 ────────────────────────────────────────

    def _build_input_tab(self):
        f = ttk.Frame(self.tab_input, padding=12)
        f.pack(fill=tk.BOTH, expand=True)

        grp = ttk.LabelFrame(f, text="输入文件配置", padding=8)
        grp.pack(fill=tk.X, pady=(0, 10))

        row = ttk.Frame(grp)
        row.pack(fill=tk.X, pady=4)
        ttk.Label(row, text="源文件:", width=12).pack(side=tk.LEFT)
        self.source_file_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.source_file_var, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(row, text="浏览...", command=lambda: self._browse_file(self.source_file_var, [("文本文件", "*.txt"), ("所有文件", "*.*")])).pack(side=tk.LEFT, padx=2)

        row = ttk.Frame(grp)
        row.pack(fill=tk.X, pady=4)
        ttk.Label(row, text="文件编码:", width=12).pack(side=tk.LEFT)
        self.encoding_var = tk.StringVar(value="utf-8")
        encodings = ["utf-8", "utf-8-sig", "gbk", "gb2312", "gb18030", "big5", "shift-jis"]
        ttk.Combobox(row, textvariable=self.encoding_var, values=encodings, width=20, state="readonly").pack(side=tk.LEFT)

        self.file_status = ttk.Label(grp, text="", foreground="gray")
        self.file_status.pack(anchor=tk.W, pady=(5, 0))
        self.source_file_var.trace_add("write", lambda *a: self._check_input_file())

        info = ttk.LabelFrame(f, text="编码说明", padding=6)
        info.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(info, text="• UTF-8: 通用编码（推荐）\n• UTF-8 BOM: 带BOM的UTF-8（部分Windows文本）\n• GBK/GB2312: 简体中文（Windows记事本ANSI）\n• Big5: 繁体中文", foreground="#555", font=("", 9)).pack(anchor=tk.W)

    # ── Tab: API & 模型 ───────────────────────────────────────

    def _build_api_tab(self):
        f = ttk.Frame(self.tab_api, padding=12)
        f.pack(fill=tk.BOTH, expand=True)

        grp1 = ttk.LabelFrame(f, text="API 配置", padding=8)
        grp1.pack(fill=tk.X, pady=(0, 10))

        row = ttk.Frame(grp1)
        row.pack(fill=tk.X, pady=3)
        ttk.Label(row, text="API 密钥:", width=12).pack(side=tk.LEFT)
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(row, textvariable=self.api_key_var, show="*", width=60)
        self.api_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(row, text="显示", width=4,
                   command=lambda: self._toggle_show(self.api_key_entry)).pack(side=tk.LEFT, padx=2)

        row = ttk.Frame(grp1)
        row.pack(fill=tk.X, pady=3)
        ttk.Label(row, text="基础 URL:", width=12).pack(side=tk.LEFT)
        self.api_base_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.api_base_var, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True)

        grp2 = ttk.LabelFrame(f, text="主要模型", padding=8)
        grp2.pack(fill=tk.X, pady=(0, 10))

        row = ttk.Frame(grp2)
        row.pack(fill=tk.X, pady=3)
        ttk.Label(row, text="提取模型:", width=12).pack(side=tk.LEFT)
        self.extraction_model_var = tk.StringVar()
        models = ["models/gemini-2.5-flash", "models/gemini-2.0-flash", "gpt-4o-mini", "gpt-4o", "claude-sonnet-4-6", "claude-haiku-4-5"]
        ttk.Combobox(row, textvariable=self.extraction_model_var, values=models, width=57).pack(side=tk.LEFT)

        row = ttk.Frame(grp2)
        row.pack(fill=tk.X, pady=3)
        ttk.Label(row, text="生成模型:", width=12).pack(side=tk.LEFT)
        self.generation_model_var = tk.StringVar()
        pro_models = ["models/gemini-2.5-pro", "models/gemini-2.0-flash", "gpt-4o", "claude-opus-4-7", "claude-sonnet-4-6"]
        ttk.Combobox(row, textvariable=self.generation_model_var, values=pro_models, width=57).pack(side=tk.LEFT)

    # ── Tab: 模型参数 ────────────────────────────────────────

    def _build_params_tab(self):
        f = ttk.Frame(self.tab_params, padding=12)
        f.pack(fill=tk.BOTH, expand=True)

        grp = ttk.LabelFrame(f, text="模型参数", padding=8)
        grp.pack(fill=tk.X, pady=(0, 10))

        # 温度参数
        row = ttk.Frame(grp)
        row.pack(fill=tk.X, pady=4)
        ttk.Label(row, text="提取温度:", width=16).pack(side=tk.LEFT)
        self.extraction_temp_var = tk.DoubleVar(value=0.3)
        ttk.Scale(row, from_=0.0, to=2.0, orient=tk.HORIZONTAL,
                  variable=self.extraction_temp_var, length=200).pack(side=tk.LEFT, padx=5)
        self._temp_label1 = ttk.Label(row, text="0.3", width=5)
        self._temp_label1.pack(side=tk.LEFT)
        ttk.Label(row, text="  较低=更确定", foreground="gray").pack(side=tk.LEFT, padx=10)
        self.extraction_temp_var.trace_add("write", lambda *a: self._temp_label1.config(text=f"{self.extraction_temp_var.get():.1f}"))

        row = ttk.Frame(grp)
        row.pack(fill=tk.X, pady=4)
        ttk.Label(row, text="生成温度:", width=16).pack(side=tk.LEFT)
        self.generation_temp_var = tk.DoubleVar(value=0.2)
        ttk.Scale(row, from_=0.0, to=2.0, orient=tk.HORIZONTAL,
                  variable=self.generation_temp_var, length=200).pack(side=tk.LEFT, padx=5)
        self._temp_label2 = ttk.Label(row, text="0.2", width=5)
        self._temp_label2.pack(side=tk.LEFT)
        self.generation_temp_var.trace_add("write", lambda *a: self._temp_label2.config(text=f"{self.generation_temp_var.get():.1f}"))

        row = ttk.Frame(grp)
        row.pack(fill=tk.X, pady=4)
        ttk.Label(row, text="世界书温度:", width=16).pack(side=tk.LEFT)
        self.worldbook_temp_var = tk.DoubleVar(value=0.2)
        ttk.Scale(row, from_=0.0, to=2.0, orient=tk.HORIZONTAL,
                  variable=self.worldbook_temp_var, length=200).pack(side=tk.LEFT, padx=5)
        self._temp_label3 = ttk.Label(row, text="0.2", width=5)
        self._temp_label3.pack(side=tk.LEFT)
        self.worldbook_temp_var.trace_add("write", lambda *a: self._temp_label3.config(text=f"{self.worldbook_temp_var.get():.1f}"))

        # Token / 超时
        sep = ttk.Separator(grp, orient=tk.HORIZONTAL)
        sep.pack(fill=tk.X, pady=8)

        row = ttk.Frame(grp)
        row.pack(fill=tk.X, pady=4)
        ttk.Label(row, text="最大输出 Token:", width=16).pack(side=tk.LEFT)
        self.max_tokens_var = tk.IntVar(value=60000)
        ttk.Spinbox(row, from_=1000, to=200000, increment=1000, textvariable=self.max_tokens_var, width=12).pack(side=tk.LEFT)
        ttk.Label(row, text="  API超时(秒):").pack(side=tk.LEFT, padx=(20, 0))
        self.timeout_var = tk.IntVar(value=300)
        ttk.Spinbox(row, from_=30, to=600, increment=10, textvariable=self.timeout_var, width=10).pack(side=tk.LEFT)

        # 分块参数
        sep2 = ttk.Separator(grp, orient=tk.HORIZONTAL)
        sep2.pack(fill=tk.X, pady=8)

        row = ttk.Frame(grp)
        row.pack(fill=tk.X, pady=4)
        ttk.Label(row, text="文本分块大小:", width=16).pack(side=tk.LEFT)
        self.max_chunk_var = tk.IntVar(value=60000)
        ttk.Spinbox(row, from_=1000, to=200000, increment=1000, textvariable=self.max_chunk_var, width=12).pack(side=tk.LEFT)
        ttk.Label(row, text="  重叠字符:").pack(side=tk.LEFT, padx=(20, 0))
        self.buffer_chars_var = tk.IntVar(value=200)
        ttk.Spinbox(row, from_=0, to=2000, increment=10, textvariable=self.buffer_chars_var, width=10).pack(side=tk.LEFT)

    # ── Tab: 网络与性能 ──────────────────────────────────────

    def _build_perf_tab(self):
        f = ttk.Frame(self.tab_perf, padding=12)
        f.pack(fill=tk.BOTH, expand=True)

        grp = ttk.LabelFrame(f, text="网络与性能参数", padding=8)
        grp.pack(fill=tk.X, pady=(0, 10))

        params = [
            ("最大并发请求数:", "max_concurrent", 1, 1, 20, 1),
            ("重试次数:", "retry_limit", 5, 0, 50, 1),
            ("重试延迟(秒):", "retry_delay", 10, 1, 120, 1),
            ("API限流延迟(秒):", "rate_limit_delay", 5, 0, 60, 1),
            ("批处理大小:", "batch_size", 1, 1, 50, 1),
        ]
        self._perf_vars = {}
        for label, key, default, min_v, max_v, step in params:
            row = ttk.Frame(grp)
            row.pack(fill=tk.X, pady=4)
            ttk.Label(row, text=label, width=20).pack(side=tk.LEFT)
            var = tk.IntVar(value=default)
            ttk.Spinbox(row, from_=min_v, to=max_v, increment=step, textvariable=var, width=10).pack(side=tk.LEFT)
            self._perf_vars[key] = var

    # ── Tab: 缓存配置 ────────────────────────────────────────

    def _build_cache_tab(self):
        f = ttk.Frame(self.tab_cache, padding=12)
        f.pack(fill=tk.BOTH, expand=True)

        grp = ttk.LabelFrame(f, text="缓存设置", padding=8)
        grp.pack(fill=tk.X, pady=(0, 10))

        self.enable_cache_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(grp, text="启用缓存 (推荐开启，避免重复API调用)", variable=self.enable_cache_var).pack(anchor=tk.W, pady=5)

        row = ttk.Frame(grp)
        row.pack(fill=tk.X, pady=5)
        ttk.Label(row, text="缓存目录:", width=12).pack(side=tk.LEFT)
        self.cache_dir_var = tk.StringVar(value="cache")
        ttk.Entry(row, textvariable=self.cache_dir_var, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(row, text="浏览...", command=lambda: self._browse_dir(self.cache_dir_var)).pack(side=tk.LEFT, padx=2)

        row = ttk.Frame(grp)
        row.pack(fill=tk.X, pady=5)
        ttk.Label(row, text="缓存过期(天):", width=12).pack(side=tk.LEFT)
        self.cache_expiry_var = tk.IntVar(value=30)
        ttk.Spinbox(row, from_=1, to=365, increment=1, textvariable=self.cache_expiry_var, width=10).pack(side=tk.LEFT)
        ttk.Label(row, text="  超过此天数的缓存将被清理", foreground="gray").pack(side=tk.LEFT, padx=10)

        info = ttk.LabelFrame(f, text="缓存状态", padding=6)
        info.pack(fill=tk.X, pady=(0, 10))
        self.cache_info_label = ttk.Label(info, text="点击「查看缓存」扫描缓存目录", foreground="gray")
        self.cache_info_label.pack(anchor=tk.W)
        ttk.Button(info, text="查看缓存", command=self.show_cache_info).pack(anchor=tk.W, pady=3)

    # ── Tab: 输出目录 ────────────────────────────────────────

    def _build_output_tab(self):
        f = ttk.Frame(self.tab_output, padding=12)
        f.pack(fill=tk.BOTH, expand=True)

        grp = ttk.LabelFrame(f, text="输出目录", padding=8)
        grp.pack(fill=tk.X, pady=(0, 10))

        outputs = [
            ("文本分块:", "chunk_dir", "chunks"),
            ("角色原始响应:", "character_responses_dir", "character_responses"),
            ("合并角色JSON:", "roles_json_dir", "roles_json"),
            ("角色卡输出:", "cards_dir", "cards"),
            ("世界书输出:", "worldbook_dir", "worldbook"),
            ("缓存目录:", "cache_dir_output", "cache"),
            ("日志文件:", "log_file", "logs/st_book.log"),
        ]
        self._output_vars = {}
        for label, key, default in outputs:
            row = ttk.Frame(grp)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=label, width=18).pack(side=tk.LEFT)
            var = tk.StringVar(value=default)
            ttk.Entry(row, textvariable=var).pack(side=tk.LEFT, fill=tk.X, expand=True)
            self._output_vars[key] = var

        # 角色筛选数量配置
        filter_frame = ttk.LabelFrame(f, text="角色筛选配置", padding=8)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        row = ttk.Frame(filter_frame)
        row.pack(fill=tk.X, pady=4)
        ttk.Label(row, text="保留角色数量:", width=18).pack(side=tk.LEFT)
        self.keep_count_var = tk.IntVar(value=30)
        ttk.Spinbox(row, from_=1, to=500, increment=1, textvariable=self.keep_count_var, width=10).pack(side=tk.LEFT)
        ttk.Label(row, text="  按内容丰富度保留前N个角色", foreground="gray").pack(side=tk.LEFT, padx=10)

        # 筛选按钮提示文本随 keep_count_var 联动
        self._filter_desc_var = tk.StringVar(value=f"保留前 30 个内容最丰富的角色文件")
        self.keep_count_var.trace_add("write", self._update_filter_desc)

        actions = ttk.LabelFrame(f, text="快捷操作", padding=8)
        actions.pack(fill=tk.X)
        ttk.Button(actions, text="打开输出目录", command=self.open_output_dir).pack(side=tk.LEFT, padx=2)
        ttk.Button(actions, text="清理所有输出", command=self.clean_output).pack(side=tk.LEFT, padx=2)

    # ── 工作流按钮栏 ────────────────────────────────────────

    def _build_workflow_bar(self, parent):
        """三行排列，带悬浮提示"""
        groups = [
            ("角色卡", [
                ("auto",       "一键全自动",  "【推荐】清理并完整运行整个制卡流程"),
                ("full",       "完整流程",   "不清理，直接执行完整制卡流程"),
                ("split",      "分割",       "将小说文本分割为文本块"),
                ("extract",    "提取",       "从文本块中提取角色信息"),
                ("merge",      "合并",       "合并重复的角色数据"),
                ("filter",     "筛选",       None),  # 提示文本由 _filter_desc_var 动态提供
                ("create",     "制卡",       "从合并后的数据创建角色卡"),
            ]),
            ("世界书", [
                ("wb-auto",     "一键全自动",  "【推荐】清理并完整运行世界书流程"),
                ("wb-extract",  "提取条目",   "步骤1: 提取世界书原始条目"),
                ("wb-generate", "结构化生成",  "步骤2: 将原始条目升华为结构化世界书"),
            ]),
            ("通用", [
                ("status",  "状态",  "查看各处理阶段目录和文件状态"),
                ("clean",   "清理",  "删除所有中间及最终输出文件"),
                ("help",    "帮助",  "在日志区打印完整帮助信息"),
            ]),
        ]
        for group_label, items in groups:
            row = ttk.Frame(parent)
            row.pack(fill=tk.X, pady=1)
            ttk.Label(row, text=group_label, width=6, font=("", 9, "bold"),
                      anchor=tk.E, foreground="#333").pack(side=tk.LEFT)
            for mode, label, desc in items:
                btn = ttk.Button(row, text=label, width=10,
                                 command=lambda m=mode: self.run_workflow(m))
                btn.pack(side=tk.LEFT, padx=2)
                # 筛选按钮使用动态提示文本
                if mode == "filter":
                    self._tooltip(btn, self._filter_desc_var)
                elif desc:
                    self._tooltip(btn, desc)

    def _tooltip(self, widget, text):
        """为控件绑定悬浮提示。text 可为字符串或 StringVar（动态更新）"""
        tw = None
        lbl = None
        def get_text():
            if isinstance(text, tk.StringVar):
                return text.get()
            return text
        def show(event):
            nonlocal tw, lbl
            if tw:
                return
            x = widget.winfo_rootx() + 25
            y = widget.winfo_rooty() + 25
            tw = tk.Toplevel(widget)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{x}+{y}")
            lbl = ttk.Label(tw, text=get_text(), background="#ffffcc", relief=tk.SOLID,
                            borderwidth=1, padding=4, font=("", 9))
            lbl.pack()
            # 如果是 StringVar，追踪变化实时更新显示
            if isinstance(text, tk.StringVar):
                def update(*a):
                    if lbl and lbl.winfo_exists():
                        lbl.config(text=text.get())
                text.trace_add("write", update)
        def hide(event):
            nonlocal tw, lbl
            if tw:
                tw.destroy()
                tw = None
                lbl = None
        widget.bind("<Enter>", show, add="+")
        widget.bind("<Leave>", hide, add="+")

    # ── 辅助方法 ─────────────────────────────────────────────

    def _update_filter_desc(self, *args):
        """当 keep_count 改变时更新筛选按钮的提示文本"""
        count = self.keep_count_var.get()
        self._filter_desc_var.set(f"保留前 {count} 个内容最丰富的角色文件")

    def _toggle_show(self, entry_widget):
        """切换密码显示"""
        current = entry_widget.cget("show")
        entry_widget.config(show="" if current == "*" else "*")

    def _browse_file(self, var, filetypes):
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            var.set(path)

    def _browse_dir(self, var):
        path = filedialog.askdirectory()
        if path:
            var.set(path)

    def _check_input_file(self):
        path = self.source_file_var.get().strip()
        if path:
            p = Path(path)
            if p.exists():
                size = p.stat().st_size
                self.file_status.config(text=f"✅ 文件存在 ({size/1024:.1f} KB)", foreground="green")
            else:
                self.file_status.config(text="⚠️ 文件不存在", foreground="orange")
        else:
            self.file_status.config(text="", foreground="gray")

    def log(self, msg):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.master.update_idletasks()

    def set_status(self, msg, color="gray"):
        self.status_label.config(text=msg, foreground=color)

    # ── 配置读写 ─────────────────────────────────────────────

    def load_config(self):
        """加载 config.yaml，不存在时从模板复制"""
        if self.config_path.exists():
            self._load_from_path(self.config_path)
            self.log(f"✅ 已加载配置: {self.config_path}")
            self.set_status(f"已加载: {self.config_path.name}", "green")
            return

        tmpl = Path("config_template.yaml")
        if tmpl.exists():
            shutil.copy2(tmpl, self.config_path)
            self._load_from_path(self.config_path)
            self.log(f"✅ 已从 {tmpl.name} 复制并加载 {self.config_path}")
            self.set_status(f"已创建: {self.config_path.name}", "orange")
        else:
            self.log(f"❌ 未找到 {self.config_path} 或 {tmpl.name}")
            self.set_status("未找到配置文件", "red")

    def reload_config(self):
        """从磁盘重新加载 config.yaml（丢弃未保存的更改）"""
        if self.config_path.exists():
            self._load_from_path(self.config_path)
            self.log(f"✅ 已重新加载: {self.config_path}")

    def _load_from_path(self, path):
        """从指定路径加载配置到界面（保留注释和格式）"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                if HAVE_RUAMEL:
                    self.data = _ruamel.load(f)
                else:
                    self.data = yaml.safe_load(f) or {}
        except Exception as e:
            self.log(f"❌ 加载失败: {e}")
            self.data = {}
            return

        self._config_to_ui()

    def _config_to_ui(self):
        """将 self.data 写入界面控件"""
        api = self.data.get("api", {})
        self.api_key_var.set(api.get("api_key", ""))
        self.api_base_var.set(api.get("api_base", ""))

        models = self.data.get("models", {})
        self.extraction_model_var.set(models.get("extraction_model", ""))
        self.generation_model_var.set(models.get("generation_model", ""))
        self._set_val(self.extraction_temp_var, models.get("extraction_temperature", 0.3))
        self._set_val(self.generation_temp_var, models.get("generation_temperature", 0.2))
        self._set_val(self.worldbook_temp_var, models.get("worldbook_temperature", 0.2))
        self._set_val(self.max_tokens_var, models.get("max_tokens", 60000))
        self._set_val(self.timeout_var, models.get("timeout", 300))

        inp = self.data.get("input", {})
        self.source_file_var.set(inp.get("source_file", ""))
        self.encoding_var.set(inp.get("encoding", "utf-8"))

        perf = self.data.get("performance", {})
        mapping = {"max_concurrent": "max_concurrent", "retry_limit": "retry_limit",
                   "retry_delay": "retry_delay", "rate_limit_delay": "rate_limit_delay",
                   "batch_size": "batch_size"}
        for ui_key, cfg_key in mapping.items():
            if ui_key in self._perf_vars and cfg_key in perf:
                self._set_val(self._perf_vars[ui_key], perf[cfg_key])

        cache = self.data.get("cache", {})
        self._set_val(self.enable_cache_var, cache.get("enable_cache", True))
        self.cache_dir_var.set(cache.get("cache_dir", "cache"))
        self._set_val(self.cache_expiry_var, cache.get("cache_expiry_days", 30))

        output = self.data.get("output", {})
        out_map = {"chunk_dir": "chunk_dir", "character_responses_dir": "character_responses_dir",
                   "roles_json_dir": "roles_json_dir", "cards_dir": "cards_dir",
                   "worldbook_dir": "worldbook_dir"}
        for ui_key, cfg_key in out_map.items():
            if ui_key in self._output_vars and cfg_key in output:
                self._output_vars[ui_key].set(output.get(cfg_key, ""))

        if "cache_dir_output" in self._output_vars:
            self._output_vars["cache_dir_output"].set(cache.get("cache_dir", "cache"))
        if "log_file" in self._output_vars:
            logging = self.data.get("logging", {})
            self._output_vars["log_file"].set(logging.get("log_file", "logs/st_book.log"))

        tp = self.data.get("text_processing", {})
        self._set_val(self.max_chunk_var, tp.get("max_chunk_chars", 60000))
        self._set_val(self.buffer_chars_var, tp.get("buffer_chars", 200))

        cf = self.data.get("character_filter", {})
        self._set_val(self.keep_count_var, cf.get("keep_count", 30))

        self._check_input_file()

    def save_config(self):
        """将界面值写入配置文件（保留注释和格式）"""
        self._ui_to_config()
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                if HAVE_RUAMEL:
                    _ruamel.dump(self.data, f)
                else:
                    yaml.dump(self.data, f, default_flow_style=False, allow_unicode=True,
                              sort_keys=False, indent=2)
                    self.log("⚠ 未安装 ruamel.yaml，注释可能丢失: pip install ruamel.yaml")
            self.log(f"✅ 配置已保存: {self.config_path}")
            self.set_status("已保存", "green")
        except Exception as e:
            self.log(f"❌ 保存失败: {e}")
            self.set_status("保存失败", "red")

    def _ui_to_config(self):
        """将界面控件值写回 self.data"""
        self.data.setdefault("api", {})["api_key"] = self.api_key_var.get()
        self.data["api"]["api_base"] = self.api_base_var.get()

        self.data.setdefault("models", {})["extraction_model"] = self.extraction_model_var.get()
        self.data["models"]["generation_model"] = self.generation_model_var.get()
        self.data["models"]["extraction_temperature"] = round(self.extraction_temp_var.get(), 1)
        self.data["models"]["generation_temperature"] = round(self.generation_temp_var.get(), 1)
        self.data["models"]["worldbook_temperature"] = round(self.worldbook_temp_var.get(), 1)
        self.data["models"]["max_tokens"] = self.max_tokens_var.get()
        self.data["models"]["timeout"] = self.timeout_var.get()

        self.data.setdefault("input", {})["source_file"] = self.source_file_var.get()
        self.data["input"]["encoding"] = self.encoding_var.get()

        self.data.setdefault("performance", {})
        for ui_key, cfg_key in [("max_concurrent", "max_concurrent"), ("retry_limit", "retry_limit"),
                                ("retry_delay", "retry_delay"), ("rate_limit_delay", "rate_limit_delay"),
                                ("batch_size", "batch_size")]:
            self.data["performance"][cfg_key] = self._perf_vars[ui_key].get()

        self.data.setdefault("cache", {})["enable_cache"] = bool(self.enable_cache_var.get())
        self.data["cache"]["cache_dir"] = self.cache_dir_var.get()
        self.data["cache"]["cache_expiry_days"] = self.cache_expiry_var.get()

        self.data.setdefault("text_processing", {})["max_chunk_chars"] = self.max_chunk_var.get()
        self.data["text_processing"]["buffer_chars"] = self.buffer_chars_var.get()

        self.data.setdefault("character_filter", {})["keep_count"] = self.keep_count_var.get()

    def _set_val(self, var, val):
        try:
            if isinstance(var, tk.StringVar):
                var.set(str(val) if val is not None else "")
            elif isinstance(var, tk.IntVar):
                var.set(int(val) if val is not None else 0)
            elif isinstance(var, tk.DoubleVar):
                var.set(float(val) if val is not None else 0.0)
            elif isinstance(var, tk.BooleanVar):
                var.set(bool(val) if val is not None else False)
        except Exception:
            pass

    # ── 工作流运行 ───────────────────────────────────────────

    def run_workflow(self, mode):
        """保存配置并运行指定工作流模式"""
        self.save_config()
        mode_name = self._mode_names.get(mode, mode)
        self.log(f"▶ 开始运行: {mode_name}")
        threading.Thread(target=self._run_workflow_thread, args=(mode,), daemon=True).start()

    def _get_python_exe(self):
        """获取 venv 中 python.exe 的绝对路径"""
        exe = sys.executable
        if not exe:
            # 回退：从当前 venv 路径查找
            exe = str(Path(__file__).parent / ".venv" / "Scripts" / "python.exe")
        elif exe.endswith("pythonw.exe"):
            exe = exe.replace("pythonw.exe", "python.exe")
        # 确保返回绝对路径
        return str(Path(exe).resolve())

    def _run_workflow_thread(self, mode):
        try:
            mode_name = self._mode_names.get(mode, mode)
            self.set_status(f"正在{mode_name}...", "blue")
            python_exe = self._get_python_exe()
            script_dir = Path(__file__).parent.resolve()

            # 显式传入环境变量，确保子进程使用 venv
            env = os.environ.copy()
            env["VIRTUAL_ENV"] = str(script_dir / ".venv")
            env["PATH"] = str(script_dir / ".venv/Scripts") + ";" + env.get("PATH", "")
            # Windows 中文控制台输出为 GBK，先捕获字节再解码
            result = subprocess.run(
                [python_exe, str(script_dir / "character_workflow.py"), mode],
                capture_output=True, cwd=script_dir, env=env
            )
            stdout = result.stdout
            # 尝试 UTF-8 解码，失败则用 GBK
            try:
                text = stdout.decode("utf-8")
            except UnicodeDecodeError:
                text = stdout.decode("gbk", errors="replace")

            if text:
                for line in text.strip().split("\n"):
                    if line.strip():
                        self.log(f"  {line}")

            stderr = result.stderr
            if stderr:
                try:
                    err_text = stderr.decode("utf-8")
                except UnicodeDecodeError:
                    err_text = stderr.decode("gbk", errors="replace")
                if err_text.strip():
                    for line in err_text.strip().split("\n"):
                        if line.strip():
                            self.log(f"  ⚠ {line.strip()}")
            if result.returncode == 0:
                self.log(f"✅ {mode_name} 执行完毕")
                self.set_status("执行完毕", "green")
            else:
                self.log(f"❌ {mode_name} 失败")
                self.set_status("执行失败", "red")
        except Exception as e:
            self.log(f"❌ 运行异常: {e}")
            self.set_status("运行异常", "red")

    def open_output_dir(self):
        path = Path(".")
        try:
            import os
            os.startfile(path.resolve())
        except Exception:
            pass

    def clean_output(self):
        confirm = messagebox.askyesno("确认清理", "确定要清理所有中间文件和输出文件吗？\n此操作不可撤销！")
        if confirm:
            try:
                result = subprocess.run(
                    [sys.executable, "character_workflow.py", "clean"],
                    capture_output=True, text=True, encoding="utf-8", errors="replace"
                )
                if result.stdout:
                    for line in result.stdout.strip().split("\n"):
                        if line.strip():
                            self.log(f"  {line}")
                self.log("✅ 清理完成")
            except Exception as e:
                self.log(f"❌ 清理失败: {e}")

    def show_cache_info(self):
        cache_dir = self.cache_dir_var.get().strip()
        if not cache_dir:
            self.cache_info_label.config(text="未设置缓存目录", foreground="orange")
            return
        p = Path(cache_dir)
        if not p.exists():
            self.cache_info_label.config(text="缓存目录不存在", foreground="orange")
            return
        total = 0
        count = 0
        for f in p.rglob("*"):
            if f.is_file():
                total += f.stat().st_size
                count += 1
        self.cache_info_label.config(
            text=f"📦 {count} 个缓存文件，共 {total/1024/1024:.1f} MB",
            foreground="#333"
        )

    def show_help(self):
        msg = (
            "st_book 配置管理 GUI\n"
            "─────────────────────\n\n"
            "【配置各选项卡说明】\n"
            "  1. 加载小说 — 源文件(.txt)路径和编码\n"
            "  2. API & 模型 — API密钥/URL，提取/生成模型\n"
            "  3. 模型参数 — 温度、Token限制、超时等\n"
            "  4. 网络与性能 — 并发、重试、限流参数\n"
            "  5. 缓存配置 — 缓存开关、目录、过期时间\n"
            "  6. 输出目录 — 各中间产物输出位置\n\n"
            "【使用流程】\n"
            "  ① 填写 API 密钥和模型配置\n"
            "  ② 选择源文件 (.txt)\n"
            "  ③ 调整参数（可使用默认值）\n"
            "  ④ 点击「保存配置」\n"
            "  ⑤ 点击工作流按钮运行\n\n"
            "【注意】\n"
            "  - 配置保存在 config.yaml，首次使用会自动从 config_template.yaml 复制\n"
            "  - 修改后点击「保存配置」即可生效"
        )
        messagebox.showinfo("帮助", msg)


def main():
    if not HAVE_RUAMEL and yaml is None:
        print("❌ 需要 PyYAML 或 ruamel.yaml: pip install pyyaml")
        sys.exit(1)

    root = tk.Tk()
    app = ConfigGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
