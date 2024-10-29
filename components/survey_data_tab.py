import tkinter as tk
from tkinter import filedialog
from components.input_data_table import InputDataTable
from grav_proc.loader import read_data
from grav_proc.calculations import make_frame_to_proc
import pandas as pd


class SurveyDataTab:
    def __init__(self, notebook):
        self.frame = tk.Frame(notebook)
        self.data_files_entry = None
        self.coeff_files_entry = None
        self.table = None
        self.data = None

        # Левый фрейм для таблицы
        self.table_frame = tk.Frame(self.frame)
        self.table_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Правый фрейм для управления
        controls_frame = tk.Frame(self.frame)
        controls_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Поля выбора файлов данных
        self.data_files_label = tk.Label(controls_frame, text="Survey Data:")
        self.data_files_label.pack(pady=5)
        self.data_files_entry = tk.Entry(controls_frame, width=50)
        self.data_files_entry.pack(pady=5)
        self.data_files_button = tk.Button(controls_frame, text="Import", command=self.load_data_files)
        self.data_files_button.pack(pady=5)

        # Поля выбора файлов коэффициентов
        self.coeff_files_label = tk.Label(controls_frame, text="Calibration Data (optional):")
        self.coeff_files_label.pack(pady=5)
        self.coeff_files_entry = tk.Entry(controls_frame, width=50)
        self.coeff_files_entry.pack(pady=5)
        self.coeff_files_button = tk.Button(controls_frame, text="Import", command=self.load_coeff_files)
        self.coeff_files_button.pack(pady=5)

        # Добавляем кнопку "Use GRS2"
        self.use_grs2_button = tk.Button(controls_frame, text="Use GRS2", command=self.use_grs2)
        self.use_grs2_button.pack(pady=5)

        # Настройка адаптивного изменения размеров
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

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

    def use_grs2(self):
        """Обработка данных в соответствии с требованиями GRS2"""
        if self.data is not None:
            self.data = self.process_grs2_data(self.data)
            # Обновляем отображение таблицы
            if self.table:
                self.table.update_data(self.data)

    def process_grs2_data(self, df):
        """Обработка DataFrame для приведения к программе измерений ГРС2"""
        df = df.copy()
        station_count = 1
        line_count = 1
        survey_count = 0
        station_name = df.iloc[0]['station']
        instrument = df.iloc[0]['instrument_serial_number']
        df['line'] = 0  # Инициализируем колонку 'Line'

        processed_rows = []
        temp_rows = []

        for idx, row in df.iterrows():
            current_station = row['station']
            current_instrument = row['instrument_serial_number']
            if current_instrument != instrument:
                station_count = 1
                instrument = row['instrument_serial_number']
                line_count += 1
                station_name = row['station']
            if current_station == station_name:
                survey_count += 1
                row['line'] = line_count
                temp_rows.append(row.copy())
                processed_rows.append(row.copy())
            else:
                station_count += 1
                if station_count == 5 or station_count == 8:
                    line_count += 1
                    # Дублируем последние survey_count строк
                    for temp_row in temp_rows[-survey_count:]:
                        duplicated_row = temp_row.copy()
                        duplicated_row['line'] = line_count
                        processed_rows.append(duplicated_row)

                # Обновляем station_name и сбрасываем survey_count
                station_name = current_station
                survey_count = 1
                row['line'] = line_count
                temp_rows.append(row.copy())
                processed_rows.append(row.copy())

        df_processed = pd.DataFrame(processed_rows)
        df_processed.reset_index(drop=True, inplace=True)

        return df_processed

    def load_coeff_files(self):
        """Загрузка файлов коэффициентов"""
        file = filedialog.askopenfilename(
            title="Select the Calibration Files",
            filetypes=[("Calibration Files", "*.txt"), ("All files", "*.*")]
        )
        self.coeff_files_entry.delete(0, tk.END)
        self.coeff_files_entry.insert(0, file)

    def get_dataframe(self):
        """Возвращает актуальный DataFrame с текущими данными из таблицы."""
        if self.table:
            # Получаем актуальные данные из таблицы
            return self.table.get_dataframe()
        return self.data  # Возвращаем исходные данные, если таблица еще не создана
