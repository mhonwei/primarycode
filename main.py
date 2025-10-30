"""
健康内容网络爬虫系统 - 主程序
支持 Windows 图形界面
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import logging
from typing import List
import webbrowser
import os

from scraper import HealthContentScraper, CustomSourceScraper
from data_manager import DataManager, URLManager
import config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthScraperGUI:
    """健康内容爬虫图形界面"""

    def __init__(self, root):
        self.root = root
        self.root.title("健康内容网络爬虫系统")
        self.root.geometry("1000x700")

        # 初始化组件
        self.scraper = HealthContentScraper()
        self.custom_scraper = CustomSourceScraper()
        self.data_manager = DataManager()
        self.url_manager = URLManager()

        # 数据存储
        self.scraped_data = []
        self.is_scraping = False

        # 创建界面
        self.create_widgets()

        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        """创建GUI组件"""

        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

        # 标题
        title_label = ttk.Label(
            main_frame,
            text="健康内容网络爬虫系统",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, pady=10)

        # 创建选项卡
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # 标签1: 快速抓取
        quick_frame = ttk.Frame(notebook, padding="10")
        notebook.add(quick_frame, text="快速抓取")
        self.create_quick_scrape_tab(quick_frame)

        # 标签2: 自定义抓取
        custom_frame = ttk.Frame(notebook, padding="10")
        notebook.add(custom_frame, text="自定义抓取")
        self.create_custom_scrape_tab(custom_frame)

        # 标签3: 学术搜索
        academic_frame = ttk.Frame(notebook, padding="10")
        notebook.add(academic_frame, text="学术搜索")
        self.create_academic_search_tab(academic_frame)

        # 标签4: 数据管理
        data_frame = ttk.Frame(notebook, padding="10")
        notebook.add(data_frame, text="数据管理")
        self.create_data_management_tab(data_frame)

        # 进度条
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(progress_frame, text="进度:").pack(side=tk.LEFT, padx=5)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=400
        )
        self.progress_bar.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        self.progress_label = ttk.Label(progress_frame, text="就绪")
        self.progress_label.pack(side=tk.LEFT, padx=5)

        # 日志显示区域
        log_frame = ttk.LabelFrame(main_frame, text="日志输出", padding="5")
        log_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=10,
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 控制按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, pady=5)

        self.clear_log_btn = ttk.Button(
            button_frame,
            text="清空日志",
            command=self.clear_log
        )
        self.clear_log_btn.pack(side=tk.LEFT, padx=5)

        self.open_output_btn = ttk.Button(
            button_frame,
            text="打开输出文件夹",
            command=self.open_output_folder
        )
        self.open_output_btn.pack(side=tk.LEFT, padx=5)

    def create_quick_scrape_tab(self, parent):
        """创建快速抓取标签页"""

        # 说明文字
        info_label = ttk.Label(
            parent,
            text="选择要抓取的内容类型，系统将自动搜索相关内容",
            font=("Arial", 10)
        )
        info_label.grid(row=0, column=0, columnspan=2, pady=10)

        # 分类选择
        category_frame = ttk.LabelFrame(parent, text="内容分类", padding="10")
        category_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        self.category_vars = {}
        categories = list(config.CONTENT_CATEGORIES.keys())

        for i, category in enumerate(categories):
            var = tk.BooleanVar()
            self.category_vars[category] = var
            chk = ttk.Checkbutton(
                category_frame,
                text=category,
                variable=var
            )
            chk.grid(row=i // 3, column=i % 3, sticky=tk.W, padx=10, pady=5)

        # 抓取数量
        count_frame = ttk.Frame(parent)
        count_frame.grid(row=2, column=0, columnspan=2, pady=10)

        ttk.Label(count_frame, text="每个分类抓取数量:").pack(side=tk.LEFT, padx=5)
        self.count_var = tk.StringVar(value="10")
        count_spinbox = ttk.Spinbox(
            count_frame,
            from_=1,
            to=100,
            textvariable=self.count_var,
            width=10
        )
        count_spinbox.pack(side=tk.LEFT, padx=5)

        # 开始按钮
        self.quick_start_btn = ttk.Button(
            parent,
            text="开始抓取",
            command=self.start_quick_scrape,
            style="Accent.TButton"
        )
        self.quick_start_btn.grid(row=3, column=0, columnspan=2, pady=20)

    def create_custom_scrape_tab(self, parent):
        """创建自定义抓取标签页"""

        # 说明
        info_label = ttk.Label(
            parent,
            text="输入要抓取的URL列表（每行一个URL）",
            font=("Arial", 10)
        )
        info_label.grid(row=0, column=0, columnspan=2, pady=10)

        # 分类选择
        category_frame = ttk.Frame(parent)
        category_frame.grid(row=1, column=0, columnspan=2, pady=5)

        ttk.Label(category_frame, text="内容分类:").pack(side=tk.LEFT, padx=5)
        self.custom_category_var = tk.StringVar()
        category_combo = ttk.Combobox(
            category_frame,
            textvariable=self.custom_category_var,
            values=list(config.CONTENT_CATEGORIES.keys()) + ["自定义"],
            width=20
        )
        category_combo.pack(side=tk.LEFT, padx=5)
        category_combo.current(0)

        # URL输入区域
        url_frame = ttk.LabelFrame(parent, text="URL列表", padding="5")
        url_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        url_frame.columnconfigure(0, weight=1)
        url_frame.rowconfigure(0, weight=1)

        self.url_text = scrolledtext.ScrolledText(
            url_frame,
            height=15,
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.url_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 按钮框架
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        self.import_urls_btn = ttk.Button(
            button_frame,
            text="从文件导入",
            command=self.import_urls
        )
        self.import_urls_btn.pack(side=tk.LEFT, padx=5)

        self.custom_start_btn = ttk.Button(
            button_frame,
            text="开始抓取",
            command=self.start_custom_scrape,
            style="Accent.TButton"
        )
        self.custom_start_btn.pack(side=tk.LEFT, padx=5)

        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(2, weight=1)

    def create_academic_search_tab(self, parent):
        """创建学术搜索标签页"""

        # 说明
        info_label = ttk.Label(
            parent,
            text="搜索 PubMed 等学术数据库中的健康相关研究论文",
            font=("Arial", 10)
        )
        info_label.grid(row=0, column=0, columnspan=2, pady=10)

        # 搜索关键词
        keyword_frame = ttk.Frame(parent)
        keyword_frame.grid(row=1, column=0, columnspan=2, pady=10)

        ttk.Label(keyword_frame, text="搜索关键词:").pack(side=tk.LEFT, padx=5)
        self.keyword_var = tk.StringVar()
        keyword_entry = ttk.Entry(
            keyword_frame,
            textvariable=self.keyword_var,
            width=40
        )
        keyword_entry.pack(side=tk.LEFT, padx=5)

        # 结果数量
        count_frame = ttk.Frame(parent)
        count_frame.grid(row=2, column=0, columnspan=2, pady=10)

        ttk.Label(count_frame, text="结果数量:").pack(side=tk.LEFT, padx=5)
        self.academic_count_var = tk.StringVar(value="10")
        count_spinbox = ttk.Spinbox(
            count_frame,
            from_=1,
            to=50,
            textvariable=self.academic_count_var,
            width=10
        )
        count_spinbox.pack(side=tk.LEFT, padx=5)

        # 搜索按钮
        self.academic_search_btn = ttk.Button(
            parent,
            text="开始搜索",
            command=self.start_academic_search,
            style="Accent.TButton"
        )
        self.academic_search_btn.grid(row=3, column=0, columnspan=2, pady=20)

        # 示例关键词
        examples_frame = ttk.LabelFrame(parent, text="示例关键词", padding="10")
        examples_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        examples = [
            "diabetes prevention",
            "nutrition and health",
            "cardiovascular disease",
            "mental health treatment",
            "cancer prevention"
        ]

        for i, example in enumerate(examples):
            btn = ttk.Button(
                examples_frame,
                text=example,
                command=lambda e=example: self.keyword_var.set(e)
            )
            btn.grid(row=i // 2, column=i % 2, padx=5, pady=3, sticky=tk.W)

    def create_data_management_tab(self, parent):
        """创建数据管理标签页"""

        # 统计信息
        stats_frame = ttk.LabelFrame(parent, text="数据统计", padding="10")
        stats_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        self.stats_text = tk.Text(stats_frame, height=8, wrap=tk.WORD, font=("Consolas", 9))
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        self.update_statistics()

        # 导出选项
        export_frame = ttk.LabelFrame(parent, text="导出数据", padding="10")
        export_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        self.export_format_var = tk.StringVar(value="所有格式")
        formats = ["所有格式", "JSON", "CSV", "Excel", "TXT"]

        for i, fmt in enumerate(formats):
            rb = ttk.Radiobutton(
                export_frame,
                text=fmt,
                value=fmt,
                variable=self.export_format_var
            )
            rb.grid(row=0, column=i, padx=10, pady=5)

        # 导出按钮
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)

        self.export_btn = ttk.Button(
            button_frame,
            text="导出数据",
            command=self.export_data,
            style="Accent.TButton"
        )
        self.export_btn.pack(side=tk.LEFT, padx=5)

        self.clear_data_btn = ttk.Button(
            button_frame,
            text="清空当前数据",
            command=self.clear_data
        )
        self.clear_data_btn.pack(side=tk.LEFT, padx=5)

        self.refresh_stats_btn = ttk.Button(
            button_frame,
            text="刷新统计",
            command=self.update_statistics
        )
        self.refresh_stats_btn.pack(side=tk.LEFT, padx=5)

    def log(self, message: str):
        """在日志区域显示消息"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)

    def update_progress(self, value: float, message: str = ""):
        """更新进度条"""
        self.progress_var.set(value)
        if message:
            self.progress_label.config(text=message)
        self.root.update_idletasks()

    def start_quick_scrape(self):
        """开始快速抓取"""
        if self.is_scraping:
            messagebox.showwarning("警告", "抓取任务正在进行中，请稍候...")
            return

        # 获取选中的分类
        selected_categories = [
            cat for cat, var in self.category_vars.items() if var.get()
        ]

        if not selected_categories:
            messagebox.showwarning("警告", "请至少选择一个内容分类")
            return

        count = int(self.count_var.get())

        # 在新线程中执行抓取
        thread = threading.Thread(
            target=self._quick_scrape_thread,
            args=(selected_categories, count)
        )
        thread.daemon = True
        thread.start()

    def _quick_scrape_thread(self, categories: List[str], count: int):
        """快速抓取线程"""
        self.is_scraping = True
        self.log(f"开始快速抓取，分类: {', '.join(categories)}, 每个分类 {count} 条")

        try:
            total_categories = len(categories)

            for i, category in enumerate(categories):
                self.log(f"\n正在抓取分类: {category}")

                # 这里可以实现具体的抓取逻辑
                # 示例：从配置的源抓取
                category_config = config.CONTENT_CATEGORIES.get(category, {})
                sources = category_config.get('sources', [])

                if sources:
                    # 抓取每个源的第一个页面作为示例
                    for source in sources[:count]:
                        article = self.scraper.scrape_url(source, category)
                        if article:
                            self.scraped_data.append(article)
                            self.log(f"✓ 成功抓取: {article['title'][:50]}...")

                # 更新进度
                progress = ((i + 1) / total_categories) * 100
                self.update_progress(progress, f"已完成 {i + 1}/{total_categories} 个分类")

            self.log(f"\n快速抓取完成！共抓取 {len(self.scraped_data)} 篇文章")
            self.update_statistics()
            messagebox.showinfo("完成", f"抓取完成！共获取 {len(self.scraped_data)} 篇文章")

        except Exception as e:
            logger.error(f"抓取过程出错: {e}")
            self.log(f"错误: {e}")
            messagebox.showerror("错误", f"抓取过程出错: {e}")

        finally:
            self.is_scraping = False
            self.update_progress(0, "就绪")

    def start_custom_scrape(self):
        """开始自定义抓取"""
        if self.is_scraping:
            messagebox.showwarning("警告", "抓取任务正在进行中，请稍候...")
            return

        # 获取URL列表
        urls_text = self.url_text.get(1.0, tk.END).strip()
        if not urls_text:
            messagebox.showwarning("警告", "请输入至少一个URL")
            return

        urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
        category = self.custom_category_var.get()

        # 在新线程中执行抓取
        thread = threading.Thread(
            target=self._custom_scrape_thread,
            args=(urls, category)
        )
        thread.daemon = True
        thread.start()

    def _custom_scrape_thread(self, urls: List[str], category: str):
        """自定义抓取线程"""
        self.is_scraping = True
        self.log(f"开始自定义抓取，URL 数量: {len(urls)}, 分类: {category}")

        try:
            articles = self.custom_scraper.scrape_custom_urls(
                urls,
                category,
                progress_callback=lambda p, m: self.update_progress(p, m)
            )

            self.scraped_data.extend(articles)
            self.log(f"\n自定义抓取完成！共抓取 {len(articles)} 篇文章")
            self.update_statistics()
            messagebox.showinfo("完成", f"抓取完成！共获取 {len(articles)} 篇文章")

        except Exception as e:
            logger.error(f"抓取过程出错: {e}")
            self.log(f"错误: {e}")
            messagebox.showerror("错误", f"抓取过程出错: {e}")

        finally:
            self.is_scraping = False
            self.update_progress(0, "就绪")

    def start_academic_search(self):
        """开始学术搜索"""
        if self.is_scraping:
            messagebox.showwarning("警告", "抓取任务正在进行中，请稍候...")
            return

        keyword = self.keyword_var.get().strip()
        if not keyword:
            messagebox.showwarning("警告", "请输入搜索关键词")
            return

        count = int(self.academic_count_var.get())

        # 在新线程中执行搜索
        thread = threading.Thread(
            target=self._academic_search_thread,
            args=(keyword, count)
        )
        thread.daemon = True
        thread.start()

    def _academic_search_thread(self, keyword: str, count: int):
        """学术搜索线程"""
        self.is_scraping = True
        self.log(f"开始搜索 PubMed，关键词: {keyword}, 结果数量: {count}")

        try:
            self.update_progress(30, "正在搜索...")
            articles = self.scraper.search_pubmed(keyword, count)

            if articles:
                # 获取详细信息
                total = len(articles)
                for i, article_info in enumerate(articles):
                    url = article_info['url']
                    article = self.scraper.scrape_url(url, '学术论文')
                    if article:
                        self.scraped_data.append(article)
                        self.log(f"✓ 成功抓取: {article['title'][:50]}...")

                    progress = 30 + ((i + 1) / total) * 70
                    self.update_progress(progress, f"已完成 {i + 1}/{total}")

            self.log(f"\n学术搜索完成！共找到 {len(articles)} 篇文章")
            self.update_statistics()
            messagebox.showinfo("完成", f"搜索完成！共找到 {len(articles)} 篇文章")

        except Exception as e:
            logger.error(f"搜索过程出错: {e}")
            self.log(f"错误: {e}")
            messagebox.showerror("错误", f"搜索过程出错: {e}")

        finally:
            self.is_scraping = False
            self.update_progress(0, "就绪")

    def import_urls(self):
        """从文件导入URL"""
        filename = filedialog.askopenfilename(
            title="选择URL文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    urls = f.read()
                self.url_text.delete(1.0, tk.END)
                self.url_text.insert(1.0, urls)
                self.log(f"已从文件导入 URL: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"读取文件失败: {e}")

    def export_data(self):
        """导出数据"""
        if not self.scraped_data:
            messagebox.showwarning("警告", "没有可导出的数据")
            return

        export_format = self.export_format_var.get()

        try:
            if export_format == "所有格式":
                results = self.data_manager.save_to_all_formats(self.scraped_data)
                message = "数据已导出到以下文件:\n" + "\n".join(results.values())
            elif export_format == "JSON":
                filepath = self.data_manager.save_to_json(self.scraped_data)
                message = f"数据已导出到: {filepath}"
            elif export_format == "CSV":
                filepath = self.data_manager.save_to_csv(self.scraped_data)
                message = f"数据已导出到: {filepath}"
            elif export_format == "Excel":
                filepath = self.data_manager.save_to_excel(self.scraped_data)
                message = f"数据已导出到: {filepath}"
            elif export_format == "TXT":
                filepath = self.data_manager.save_to_txt(self.scraped_data)
                message = f"数据已导出到: {filepath}"

            self.log(message)
            messagebox.showinfo("成功", message)

        except Exception as e:
            logger.error(f"导出数据失败: {e}")
            messagebox.showerror("错误", f"导出数据失败: {e}")

    def clear_data(self):
        """清空当前数据"""
        if messagebox.askyesno("确认", "确定要清空当前所有数据吗？"):
            self.scraped_data = []
            self.update_statistics()
            self.log("已清空所有数据")

    def update_statistics(self):
        """更新统计信息"""
        stats = self.data_manager.get_statistics(self.scraped_data)

        stats_text = f"""
数据统计信息
{'=' * 50}
总文章数: {stats['total_articles']}
总字数: {stats['total_words']:,}
平均字数: {stats['average_words']:,}

分类统计:
"""
        for category, count in stats.get('categories', {}).items():
            stats_text += f"  - {category}: {count} 篇\n"

        if stats.get('sources'):
            stats_text += f"\n数据源数量: {stats['unique_sources']}\n"

        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)

    def open_output_folder(self):
        """打开输出文件夹"""
        output_dir = config.EXPORT_CONFIG['output_dir']
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 在不同操作系统中打开文件夹
        if os.name == 'nt':  # Windows
            os.startfile(output_dir)
        elif os.name == 'posix':  # macOS 和 Linux
            import subprocess
            subprocess.Popen(['xdg-open', output_dir])

    def on_closing(self):
        """窗口关闭事件"""
        if self.is_scraping:
            if messagebox.askokcancel("退出", "抓取任务正在进行中，确定要退出吗？"):
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    """主函数"""
    root = tk.Tk()

    # 设置主题（可选）
    try:
        style = ttk.Style()
        # 设置一些样式
        style.configure("Accent.TButton", foreground="blue", font=("Arial", 10, "bold"))
    except:
        pass

    app = HealthScraperGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
