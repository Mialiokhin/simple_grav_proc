import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, PanedWindow
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
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

        # Флажок для создания карты
        self.map_var = tk.BooleanVar()
        self.map_check = tk.Checkbutton(controls_frame, text="Create map", variable=self.map_var)
        self.map_check.grid(row=4, column=0, padx=5, pady=5, sticky="w")

        # Кнопка запуска расчета (Ties)
        self.ties_button = tk.Button(controls_frame, text="Solve ties", command=self.calculate_ties)
        self.ties_button.grid(row=5, column=0, padx=5, pady=10)

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
        """Расчет привязок (Ties)"""
        try:
            method = self.method_var.get()
            by_lines = self.by_lines_var.get()

            # Получение данных из вкладки Survey Data
            data = self.survey_data_tab.get_dataframe()

            # Применение коэффициентов, если загружены
            data = self.apply_scale_factors(data)

            # Запрашиваем название съемки
            survey_name = os.path.basename(self.survey_data_tab.data_files_entry.get().split(',')[0]).split('.')[0]

            # Выбираем папку для сохранения
            result_dir = self.choose_output_directory(survey_name, "ties")
            if not result_dir:
                return

            # Расчет привязок
            ties = fit_by_meter_created(data, anchor=None, method=method, by_lines=by_lines)
            report = get_report(ties)

            # Сохраняем отчет
            report_file = os.path.join(result_dir, f"{survey_name}_ties_report.txt")
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)

            # Выводим отчет в текстовом поле
            self.report_text_ties.delete(1.0, tk.END)
            self.report_text_ties.insert(tk.END, report)

            # Очистка вкладок с графиками перед их обновлением
            for tab in self.graphs_notebook.tabs():
                self.graphs_notebook.forget(tab)

            # Проверка на необходимость построения графика остатков
            if self.plot_var.get():
                fig = residuals_plot(data)
                # Сохраняем график остатков
                fig.savefig(os.path.join(result_dir, f"{survey_name}_residuals.png"))

                # Отображаем график в новом фрейме внутри Notebook
                canvas_frame = tk.Frame(self.graphs_notebook)
                canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
                self.graphs_notebook.add(canvas_frame, text="Residuals")

            # Проверка на необходимость создания карты
            if self.map_var.get():
                fig_map = get_map(ties)
                # Сохраняем карту
                fig_map.savefig(os.path.join(result_dir, f"{survey_name}_map.pdf"), bbox_inches='tight')

                # Отображаем карту в новом фрейме внутри Notebook
                canvas_frame = tk.Frame(self.graphs_notebook)
                canvas_map = FigureCanvasTkAgg(fig_map, master=canvas_frame)
                canvas_map.draw()
                canvas_map.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
                self.graphs_notebook.add(canvas_frame, text="Map")

            messagebox.showinfo("Successfully", f"The calculation of the ties is completed!")
        except Exception as e:
            messagebox.showerror("Error", f"Error in calculating ties: {e}")
