import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from tkinter import PanedWindow
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from grav_proc.vertical_gradient import get_vg
from grav_proc.plots import vg_plot
from grav_proc.reports import make_vg_ties_report, make_vg_coeffs_report
from grav_proc.loader import read_scale_factors
import pandas as pd


class VGTab:
    def __init__(self, notebook, survey_data_tab):
        self.frame = tk.Frame(notebook)
        self.survey_data_tab = survey_data_tab

        # Флаги для предотвращения рекурсивных вызовов при изменении sash
        self.updating_main_sash = False
        self.updating_bottom_sash = False

        # Создание вертикального PanedWindow для верхней и нижней части
        self.main_paned_window = PanedWindow(self.frame, orient=tk.VERTICAL)
        self.main_paned_window.pack(fill="both", expand=True)

        # Верхняя часть для кнопки и отчета по ties
        self.top_frame = tk.Frame(self.main_paned_window)
        self.main_paned_window.add(self.top_frame, minsize=100)  # Установка минимального размера

        # Нижняя часть - это еще одно PanedWindow для разделения отчета и графиков
        self.bottom_paned_window = PanedWindow(self.main_paned_window, orient=tk.HORIZONTAL)
        self.main_paned_window.add(self.bottom_paned_window, minsize=100)  # Установка минимального размера

        # Кнопка для расчета вертикального градиента
        self.vg_button = tk.Button(self.top_frame, text="Solve VG", command=self.calculate_vg)
        self.vg_button.pack(pady=10)

        # Поле для отчета с прокрутками (для ties отчета)
        self.report_text_vg_ties = ScrolledText(self.top_frame, height=10, wrap=tk.NONE)
        self.report_text_vg_ties.pack(fill="both", expand=True)

        # Левая часть нижнего окна с прокруткой для отчета по coefficients
        self.left_bottom_frame = tk.Frame(self.bottom_paned_window)
        self.bottom_paned_window.add(self.left_bottom_frame, minsize=100)  # Установка минимального размера

        # Прокручиваемое текстовое поле для отчета по coefficients
        self.report_text_vg_coeffs = ScrolledText(self.left_bottom_frame, height=10, wrap=tk.NONE)
        self.report_text_vg_coeffs.pack(fill="both", expand=True)

        # Правая часть для графиков
        self.graphs_notebook = ttk.Notebook(self.bottom_paned_window)
        self.bottom_paned_window.add(self.graphs_notebook, minsize=100)  # Установка минимального размера

        # Привязка событий <Configure> для установки начальных позиций sash и при изменении размеров
        self.main_paned_window.bind('<Configure>', self.on_main_paned_configure)
        self.bottom_paned_window.bind('<Configure>', self.on_bottom_paned_configure)

        # Установка начальных позиций sash после инициализации интерфейса
        self.frame.after(100, self.set_initial_sash_positions)

        # Создание контекстного меню для копирования
        self.create_context_menu(self.report_text_vg_ties)
        self.create_context_menu(self.report_text_vg_coeffs)

        # Добавление поддержки Ctrl + C для копирования текста
        self.bind_copy_shortcut(self.report_text_vg_ties)
        self.bind_copy_shortcut(self.report_text_vg_coeffs)

    def set_initial_sash_positions(self):
        """Устанавливает начальные позиции sash для main и bottom PanedWindow."""
        self.set_main_paned_sash()
        self.set_bottom_paned_sash()

    def set_main_paned_sash(self):
        """Устанавливает sash для main_paned_window на 50% высоты."""
        if not self.updating_main_sash:
            self.updating_main_sash = True
            self.main_paned_window.update_idletasks()  # Обновляем задачи
            total_height = self.main_paned_window.winfo_height()
            if total_height > 0:
                # Устанавливаем разделитель на половину высоты
                self.main_paned_window.sash_place(0, 0, total_height // 2)
            self.updating_main_sash = False

    def set_bottom_paned_sash(self):
        """Устанавливает sash для bottom_paned_window на 75% ширины."""
        if not self.updating_bottom_sash:
            self.updating_bottom_sash = True
            self.bottom_paned_window.update_idletasks()  # Обновляем задачи
            total_width = self.bottom_paned_window.winfo_width()
            if total_width > 0:
                # Устанавливаем разделитель на 75% ширины
                sash_position = int(total_width * 0.75)
                self.bottom_paned_window.sash_place(0, sash_position, 0)
            self.updating_bottom_sash = False

    def on_main_paned_configure(self, event):
        """Обработчик события <Configure> для main_paned_window."""
        if not self.updating_main_sash:
            self.updating_main_sash = True
            self.main_paned_window.update_idletasks()  # Обновляем задачи
            total_height = self.main_paned_window.winfo_height()
            if total_height > 0:
                # Устанавливаем разделитель на половину высоты
                self.main_paned_window.sash_place(0, 0, total_height // 2)
            self.updating_main_sash = False

    def on_bottom_paned_configure(self, event):
        """Обработчик события <Configure> для bottom_paned_window."""
        if not self.updating_bottom_sash:
            self.updating_bottom_sash = True
            self.bottom_paned_window.update_idletasks()  # Обновляем задачи
            total_width = self.bottom_paned_window.winfo_width()
            if total_width > 0:
                # Устанавливаем разделитель на 75% ширины
                sash_position = int(total_width * 0.75)
                self.bottom_paned_window.sash_place(0, sash_position, 0)
            self.updating_bottom_sash = False

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

    def apply_scale_factors(self, data):
        """Применение коэффициентов, если загружен файл"""
        coeff_file = self.survey_data_tab.coeff_files_entry.get()
        if not coeff_file:
            return data

        # Чтение файла с коэффициентами
        try:
            with open(coeff_file, 'r', encoding='utf-8') as f:
                scale_factors = read_scale_factors([f])
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
                ['created_date', 'survey', 'operator', 'meter', 'line', 'from_point', 'to_point', 'from_height',
                 'to_height', 'gravity',
                 'std_gravity']]
            ties_report_md = vg_ties_filtered.to_markdown(index=False, tablefmt='grid', floatfmt='.3f')

            # Фильтруем только нужные колонки для VG Coefficients отчета
            vg_coef_filtered = vg_coef[['survey', 'a', 'b', 'ua', 'ub', 'covab']]
            coeffs_report_md = vg_coef_filtered.to_markdown(index=False, tablefmt='grid', floatfmt='.3f')

            # Очистка текстового поля и вывод отчетов
            self.report_text_vg_ties.delete(1.0, tk.END)
            self.report_text_vg_ties.insert(tk.END, "Vertical Gradient Ties Report:\n")
            self.report_text_vg_ties.insert(tk.END, ties_report_md)

            self.report_text_vg_coeffs.delete(1.0, tk.END)
            self.report_text_vg_coeffs.insert(tk.END, "Vertical Gradient Coefficients Report:\n")
            self.report_text_vg_coeffs.insert(tk.END, coeffs_report_md)

            # Удаляем все вкладки с графиками перед их обновлением
            for tab in self.graphs_notebook.tabs():
                self.graphs_notebook.forget(tab)

            # Сохранение и отображение графиков
            figs = vg_plot(vg_coef, vg_ties)
            for fig, filename in figs:
                # Настройка графика для предотвращения обрезки
                fig.subplots_adjust(left=0.2, right=0.8, top=0.9, bottom=0.15)  # Настройка боковых и вертикальных отступов отдельно

                # Сохранение оригинальной фигуры
                fig.savefig(os.path.join(result_dir, f"{survey_name}_{filename}.png"))

                # Создаем новый Canvas для каждого графика и добавляем его во вкладки Notebook
                canvas_frame = tk.Frame(self.graphs_notebook)
                canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
                self.graphs_notebook.add(canvas_frame, text=filename)

            messagebox.showinfo("Successfully", f"Vertical gradient calculation completed!")
        except Exception as e:
            messagebox.showerror("Error", f"Error in calculating vertical gradient: {e}")
