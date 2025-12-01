import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import paddle
from paddleocr import PaddleOCR
import threading
import os  # ← 修复：添加缺失的导入

class PaddleOCR_GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PaddleOCR 3.x - 图形识别工具")
        self.root.geometry("1200x700")
        
        # 初始化 OCR
        self.ocr = None
        self.current_image_path = None
        self.init_ocr()
        
        # 创建主布局
        self.create_widgets()
        
    def init_ocr(self):
        """初始化 PaddleOCR"""
        try:
            self.ocr = PaddleOCR(
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False
            )
            print("✅ OCR 初始化成功！")
        except Exception as e:
            messagebox.showerror("初始化失败", f"OCR 初始化失败: {e}")
            
    def create_widgets(self):
        """创建 GUI 组件"""
        # 顶部工具栏
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="打开图片", command=self.open_image, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="开始识别", command=self.start_ocr, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="清空结果", command=self.clear_results, width=12).pack(side=tk.LEFT, padx=2)
        
        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(toolbar, textvariable=self.status_var).pack(side=tk.RIGHT, padx=10)
        
        # 进度条
        self.progress = ttk.Progressbar(toolbar, mode='indeterminate', length=200)
        self.progress.pack(side=tk.RIGHT, padx=10)
        
        # 主布局
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧图片显示区
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text="图片预览:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, padx=5, pady=2)
        
        self.canvas = tk.Canvas(left_frame, bg='#f0f0f0', width=600)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 右侧结果显示区
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)
        
        ttk.Label(right_frame, text="识别结果:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, padx=5, pady=2)
        
        text_frame = ttk.Frame(right_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.text_result = scrolledtext.ScrolledText(
            text_frame, 
            wrap=tk.WORD, 
            font=('Consolas', 11),
            bg='#fafafa',
            fg='#333'
        )
        self.text_result.pack(fill=tk.BOTH, expand=True)
        
        # 底部信息栏
        info_frame = ttk.LabelFrame(self.root, text="系统信息", padding=5)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        info_text = (
            f"PaddlePaddle 版本: {paddle.__version__}  |  "
            f"CUDA 可用: {paddle.is_compiled_with_cuda()}  |  "
            f"OCR 版本: 3.x  |  "
            f"模型: PP-OCRv5"
        )
        ttk.Label(info_frame, text=info_text, foreground='#0055aa', font=('Arial', 9)).pack(anchor=tk.W)
        
    def open_image(self):
        """打开图片文件"""
        file_path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.bmp *.tiff"),
                ("所有文件", "*.*")
            ],
            initialdir=r"D:\Backup\Downloads"
        )
        
        if file_path:
            self.current_image_path = file_path
            self.display_image(file_path)
            self.status_var.set(f"✅ 已加载: {os.path.basename(file_path)}")
            
    def display_image(self, image_path):
        """在画布上显示图片"""
        try:
            image = Image.open(image_path)
            canvas_width = self.canvas.winfo_width() or 600
            canvas_height = self.canvas.winfo_height() or 500
                
            img_ratio = image.width / image.height
            canvas_ratio = canvas_width / canvas_height
            
            if img_ratio > canvas_ratio:
                new_width = canvas_width
                new_height = int(canvas_width / img_ratio)
            else:
                new_height = canvas_height
                new_width = int(canvas_height * img_ratio)
                
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(image)
            
            self.canvas.delete("all")
            self.canvas.create_image(
                canvas_width//2, canvas_height//2,
                image=self.photo,
                anchor=tk.CENTER
            )
            
        except Exception as e:
            messagebox.showerror("图片加载失败", f"无法加载图片: {e}")
            
    def start_ocr(self):
        """开始 OCR 识别"""
        if not self.current_image_path:
            messagebox.showwarning("警告", "请先打开一张图片！")
            return
            
        if not self.ocr:
            messagebox.showerror("错误", "OCR 未初始化！")
            return
            
        # 启动进度条
        self.progress.start(10)
        self.status_var.set("⏳ 正在识别...")
        self.text_result.delete(1.0, tk.END)
        self.text_result.insert(tk.END, "识别中，请稍候...\n")
        
        # 后台线程运行 OCR
        thread = threading.Thread(target=self.run_ocr)
        thread.daemon = True
        thread.start()
        
    def run_ocr(self):
        """执行 OCR 识别（后台线程）"""
        try:
            results = list(self.ocr.predict(input=self.current_image_path))
            self.root.after(0, self.display_ocr_results, results)
            
        except Exception as e:
            error_msg = f"识别失败: {e}"
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
            self.root.after(0, self.stop_progress)
            
    def stop_progress(self):
        """停止进度条"""
        self.progress.stop()
        self.status_var.set("就绪")
            
    def display_ocr_results(self, results):
        """显示 OCR 结果"""
        self.text_result.delete(1.0, tk.END)
        self.progress.stop()
        
        if not results:
            self.status_var.set("❌ 未识别到任何内容")
            self.text_result.insert(tk.END, "未识别到文本，请检查图片质量。\n")
            return
        
        all_text = []
        
        # 正确解析 PaddleOCR 3.x 结果
        for idx, res in enumerate(results):
            self.text_result.insert(tk.END, f"\n{'='*60}\n", 'header')
            self.text_result.insert(tk.END, f"识别区域 {idx + 1}:\n", 'header')
            self.text_result.insert(tk.END, f"{'='*60}\n\n", 'header')
            
            # 关键：使用正确的键名 rec_texts（复数）
            texts = []
            scores = []
            polys = []
            
            if isinstance(res, dict):
                texts = res.get('rec_texts', [])  # ← 正确键名
                scores = res.get('rec_scores', [])
                polys = res.get('rec_polys', [])
            
            # 显示结果
            if texts and len(texts) > 0:
                for i, text in enumerate(texts):
                    if text and text.strip():
                        all_text.append(text)
                        self.text_result.insert(tk.END, f"【文本 {i+1}】 {text}\n", 'text')
                        
                        # 显示置信度
                        if i < len(scores):
                            self.text_result.insert(tk.END, f"  置信度: {scores[i]:.4f}\n", 'info')
                        
                        # 显示坐标
                        if i < len(polys):
                            poly = polys[i]
                            if hasattr(poly, 'tolist'):
                                poly = poly.tolist()
                            self.text_result.insert(tk.END, f"  坐标: {poly}\n", 'info')
                        
                        self.text_result.insert(tk.END, "\n")
            else:
                self.text_result.insert(tk.END, "  (未识别到文本)\n", 'warning')
        
        # 纯文本汇总
        self.text_result.insert(tk.END, f"\n{'='*60}\n", 'header')
        self.text_result.insert(tk.END, "【纯文本汇总】\n", 'header')
        self.text_result.insert(tk.END, f"{'='*60}\n\n", 'header')
        
        if all_text:
            self.text_result.insert(tk.END, "\n".join(all_text))
            self.status_var.set(f"✅ 识别完成！共 {len(all_text)} 行文本")
        else:
            self.text_result.insert(tk.END, "⚠️ 识别完成，但未提取到有效文本", 'warning')
            self.status_var.set("⚠️ 结果为空")
        
        self.text_result.see(1.0)
        
    def clear_results(self):
        """清空结果显示"""
        self.text_result.delete(1.0, tk.END)
        self.canvas.delete("all")
        self.current_image_path = None
        self.status_var.set("就绪")
        self.progress.stop()
        self.text_result.insert(tk.END, "等待图片...\n")

def main():
    root = tk.Tk()
    app = PaddleOCR_GUI(root)
    
    # 设置文本样式
    app.text_result.tag_configure('header', font=('Arial', 10, 'bold'), foreground='#0055aa')
    app.text_result.tag_configure('text', font=('Consolas', 11), foreground='#000000')
    app.text_result.tag_configure('info', font=('Consolas', 9), foreground='#666666')
    app.text_result.tag_configure('warning', font=('Arial', 10, 'bold'), foreground='#ff6600')
    
    root.mainloop()

if __name__ == "__main__":
    main()