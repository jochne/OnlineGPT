# search_app.py
import sys
import logging
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QTextEdit, QVBoxLayout,
    QHBoxLayout, QMessageBox, QFileDialog, QProgressBar, QTableWidget,
    QTableWidgetItem, QGroupBox, QHeaderView, QSpinBox, QComboBox, QCheckBox,
    QGridLayout, QSplitter, QShortcut, QFrame
)
from PyQt5.QtCore import Qt, QThread, QUrl
from PyQt5.QtGui import QFont, QIcon, QDesktopServices, QKeySequence
from datetime import datetime
from worker import Worker
from gui_components import GuiLogHandler, MyLineEdit, MyTextEdit, CheckBoxHeader, CenteredCheckBoxDelegate
from utils import save_results_to_txt, generate_txt_content
import os


class SearchApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.thread = None  # 初始化线程为None
        self.saved_file = None  # 初始化保存文件路径为None
        self.all_results = []  # 存储所有结果
        self.current_content = ""  # 存储当前内容

    def init_ui(self):
        """
        初始化用户界面。
        """
        # 设置窗口属性
        self.setWindowTitle("OnlineGPT 6.1")
        self.setWindowIcon(QIcon('logo.png'))  # 添加窗口图标
        self.setGeometry(100, 100, 1200, 800)  # 保持窗口高度为800
        self.setMinimumSize(1200, 800)         # 保持窗口最小高度为800

        # 创建字体
        label_font = QFont("微软雅黑", 12)
        input_font = QFont("微软雅黑", 12)
        button_font = QFont("微软雅黑", 12)
        status_font = QFont("微软雅黑", 10)
        table_font = QFont("微软雅黑", 10)
        log_font = QFont("Consolas", 10)

        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 创建搜索设置分组框
        search_group = QGroupBox("搜索设置")
        search_layout = QGridLayout()
        search_layout.setSpacing(5)  # 调整控件之间的间距
        search_group.setLayout(search_layout)

        # 进阶模式复选框
        self.advanced_mode_checkbox = QCheckBox("进阶模式")
        self.advanced_mode_checkbox.setFont(label_font)
        self.advanced_mode_checkbox.stateChanged.connect(self.on_advanced_mode_changed)

        # 搜索引擎选择
        self.engine_label = QLabel("搜索引擎：")
        self.engine_label.setFont(label_font)
        self.engine_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # 右对齐
        self.engine_combo = QComboBox()
        self.engine_combo.setFont(input_font)
        self.engines = {
            "Google": "Google",
            "Bing": "Bing",
            "百度": "百度"
        }
        for engine in self.engines.keys():
            self.engine_combo.addItem(engine)
        self.engine_combo.setCurrentText("Google")  # 默认选择Google

        # 搜索结果数量选择
        self.result_num_label = QLabel("搜索结果数量：")
        self.result_num_label.setFont(label_font)
        self.result_num_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # 右对齐
        self.result_num_spinbox = QSpinBox()
        self.result_num_spinbox.setFont(input_font)
        self.result_num_spinbox.setRange(1, 20)  # 设置范围为1到20
        self.result_num_spinbox.setValue(5)  # 默认值为5

        # 搜索关键词输入（普通模式）
        self.search_label = QLabel("请输入搜索关键词：")
        self.search_label.setFont(label_font)
        self.search_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # 右对齐
        self.search_input = MyLineEdit()
        self.search_input.setFont(input_font)
        self.search_input.setPlaceholderText("例如：明天天气怎么样")

        # 搜索关键词输入（进阶模式）
        self.search_input_advanced = MyTextEdit()
        self.search_input_advanced.setFont(input_font)
        self.search_input_advanced.setPlaceholderText("每行一个关键词，如：\n明天天气怎么样\n上海旅游攻略")
        self.search_input_advanced.setVisible(False)  # 初始隐藏

        # 在程序启动时设置焦点到关键词输入框
        self.search_input.setFocus()

        # 问题输入（仅进阶模式）
        self.question_label = QLabel("请输入问题：")
        self.question_label.setFont(label_font)
        self.question_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # 右对齐
        self.question_input = QTextEdit()
        self.question_input.setFont(input_font)
        self.question_input.setPlaceholderText("在此输入您的问题")
        self.question_label.setVisible(False)
        self.question_input.setVisible(False)

        # 搜索按钮
        self.search_button = QPushButton("搜索")
        self.search_button.setFont(button_font)
        self.search_button.setFixedWidth(120)
        self.search_button.clicked.connect(self.on_search_click)

        # 中断按钮
        self.interrupt_button = QPushButton("中断")
        self.interrupt_button.setFont(button_font)
        self.interrupt_button.setFixedWidth(120)
        self.interrupt_button.clicked.connect(self.on_interrupt_click)
        self.interrupt_button.setEnabled(False)  # 初始禁用

        # 连接输入框的 returnPressed 信号到搜索函数
        self.search_input.returnPressed.connect(self.on_search_click)

        # 添加 Ctrl+C 快捷键
        self.interrupt_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        self.interrupt_shortcut.activated.connect(self.on_interrupt_click)

        # 保存按钮
        self.save_button = QPushButton("保存结果")
        self.save_button.setFont(button_font)
        self.save_button.setFixedWidth(120)
        self.save_button.clicked.connect(self.on_save_click)
        self.save_button.setEnabled(False)  # 初始禁用

        # 打开结果按钮
        self.open_button = QPushButton("打开结果")
        self.open_button.setFont(button_font)
        self.open_button.setFixedWidth(120)
        self.open_button.clicked.connect(self.on_open_click)
        self.open_button.setEnabled(False)  # 初始禁用

        # 复制按钮
        self.copy_button = QPushButton("复制")
        self.copy_button.setFont(button_font)
        self.copy_button.setFixedWidth(120)
        self.copy_button.clicked.connect(self.on_copy_click)
        self.copy_button.setEnabled(False)  # 初始禁用

        # 创建关键词输入和按钮的水平布局
        self.input_button_layout = QHBoxLayout()
        self.input_button_layout.addWidget(self.search_input)
        self.input_button_layout.addWidget(self.search_input_advanced)

        # 按钮布局
        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.search_button)
        self.button_layout.addWidget(self.interrupt_button)

        # 在“中断”按钮后添加弹性空间，使右边的按钮靠右
        self.button_layout.addStretch()

        # 添加底部三个按钮到按钮布局
        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.open_button)
        self.button_layout.addWidget(self.copy_button)

        self.input_button_layout.addLayout(self.button_layout)

        # 在布局中添加控件
        # 第一行：进阶模式、搜索引擎、搜索结果数量
        search_layout.addWidget(self.advanced_mode_checkbox, 0, 0)

        # 搜索引擎布局
        engine_layout = QHBoxLayout()
        engine_layout.addWidget(self.engine_label)
        engine_layout.addWidget(self.engine_combo)
        engine_layout.setSpacing(5)
        search_layout.addLayout(engine_layout, 0, 1)

        # 搜索结果数量布局
        result_num_layout = QHBoxLayout()
        result_num_layout.addWidget(self.result_num_label)
        result_num_layout.addWidget(self.result_num_spinbox)
        result_num_layout.setSpacing(5)
        search_layout.addLayout(result_num_layout, 0, 2)

        # 第二行：搜索关键词和按钮
        search_layout.addWidget(self.search_label, 1, 0)
        search_layout.addLayout(self.input_button_layout, 1, 1, 1, 2)

        # 第三行：自定义问题
        search_layout.addWidget(self.question_label, 2, 0)
        search_layout.addWidget(self.question_input, 2, 1, 1, 2)

        # 调整列伸缩比例
        search_layout.setColumnStretch(0, 0)
        search_layout.setColumnStretch(1, 1)
        search_layout.setColumnStretch(2, 1)

        # 状态标签
        self.status_label = QLabel("等待输入...")
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignLeft)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 设置为无限模式
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bbb;
                background-color: #eee;
                height: 10px;
            }
            QProgressBar::chunk {
                background-color: #4caf50;
            }
        """)

        # 结果显示区（使用QTableWidget）
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(5)  # 修改为5列，移除搜索引擎列
        self.result_table.setHorizontalHeaderLabels(["选择", "URL", "标题", "摘要", "内容"])

        # 使用自定义的表头
        self.checkbox_header = CheckBoxHeader()
        self.result_table.setHorizontalHeader(self.checkbox_header)
        self.checkbox_header.checkBoxClicked.connect(self.on_header_checkbox_clicked)

        self.result_table.verticalHeader().setVisible(False)
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.result_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.result_table.setSelectionMode(QTableWidget.SingleSelection)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setFont(table_font)
        self.result_table.setStyleSheet("""
            QTableWidget {
                background-color: #fff;
                alternate-background-color: #f9f9f9;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 4px;
                border: 1px solid #d6d6d6;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #cce5ff;
            }
        """)

        # 调整列宽
        self.result_table.setColumnWidth(0, 30)  # 复选框列宽度

        # 设置列的伸缩模式，使 URL、标题、摘要、内容 列宽相等
        self.result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        for i in range(1, 5):
            self.result_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)

        # 设置复选框居中
        self.result_table.setItemDelegateForColumn(0, CenteredCheckBoxDelegate())

        # 连接表格的单元格点击信号
        self.result_table.cellClicked.connect(self.on_result_cell_clicked)

        # 日志显示区
        log_group = QGroupBox("日志")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(log_font)
        self.log_text.setStyleSheet("background-color: #1e1e1e; color: #dcdcdc;")
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)

        # 使用QSplitter分割搜索结果区域和日志区域
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.result_table)
        splitter.addWidget(log_group)

        # 设置初始大小，调整比例
        splitter.setSizes([360, 240])  # 爬取内容区域增加20%，日志区域减少20%

        # 将控件添加到主布局
        main_layout.addWidget(search_group)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(splitter)

        self.setLayout(main_layout)

        # 设置日志到GUI
        self.setup_logging()

    def setup_logging(self):
        """
        设置日志记录到GUI的log_text控件。
        """
        # 创建一个新的日志处理器
        gui_handler = GuiLogHandler(self.log_text)
        gui_handler.setLevel(logging.DEBUG)

        # 设置日志格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        gui_handler.setFormatter(formatter)

        # 获取根日志记录器并添加处理器
        logging.getLogger().addHandler(gui_handler)
        logging.getLogger().setLevel(logging.DEBUG)  # 设置全局日志级别

    def on_advanced_mode_changed(self, state):
        """
        处理进阶模式复选框状态变化。
        """
        is_advanced = (state == Qt.Checked)
        logging.info(f"进阶模式 {'开启' if is_advanced else '关闭'}")
        if is_advanced:
            self.search_label.setText("请输入搜索关键词（每行一个）：")
            self.search_input.setVisible(False)
            self.search_input_advanced.setVisible(True)
            self.question_label.setVisible(True)
            self.question_input.setVisible(True)
            self.search_input_advanced.setFocus()  # 设置焦点到多行输入框
        else:
            self.search_label.setText("请输入搜索关键词：")
            self.search_input.setVisible(True)
            self.search_input_advanced.setVisible(False)
            self.question_label.setVisible(False)
            self.question_input.setVisible(False)
            self.search_input.setFocus()  # 设置焦点到单行输入框

    def on_search_click(self):
        """
        处理搜索按钮点击事件。
        """
        is_advanced = self.advanced_mode_checkbox.isChecked()
        if is_advanced:
            keywords_text = self.search_input_advanced.toPlainText().strip()
            if not keywords_text:
                QMessageBox.warning(self, "输入错误", "请输入至少一个搜索关键词！")
                logging.warning("用户尝试进行空关键词搜索（进阶模式）。")
                return
            queries = [line.strip() for line in keywords_text.splitlines() if line.strip()]
            if not queries:
                QMessageBox.warning(self, "输入错误", "请输入至少一个有效的搜索关键词！")
                logging.warning("用户尝试进行空关键词搜索（进阶模式）。")
                return
            custom_question = self.question_input.toPlainText().strip()
            if not custom_question:
                QMessageBox.warning(self, "输入错误", "请输入自定义问题！")
                logging.warning("用户未输入自定义问题（进阶模式）。")
                return
        else:
            query = self.search_input.text().strip()
            if not query:
                QMessageBox.warning(self, "输入错误", "请输入搜索关键词！")
                logging.warning("用户尝试进行空关键词搜索。")
                return
            queries = [query]
            custom_question = None

        num_results = self.result_num_spinbox.value()
        engine_display = self.engine_combo.currentText()
        engine = self.engines.get(engine_display, 'Google')  # 默认Google

        logging.info(f"用户发起搜索，关键词: {queries}, 结果数量: {num_results}, 搜索引擎: {engine}")

        # 禁用搜索按钮和输入框
        self.search_button.setEnabled(False)
        self.open_button.setEnabled(False)  # 禁用打开结果按钮
        self.save_button.setEnabled(False)
        self.copy_button.setEnabled(False)
        self.interrupt_button.setEnabled(True)  # 启用中断按钮
        self.search_input.setEnabled(False)
        self.search_input_advanced.setEnabled(False)
        self.question_input.setEnabled(False)
        self.result_num_spinbox.setEnabled(False)
        self.engine_combo.setEnabled(False)

        # 清空之前的结果
        self.result_table.setRowCount(0)
        self.status_label.setText("正在搜索，请稍候...")
        self.progress_bar.setVisible(True)

        # 创建工作线程
        self.thread = QThread()
        self.worker = Worker(queries, num_results, engine, custom_question)
        self.worker.moveToThread(self.thread)

        # 连接信号和槽
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_search_complete)
        self.worker.error.connect(self.on_search_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # 启动线程
        self.thread.start()

    def on_interrupt_click(self):
        """
        处理中断按钮点击事件或 Ctrl+C 快捷键。
        """
        if self.thread and self.thread.isRunning():
            logging.info("用户中断了搜索任务。")
            self.worker.stop()
            self.thread.quit()
            self.thread.wait()  # 等待线程退出
            self.interrupt_button.setEnabled(False)
            self.status_label.setText("搜索已被中断。")

            # 恢复 GUI 控件的状态
            self.search_button.setEnabled(True)
            self.search_input.setEnabled(True)
            self.search_input_advanced.setEnabled(True)
            self.question_input.setEnabled(True)
            self.result_num_spinbox.setEnabled(True)
            self.engine_combo.setEnabled(True)
        else:
            logging.warning("没有正在运行的搜索任务可中断。")

    def on_search_complete(self, results, filename):
        """
        处理搜索任务完成后的逻辑。
        """
        self.progress_bar.setVisible(False)
        self.interrupt_button.setEnabled(False)  # 禁用中断按钮
        if results:
            try:
                self.saved_file = filename  # 存储保存的文件路径
                self.all_results = results  # 存储所有结果
                logging.info("搜索结果成功保存到默认下载文件夹。")
            except Exception as e:
                logging.error(f"保存文件时出错：{e}")
                QMessageBox.critical(self, "保存错误", f"保存文件时出错：\n{e}")
                self.status_label.setText("搜索完成，但保存文件时出错。")
                self.search_button.setEnabled(True)
                self.search_input.setEnabled(True)
                self.search_input_advanced.setEnabled(True)
                self.question_input.setEnabled(True)
                self.result_num_spinbox.setEnabled(True)
                self.engine_combo.setEnabled(True)
                return

            self.result_table.setRowCount(0)  # 清空表格
            for idx, result in enumerate(results):
                self.result_table.insertRow(idx)
                # 添加复选框
                checkbox_item = QTableWidgetItem()
                checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                checkbox_item.setCheckState(Qt.Checked)
                # 添加其他数据项
                url_item = QTableWidgetItem(result['link'])
                url_item.setFont(QFont("微软雅黑", 10))
                title_item = QTableWidgetItem(result['title'])
                title_item.setFont(QFont("微软雅黑", 10))
                snippet_item = QTableWidgetItem(result['snippet'])
                snippet_item.setFont(QFont("微软雅黑", 9))
                content_item = QTableWidgetItem(result['content'])
                content_item.setFont(QFont("微软雅黑", 9))
                self.result_table.setItem(idx, 0, checkbox_item)
                self.result_table.setItem(idx, 1, url_item)
                self.result_table.setItem(idx, 2, title_item)
                self.result_table.setItem(idx, 3, snippet_item)
                self.result_table.setItem(idx, 4, content_item)

            # 连接复选框状态改变的信号
            self.result_table.itemChanged.connect(self.on_checkbox_state_changed)

            # 更新保存和复制的内容
            self.update_saved_content()

            self.status_label.setText("搜索完成，结果已保存并已自动复制。")
            self.save_button.setEnabled(True)
            self.open_button.setEnabled(True)
            self.copy_button.setEnabled(True)
            self.search_button.setEnabled(True)  # 重新启用搜索按钮
            self.search_input.setEnabled(True)
            self.search_input_advanced.setEnabled(True)
            self.question_input.setEnabled(True)
            self.result_num_spinbox.setEnabled(True)
            self.engine_combo.setEnabled(True)
            # 增加爬取成功后焦点回到关键词输入框
            if self.advanced_mode_checkbox.isChecked():
                self.search_input_advanced.setFocus()
            else:
                self.search_input.setFocus()
            logging.info("搜索完成，结果已显示在界面。")

            # 自动复制结果
            self.copy_results_silently()

        else:
            self.result_table.setRowCount(0)
            self.status_label.setText("未获取到搜索结果。")
            QMessageBox.information(self, "无结果", "未获取到搜索结果。")
            logging.info("搜索完成，但未获取到任何结果。")

            # 重新启用搜索按钮和输入框
            self.search_button.setEnabled(True)
            self.search_input.setEnabled(True)
            self.search_input_advanced.setEnabled(True)
            self.question_input.setEnabled(True)
            self.result_num_spinbox.setEnabled(True)
            self.engine_combo.setEnabled(True)
            self.interrupt_button.setEnabled(False)
            # 增加爬取成功后焦点回到关键词输入框
            if self.advanced_mode_checkbox.isChecked():
                self.search_input_advanced.setFocus()
            else:
                self.search_input.setFocus()

    def on_search_error(self, error_message):
        """
        处理搜索任务发生错误的逻辑。
        """
        self.progress_bar.setVisible(False)
        self.result_table.setRowCount(0)
        self.status_label.setText("搜索失败。")
        QMessageBox.critical(self, "错误", f"搜索过程中发生错误：\n{error_message}")
        logging.error(f"搜索过程中发生错误：{error_message}")

        # 重新启用搜索按钮和输入框
        self.search_button.setEnabled(True)
        self.open_button.setEnabled(False)  # 禁用打开结果按钮
        self.save_button.setEnabled(False)
        self.copy_button.setEnabled(False)
        self.search_input.setEnabled(True)
        self.search_input_advanced.setEnabled(True)
        self.question_input.setEnabled(True)
        self.result_num_spinbox.setEnabled(True)
        self.engine_combo.setEnabled(True)
        self.interrupt_button.setEnabled(False)

    def on_save_click(self):
        """
        处理保存结果按钮点击事件。
        """
        is_advanced = self.advanced_mode_checkbox.isChecked()
        if is_advanced:
            queries = [line.strip() for line in self.search_input_advanced.toPlainText().strip().splitlines() if line.strip()]
            custom_question = self.question_input.toPlainText().strip()
        else:
            query = self.search_input.text().strip()
            queries = [query]
            custom_question = None

        if not queries:
            QMessageBox.warning(self, "保存错误", "没有搜索关键词，无法保存结果。")
            logging.warning("用户尝试保存结果时未输入搜索关键词。")
            return

        # 打开文件保存对话框，默认路径为下载文件夹
        downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads')
        default_filename = os.path.join(downloads_path, "search_results.txt")
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "保存搜索结果",
            default_filename,
            "Text Files (*.txt);;All Files (*)",
            options=options
        )
        if filename:
            logging.info(f"用户选择保存文件，路径: {filename}")
            try:
                selected_results = self.get_selected_results()

                # 调用保存函数
                save_results_to_txt(
                    [selected_results],
                    ', '.join(queries),
                    filename=filename,
                    engine=self.engine_combo.currentText(),
                    custom_question=custom_question
                )

                QMessageBox.information(self, "保存成功", f"搜索结果已保存到 {filename}")
                logging.info(f"搜索结果成功保存到 {filename}")
                self.saved_file = filename  # 更新保存的文件路径
                self.open_button.setEnabled(True)  # 启用打开结果按钮
            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"保存文件时出错：{e}")
                logging.error(f"保存文件时出错：{e}")

    def on_open_click(self):
        """
        处理打开结果按钮点击事件。
        """
        if self.saved_file and os.path.exists(self.saved_file):
            logging.info(f"用户尝试打开文件: {self.saved_file}")
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.saved_file))
        else:
            QMessageBox.warning(self, "打开错误", "没有可打开的结果文件。")
            logging.warning("用户尝试打开结果文件，但文件不存在或未保存。")

    def on_copy_click(self):
        """
        处理复制按钮点击事件。
        """
        selected_results = self.get_selected_results()
        if selected_results:
            is_advanced = self.advanced_mode_checkbox.isChecked()
            if is_advanced:
                queries = [line.strip() for line in self.search_input_advanced.toPlainText().strip().splitlines() if line.strip()]
                custom_question = self.question_input.toPlainText().strip()
            else:
                query = self.search_input.text().strip()
                queries = [query]
                custom_question = None

            try:
                content = generate_txt_content(
                    [selected_results],
                    ', '.join(queries),
                    engine=self.engine_combo.currentText(),
                    custom_question=custom_question
                )
                clipboard = QApplication.clipboard()
                clipboard.setText(content)
                logging.info("已复制选中的内容到剪贴板。")
                QMessageBox.information(self, "复制成功", "已复制选中的内容到剪贴板。")
            except Exception as e:
                QMessageBox.warning(self, "复制失败", f"复制内容时出错：{e}")
                logging.error(f"复制内容时出错：{e}")
        else:
            QMessageBox.warning(self, "复制失败", "未选择任何内容。")
            logging.warning("用户尝试复制，但未选择任何内容。")

    def copy_results_silently(self):
        """
        自动复制选中的内容到剪贴板，不弹出消息框。
        """
        selected_results = self.get_selected_results()
        if selected_results:
            is_advanced = self.advanced_mode_checkbox.isChecked()
            if is_advanced:
                queries = [line.strip() for line in self.search_input_advanced.toPlainText().strip().splitlines() if line.strip()]
                custom_question = self.question_input.toPlainText().strip()
            else:
                query = self.search_input.text().strip()
                queries = [query]
                custom_question = None

            try:
                content = generate_txt_content(
                    [selected_results],
                    ', '.join(queries),
                    engine=self.engine_combo.currentText(),
                    custom_question=custom_question
                )
                clipboard = QApplication.clipboard()
                clipboard.setText(content)
                logging.info("已自动复制选中的内容到剪贴板。")
            except Exception as e:
                logging.error(f"自动复制内容时出错：{e}")
        else:
            logging.warning("自动复制时未选择任何内容。")

    def on_result_cell_clicked(self, row, column):
        """
        处理结果表格单元格点击事件，点击URL列时打开链接。
        """
        if column == 1:  # URL列
            item = self.result_table.item(row, column)
            if item:
                url = item.text()
                logging.info(f"用户点击URL链接: {url}")
                QDesktopServices.openUrl(QUrl(url))
            else:
                logging.warning(f"点击的单元格内容为空，无法获取URL。")

    def on_checkbox_state_changed(self, item):
        """
        处理复选框状态改变事件，更新保存和复制的内容。
        """
        if item.column() == 0:
            self.update_saved_content()
            # 更新表头复选框状态
            all_checked = True
            for row in range(self.result_table.rowCount()):
                checkbox_item = self.result_table.item(row, 0)
                if checkbox_item is None or checkbox_item.checkState() != Qt.Checked:
                    all_checked = False
                    break
            self.checkbox_header.isOn = all_checked
            self.checkbox_header.updateSection(0)

    def on_header_checkbox_clicked(self, checked):
        """
        处理表头复选框的点击事件，选中或取消选中所有行的复选框。
        """
        for row in range(self.result_table.rowCount()):
            checkbox_item = self.result_table.item(row, 0)
            if checkbox_item is not None:
                checkbox_item.setCheckState(Qt.Checked if checked else Qt.Unchecked)

    def get_selected_results(self):
        """
        获取用户选中的结果列表。
        """
        selected_results = []
        for row in range(self.result_table.rowCount()):
            checkbox_item = self.result_table.item(row, 0)
            if checkbox_item is not None and checkbox_item.checkState() == Qt.Checked:
                title_item = self.result_table.item(row, 2)
                link_item = self.result_table.item(row, 1)
                snippet_item = self.result_table.item(row, 3)
                content_item = self.result_table.item(row, 4)
                if title_item and link_item and snippet_item and content_item:
                    result = {
                        'title': title_item.text(),
                        'link': link_item.text(),
                        'snippet': snippet_item.text(),
                        'content': content_item.text(),
                        'engine': self.engine_combo.currentText()  # 使用当前选择的搜索引擎
                    }
                    selected_results.append(result)
                else:
                    logging.warning(f"行 {row} 的数据项存在空值，无法获取完整数据。")
        return selected_results

    def update_saved_content(self):
        """
        更新保存和复制的内容，仅包含选中的结果。
        """
        selected_results = self.get_selected_results()
        is_advanced = self.advanced_mode_checkbox.isChecked()
        if is_advanced:
            queries = [line.strip() for line in self.search_input_advanced.toPlainText().strip().splitlines() if line.strip()]
            custom_question = self.question_input.toPlainText().strip()
        else:
            query = self.search_input.text().strip()
            queries = [query]
            custom_question = None

        try:
            content = generate_txt_content(
                [selected_results],
                ', '.join(queries),
                engine=self.engine_combo.currentText(),
                custom_question=custom_question
            )
            # 更新保存的文件内容
            self.current_content = content
        except Exception as e:
            logging.error(f"更新保存内容时出错：{e}")

