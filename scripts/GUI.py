import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
from components.input_data_table import InputDataTable
from grav_proc.loader import read_data, read_scale_factors
from grav_proc.calculations import make_frame_to_proc, fit_by_meter_created
from grav_proc.vertical_gradient import get_vg
from grav_proc.plots import vg_plot
from grav_proc.reports import get_report, make_vg_ties_report, make_vg_coeffs_report


class GravityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple_grav_proc")

        # Заголовок
        self.title_label = tk.Label(root, text="Simple_grav_proc", font=("Helvetica", 16))
        self.title_label.pack(pady=10)

        # Поля выбора файлов данных
        self.data_files_label = tk.Label(root, text="Survey Data:")
        self.data_files_label.pack(pady=5)
        self.data_files_entry = tk.Entry(root, width=50)
        self.data_files_entry.pack(pady=5)
        self.data_files_button = tk.Button(root, text="Import", command=self.load_data_files)
        self.data_files_button.pack(pady=5)

        # Поля выбора файлов коэффициентов
        self.coeff_files_label = tk.Label(root, text="Calibration Data (optional):")
        self.coeff_files_label.pack(pady=5)
        self.coeff_files_entry = tk.Entry(root, width=50)
        self.coeff_files_entry.pack(pady=5)
        self.coeff_files_button = tk.Button(root, text="Import", command=self.load_coeff_files)
        self.coeff_files_button.pack(pady=5)

        # Выбор метода расчета
        self.method_label = tk.Label(root, text="Select the calculation method:")
        self.method_label.pack(pady=5)
        self.method_var = tk.StringVar()
        self.method_combo = ttk.Combobox(root, textvariable=self.method_var)
        self.method_combo['values'] = ('WLS', 'RLM')
        self.method_combo.current(0)
        self.method_combo.pack(pady=5)

        # Флаг расчета по линиям
        self.by_lines_var = tk.BooleanVar()
        self.by_lines_check = tk.Checkbutton(root, text="Use Loops", variable=self.by_lines_var)
        self.by_lines_check.pack(pady=5)

        # Кнопка запуска расчета (Ties)
        self.ties_button = tk.Button(root, text="Solve ties", command=self.calculate_ties)
        self.ties_button.pack(pady=10)

        # Кнопка для расчета вертикального градиента
        self.vg_button = tk.Button(root, text="Calculate vertical gradient", command=self.calculate_vg)
        self.vg_button.pack(pady=10)

               # Таблица для отображения данных
        self.table_frame = tk.Frame(root)
        self.table_frame.pack(pady=10)
        self.table = None  # Здесь будет EditableTable

        self.data = None

        # Поле для отчета
        self.report_text = tk.Text(root, height=10, width=100, wrap=tk.NONE)
        self.report_text.pack(pady=10)

    def load_data_files(self):
        """Загрузка файлов данных и отображение в таблице"""
        files = filedialog.askopenfilenames(
            title="Select the data files",
            filetypes=[("CG-6 Data Files", "*.dat"), ("All files", "*.*")]
        )
        self.data_files_entry.delete(0, tk.END)
        self.data_files_entry.insert(0, ','.join(files))

        # Загрузка данных
        data_files = [open(file, 'r', encoding='utf-8') for file in files]
        self.data = make_frame_to_proc(read_data(data_files))

        # Если таблица уже существует, удаляем ее перед созданием новой
        if self.table:
            self.table.tree.pack_forget()
            self.table.v_scroll.pack_forget()
            self.table.h_scroll.pack_forget()

        # Отображаем данные в таблице
        self.table = InputDataTable(self.table_frame, self.data)

    def load_coeff_files(self):
        """Загрузка файлов коэффициентов"""
        file = filedialog.askopenfilename(
            title="Select the Calibration Files",
            filetypes=[("Calibration Files", "*.txt"), ("All files", "*.*")]
        )
        self.coeff_files_entry.delete(0, tk.END)
        self.coeff_files_entry.insert(0, file)

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

    def apply_scale_factors(self, raw_data, scale_factors_file):
        """Применение коэффициентов, если загружен файл"""
        if not scale_factors_file:
            return raw_data

        # Чтение файла с коэффициентами
        try:
            scale_factors = read_scale_factors([open(scale_factors_file, 'r', encoding='utf-8')])
            group_by_meter = scale_factors.groupby('instrument_serial_number')
            for meter, meter_scale_factors in group_by_meter:
                scale_factor = meter_scale_factors['scale_factor'].values[0]
                raw_data.loc[raw_data['instrument_serial_number'] == meter, 'corr_grav'] *= scale_factor
        except Exception as e:
            messagebox.showerror("Error", f"Error when applying calibration factor: {e}")

        return raw_data

    def calculate_ties(self):
        """Расчет привязок (Ties)"""
        try:
            coeff_file = self.coeff_files_entry.get()
            method = self.method_var.get()
            by_lines = self.by_lines_var.get()

            # Обновление данных из таблицы
            self.data = self.table.get_dataframe()

            # Применение коэффициентов, если загружены
            self.data = self.apply_scale_factors(self.data, coeff_file)

            # Запрашиваем название съемки
            survey_name = os.path.basename(self.data_files_entry.get().split(',')[0]).split('.')[0]

            # Выбираем папку для сохранения
            result_dir = self.choose_output_directory(survey_name, "ties")
            if not result_dir:
                return

            # Расчет привязок
            ties = fit_by_meter_created(self.data, anchor=None, method=method, by_lines=by_lines)
            report = get_report(ties)

            # Сохраняем отчет
            ties_report_file = os.path.join(result_dir, f"{survey_name}_ties_report.txt")
            with open(ties_report_file, 'w', encoding='utf-8') as f:
                f.write(report)

            # Выводим отчет
            self.report_text.delete(1.0, tk.END)
            self.report_text.insert(tk.END, report)

            messagebox.showinfo("Successfully", f"The calculation of the ties is completed! The report is saved in {ties_report_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Error in calculating ties: {e}")

    def calculate_vg(self):
        """Расчет вертикального градиента"""
        try:
            coeff_file = self.coeff_files_entry.get()

            # Обновление данных из таблицы
            self.data = self.table.get_dataframe()

            # Применение коэффициентов, если загружены
            self.data = self.apply_scale_factors(self.data, coeff_file)

            # Запрашиваем название съемки
            survey_name = os.path.basename(self.data_files_entry.get().split(',')[0]).split('.')[0]

            # Выбираем папку для сохранения
            result_dir = self.choose_output_directory(survey_name, "gradient")
            if not result_dir:
                return

            # Расчет вертикального градиента
            vg_ties, vg_coef = get_vg(self.data)

            # Генерация отчетов
            make_vg_ties_report(vg_ties, os.path.join(result_dir, f"{survey_name}_vg_ties.csv"), verbose=True)
            make_vg_coeffs_report(vg_coef, os.path.join(result_dir, f"{survey_name}_vg_coeffs.csv"), verbose=True)

            # Сохранение графиков
            figs = vg_plot(vg_coef, vg_ties)
            for fig, filename in figs:
                fig.savefig(os.path.join(result_dir, f"{survey_name}_{filename}.png"))

            self.report_text.delete(1.0, tk.END)
            self.report_text.insert(tk.END,
                                    f"The calculation of the vertical gradient is completed. Reports and graphs are saved in {result_dir}.")
            messagebox.showinfo("Successfully", f"The calculation of the vertical gradient is completed. Reports and graphs are saved in {result_dir}")
        except Exception as e:
            messagebox.showerror("Error", f"Error in calculating the vertical gradient: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = GravityApp(root)
    root.mainloop()
