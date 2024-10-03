import os
import tkinter as tk
from tkinter import filedialog, messagebox
from grav_proc.vertical_gradient import get_vg
from grav_proc.plots import vg_plot
from grav_proc.reports import make_vg_ties_report, make_vg_coeffs_report
from grav_proc.loader import read_scale_factors
import pandas as pd

class VGTab:
    def __init__(self, notebook, survey_data_tab):
        self.frame = tk.Frame(notebook)
        self.survey_data_tab = survey_data_tab

        # Кнопка для расчета вертикального градиента
        self.vg_button = tk.Button(self.frame, text="Solve VG", command=self.calculate_vg)
        self.vg_button.pack(pady=10)

        # Поле для отчета с прокрутками
        self.report_text_vg = tk.Text(self.frame, height=10, wrap=tk.NONE)
        self.report_text_vg.pack(fill="both", expand=True)

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

    def calculate_vg(self):
        """Расчет вертикального градиента"""
        try:
            # Получение данных из вкладки Survey Data
            data = self.survey_data_tab.get_dataframe()

            # Применение коэффициентов, если загружены
            data = self.apply_scale_factors(data)

            # Запрашиваем название съемки
            survey_name = os.path.basename(self.survey_data_tab.data_files_entry.get().split(',')[0]).split('.')[0]

            # Выбираем папку для сохранения
            result_dir = self.choose_output_directory(survey_name, "gradient")
            if not result_dir:
                return

            # Расчет вертикального градиента
            vg_ties, vg_coef = get_vg(data)

            # Генерация отчетов и сохранение их в файлы
            ties_report_path = os.path.join(result_dir, f"{survey_name}_vg_ties.csv")
            coeffs_report_path = os.path.join(result_dir, f"{survey_name}_vg_coeffs.csv")
            make_vg_ties_report(vg_ties, ties_report_path, verbose=True)
            make_vg_coeffs_report(vg_coef, coeffs_report_path, verbose=True)

            # Фильтруем только нужные колонки для VG Ties отчета
            vg_ties_filtered = vg_ties[
                ['created_date', 'survey', 'operator', 'meter', 'line', 'from_point', 'to_point', 'from_height', 'to_height', 'gravity',
                 'std_gravity']]
            ties_report_md = vg_ties_filtered.to_markdown(index=False, tablefmt='grid', floatfmt='.3f')

            # Фильтруем только нужные колонки для VG Coefficients отчета
            vg_coef_filtered = vg_coef[['survey', 'a', 'b', 'ua', 'ub', 'covab']]
            coeffs_report_md = vg_coef_filtered.to_markdown(index=False, tablefmt='grid', floatfmt='.3f')

            # Очистка текстового поля и вывод отчетов
            self.report_text_vg.delete(1.0, tk.END)
            self.report_text_vg.insert(tk.END, "Vertical Gradient Ties Report:\n")
            self.report_text_vg.insert(tk.END, ties_report_md)
            self.report_text_vg.insert(tk.END, "\n\nVertical Gradient Coefficients Report:\n")
            self.report_text_vg.insert(tk.END, coeffs_report_md)

            # Сохранение графиков
            figs = vg_plot(vg_coef, vg_ties)
            for fig, filename in figs:
                fig.savefig(os.path.join(result_dir, f"{survey_name}_{filename}.png"))

            messagebox.showinfo("Successfully", f"Vertical gradient calculation completed!")
        except Exception as e:
            messagebox.showerror("Error", f"Error in calculating vertical gradient: {e}")
