import tkinter as tk
from tkinter import messagebox, ttk


class InputDataTable:
    def __init__(self, parent, dataframe):
        self.parent = parent
        self.dataframe = dataframe.copy()  # Копируем DataFrame
        self.tree = None  # Здесь будет таблица
        self.v_scroll = None  # Вертикальный скролл
        self.h_scroll = None  # Горизонтальный скролл
        self.entry_popup = None  # Поле для редактирования ячейки

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
        columns_to_format_1_decimal = ['instr_height', 'corr_grav', 'std_err']  # Колонки с 1 знаком после запятой
        columns_to_format_9_decimals = ['lat', 'lon']  # Колонки с 9 знаками после запятой

        # Цвета для станций (пастельные)
        colors = ["#f0f8ff", "#e6e6fa", "#f5f5dc", "#f0fff0", "#fafad2", "#ffe4e1", "#ffe4b5"]

        # Словарь для хранения номера строк по комбинации линии и станции
        group_row_numbers = {}
        current_group_key = None  # Переменная для отслеживания текущей группы (линия, станция)

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

    def on_double_click(self, event):
        """Редактирование значения ячейки прямо в таблице."""
        # Получаем номер столбца и строки
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

            # Сохраняем изменения при нажатии Enter
            self.entry_popup.bind("<Return>", lambda e: self.save_value(row_id, column_index))
            # Закрываем поле и сохраняем данные при потере фокуса
            self.entry_popup.bind("<FocusOut>", lambda e: self.save_value(row_id, column_index))

    def save_value(self, row_id, column_index):
        """Сохранение значения ячейки при нажатии Enter или потере фокуса."""
        if self.entry_popup:
            new_value = self.entry_popup.get()
            current_values = list(self.tree.item(row_id, "values"))
            current_values[column_index] = new_value

            # Обновляем данные в дереве
            self.tree.item(row_id, values=current_values)

            # Обновляем данные в DataFrame
            row_index = self.tree.index(row_id)
            if column_index == 0:
                pass  # Не обновляем номер строки
            else:
                df_col_index = column_index - 1  # Учитываем смещение из-за колонки "#"
                col_name = self.dataframe.columns[df_col_index]

                # Приведение типов данных
                if self.dataframe[col_name].dtype == 'float64':
                    new_value = float(new_value)
                elif self.dataframe[col_name].dtype == 'int64':
                    new_value = int(new_value)

                self.dataframe.at[row_index, col_name] = new_value

                # Если изменили 'line' или 'station', обновляем таблицу
                if col_name in ['line', 'station']:
                    self.entry_popup.destroy()
                    self.entry_popup = None

                    self.dataframe.reset_index(drop=True, inplace=True)
                    self.setup_table()
                    return  # Уже обновили, выходим из функции

            # Закрываем поле редактирования
            self.entry_popup.destroy()
            self.entry_popup = None

    def delete_selected_rows(self, event=None):
        """Удаление выделенных строк и обновление нумерации."""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        confirm = messagebox.askyesno("Удаление", "Вы уверены, что хотите удалить выбранные строки?")
        if confirm:
            # Получаем индексы удаляемых строк
            indices_to_delete = [self.tree.index(item) for item in selected_items]

            # Удаляем строки из DataFrame
            self.dataframe.drop(self.dataframe.index[indices_to_delete], inplace=True)
            self.dataframe.reset_index(drop=True, inplace=True)  # Сброс индексов

            # Очищаем дерево и пересоздаем таблицу
            self.setup_table()

    def get_dataframe(self):
        """Возвращаем DataFrame с изменениями."""
        return self.dataframe.copy()
