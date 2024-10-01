import os
import tkinter as tk
from tkinter import filedialog, messagebox
from grav_proc.calculations import fit_by_meter_created
from grav_proc.reports import get_report
from grav_proc.plots import residuals_plot, get_map
from grav_proc.loader import read_scale_factors
from tkinter import ttk

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

        # Поле для отчета с прокрутками
        self.report_text_ties = tk.Text(self.frame, height=10, wrap=tk.NONE)
        self.report_text_ties.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Настройка адаптивного изменения размеров
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

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

            # Выводим отчет
            self.report_text_ties.delete(1.0, tk.END)
            self.report_text_ties.insert(tk.END, report)

            # Проверка на необходимость построения графика остатков
            if self.plot_var.get():
                fig = residuals_plot(data)
                fig.savefig(os.path.join(result_dir, f"{survey_name}_residuals.png"))
                fig.show()

            # Проверка на необходимость создания карты
            if self.map_var.get():
                fig_map = get_map(ties)
                fig_map.savefig(os.path.join(result_dir, f"{survey_name}_map.pdf"), bbox_inches='tight')
                fig_map.show()

            messagebox.showinfo("Successfully", f"The calculation of the ties is completed!")
        except Exception as e:
            messagebox.showerror("Error", f"Error in calculating ties: {e}")
