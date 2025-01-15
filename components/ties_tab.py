import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, PanedWindow
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from grav_proc.calculations import fit_by_meter_created
from grav_proc.reports import get_report
from grav_proc.plots import residuals_plot, get_map
from grav_proc.loader import read_scale_factors


class TiesTab:
    def __init__(self, notebook, survey_data_tab):
        self.frame = tk.Frame(notebook)
        self.survey_data_tab = survey_data_tab

        # Фрейм для элементов управления
        controls_frame = tk.Frame(self.frame)
        controls_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Подпись для выбора метода расчета
        method_label = tk.Label(controls_frame, text="Select the calculation method:")
        method_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Выпадающий список (Combobox)
        self.method_var = tk.StringVar()
        self.method_combo = ttk.Combobox(controls_frame, textvariable=self.method_var)
        self.method_combo['values'] = ('WLS', 'RLM')  # Значения в выпадающем списке
        self.method_combo.current(0)  # Значение по умолчанию
        self.method_combo.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        # Флаг расчета по линиям
        self.by_lines_var = tk.BooleanVar()
        self.by_lines_check = tk.Checkbutton(controls_frame, text="Calc by lines", variable=self.by_lines_var)
        self.by_lines_check.grid(row=2, column=0, padx=5, pady=5, sticky="w")

        # Флажок для построения графиков остатков
        self.plot_var = tk.BooleanVar()
        self.plot_check = tk.Checkbutton(controls_frame, text="Plot residuals", variable=self.plot_var)
        self.plot_check.grid(row=3, column=0, padx=5, pady=5, sticky="w")

        # Флажок для построения графиков по линиям
        self.plots_by_lines_var = tk.BooleanVar()
        self.plots_by_lines_check = tk.Checkbutton(controls_frame, text="Plots by lines",
                                                   variable=self.plots_by_lines_var)
        self.plots_by_lines_check.grid(row=3, column=1, padx=5, pady=5,
                                       sticky="w")  # Расположен справа от Plot residuals

        # Флажок для создания карты
        self.map_var = tk.BooleanVar()
        self.map_check = tk.Checkbutton(controls_frame, text="Create map", variable=self.map_var)
        self.map_check.grid(row=4, column=0, padx=5, pady=5, sticky="w")

        # Выпадающий список для выбора Confidence Interval
        ci_label = tk.Label(controls_frame, text="Residual Confidence Interval (%):")
        ci_label.grid(row=5, column=0, padx=5, pady=5, sticky="w")

        self.ci_var = tk.IntVar(value=95)  # Значение по умолчанию
        self.ci_combo = ttk.Combobox(controls_frame, textvariable=self.ci_var, state="readonly")
        self.ci_combo['values'] = list(range(1, 101))  # От 1 до 100
        self.ci_combo.grid(row=6, column=0, padx=5, pady=5, sticky="w")

        # Выпадающий список для выбора метода детекции выбросов
        outlier_method_label = tk.Label(controls_frame, text="Outlier Detection Method:")
        outlier_method_label.grid(row=5, column=1, padx=5, pady=5, sticky="w")

        self.outlier_method_var = tk.StringVar(value='IsolationForest')
        self.outlier_method_combo = ttk.Combobox(controls_frame, textvariable=self.outlier_method_var, state="readonly")
        self.outlier_method_combo['values'] = ('IsolationForest', 'LOF', 'Z-score', 'IsolationForest+LOF')
        self.outlier_method_combo.grid(row=6, column=1, padx=5, pady=5, sticky="w")

        # Кнопка запуска расчета (Ties)
        self.ties_button = tk.Button(controls_frame, text="Solve ties", command=self.calculate_ties)
        self.ties_button.grid(row=7, column=0, padx=5, pady=10)

        # Создаем PanedWindow для разделения окна пополам
        self.main_paned_window = PanedWindow(self.frame, orient=tk.VERTICAL)
        self.main_paned_window.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Верхняя половина для отчета
        self.report_text_ties = tk.Text(self.main_paned_window, height=10, wrap=tk.NONE)
        self.create_context_menu(self.report_text_ties)
        self.bind_copy_shortcut(self.report_text_ties)
        self.main_paned_window.add(self.report_text_ties)  # Добавляем в PanedWindow

        # Нижняя половина для графиков/карт (Notebook)
        self.graphs_notebook = ttk.Notebook(self.main_paned_window)
        self.main_paned_window.add(self.graphs_notebook)  # Добавляем в PanedWindow

        # Настройка адаптивного изменения размеров
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

    def create_context_menu(self, widget):
        """Создание контекстного меню с командой копирования для заданного виджета."""
        context_menu = tk.Menu(widget, tearoff=0)
        context_menu.add_command(label="Copy", command=lambda: widget.event_generate("<<Copy>>"))

        widget.bind("<Button-3>", lambda event: self.show_context_menu(event, context_menu))

    def show_context_menu(self, event, context_menu):
        """Отображает контекстное меню в позиции клика правой кнопки мыши."""
        context_menu.tk_popup(event.x_root, event.y_root)

    def bind_copy_shortcut(self, widget):
        """Привязывает обработку Ctrl+C для копирования текста."""
        widget.bind("<Control-c>", lambda event: widget.event_generate("<<Copy>>"))

    def choose_output_directory(self, survey_name, task_name):
        """Функция для выбора папки сохранения и создания новой папки для результатов"""
        output_dir = filedialog.askdirectory(title="Select a folder to save the results to")
        if not output_dir:
            messagebox.showwarning("Error", "The folder to save is not selected!")
            return None

        result_dir = os.path.join(output_dir, f"{survey_name}_{task_name}")
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)
        return result_dir

    def apply_scale_factors(self, data):
        """Применение коэффициентов, если загружен файл"""
        coeff_file = self.survey_data_tab.coeff_files_entry.get()
        if not coeff_file:
            return data

        # Чтение файла с коэффициентами
        try:
            scale_factors = read_scale_factors([open(coeff_file, 'r', encoding='utf-8')])
            group_by_meter = scale_factors.groupby('instrument_serial_number')
            for meter, meter_scale_factors in group_by_meter:
                scale_factor = meter_scale_factors['scale_factor'].values[0]
                data.loc[data['instrument_serial_number'] == meter, 'corr_grav'] *= scale_factor
        except Exception as e:
            messagebox.showerror("Error", f"Error when applying calibration factor: {e}")
        return data

    def calculate_ties(self):
        """Расчет привязок (Ties) с сохранением логов."""
        try:
            method = self.method_var.get()
            by_lines = self.by_lines_var.get()
            confidence_interval = self.ci_var.get()
            outlier_method = self.outlier_method_var.get()

            # Получение данных из вкладки Survey Data
            data = self.survey_data_tab.get_dataframe()

            # Применение коэффициентов, если загружены
            data = self.apply_scale_factors(data)

            # Получить survey_name из пути к данным или файла проекта
            survey_name = self.survey_data_tab.data_files_entry.get()
            if not survey_name:
                survey_name = self.survey_data_tab.data['survey_name'].iloc[0] \
                    if 'survey_name' in self.survey_data_tab.data.columns else "unknown_survey"
            else:
                survey_name = os.path.basename(survey_name.split(',')[0]).split('.')[0]

            # Выбор папки для сохранения
            result_dir = self.choose_output_directory(survey_name, "ties")
            if not result_dir:
                return

            # Открытие файла логов для записи
            log_file_path = os.path.join(result_dir, f"{survey_name}_ties_log.txt")
            with open(log_file_path, 'w', encoding='utf-8') as log_file:

                # Логи из SurveyDataTab
                log_file.write("=== Logs from SurveyDataTab ===\n")
                survey_logs = self.survey_data_tab.message_text.get(1.0, tk.END)
                log_file.write(survey_logs + "\n")
                log_file.write("=" * 50 + "\n")

                # Запись начальных параметров
                log_file.write(f"Calculation method: {method}\n")
                log_file.write(f"Calculate by lines: {by_lines}\n")
                log_file.write(f"Confidence Interval: {confidence_interval}%\n")
                log_file.write(f"Outlier Detection Method: {outlier_method}\n")
                log_file.write("=" * 50 + "\n")

                # Расчет привязок
                log_file.write("Starting ties calculation...\n")
                ties = fit_by_meter_created(data, anchor=None, method=method, by_lines=by_lines,
                                            confidence_interval=confidence_interval, outlier_method=outlier_method)
                log_file.write("Ties calculation completed.\n")

                report = get_report(ties)
                report_file = os.path.join(result_dir, f"{survey_name}_ties_report.txt")
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(report)

                log_file.write(f"Report saved\n")

                # Вывод отчета в текстовом поле
                self.report_text_ties.delete(1.0, tk.END)
                self.report_text_ties.insert(tk.END, report)

                # Очистка вкладок с графиками перед обновлением
                for tab in self.graphs_notebook.tabs():
                    self.graphs_notebook.forget(tab)

                # Построение графиков остатков
                if self.plot_var.get():
                    fig = residuals_plot(data)
                    residuals_file = os.path.join(result_dir, f"{survey_name}_residuals.png")
                    fig.savefig(residuals_file)
                    log_file.write(f"Residuals plot saved\n")

                    canvas_frame = tk.Frame(self.graphs_notebook)
                    canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
                    self.graphs_notebook.add(canvas_frame, text="Residuals")

                    if len(data['line'].unique()) > 1 and self.plots_by_lines_var.get():
                        line_plots_dir = os.path.join(result_dir, "residuals_plots_by_lines")
                        os.makedirs(line_plots_dir, exist_ok=True)
                        log_file.write(f"Residuals plots by lines saved\n")

                        for (line, meter), line_data in data.groupby(['line', 'instrument_serial_number']):
                            line_fig = residuals_plot(line_data)
                            meter_suffix = str(meter)[-3:]
                            line_file = os.path.join(line_plots_dir, f"{survey_name}-{meter_suffix}-line_{line}.png")
                            line_fig.savefig(line_file)
                            plt.close(line_fig)
                            log_file.write(f"Line {line}, Meter {meter_suffix} plot saved\n")

                # Построение карты
                if self.map_var.get():
                    fig_map = get_map(ties)
                    map_file = os.path.join(result_dir, f"{survey_name}_map.pdf")
                    fig_map.savefig(map_file, bbox_inches='tight')
                    log_file.write(f"Map saved\n")

                    canvas_frame = tk.Frame(self.graphs_notebook)
                    canvas_map = FigureCanvasTkAgg(fig_map, master=canvas_frame)
                    canvas_map.draw()
                    canvas_map.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
                    self.graphs_notebook.add(canvas_frame, text="Map")

                # Сохранение проекта после обработки
                project_save_path = os.path.join(result_dir, f"{survey_name}_project.csv")
                self.survey_data_tab.save_data_to_file(project_save_path)
                log_file.write(f"Project saved\n")

            messagebox.showinfo("Successfully",
                                f"The calculation of the ties is completed!\nLogs saved")
        except Exception as e:
            messagebox.showerror("Error", f"Error in calculating ties: {e}")
