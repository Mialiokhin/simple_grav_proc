import tkinter as tk
from tkinter import messagebox, ttk


class InputDataTable:
    def __init__(self, parent, dataframe, data_modified_callback=None, survey_tab=None):
        self.parent = parent
        self.dataframe = dataframe.copy()
        self.data_modified_callback = data_modified_callback  # Обратный вызов для обновления данных
        self.survey_tab = survey_tab  # Ссылка на SurveyDataTab
        self.tree = None
        self.v_scroll = None
        self.h_scroll = None
        self.entry_popup = None

        # Словарь для хранения цвета для каждой станции
        self.station_colors = {}

        self.setup_table()

    def setup_table(self):
        """Создаем таблицу и скроллы."""
        # Проверяем, существует ли таблица, если да, то очищаем ее
        if self.tree:
            self.tree.delete(*self.tree.get_children())
        else:
            # Если таблица не существует, создаем её и скроллы
            self.tree = ttk.Treeview(self.parent, show='headings')
            self.v_scroll = ttk.Scrollbar(self.parent, orient="vertical", command=self.tree.yview)
            self.h_scroll = ttk.Scrollbar(self.parent, orient="horizontal", command=self.tree.xview)
            self.tree.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)

            # Размещаем элементы с правильной привязкой
            self.tree.grid(row=0, column=0, sticky='nsew')  # Размещаем таблицу
            self.v_scroll.grid(row=0, column=1, sticky='ns')  # Вертикальный скролл
            self.h_scroll.grid(row=1, column=0, sticky='ew')  # Горизонтальный скролл

            # Настройка родительского фрейма для растягивания таблицы
            self.parent.grid_rowconfigure(0, weight=1)
            self.parent.grid_columnconfigure(0, weight=1)

        # Настройка колонок
        columns = ["#", *list(self.dataframe.columns)]  # Добавляем колонку для нумерации
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="w", width=100)

        # Определяем, для каких колонок нужно форматировать данные
        columns_to_format_1_decimal = ['instr_height', 'std_err']  # Колонки с 1 знаком после запятой
        columns_to_format_4_decimal = ['corr_grav', 'pressure_corr']  # Колонки с 1 знаком после запятой
        columns_to_format_9_decimals = ['lat', 'lon']  # Колонки с 9 знаками после запятой

        # Цвета для станций (пастельные)
        colors = ["#f0f8ff", "#e6e6fa", "#f5f5dc", "#f0fff0", "#fafad2", "#ffe4e1", "#ffe4b5"]

        # Словарь для хранения номера строк по комбинации линии и станции
        group_row_numbers = {}
        current_group_key = None

        # Очищаем цвета станций
        self.station_colors = {}

        # Добавляем данные с правильным округлением для чисел с плавающей запятой
        for _, row in self.dataframe.iterrows():
            line_value = row['line']
            station_value = row['station']
            group_key = (line_value, station_value)

            # Если линия или станция изменилась, сбрасываем нумерацию
            if group_key != current_group_key:
                group_row_numbers[group_key] = 1
                current_group_key = group_key
            else:
                group_row_numbers[group_key] += 1

            # Форматирование строки
            formatted_row = [
                f'{val:.1f}' if col in columns_to_format_1_decimal and isinstance(val, float) else
                f'{val:.4f}' if col in columns_to_format_4_decimal and isinstance(val, float) else
                f'{val:.9f}' if col in columns_to_format_9_decimals and isinstance(val, float) else
                val
                for col, val in zip(self.dataframe.columns, row)
            ]

            # Добавляем номер строки как первый элемент
            row_with_number = [group_row_numbers[group_key], *formatted_row]

            # Если станция еще не имеет цвета, назначаем ей один из цветов
            if station_value not in self.station_colors:
                self.station_colors[station_value] = colors[len(self.station_colors) % len(colors)]

            # Назначаем тег с цветом для текущей строки
            self.tree.insert("", "end", values=row_with_number, tags=(station_value,))

        # Настройка тегов для изменения фона
        for station, color in self.station_colors.items():
            self.tree.tag_configure(station, background=color)

        # Привязываем события
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Delete>", self.delete_selected_rows)

    def update_data(self, dataframe):
        """Обновление таблицы с новыми данными."""
        self.dataframe = dataframe.copy()
        self.setup_table()

    def on_double_click(self, event):
        """Редактирование значения ячейки прямо в таблице."""
        # Получаем номер колонки и строки
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            row_id = self.tree.identify_row(event.y)
            column = self.tree.identify_column(event.x)
            column_index = int(column.replace("#", "")) - 1

            # Получаем координаты ячейки для редактирования
            x, y, width, height = self.tree.bbox(row_id, column)

            # Получаем текущее значение ячейки
            values = self.tree.item(row_id, "values")
            current_value = values[column_index]

            # Создаем поле для редактирования внутри таблицы
            self.entry_popup = tk.Entry(self.tree)
            self.entry_popup.place(x=x, y=y, width=width, height=height)
            self.entry_popup.insert(0, current_value)
            self.entry_popup.focus()

            # Сохраняем изменения по нажатию Enter
            self.entry_popup.bind("<Return>", lambda e: self.save_value(row_id, column_index))
            # Закрываем поле и сохраняем данные при потере фокуса
            self.entry_popup.bind("<FocusOut>", lambda e: self.save_value(row_id, column_index))

    def save_value(self, row_id, column_index):
        """Сохраняем значение ячейки по нажатию Enter или потере фокуса."""
        if self.entry_popup:
            new_value = self.entry_popup.get()
            current_values = list(self.tree.item(row_id, "values"))
            old_value = current_values[column_index]

            # Если значение не изменилось, ничего не делаем
            if str(old_value) == str(new_value):
                self.entry_popup.destroy()
                self.entry_popup = None
                return

            current_values[column_index] = new_value

            row_index = self.tree.index(row_id)
            df_col_index = column_index - 1  # Смещение из-за колонки "#"
            col_name = self.dataframe.columns[df_col_index]
            station = self.dataframe.loc[row_index, 'station']
            line = self.dataframe.loc[row_index, 'line']
            series = self.dataframe.loc[row_index, 'series_id']

            # Приведение типов
            if self.dataframe[col_name].dtype == "float64":
                try:
                    new_value = float(new_value)
                except ValueError:
                    messagebox.showerror("Ошибка", "Пожалуйста, введите корректное числовое значение.")
                    self.entry_popup.destroy()
                    self.entry_popup = None
                    return
            elif self.dataframe[col_name].dtype == "int64":
                try:
                    new_value = int(new_value)
                except ValueError:
                    messagebox.showerror("Ошибка", "Пожалуйста, введите корректное целочисленное значение.")
                    self.entry_popup.destroy()
                    self.entry_popup = None
                    return

            # Обновляем DataFrame
            self.dataframe.at[row_index, col_name] = new_value

            # Если 'line' или 'station' изменились, обновляем таблицу
            if col_name in ["line", "station"]:
                # Отправляем сообщение в SurveyDataTab
                if self.survey_tab:
                    self.survey_tab.display_message(
                        f"Изменение данных: линия {line}, серия {series}, станция {station}, строка {row_index + 1}, "
                        f"колонка '{col_name}', старое значение: {old_value}, новое значение: {new_value}.",
                        message_type="info"
                    )

                # Закрываем поле редактирования
                self.entry_popup.destroy()
                self.entry_popup = None

                # Сбрасываем индекс и обновляем таблицу
                self.dataframe.reset_index(drop=True, inplace=True)
                self.setup_table()

                # Вызываем обратный вызов
                if self.data_modified_callback:
                    self.data_modified_callback()
                return


            # Закрываем поле редактирования
            self.entry_popup.destroy()
            self.entry_popup = None

            # Отправляем сообщение в SurveyDataTab
            if self.survey_tab:
                self.survey_tab.display_message(
                    f"Изменение данных: линия {line}, серия {series}, станция {station}, строка {row_index + 1}, "
                    f"колонка '{col_name}', старое значение: {old_value}, новое значение: {new_value}.",
                    message_type="info"
                )

            # Вызываем обратный вызов после изменения данных
            if self.data_modified_callback:
                self.data_modified_callback()

    def delete_selected_rows(self, event=None):
        """Удаление выбранных строк и отправка сообщений."""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        confirm = messagebox.askyesno(
            "Удаление", "Вы уверены, что хотите удалить выбранные строки?"
        )
        if confirm:
            # Список для хранения информации о удаленных строках
            deleted_rows_info = []

            for item in selected_items:
                row_index = self.tree.index(item)
                row_data = self.dataframe.iloc[row_index]

                # Извлечение значений corr_grav и std_err
                corr_grav = row_data.get('corr_grav', 'N/A')  # Если столбец отсутствует, используется 'N/A'
                std_err = row_data.get('std_err', 'N/A')

                # Добавляем информацию о строке
                deleted_rows_info.append(
                    f"строка {row_index + 1}, линия {row_data['line']}, серия {row_data['series_id']}, "
                    f"станция {row_data['station']}, corr_grav={corr_grav}, std_err={std_err}"
                )

            # Удаляем строки из DataFrame
            indices_to_delete = [self.tree.index(item) for item in selected_items]
            self.dataframe.drop(self.dataframe.index[indices_to_delete], inplace=True)
            self.dataframe.reset_index(drop=True, inplace=True)

            # Очищаем дерево и пересоздаем таблицу
            self.setup_table()

            # Вызываем обратный вызов после изменения данных
            if self.data_modified_callback:
                self.data_modified_callback()

            # Формируем сообщение с переносами строк
            deleted_rows_message = "Удалены строки:\n" + "\n".join(deleted_rows_info)

            # Отправляем сообщение в SurveyDataTab
            if self.survey_tab:
                self.survey_tab.display_message(deleted_rows_message, message_type="warning")

    def get_dataframe(self):
        """Возвращаем DataFrame с изменениями."""
        return self.dataframe.copy()
