import tkinter as tk
from tkinter import filedialog
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
        self.current_station_pressure = None

        self.current_series_id = None
        self.current_series_station_name = None
        self.current_series_lat = None
        self.current_series_lon = None
        self.current_series_pressure = None
        self.current_series_line = None

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

        # Добавляем кнопку "Check" в интерфейс
        self.check_button = tk.Button(buttons_frame, text="Check", command=self.checks)
        self.check_button.pack(side='left', padx=5)

        # Переключатель режима: Edit Station или Edit Series
        mode_frame = tk.Frame(controls_frame)
        mode_frame.pack(pady=5)

        self.mode_var = tk.StringVar(value="edit_station")

        self.edit_station_radio = tk.Radiobutton(
            mode_frame, text="Edit Station", variable=self.mode_var,
            value="edit_station", command=self.update_mode
        )
        self.edit_station_radio.pack(side='left', padx=10, pady=5)

        self.edit_series_radio = tk.Radiobutton(
            mode_frame, text="Edit Series", variable=self.mode_var,
            value="edit_series", command=self.update_mode
        )
        self.edit_series_radio.pack(side='left', padx=10, pady=5)

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

        # Создаем субфрейм для координат (Lat и Lon)
        station_coords_frame = tk.Frame(self.edit_station_frame)
        station_coords_frame.pack(pady=2)

        self.station_lat_label = tk.Label(station_coords_frame, text="Lat:")
        self.station_lat_label.pack(side='left', padx=(0, 5))
        self.station_lat_entry = tk.Entry(station_coords_frame, width=20)
        self.station_lat_entry.pack(side='left', padx=(0, 15))

        self.station_lon_label = tk.Label(station_coords_frame, text="Lon:")
        self.station_lon_label.pack(side='left', padx=(0, 5))
        self.station_lon_entry = tk.Entry(station_coords_frame, width=20)
        self.station_lon_entry.pack(side='left')

        # Субфрейм для имени станции и давления (в одну строчку)
        station_name_pressure_frame = tk.Frame(self.edit_station_frame)
        station_name_pressure_frame.pack(pady=2)

        self.series_station_label = tk.Label(station_name_pressure_frame, text="Station Name:")
        self.series_station_label.pack(side='left', padx=(0, 5))
        self.rename_station_entry = tk.Entry(station_name_pressure_frame, width=20)
        self.rename_station_entry.pack(side='left', padx=(0, 15))

        self.pressure_label_station = tk.Label(station_name_pressure_frame, text="Pressure (hPa):")
        self.pressure_label_station.pack(side='left', padx=(0, 5))
        self.pressure_entry_station = tk.Entry(station_name_pressure_frame, width=20)
        self.pressure_entry_station.pack(side='left')

        station_height_frame = tk.Frame(self.edit_station_frame)
        station_height_frame.pack(pady=2)

        self.station_height_label = tk.Label(station_height_frame, text="Instr.Height(mm):")
        self.station_height_label.pack(side='left', padx=(0, 5))
        self.station_height_entry = tk.Entry(station_height_frame, width=20)
        self.station_height_entry.pack(side='left')

        # Фрейм для кнопок управления станцией
        station_buttons_frame = tk.Frame(self.edit_station_frame)
        station_buttons_frame.pack(pady=5)

        # Кнопка сохранения изменений станции
        self.save_station_changes_button = tk.Button(
            station_buttons_frame, text="Save Changes",
            command=self.save_station_changes
        )
        self.save_station_changes_button.pack(side='left', padx=5)

        # Кнопка удаления станции
        self.delete_station_button = tk.Button(
            station_buttons_frame, text="Delete",
            command=self.delete_station
        )
        self.delete_station_button.pack(side='left', padx=5)

        # Фрейм для редактирования серий
        self.edit_series_frame = tk.Frame(controls_frame)
        # Изначально скрываем
        self.edit_series_frame.pack_forget()

        self.series_list_label = tk.Label(self.edit_series_frame, text="Series:\nline-survey-instrument-series-station")
        self.series_list_label.pack(pady=5)
        self.series_listbox = tk.Listbox(
            self.edit_series_frame, selectmode=tk.SINGLE,
            exportselection=False, height=10, width=50
        )
        self.series_listbox.pack(pady=5)
        self.series_listbox.bind('<<ListboxSelect>>', self.on_series_select)

        # Создаем субфрейм для координат (Lat и Lon)
        series_coords_frame = tk.Frame(self.edit_series_frame)
        series_coords_frame.pack(pady=2)

        self.series_lat_label = tk.Label(series_coords_frame, text="Lat:")
        self.series_lat_label.pack(side='left', padx=(0, 5))
        self.series_lat_entry = tk.Entry(series_coords_frame, width=20)
        self.series_lat_entry.pack(side='left', padx=(0, 15))

        self.series_lon_label = tk.Label(series_coords_frame, text="Lon:")
        self.series_lon_label.pack(side='left', padx=(0, 5))
        self.series_lon_entry = tk.Entry(series_coords_frame, width=20)
        self.series_lon_entry.pack(side='left')

        # Субфрейм для имени станции и давления (в одну строчку)
        series_name_pressure_frame = tk.Frame(self.edit_series_frame)
        series_name_pressure_frame.pack(pady=2)

        self.series_station_label = tk.Label(series_name_pressure_frame, text="Station Name:")
        self.series_station_label.pack(side='left', padx=(0, 5))
        self.series_station_entry = tk.Entry(series_name_pressure_frame, width=20)
        self.series_station_entry.pack(side='left', padx=(0, 15))

        self.pressure_label = tk.Label(series_name_pressure_frame, text="Pressure (hPa):")
        self.pressure_label.pack(side='left', padx=(0, 5))
        self.pressure_entry = tk.Entry(series_name_pressure_frame, width=20)
        self.pressure_entry.pack(side='left')

        # Субфрейм для линии и высоты инструмента (в одну строчку)
        series_line_frame = tk.Frame(self.edit_series_frame)
        series_line_frame.pack(pady=2)

        self.series_line_label = tk.Label(series_line_frame, text="Line:")
        self.series_line_label.pack(side='left', padx=(0, 5))
        self.series_line_entry = tk.Entry(series_line_frame, width=20)
        self.series_line_entry.pack(side='left', padx=(0, 15))

        self.series_height_label = tk.Label(series_line_frame, text="Instr.Height(mm):")
        self.series_height_label.pack(side='left', padx=(0, 5))
        self.series_height_entry = tk.Entry(series_line_frame, width=20)
        self.series_height_entry.pack(side='left')

        # Фрейм для кнопок управления серией
        series_buttons_frame = tk.Frame(self.edit_series_frame)
        series_buttons_frame.pack(pady=5)

        # Кнопка сохранения изменений серии
        self.save_series_changes_button = tk.Button(
            series_buttons_frame, text="Save Changes",
            command=self.save_series_changes
        )
        self.save_series_changes_button.pack(side='left', padx=5)

        # Кнопка удаления серии
        self.delete_series_button = tk.Button(
            series_buttons_frame, text="Delete",
            command=self.delete_series
        )
        self.delete_series_button.pack(side='left', padx=5)

        self.copy_series_button = tk.Button(
            series_buttons_frame, text="Copy",
            command=self.copy_selected_series
        )
        self.copy_series_button.pack(side='left', padx=5)

        # Добавляем фрейм для сообщений и размещаем его внизу
        message_frame = tk.Frame(controls_frame)
        message_frame.pack(side='bottom', fill='x', pady=10)

        # Используем Text виджет для отображения сообщений
        self.message_text = tk.Text(
            message_frame, width=50, height=4,
            wrap='word', relief='sunken', state='disabled'
        )
        self.message_text.pack(fill='both', expand=True)

        # Настройка адаптивного изменения размеров
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

    def display_message(self, message, message_type="info"):
        """Отображение сообщения в message_text с соответствующим цветом фона."""
        colors = {
            "error": "#ffcccc",  # pale red
            "warning": "#ffebcc",  # pale orange
            "success": "#ccffcc",  # pale green
            "info": "#ccffcc"  # treat info as success
        }
        bg_color = colors.get(message_type, "#ccffcc")  # default to pale green

        self.message_text.configure(state='normal', bg=bg_color)
        self.message_text.delete(1.0, tk.END)
        self.message_text.insert(tk.END, message)
        self.message_text.configure(state='disabled')

    def update_mode(self):
        """Обновление интерфейса в зависимости от выбранного режима"""
        mode = self.mode_var.get()
        if mode == "edit_station":
            self.edit_series_frame.pack_forget()
            self.edit_station_frame.pack(pady=5)
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

            self.data = make_frame_to_proc(raw_data).copy()
        except Exception as e:
            self.display_message(f"Не удалось загрузить данные: {e}", message_type="error")
            return

        # Проверка наличия необходимых столбцов
        required_columns = ['station', 'instrument_serial_number', 'created', 'line', 'lat', 'lon', 'corr_grav',
                            'date_time']
        missing_columns = [col for col in required_columns if col not in self.data.columns]
        if missing_columns:
            self.display_message(f"Отсутствуют необходимые столбцы: {', '.join(missing_columns)}", message_type="error")
            return

        # Добавляем колонку для серии
        self.update_series_id()

        # Добавляем колонку для атмосферного давления, если её нет
        if 'pressure' not in self.data.columns:
            self.data.loc[:, 'pressure'] = None

        # Если таблица уже существует, удаляем её перед созданием новой
        if self.table:
            self.table.tree.pack_forget()
            self.table.v_scroll.pack_forget()
            self.table.h_scroll.pack_forget()

        # Отображаем данные в таблице
        self.table = InputDataTable(self.table_frame, self.data, data_modified_callback=self.on_data_modified)

        # Обновляем списки в Listbox
        self.update_station_listbox()
        self.update_series_listbox()

    def update_series_id(self):
        """Обновление столбца 'series_id' на основе текущих данных"""
        if self.data is not None:
            self.data = self.data.copy()
            self.data['series_id'] = (
                self.data[['station', 'instrument_serial_number', 'created', 'line']]
                .ne(self.data[['station', 'instrument_serial_number', 'created', 'line']].shift())
                .any(axis=1)
                .cumsum()
            )

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
            unique_series = self.data[
                ['series_id', 'station', 'line', 'instrument_serial_number',
                 'survey_name']].drop_duplicates().sort_values(
                'series_id')
            # Очищаем Listbox
            self.series_listbox.delete(0, tk.END)
            # Заполняем Listbox сериями
            for _, row in unique_series.iterrows():
                instr_serial = str(row['instrument_serial_number'])[-3:]
                series_text = f"line{row['line']}-({row['survey_name']})-<{instr_serial}>-S{row['series_id']}-{row['station']}"
                self.series_listbox.insert(tk.END, series_text)

    def save_station_changes(self):
        """Сохранение изменений станции: переименование, координаты и давление"""
        selected_index = self.station_listbox.curselection()
        if selected_index:
            station_name = self.station_listbox.get(selected_index)
            new_name = self.rename_station_entry.get().strip()
            new_lat_str = self.station_lat_entry.get().strip()
            new_lon_str = self.station_lon_entry.get().strip()
            new_pressure_str = self.pressure_entry_station.get().strip()
            new_height_str = self.station_height_entry.get().strip()

            changes_made = False  # Флаг, указывающий на наличие изменений

            # Проверяем и обновляем высоту инструмента
            if new_height_str:
                try:
                    new_height = float(new_height_str.replace(",", "."))
                    current_height = self.data.loc[self.data['station'] == station_name, 'instr_height'].iloc[0]
                    if new_height != current_height:
                        self.data.loc[self.data['station'] == station_name, 'instr_height'] = new_height
                        changes_made = True
                except ValueError:
                    self.display_message("Пожалуйста, введите корректное значение для высоты инструмента.",
                                         message_type="warning")
                    return

            # Проверяем и обновляем название станции, если введено новое имя и оно отличается
            if new_name and new_name != station_name:
                self.data.loc[self.data['station'] == station_name, 'station'] = new_name
                changes_made = True

            # Проверяем и обновляем широту, если введено новое значение и оно отличается
            if new_lat_str:
                try:
                    new_lat = float(new_lat_str.replace(",", "."))
                    current_lat = self.data.loc[
                        self.data['station'] == (new_name if new_name else station_name), 'lat'
                    ].iloc[0]
                    if new_lat != current_lat:
                        self.data.loc[self.data['station'] == (new_name if new_name else station_name), 'lat'] = new_lat
                        changes_made = True
                except ValueError:
                    self.display_message("Пожалуйста, введите корректное числовое значение для широты.",
                                         message_type="warning")
                    return

            # Проверяем и обновляем долготу, если введено новое значение и оно отличается
            if new_lon_str:
                try:
                    new_lon = float(new_lon_str.replace(",", "."))
                    current_lon = self.data.loc[
                        self.data['station'] == (new_name if new_name else station_name), 'lon'
                    ].iloc[0]
                    if new_lon != current_lon:
                        self.data.loc[self.data['station'] == (new_name if new_name else station_name), 'lon'] = new_lon
                        changes_made = True
                except ValueError:
                    self.display_message("Пожалуйста, введите корректное числовое значение для долготы.",
                                         message_type="warning")
                    return

            # Проверяем и обновляем атмосферное давление, если введено новое значение и оно отличается
            if new_pressure_str:
                try:
                    new_pressure = float(new_pressure_str.replace(",", "."))
                    current_pressure = self.data.loc[
                        self.data['station'] == (new_name if new_name else station_name), 'pressure'
                    ].iloc[0]
                    if pd.isnull(current_pressure) or new_pressure != current_pressure:
                        self.data.loc[
                            self.data['station'] == (new_name if new_name else station_name), 'pressure'] = new_pressure
                        changes_made = True
                except ValueError:
                    self.display_message("Пожалуйста, введите корректное числовое значение для давления.",
                                         message_type="warning")
                    return

            if changes_made:
                # Обновляем series_id
                self.update_series_id()

                # Обновляем отображение таблицы
                self.table.update_data(self.data)

                # Обновляем списки
                self.update_station_listbox()
                self.update_series_listbox()

                # Очищаем поля ввода
                self.rename_station_entry.delete(0, tk.END)
                self.station_lat_entry.delete(0, tk.END)
                self.station_lon_entry.delete(0, tk.END)
                self.pressure_entry_station.delete(0, tk.END)

                self.display_message(f"Станция '{station_name}' успешно обновлена.", message_type="success")
            else:
                self.display_message("Нет изменений для сохранения.", message_type="success")
        else:
            self.display_message("Пожалуйста, выберите станцию для изменения.", message_type="warning")

    def delete_station(self):
        """Удаление выбранной станции"""
        selected_index = self.station_listbox.curselection()
        if selected_index:
            station_name = self.station_listbox.get(selected_index)
            # Удаляем данные станции из DataFrame
            self.data = self.data[self.data['station'] != station_name].copy()
            # Обновляем series_id после удаления
            self.update_series_id()
            # Обновляем отображение таблицы
            self.table.update_data(self.data)
            # Обновляем списки
            self.update_station_listbox()
            self.update_series_listbox()
            # Очищаем поля ввода
            self.rename_station_entry.delete(0, tk.END)
            self.station_lat_entry.delete(0, tk.END)
            self.station_lon_entry.delete(0, tk.END)
            self.pressure_entry_station.delete(0, tk.END)
            self.display_message(f"Станция '{station_name}' успешно удалена.", message_type="success")
        else:
            self.display_message("Пожалуйста, выберите станцию для удаления.", message_type="warning")

    def save_series_changes(self):
        """Сохранение изменений серии: переименование станции, координат и давления"""
        selected_index = self.series_listbox.curselection()
        if selected_index:
            series_id = self.data['series_id'].unique()[selected_index[0]]
            new_station_name = self.series_station_entry.get().strip()
            new_lat_str = self.series_lat_entry.get().strip()
            new_lon_str = self.series_lon_entry.get().strip()
            new_pressure_str = self.pressure_entry.get().strip()
            new_line_str = self.series_line_entry.get().strip()
            new_height_str = self.series_height_entry.get().strip()
            changes_made = False  # Флаг, указывающий на наличие изменений
            pressure_changed = False  # Флаг, указывающий на изменение давления

            # Проверяем и обновляем высоту инструмента
            if new_height_str:
                try:
                    new_height = float(new_height_str.replace(",", "."))
                    current_height = self.data.loc[self.data['series_id'] == series_id, 'instr_height'].iloc[0]
                    if new_height != current_height:
                        self.data.loc[self.data['series_id'] == series_id, 'instr_height'] = new_height
                        changes_made = True
                except ValueError:
                    self.display_message("Пожалуйста, введите корректное значение для высоты инструмента.",
                                         message_type="warning")
                    return

            # Проверяем и обновляем название станции, если введено новое имя и оно отличается
            if new_station_name and new_station_name != \
                    self.data.loc[self.data['series_id'] == series_id, 'station'].iloc[0]:
                self.data.loc[self.data['series_id'] == series_id, 'station'] = new_station_name
                changes_made = True

            # Проверяем и обновляем линию, если введена новая линия и она отличается
            if new_line_str:
                try:
                    new_line = int(new_line_str)
                    current_line = self.data.loc[self.data['series_id'] == series_id, 'line'].iloc[0]
                    if new_line != current_line:
                        self.data.loc[self.data['series_id'] == series_id, 'line'] = new_line
                        changes_made = True
                except ValueError:
                    self.display_message("Пожалуйста, введите корректное числовое значение для линии.",
                                         message_type="warning")
                    return

            # Проверяем и обновляем широту, если введено новое значение и оно отличается
            if new_lat_str:
                try:
                    new_lat = float(new_lat_str.replace(",", "."))
                    current_lat = self.data.loc[self.data['series_id'] == series_id, 'lat'].iloc[0]
                    if new_lat != current_lat:
                        self.data.loc[self.data['series_id'] == series_id, 'lat'] = new_lat
                        changes_made = True
                except ValueError:
                    self.display_message("Пожалуйста, введите корректное числовое значение для широты.",
                                         message_type="warning")
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
                    self.display_message("Пожалуйста, введите корректное числовое значение для долготы.",
                                         message_type="warning")
                    return

            # Проверяем и обновляем атмосферное давление, если введено новое значение и оно отличается
            if new_pressure_str:
                try:
                    new_pressure = float(new_pressure_str.replace(",", "."))
                    current_pressure = self.data.loc[self.data['series_id'] == series_id, 'pressure'].iloc[0]
                    if pd.isnull(current_pressure) or new_pressure != current_pressure:
                        self.data.loc[self.data['series_id'] == series_id, 'pressure'] = new_pressure
                        changes_made = True
                        pressure_changed = True  # Устанавливаем флаг изменения давления
                    else:
                        # Давление не изменилось
                        pass
                except ValueError:
                    self.display_message("Пожалуйста, введите корректное числовое значение для давления.",
                                         message_type="warning")
                    return

            if changes_made:
                # Обновляем series_id
                self.update_series_id()

                # Дополнительная обработка давления для других серий только если давление было изменено
                if pressure_changed:
                    updated_series_data = self.data[self.data['series_id'] == series_id]
                    if not updated_series_data.empty:
                        # Убедимся, что date_time в формате datetime
                        if not pd.api.types.is_datetime64_any_dtype(self.data['date_time']):
                            self.data['date_time'] = pd.to_datetime(self.data['date_time'])

                        updated_series_first_time = self.data.loc[
                            self.data['series_id'] == series_id, 'date_time'].min()
                        updated_series_station = updated_series_data['station'].iloc[0]
                        updated_series_pressure = updated_series_data['pressure'].iloc[0]
                        updated_series_instrument = updated_series_data['instrument_serial_number'].iloc[0]

                        # Группируем данные по series_id
                        series_groups = self.data.groupby('series_id')

                        for other_series_id, group in series_groups:
                            if other_series_id == series_id:
                                continue  # Пропускаем текущую серию
                            first_row = group.iloc[0]
                            other_station = first_row['station']
                            other_instrument = first_row['instrument_serial_number']
                            other_first_time = first_row['date_time']

                            # Проверяем условия
                            if other_station == updated_series_station and other_instrument != updated_series_instrument:
                                time_diff = abs(other_first_time - updated_series_first_time)
                                if time_diff <= pd.Timedelta(minutes=15):
                                    # Обновляем давление в этой серии
                                    self.data.loc[
                                        self.data['series_id'] == other_series_id, 'pressure'] = updated_series_pressure
                                    self.display_message(f"Давление для серии {other_series_id} обновлено.",
                                                         message_type="success")

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

                self.display_message(f"Серия {series_id} успешно обновлена.", message_type="success")
            else:
                self.display_message("Нет изменений для сохранения.", message_type="success")
        else:
            self.display_message("Пожалуйста, выберите серию для изменения.", message_type="warning")

    def delete_series(self):
        """Удаление выбранной серии"""
        selected_index = self.series_listbox.curselection()
        if selected_index:
            series_id = self.data['series_id'].unique()[selected_index[0]]
            # Удаляем данные серии из DataFrame
            self.data = self.data[self.data['series_id'] != series_id].copy()
            # Обновляем series_id после удаления
            self.update_series_id()
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
            self.display_message(f"Серия {series_id} успешно удалена.", message_type="success")
        else:
            self.display_message("Пожалуйста, выберите серию для удаления.", message_type="warning")

    def on_station_select(self, event):
        """Обработчик выбора станции в Listbox"""
        selected_index = self.station_listbox.curselection()
        if selected_index:
            station_name = self.station_listbox.get(selected_index)
            self.current_station_name = station_name
            # Получаем текущие данные для этой станции
            station_data = self.data[self.data['station'] == station_name]
            if not station_data.empty:
                self.current_station_lat = station_data.iloc[0]['lat']
                self.current_station_lon = station_data.iloc[0]['lon']
                self.current_station_pressure = station_data.iloc[0].get('pressure', None)
                self.current_station_height = station_data.iloc[0]['instr_height']

                # Заполняем поля ввода координат и давления
                self.station_lat_entry.delete(0, tk.END)
                self.station_lat_entry.insert(0, str(self.current_station_lat))

                self.station_lon_entry.delete(0, tk.END)
                self.station_lon_entry.insert(0, str(self.current_station_lon))

                self.station_height_entry.delete(0, tk.END)
                self.station_height_entry.insert(0, str(self.current_station_height))
                # Заполняем поле для переименования текущим названием станции
                self.rename_station_entry.delete(0, tk.END)
                self.rename_station_entry.insert(0, station_name)
                # Заполняем поле давления
                self.pressure_entry_station.delete(0, tk.END)
                if pd.notnull(self.current_station_pressure):
                    self.pressure_entry_station.insert(0, str(self.current_station_pressure))
                else:
                    self.pressure_entry_station.insert(0, "")

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
                self.current_series_line = series_data.iloc[0].get('line', None)
                self.current_series_height = series_data.iloc[0]['instr_height']
                # Заполняем поля ввода координат, названия станции и давления
                self.series_line_entry.delete(0, tk.END)
                self.series_line_entry.insert(0, str(self.current_series_line))
                self.series_height_entry.delete(0, tk.END)
                self.series_height_entry.insert(0, str(self.current_series_height))
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
        """Расчет и применение поправок за атмосферное давление для каждой линии"""
        if self.data is not None:
            k = -0.003  # Коэффициент для расчета поправки

            # Проверяем, что давление введено для всех серий
            if self.data['pressure'].isnull().any():
                self.display_message("Необходимо ввести атмосферное давление для всех серий.", message_type="warning")
                return

            # Группируем данные по линии
            line_groups = self.data.groupby('line')

            for line, group in line_groups:
                # Сортируем серии по порядку
                group_sorted = group.sort_values(by='series_id')

                # Берем давление первой серии как эталонное для данной линии
                first_series_pressure = group_sorted.iloc[0]['pressure']

                # Рассчитываем поправку для каждой серии на линии
                pressure_corrections = group_sorted['pressure'].apply(lambda P: k * (P - first_series_pressure))

                # Добавляем колонку 'pressure_corr', если её нет
                if 'pressure_corr' not in self.data.columns:
                    self.data.loc[:, 'pressure_corr'] = 0.0

                # Применяем поправку для каждой серии
                for idx, correction in pressure_corrections.items():
                    # Если поправка уже была рассчитана для этой строки, то отнимаем старую
                    if pd.notnull(self.data.at[idx, 'pressure_corr']):
                        self.data.at[idx, 'corr_grav'] -= self.data.at[idx, 'pressure_corr']

                    # Применяем новую поправку
                    self.data.at[idx, 'pressure_corr'] = round(correction, 4)
                    self.data.at[
                        idx, 'corr_grav'] += correction  # Добавляем новую поправку к измеренному гравитационному значению

            # Округляем corr_grav для отображения
            self.data['corr_grav'] = self.data['corr_grav'].round(4)

            # Обновляем отображение таблицы
            self.table.update_data(self.data)

            self.display_message("Поправки за атмосферное давление успешно рассчитаны и применены.",
                                 message_type="success")

    def calculate_tidal_correction(self):
        """Расчет и применение приливных поправок"""
        if self.data is not None:
            # Пробегаем по каждой строке и вычисляем приливную поправку
            for idx, row in self.data.iterrows():
                lat = row['lat']
                lon = row['lon']
                date = pd.to_datetime(row['date_time'])

                # Рассчитываем новую приливную поправку с использованием функции TIDEFF
                new_tide_corr = - TIDEFF(lat, lon, date.day, date.month, date.year, date.hour, date.minute)

                # Обновляем значение в колонке 'tide_corr'
                self.data.at[idx, 'corr_grav'] = row['corr_grav'] - row.get('tide_corr', 0) + new_tide_corr
                self.data.at[idx, 'tide_corr'] = round(new_tide_corr, 4)

            # Округляем corr_grav для отображения
            self.data['corr_grav'] = self.data['corr_grav'].round(4)

            # Обновляем отображение таблицы
            self.table.update_data(self.data)

            self.display_message("Приливные поправки успешно рассчитаны и применены.", message_type="success")

    def use_grs2(self):
        """Обработка данных в соответствии с требованиями GRS2"""
        if self.data is not None:
            self.data = self.process_grs2_data(self.data)
            # Обновляем series_id после обработки данных
            self.update_series_id()
            # Обновляем отображение таблицы
            if self.table:
                self.table.update_data(self.data)
            # Обновляем списки
            self.update_station_listbox()
            self.update_series_listbox()

    def process_grs2_data(self, df):
        """Обработка DataFrame для приведения к программе измерений ГРС2"""
        df = df.copy()
        station_count = 1  # Счетчик станций
        line_count = 1  # Счетчик линий
        instrument = df.iloc[0]['instrument_serial_number']
        created = df.iloc[0]['created']
        station_name = df.iloc[0]['station']
        station_rows = []  # Список для хранения строк текущей станции
        stations_data = {}  # Словарь для хранения данных по станциям
        processed_rows = []  # Итоговый список обработанных строк

        df['line'] = 0  # Инициализируем колонку 'line'

        for idx, row in df.iterrows():
            current_station = row['station']
            current_instrument = row['instrument_serial_number']
            current_created = row['created']

            # Проверяем смену прибора или даты создания
            if current_instrument != instrument or current_created != created:
                # Сохраняем данные предыдущей станции перед сбросом
                if station_rows:
                    stations_data[station_count] = station_rows.copy()

                    # Обрабатываем данные предыдущей станции
                    # Обрабатываем данные в соответствии с номером станции
                    if station_count == 1:
                        # Обработка первой станции без изменений
                        for s_row in station_rows:
                            processed_rows.append(s_row.copy())
                    elif station_count in [2, 3]:
                        # Обработка второй и третьей станций без изменений
                        for s_row in station_rows:
                            processed_rows.append(s_row.copy())
                    elif station_count == 4:
                        # Обработка четвертой станции и дублирование
                        for s_row in station_rows:
                            processed_rows.append(s_row.copy())
                        # В данном случае данные после текущей станции отсутствуют, поэтому дублирование не произойдет
                        # Так как мы уже обнаружили смену прибора или даты
                    elif station_count in [5, 6]:
                        # Обработка пятой и шестой станций без изменений
                        for s_row in station_rows:
                            processed_rows.append(s_row.copy())
                    elif station_count == 7:
                        # Обработка седьмой станции и дублирование
                        for s_row in station_rows:
                            processed_rows.append(s_row.copy())
                        # Дублирование не происходит, так как прибор или дата изменились
                    elif station_count in [8, 9]:
                        # Обработка восьмой и девятой станций без изменений
                        for s_row in station_rows:
                            processed_rows.append(s_row.copy())
                    elif station_count == 10:
                        # Обработка десятой станции без изменений
                        for s_row in station_rows:
                            processed_rows.append(s_row.copy())

                    # Дублирование измерений после определенных станций
                    # Не выполняем дублирование, так как прибор или дата изменились

                # Сбрасываем счетчики
                station_count = 1
                line_count += 1
                instrument = current_instrument
                created = current_created
                station_name = current_station
                station_rows = []
                stations_data = {}
                row['line'] = line_count
                station_rows.append(row.copy())
                continue  # Переходим к следующей итерации

            if current_station == station_name:
                # Собираем строки текущей станции
                row['line'] = line_count
                station_rows.append(row.copy())
            else:
                # Станция изменилась, сохраняем данные предыдущей станции
                stations_data[station_count] = station_rows.copy()

                # Обрабатываем данные в соответствии с номером станции
                if station_count == 1:
                    # Обработка первой станции без изменений
                    for s_row in station_rows:
                        processed_rows.append(s_row.copy())
                elif station_count in [2, 3]:
                    # Обработка второй и третьей станций без изменений
                    for s_row in station_rows:
                        processed_rows.append(s_row.copy())
                elif station_count == 4:
                    # Обработка четвертой станции и дублирование
                    for s_row in station_rows:
                        processed_rows.append(s_row.copy())
                    # Проверяем наличие данных после текущей станции и отсутствие смены прибора или даты
                    if idx + 1 < len(df) and df.iloc[idx + 1]['instrument_serial_number'] == instrument and \
                            df.iloc[idx + 1]['created'] == created:
                        # Дублируем данные станции с increment line_count
                        line_count += 1
                        for s_row in station_rows:
                            dup_row = s_row.copy()
                            dup_row['line'] = line_count
                            processed_rows.append(dup_row)
                elif station_count in [5, 6]:
                    # Обработка пятой и шестой станций без изменений
                    for s_row in station_rows:
                        processed_rows.append(s_row.copy())
                elif station_count == 7:
                    # Обработка седьмой станции и дублирование
                    for s_row in station_rows:
                        processed_rows.append(s_row.copy())
                    # Проверяем наличие данных после текущей станции и отсутствие смены прибора или даты
                    if idx + 1 < len(df) and df.iloc[idx + 1]['instrument_serial_number'] == instrument and \
                            df.iloc[idx + 1]['created'] == created:
                        line_count += 1
                        for s_row in station_rows:
                            dup_row = s_row.copy()
                            dup_row['line'] = line_count
                            processed_rows.append(dup_row)
                elif station_count in [8, 9]:
                    # Обработка восьмой и девятой станций без изменений
                    for s_row in station_rows:
                        processed_rows.append(s_row.copy())
                elif station_count == 10:
                    # Обработка десятой станции без изменений
                    for s_row in station_rows:
                        processed_rows.append(s_row.copy())

                # Дублирование измерений после определенных станций
                if station_count == 3:
                    # После третьей станции дублируем вторую и третью
                    line_count += 1
                    for s_count in [2, 3]:
                        if s_count in stations_data:
                            for s_row in stations_data[s_count]:
                                dup_row = s_row.copy()
                                dup_row['line'] = line_count
                                processed_rows.append(dup_row)
                elif station_count == 6:
                    # После шестой станции дублируем пятую и шестую
                    line_count += 1
                    for s_count in [5, 6]:
                        if s_count in stations_data:
                            for s_row in stations_data[s_count]:
                                dup_row = s_row.copy()
                                dup_row['line'] = line_count
                                processed_rows.append(dup_row)
                elif station_count == 9:
                    # После девятой станции дублируем восьмую и девятую
                    line_count += 1
                    for s_count in [8, 9]:
                        if s_count in stations_data:
                            for s_row in stations_data[s_count]:
                                dup_row = s_row.copy()
                                dup_row['line'] = line_count
                                processed_rows.append(dup_row)

                # Инкрементируем счетчик станций и обновляем переменные
                station_count += 1
                station_name = current_station
                station_rows = []
                row['line'] = line_count
                station_rows.append(row.copy())

        # Обработка последней станции после завершения цикла
        if station_rows:
            stations_data[station_count] = station_rows.copy()
            # Обрабатываем данные последней станции
            if station_count == 1:
                for s_row in station_rows:
                    processed_rows.append(s_row.copy())
            elif station_count in [2, 3]:
                for s_row in station_rows:
                    processed_rows.append(s_row.copy())
            elif station_count == 4:
                for s_row in station_rows:
                    processed_rows.append(s_row.copy())
                # Проверяем наличие данных после текущей станции и отсутствие смены прибора или даты
                # В данном случае idx будет равен последнему индексу, поэтому idx + 1 >= len(df)
                # Дублирование не произойдет, если данных после текущей станции нет или изменился прибор/дата
                if idx + 1 < len(df) and df.iloc[idx + 1]['instrument_serial_number'] == instrument and \
                        df.iloc[idx + 1]['created'] == created:
                    line_count += 1
                    for s_row in station_rows:
                        dup_row = s_row.copy()
                        dup_row['line'] = line_count
                        processed_rows.append(dup_row)
            elif station_count in [5, 6]:
                for s_row in station_rows:
                    processed_rows.append(s_row.copy())
            elif station_count == 7:
                for s_row in station_rows:
                    processed_rows.append(s_row.copy())
                # Проверяем наличие данных после текущей станции и отсутствие смены прибора или даты
                if idx + 1 < len(df) and df.iloc[idx + 1]['instrument_serial_number'] == instrument and \
                        df.iloc[idx + 1]['created'] == created:
                    line_count += 1
                    for s_row in station_rows:
                        dup_row = s_row.copy()
                        dup_row['line'] = line_count
                        processed_rows.append(dup_row)
            elif station_count in [8, 9]:
                for s_row in station_rows:
                    processed_rows.append(s_row.copy())
            elif station_count == 10:
                for s_row in station_rows:
                    processed_rows.append(s_row.copy())

            # Дублирование после девятой станции
            if station_count == 9:
                # Проверяем наличие данных после текущей станции и отсутствие смены прибора или даты
                if idx + 1 < len(df) and df.iloc[idx + 1]['instrument_serial_number'] == instrument and \
                        df.iloc[idx + 1]['created'] == created:
                    line_count += 1
                    for s_count in [8, 9]:
                        if s_count in stations_data:
                            for s_row in stations_data[s_count]:
                                dup_row = s_row.copy()
                                dup_row['line'] = line_count
                                processed_rows.append(dup_row)

        df_processed = pd.DataFrame(processed_rows)
        df_processed.reset_index(drop=True, inplace=True)

        # Вывод сообщения об успешной обработке
        self.display_message("Данные успешно обработаны для программы измерений ГРС2.", message_type="success")

        return df_processed

    def copy_selected_series(self):
        """Дублирует выбранную серию и добавляет копию сразу после неё."""
        try:
            # Получаем индекс выбранной серии
            selected_index = self.series_listbox.curselection()
            if not selected_index:
                self.display_message("Пожалуйста, выберите серию для копирования.", message_type="warning")
                return

            # Определяем ID выбранной серии
            selected_series_id = self.data['series_id'].unique()[selected_index[0]]

            # Получаем данные выбранной серии
            selected_series_data = self.data[self.data['series_id'] == selected_series_id]
            if selected_series_data.empty:
                self.display_message("Выбранная серия не найдена.", message_type="error")
                return

            # Определяем индекс строки, где находится серия
            original_index = self.data[self.data['series_id'] == selected_series_id].index[-1]

            # Создаём копию серии с новым ID
            new_series = selected_series_data.copy()
            new_series_id = self.data['series_id'].max() + 1  # Устанавливаем новый ID для копии
            new_series['series_id'] = new_series_id

            # Вставляем копию после оригинальной серии
            part_before = self.data.iloc[:original_index + 1]
            part_after = self.data.iloc[original_index + 1:]
            self.data = pd.concat([part_before, new_series, part_after], ignore_index=True)

            # Обновляем отображение таблицы и списков
            self.table.update_data(self.data)
            self.update_series_listbox()

            self.display_message(f"Серия {selected_series_id} успешно скопирована как {new_series_id}.",
                                 message_type="success")
        except Exception as e:
            self.display_message(f"Ошибка при копировании серии: {e}", message_type="error")

    def checks(self):
        """Проверка расхождений в координатах для каждой станции среди серий и замыкания линий."""
        if self.data is not None:
            errors = []  # Список для хранения предупреждений о координатах
            line_closure_errors = []  # Список для ошибок замыкания линий
            grouped_by_station = self.data.groupby('station')  # Группируем данные по станции
            grouped_by_line = self.data.groupby('line')  # Группируем данные по линии
            threshold = 0.001  # Порог для стандартного отклонения

            # Проверка расхождений в координатах
            for station, group in grouped_by_station:
                # Расчет средней широты и долготы
                lat_mean = group['lat'].mean()
                lat_std = group['lat'].std()
                lon_mean = group['lon'].mean()
                lon_std = group['lon'].std()

                # Проверяем, превышает ли стандартное отклонение допустимый порог
                if lat_std > threshold or lon_std > threshold:
                    # Добавляем предупреждение в список
                    errors.append(
                        f"Станция '{station}': "
                        f"lat_std={lat_std:.6f}, lon_std={lon_std:.6f}. "
                        f"Серии: {', '.join(map(str, group['series_id'].unique()))}"
                    )

            # Проверка замыкания линий
            for line, group in grouped_by_line:
                # Получаем названия станций первой и последней серии в линии
                first_station = group.iloc[0]['station']
                last_station = group.iloc[-1]['station']

                # Если названия не совпадают, добавляем в список ошибок
                if first_station != last_station:
                    line_closure_errors.append(
                        f"Линия {line}: первая станция '{first_station}' не совпадает с последней станцией '{last_station}'."
                    )

            # Формирование сообщений
            messages = []

            if errors:
                messages.append("Обнаружены расхождения в координатах:\n" + "\n".join(errors))
            else:
                messages.append("Координаты для всех станций 一 соответствуют.")

            if line_closure_errors:
                messages.append("Линии, которые не замыкаются:\n" + "\n".join(line_closure_errors))
            else:
                messages.append("Все линии замыкаются корректно.")

            # Отображение сообщений
            self.display_message("\n\n".join(messages),
                                 message_type="error" if errors or line_closure_errors else "success")

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

    def on_data_modified(self):
        """Обработчик изменений данных в таблице."""
        # Обновляем self.data из таблицы
        self.data = self.table.get_dataframe()

        # Пересчитываем series_id
        self.update_series_id()

        # Обновляем таблицу с новыми данными
        self.table.update_data(self.data)

        # Обновляем списки
        self.update_station_listbox()
        self.update_series_listbox()
