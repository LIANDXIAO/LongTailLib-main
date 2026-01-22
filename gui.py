import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import os
import sys


class LongTailLibGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LongTailLib 联邦长尾学习评测平台控制台")
        self.root.geometry("900x700")

        # 样式设置
        style = ttk.Style()
        style.theme_use('clam')

        # 主框架
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 选项卡控件
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # --- 选项卡 1: 数据集生成 ---
        self.tab_dataset = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_dataset, text=" 1. 数据集生成 (Dataset) ")
        self._init_dataset_tab()

        # --- 选项卡 2: 算法训练 ---
        self.tab_train = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_train, text=" 2. 算法训练 (Training) ")
        self._init_train_tab()

        # --- 底部: 日志输出 ---
        log_labelframe = ttk.LabelFrame(main_frame, text="控制台日志 (Console Log)")
        log_labelframe.pack(fill=tk.BOTH, expand=True, pady=10)

        self.log_text = scrolledtext.ScrolledText(log_labelframe, height=15, state='disabled', bg="#1e1e1e",
                                                  fg="#00ff00", font=("Consolas", 10))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def _run_command(self, cmd, cwd=None):
        """在独立线程中运行命令，防止界面卡死 (已修复编码问题)"""

        def target():
            self._log(f">>> 开始执行: {' '.join(cmd)}")
            try:
                # 核心修复：
                # 1. 显式指定 encoding='utf-8' 以匹配 Python 脚本输出
                # 2. 添加 errors='replace'，遇到无法识别的乱码直接替换为 '?'，防止报错奔溃
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    cwd=cwd,
                    bufsize=1,
                    text=True,  # 保持文本模式
                    encoding='utf-8',  # 优先尝试 UTF-8
                    errors='replace'  # 遇到乱码直接替换，绝不报错
                )

                # 逐行读取输出
                for line in process.stdout:
                    self.log_text.config(state='normal')
                    self.log_text.insert(tk.END, line)
                    self.log_text.see(tk.END)
                    self.log_text.config(state='disabled')

                process.wait()
                if process.returncode == 0:
                    self._log(">>> 执行成功完成。")
                    # 如果是生成数据集，刷新训练页面的数据集列表
                    if "generate" in cmd[1]:
                        self.root.after(0, self._refresh_dataset_list)
                else:
                    self._log(f">>> 执行出错，返回码: {process.returncode}")
            except Exception as e:
                self._log(f">>> 发生系统错误: {str(e)}")

        threading.Thread(target=target, daemon=True).start()

    # ================= 数据集生成界面 =================
    def _init_dataset_tab(self):
        frame = ttk.Frame(self.tab_dataset, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        grid_opts = {'padx': 5, 'pady': 10, 'sticky': 'w'}

        # 1. IID 设置
        ttk.Label(frame, text="分布类型 (Distribution):").grid(row=0, column=0, **grid_opts)
        self.ds_niid = tk.StringVar(value="noniid")
        ttk.Combobox(frame, textvariable=self.ds_niid, values=["noniid", "iid"], state="readonly", width=10).grid(row=0,
                                                                                                                  column=1,
                                                                                                                  **grid_opts)

        # 2. 数量平衡
        ttk.Label(frame, text="数据量平衡 (Balance):").grid(row=0, column=2, **grid_opts)
        self.ds_balance = tk.StringVar(value="-")  # 对应 '-' (不平衡) 或 'balance'
        ttk.Combobox(frame, textvariable=self.ds_balance, values=["-", "balance"], state="readonly", width=10).grid(
            row=0, column=3, **grid_opts)

        # 3. 划分方式
        ttk.Label(frame, text="划分策略 (Partition):").grid(row=1, column=0, **grid_opts)
        self.ds_partition = tk.StringVar(value="dir")
        ttk.Combobox(frame, textvariable=self.ds_partition, values=["dir", "pat", "exdir"], state="readonly",
                     width=10).grid(row=1, column=1, **grid_opts)

        # 4. 长尾设置
        ttk.Label(frame, text="启用长尾 (Longtail):").grid(row=1, column=2, **grid_opts)
        self.ds_longtail = tk.StringVar(value="longtail")
        ttk.Checkbutton(frame, text="启用", variable=self.ds_longtail, onvalue="longtail", offvalue="normal").grid(
            row=1, column=3, **grid_opts)

        # 5. 长尾类型
        ttk.Label(frame, text="长尾类型 (Type):").grid(row=2, column=0, **grid_opts)
        self.ds_type = tk.StringVar(value="global")
        ttk.Combobox(frame, textvariable=self.ds_type, values=["global", "local"], state="readonly", width=10).grid(
            row=2, column=1, **grid_opts)

        # 6. 不平衡因子 IF
        ttk.Label(frame, text="不平衡因子 (IF):").grid(row=2, column=2, **grid_opts)
        self.ds_if = tk.StringVar(value="50")
        ttk.Entry(frame, textvariable=self.ds_if, width=12).grid(row=2, column=3, **grid_opts)

        # 7. Alpha
        ttk.Label(frame, text="Dirichlet Alpha:").grid(row=3, column=0, **grid_opts)
        self.ds_alpha = tk.StringVar(value="0.5")
        ttk.Entry(frame, textvariable=self.ds_alpha, width=12).grid(row=3, column=1, **grid_opts)

        # 8. 客户端数量
        ttk.Label(frame, text="客户端数量 (Num Clients):").grid(row=3, column=2, **grid_opts)
        self.ds_clients = tk.StringVar(value="20")
        ttk.Entry(frame, textvariable=self.ds_clients, width=12).grid(row=3, column=3, **grid_opts)

        # 说明
        info_lbl = ttk.Label(frame,
                             text="说明: 将调用 dataset/generate_Cifar10.py (若无数据请先手动下载CIFAR-10到rawdata)",
                             foreground="gray")
        info_lbl.grid(row=4, column=0, columnspan=4, pady=20)

        # 生成按钮
        btn = ttk.Button(frame, text="生成数据集 (Generate Dataset)", command=self._on_generate_click)
        btn.grid(row=5, column=0, columnspan=4, ipadx=20, ipady=5)

    def _on_generate_click(self):
        script = os.path.join("dataset", "generate_Cifar10.py")
        if not os.path.exists(script):
            messagebox.showerror("错误", f"找不到文件: {script}\n请确保 gui.py 在项目根目录运行。")
            return

        cmd = [
            sys.executable,
            script,
            self.ds_niid.get(),  # 1: noniid
            self.ds_balance.get(),  # 2: balance / -
            self.ds_partition.get()  # 3: dir
        ]

        if self.ds_longtail.get() == "longtail":
            cmd.append("longtail")  # 4
            cmd.append(self.ds_type.get())  # 5: global
            cmd.append(self.ds_if.get())  # 6: IF
        else:
            pass

        cmd.append(self.ds_alpha.get())  # 7
        cmd.append(self.ds_clients.get())  # 8

        self._run_command(cmd)

    # ================= 算法训练界面 =================
    def _init_train_tab(self):
        frame = ttk.Frame(self.tab_train, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        grid_opts = {'padx': 5, 'pady': 10, 'sticky': 'w'}

        # 1. 选择数据集 (自动扫描)
        ttk.Label(frame, text="选择数据集 (Dataset):").grid(row=0, column=0, **grid_opts)
        self.tr_dataset = tk.StringVar()
        self.combo_dataset = ttk.Combobox(frame, textvariable=self.tr_dataset, width=40)
        self.combo_dataset.grid(row=0, column=1, columnspan=3, **grid_opts)

        # 刷新按钮
        ttk.Button(frame, text="刷新列表", command=self._refresh_dataset_list).grid(row=0, column=4, padx=5)

        # 2. 算法选择
        ttk.Label(frame, text="算法 (Algorithm):").grid(row=1, column=0, **grid_opts)
        self.tr_algo = tk.StringVar(value="CReFF")
        algos = ["CReFF", "CLIP2FL", "CCVR", "RUCR", "FedETF", "FedLoGe", "FedNH", "FedIC", "FedGraB", "FedAvg",
                 "FedProx"]
        ttk.Combobox(frame, textvariable=self.tr_algo, values=algos, state="readonly", width=15).grid(row=1, column=1,
                                                                                                      **grid_opts)

        # 3. 模型选择
        ttk.Label(frame, text="模型 (Model):").grid(row=1, column=2, **grid_opts)
        self.tr_model = tk.StringVar(value="ResNet8")
        models = ["ResNet8", "ResNet18", "ResNet20", "ResNet34", "CNN", "MobileNet"]
        ttk.Combobox(frame, textvariable=self.tr_model, values=models, width=15).grid(row=1, column=3, **grid_opts)

        # 4. 全局轮数
        ttk.Label(frame, text="全局轮数 (Global Rounds):").grid(row=2, column=0, **grid_opts)
        self.tr_gr = tk.StringVar(value="200")
        ttk.Entry(frame, textvariable=self.tr_gr, width=10).grid(row=2, column=1, **grid_opts)

        # 5. GPU ID
        ttk.Label(frame, text="GPU 设备 ID (-did):").grid(row=2, column=2, **grid_opts)
        self.tr_did = tk.StringVar(value="0")
        ttk.Entry(frame, textvariable=self.tr_did, width=10).grid(row=2, column=3, **grid_opts)

        # 运行按钮
        btn = ttk.Button(frame, text="开始训练 (Start Training)", command=self._on_train_click)
        btn.grid(row=3, column=0, columnspan=5, ipadx=20, ipady=10, pady=20)

        # 初始化时加载一次数据集
        self._refresh_dataset_list()

    def _refresh_dataset_list(self):
        """扫描 dataset/ 目录下生成的文件夹"""
        ds_path = os.path.join("dataset")
        if os.path.exists(ds_path):
            dirs = [d for d in os.listdir(ds_path) if
                    os.path.isdir(os.path.join(ds_path, d)) and (d.startswith("Cifar") or d.startswith("MNIST"))]
            self.combo_dataset['values'] = sorted(dirs)
            if dirs:
                self.combo_dataset.current(0)
            else:
                self.tr_dataset.set("未找到数据集，请先生成")
        else:
            self.tr_dataset.set("dataset 目录不存在")

    def _on_train_click(self):
        # 修复：因为我们下面会将工作目录(cwd)切换到 system/
        # 所以脚本名称只需要 "main.py"，不需要再加 "system/" 前缀
        script = "main.py"

        # 检查文件是否存在 (拼接完整路径进行检查)
        # 这里的检查路径是：当前路径/system/main.py
        check_path = os.path.join(os.getcwd(), "system", script)
        if not os.path.exists(check_path):
            messagebox.showerror("错误", f"找不到文件: {check_path}\n请确认您的目录结构正确。")
            return

        dataset_name = self.tr_dataset.get()
        if not dataset_name or "未找到" in dataset_name:
            messagebox.showwarning("警告", "请先选择一个有效的数据集")
            return

        cmd = [
            sys.executable,
            script,  # 这里只传 "main.py"
            "-data", dataset_name,
            "-algo", self.tr_algo.get(),
            "-m", self.tr_model.get(),
            "-gr", self.tr_gr.get(),
            "-did", self.tr_did.get()
        ]

        # 设置工作目录为 system 文件夹
        cwd_path = os.path.join(os.getcwd(), "system")

        self._run_command(cmd, cwd=cwd_path)


if __name__ == "__main__":
    root = tk.Tk()
    app = LongTailLibGUI(root)
    root.mainloop()
