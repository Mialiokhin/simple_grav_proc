import tkinter as tk
from tkinter import filedialog, messagebox
from components.input_data_table import InputDataTable
from grav_proc.loader import read_data
from grav_proc.calculations import make_frame_to_proc
from grav_proc.tidal import TIDEFF
import pandas as pd
from contextlib import ExitStack


class SurveyDataTab:
    def __init__(self, notebook):
        self.frame = tk.Frame(notebook)
        self.data_files_entry = None
        self.coeff_files_entry = None
        self.table = None
        self.data = None

        # Хранение текущих значений выбранной станции и серии
        self.current_station_name = None
        self.current_station_lat = None
        self.current_station_lon = None

        self.current_series_id = None
        self.current_series_station_name = None
        self.current_series_lat = None
        self.current_series_lon = None
        self.current_series_pressure = None

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

        # Добавляем фрейм для размещения кнопок в одну строку
        buttons_frame = tk.Frame(controls_frame)
        buttons_frame.pack(pady=5)

        # Кнопка "Use GRS2"
        self.use_grs2_button = tk.Button(buttons_frame, text="Use GRS2", command=self.use_grs2)
        self.use_grs2_button.pack(side='left', padx=5)

        # Кнопка "Calc Tide"
        self.calc_tide_button = tk.Button(buttons_frame, text="Calc Tide", command=self.calculate_tidal_correction)
        self.calc_tide_button.pack(side='left', padx=5)

        # Кнопка "Calc Pressure Correction"
        self.calc_pressure_button = tk.Button(
            buttons_frame, text="Calc Pressure Correction",
            command=self.calculate_pressure_correction
        )
        self.calc_pressure_button.pack(side='left', padx=5)

        # Переключатель режима: Edit Station или Edit Series
        self.mode_var = tk.StringVar(value="edit_station")
        self.edit_station_radio = tk.Radiobutton(
            controls_frame, text="Edit Station", variable=self.mode_var,
            value="edit_station", command=self.update_mode
        )
        self.edit_station_radio.pack(pady=5)
        self.edit_series_radio = tk.Radiobutton(
            controls_frame, text="Edit Series", variable=self.mode_var,
            value="edit_series", command=self.update_mode
        )
        self.edit_series_radio.pack(pady=5)

        # Фрейм для редактирования станций
        self.edit_station_frame = tk.Frame(controls_frame)
        self.edit_station_frame.pack(pady=5)

        self.station_list_label = tk.Label(self.edit_station_frame, text="Stations:")
        self.station_list_label.pack(pady=5)
        self.station_listbox = tk.Listbox(
            self.edit_station_frame, selectmode=tk.SINGLE,
            exportselection=False, height=10
        )
        self.station_listbox.pack(pady=5)
        self.station_listbox.bind('<<ListboxSelect>>', self.on_station_select)

        self.rename_station_label = tk.Label(self.edit_station_frame, text="Edit:")
        self.rename_station_label.pack(pady=5)

        self.station_lat_label = tk.Label(self.edit_station_frame, text="Latitude:")
        self.station_lat_label.pack(pady=2)
        self.station_lat_entry = tk.Entry(self.edit_station_frame, width=30)
        self.station_lat_entry.pack(pady=2)

        self.station_lon_label = tk.Label(self.edit_station_frame, text="Longitude:")
        self.station_lon_label.pack(pady=2)
        self.station_lon_entry = tk.Entry(self.edit_station_frame, width=30)
        self.station_lon_entry.pack(pady=2)

        self.series_station_label = tk.Label(self.edit_station_frame, text="Station Name:")
        self.series_station_label.pack(pady=2)
        self.rename_station_entry = tk.Entry(self.edit_station_frame, width=30)
        self.rename_station_entry.pack(pady=5)

        # Объединённая кнопка сохранения для станций
        self.save_station_changes_button = tk.Button(
            self.edit_station_frame, text="Save Changes",
            command=self.save_station_changes
        )
        self.save_station_changes_button.pack(pady=5)

        # Фрейм для редактирования серий
        self.edit_series_frame = tk.Frame(controls_frame)
        # Изначально скрываем
        self.edit_series_frame.pack_forget()

        self.series_list_label = tk.Label(self.edit_series_frame, text="Series:")
        self.series_list_label.pack(pady=5)
        self.series_listbox = tk.Listbox(
            self.edit_series_frame, selectmode=tk.SINGLE,
            exportselection=False, height=10
        )
        self.series_listbox.pack(pady=5)
        self.series_listbox.bind('<<ListboxSelect>>', self.on_series_select)

        self.series_coords_label = tk.Label(self.edit_series_frame, text="Edit Coordinates:")
        self.series_coords_label.pack(pady=5)

        self.series_lat_label = tk.Label(self.edit_series_frame, text="Latitude:")
        self.series_lat_label.pack(pady=2)
        self.series_lat_entry = tk.Entry(self.edit_series_frame, width=30)
        self.series_lat_entry.pack(pady=2)

        self.series_lon_label = tk.Label(self.edit_series_frame, text="Longitude:")
        self.series_lon_label.pack(pady=2)
        self.series_lon_entry = tk.Entry(self.edit_series_frame, width=30)
        self.series_lon_entry.pack(pady=2)

        # Добавление полей для изменения названия станции при редактировании серии
        self.series_station_label = tk.Label(self.edit_series_frame, text="Station Name:")
        self.series_station_label.pack(pady=5)
        self.series_station_entry = tk.Entry(self.edit_series_frame, width=30)
        self.series_station_entry.pack(pady=2)

        # Добавление поля для ввода атмосферного давления
        self.pressure_label = tk.Label(self.edit_series_frame, text="Atmospheric Pressure (hPa):")
        self.pressure_label.pack(pady=5)
        self.pressure_entry = tk.Entry(self.edit_series_frame, width=30)
        self.pressure_entry.pack(pady=5)

        # Объединённая кнопка сохранения для серий
        self.save_series_changes_button = tk.Button(
            self.edit_series_frame, text="Save Changes",
            command=self.save_series_changes
        )
        self.save_series_changes_button.pack(pady=5)

        # Настройка адаптивного изменения размеров
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

    def update_mode(self):
        """Обновление интерфейса в зависимости от выбранного режима"""
        mode = self.mode_var.get()
        if mode == "edit_station":
            self.edit_station_frame.pack(pady=5)
            self.edit_series_frame.pack_forget()
        elif mode == "edit_series":
            self.edit_station_frame.pack_forget()
            self.edit_series_frame.pack(pady=5)

    def load_data_files(self):
        """Загрузка файлов данных и отображение в таблице"""
        files = filedialog.askopenfilenames(
            title="Select the data files",
            filetypes=[("CG-6 Data Files", "*.dat"), ("All files", "*.*")]
        )
        self.data_files_entry.delete(0, tk.END)
        self.data_files_entry.insert(0, ','.join(files))

        if not files:
            return

        try:
            # Загрузка данных с безопасным открытием файлов
            with ExitStack() as stack:
                data_files = [stack.enter_context(open(file, 'r', encoding='utf-8')) for file in files]
                raw_data = read_data(data_files)

            self.data = make_frame_to_proc(raw_data)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {e}")
            return

        # Проверка наличия необходимых столбцов
        required_columns = ['station', 'instrument_serial_number', 'created', 'line', 'lat', 'lon', 'corr_grav',
                            'date_time']
        missing_columns = [col for col in required_columns if col not in self.data.columns]
        if missing_columns:
            messagebox.showerror("Ошибка", f"Отсутствуют необходимые столбцы: {', '.join(missing_columns)}")
            return

        # Добавляем колонку для серии, изменяя series_id при изменении любого из указанных столбцов
        self.data['series_id'] = (
            self.data[['station', 'instrument_serial_number', 'created', 'line']]
            .ne(self.data[['station', 'instrument_serial_number', 'created', 'line']].shift())
            .any(axis=1)
            .cumsum()
        )

        # Добавляем колонку для атмосферного давления, если её нет
        if 'pressure' not in self.data.columns:
            self.data['pressure'] = None

        # Если таблица уже существует, удаляем её перед созданием новой
        if self.table:
            self.table.tree.pack_forget()
            self.table.v_scroll.pack_forget()
            self.table.h_scroll.pack_forget()

        # Отображаем данные в таблице
        self.table = InputDataTable(self.table_frame, self.data)

        # Обновляем списки в Listbox
        self.update_station_listbox()
        self.update_series_listbox()

    def update_station_listbox(self):
        """Обновление списка уникальных станций в Listbox"""
        if self.data is not None:
            # Получаем уникальные названия станций
            unique_stations = sorted(self.data['station'].unique())
            # Очищаем Listbox
            self.station_listbox.delete(0, tk.END)
            # Заполняем Listbox уникальными названиями станций
            for station in unique_stations:
                self.station_listbox.insert(tk.END, station)

    def update_series_listbox(self):
        """Обновление списка серий в Listbox"""
        if self.data is not None:
            # Получаем уникальные серии
            unique_series = self.data[['series_id', 'station', 'line']].drop_duplicates().sort_values('series_id')
            # Очищаем Listbox
            self.series_listbox.delete(0, tk.END)
            # Заполняем Listbox сериями
            for _, row in unique_series.iterrows():
                series_text = f"line{row['line']}-S{row['series_id']}-{row['station']}"
                self.series_listbox.insert(tk.END, series_text)

    def save_station_changes(self):
        """Сохранение изменений станции: переименование и координат"""
        selected_index = self.station_listbox.curselection()
        if selected_index:
            station_name = self.station_listbox.get(selected_index)
            new_name = self.rename_station_entry.get().strip()
            new_lat_str = self.station_lat_entry.get().strip()
            new_lon_str = self.station_lon_entry.get().strip()

            changes_made = False  # Флаг, указывающий на наличие изменений

            # Проверяем и обновляем название станции, если введено новое имя и оно отличается
            if new_name and new_name != station_name:
                self.data.loc[self.data['station'] == station_name, 'station'] = new_name
                changes_made = True

            # Проверяем и обновляем широту, если введено новое значение и оно отличается
            if new_lat_str:
                try:
                    new_lat = float(new_lat_str.replace(",", "."))
                    current_lat = self.data.loc[self.data['station'] == new_name if new_name else station_name, 'lat'].iloc[0]
                    if new_lat != current_lat:
                        self.data.loc[self.data['station'] == (new_name if new_name else station_name), 'lat'] = new_lat
                        changes_made = True
                except ValueError:
                    messagebox.showwarning("Предупреждение",
                                           "Пожалуйста, введите корректное числовое значение для широты.")
                    return

            # Проверяем и обновляем долготу, если введено новое значение и оно отличается
            if new_lon_str:
                try:
                    new_lon = float(new_lon_str.replace(",", "."))
                    current_lon = self.data.loc[self.data['station'] == (new_name if new_name else station_name), 'lon'].iloc[0]
                    if new_lon != current_lon:
                        self.data.loc[self.data['station'] == (new_name if new_name else station_name), 'lon'] = new_lon
                        changes_made = True
                except ValueError:
                    messagebox.showwarning("Предупреждение",
                                           "Пожалуйста, введите корректное числовое значение для долготы.")
                    return

            if changes_made:
                # Обновляем отображение таблицы
                self.table.update_data(self.data)

                # Обновляем списки
                self.update_station_listbox()
                self.update_series_listbox()

                # Очищаем поля ввода
                self.rename_station_entry.delete(0, tk.END)
                self.station_lat_entry.delete(0, tk.END)
                self.station_lon_entry.delete(0, tk.END)

                messagebox.showinfo("Информация", f"Станция '{station_name}' успешно обновлена.")
            else:
                messagebox.showinfo("Информация", "Нет изменений для сохранения.")
        else:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите станцию для изменения.")

    def save_series_changes(self):
        """Сохранение изменений серии: переименование станции, координат и давления"""
        selected_index = self.series_listbox.curselection()
        if selected_index:
            series_id = self.data['series_id'].unique()[selected_index[0]]
            new_station_name = self.series_station_entry.get().strip()
            new_lat_str = self.series_lat_entry.get().strip()
            new_lon_str = self.series_lon_entry.get().strip()
            new_pressure_str = self.pressure_entry.get().strip()

            changes_made = False  # Флаг, указывающий на наличие изменений

            # Проверяем и обновляем название станции, если введено новое имя и оно отличается
            if new_station_name and new_station_name != self.data.loc[self.data['series_id'] == series_id, 'station'].iloc[0]:
                self.data.loc[self.data['series_id'] == series_id, 'station'] = new_station_name
                changes_made = True

            # Проверяем и обновляем широту, если введено новое значение и оно отличается
            if new_lat_str:
                try:
                    new_lat = float(new_lat_str.replace(",", "."))
                    current_lat = self.data.loc[self.data['series_id'] == series_id, 'lat'].iloc[0]
                    if new_lat != current_lat:
                        self.data.loc[self.data['series_id'] == series_id, 'lat'] = new_lat
                        changes_made = True
                except ValueError:
                    messagebox.showwarning("Предупреждение",
                                           "Пожалуйста, введите корректное числовое значение для широты.")
                    return

            # Проверяем и обновляем долготу, если введено новое значение и оно отличается
            if new_lon_str:
                try:
                    new_lon = float(new_lon_str.replace(",", "."))
                    current_lon = self.data.loc[self.data['series_id'] == series_id, 'lon'].iloc[0]
                    if new_lon != current_lon:
                        self.data.loc[self.data['series_id'] == series_id, 'lon'] = new_lon
                        changes_made = True
                except ValueError:
                    messagebox.showwarning("Предупреждение",
                                           "Пожалуйста, введите корректное числовое значение для долготы.")
                    return

            # Проверяем и обновляем атмосферное давление, если введено новое значение и оно отличается
            if new_pressure_str:
                try:
                    new_pressure = float(new_pressure_str.replace(",", "."))
                    current_pressure = self.data.loc[self.data['series_id'] == series_id, 'pressure'].iloc[0]
                    if pd.isnull(current_pressure) or new_pressure != current_pressure:
                        self.data.loc[self.data['series_id'] == series_id, 'pressure'] = new_pressure
                        changes_made = True
                except ValueError:
                    messagebox.showwarning("Предупреждение",
                                           "Пожалуйста, введите корректное числовое значение для давления.")
                    return

            if changes_made:
                # Обновляем отображение таблицы
                self.table.update_data(self.data)

                # Обновляем списки
                self.update_station_listbox()
                self.update_series_listbox()

                # Очищаем поля ввода
                self.series_station_entry.delete(0, tk.END)
                self.series_lat_entry.delete(0, tk.END)
                self.series_lon_entry.delete(0, tk.END)
                self.pressure_entry.delete(0, tk.END)

                messagebox.showinfo("Информация", f"Серия {series_id} успешно обновлена.")
            else:
                messagebox.showinfo("Информация", "Нет изменений для сохранения.")
        else:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите серию для изменения.")

    def on_station_select(self, event):
        """Обработчик выбора станции в Listbox"""
        selected_index = self.station_listbox.curselection()
        if selected_index:
            station_name = self.station_listbox.get(selected_index)
            self.current_station_name = station_name
            # Получаем текущие координаты для этой станции
            station_data = self.data[self.data['station'] == station_name]
            if not station_data.empty:
                self.current_station_lat = station_data.iloc[0]['lat']
                self.current_station_lon = station_data.iloc[0]['lon']
                # Заполняем поля ввода координат
                self.station_lat_entry.delete(0, tk.END)
                self.station_lat_entry.insert(0, str(self.current_station_lat))
                self.station_lon_entry.delete(0, tk.END)
                self.station_lon_entry.insert(0, str(self.current_station_lon))
                # Заполняем поле для переименования текущим названием станции
                self.rename_station_entry.delete(0, tk.END)
                self.rename_station_entry.insert(0, station_name)

    def on_series_select(self, event):
        """Обработчик выбора серии в Listbox"""
        selected_index = self.series_listbox.curselection()
        if selected_index:
            series_id = self.data['series_id'].unique()[selected_index[0]]
            self.current_series_id = series_id
            series_data = self.data[self.data['series_id'] == series_id]
            if not series_data.empty:
                self.current_series_station_name = series_data.iloc[0]['station']
                self.current_series_lat = series_data.iloc[0]['lat']
                self.current_series_lon = series_data.iloc[0]['lon']
                self.current_series_pressure = series_data.iloc[0].get('pressure', None)
                # Заполняем поля ввода координат, названия станции и давления
                self.series_lat_entry.delete(0, tk.END)
                self.series_lat_entry.insert(0, str(self.current_series_lat))
                self.series_lon_entry.delete(0, tk.END)
                self.series_lon_entry.insert(0, str(self.current_series_lon))
                self.series_station_entry.delete(0, tk.END)
                self.series_station_entry.insert(0, self.current_series_station_name)
                self.pressure_entry.delete(0, tk.END)
                if pd.notnull(self.current_series_pressure):
                    self.pressure_entry.insert(0, str(self.current_series_pressure))
                else:
                    self.pressure_entry.insert(0, "")

    def calculate_pressure_correction(self):
        """Расчет и применение поправок за атмосферное давление"""
        if self.data is not None:
            # Стандартное атмосферное давление
            P0 = 1013.25  # hPa
            # Коэффициент чувствительности
            k = 0.003274  # может отличаться в зависимости от оборудования

            # Проверяем, что давление введено для всех серий
            if self.data['pressure'].isnull().any():
                messagebox.showwarning("Предупреждение", "Необходимо ввести атмосферное давление для всех серий.")
                return

            # Рассчитываем поправку для каждой серии
            pressure_corrections = self.data.groupby('series_id')['pressure'].first().apply(lambda P: k * (P - P0))

            # Добавляем колонку 'pressure_corr', если её нет
            if 'pressure_corr' not in self.data.columns:
                self.data['pressure_corr'] = 0.0

            # Применяем поправку к corr_grav для каждой серии
            for series_id, correction in pressure_corrections.items():
                self.data.loc[self.data['series_id'] == series_id, 'pressure_corr'] = round(correction, 4)
                self.data.loc[self.data['series_id'] == series_id, 'corr_grav'] += correction

            # Округляем corr_grav для отображения
            self.data['corr_grav'] = self.data['corr_grav'].round(4)

            # Обновляем отображение таблицы
            self.table.update_data(self.data)

            messagebox.showinfo("Информация", "Поправки за атмосферное давление успешно рассчитаны и применены.")

    def calculate_tidal_correction(self):
        """Расчет и применение приливных поправок"""
        if self.data is not None:
            # Пробегаем по каждой строке и вычисляем приливную поправку
            for idx, row in self.data.iterrows():
                lat = row['lat']
                lon = row['lon']
                date = pd.to_datetime(row['date_time'])

                # Рассчитываем новую приливную поправку с использованием функции TIDEFF
                new_tide_corr = TIDEFF(lat, lon, date.day, date.month, date.year, date.hour, date.minute)

                # Обновляем значение в колонке 'tide_corr'
                self.data.at[idx, 'corr_grav'] = row['corr_grav'] - row.get('tide_corr', 0) + new_tide_corr
                self.data.at[idx, 'tide_corr'] = round(new_tide_corr, 4)

            # Округляем corr_grav для отображения
            self.data['corr_grav'] = self.data['corr_grav'].round(4)

            # Обновляем отображение таблицы
            self.table.update_data(self.data)

            messagebox.showinfo("Информация", "Приливные поправки успешно рассчитаны и применены.")

    def use_grs2(self):
        """Обработка данных в соответствии с требованиями GRS2"""
        if self.data is not None:
            self.data = self.process_grs2_data(self.data)
            # Обновляем отображение таблицы
            if self.table:
                self.table.update_data(self.data)
            # Обновляем списки
            self.update_station_listbox()
            self.update_series_listbox()

    def process_grs2_data(self, df):
        """Обработка DataFrame для приведения к программе измерений ГРС2"""
        df = df.copy()
        station_count = 1
        line_count = 1
        survey_count = 0
        station_name = df.iloc[0]['station']
        instrument = df.iloc[0]['instrument_serial_number']
        created = df.iloc[0]['created']
        df['line'] = 0  # Инициализируем колонку 'Line'

        processed_rows = []
        temp_rows = []

        for idx, row in df.iterrows():
            current_station = row['station']
            current_instrument = row['instrument_serial_number']
            current_created = row['created']
            if current_instrument != instrument or current_created != created:
                station_count = 1
                instrument = row['instrument_serial_number']
                created = row['created']
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
