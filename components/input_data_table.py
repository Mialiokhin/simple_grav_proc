import tkinter as tk
from tkinter import messagebox, ttk

class InputDataTable:
    def __init__(self, parent, dataframe):
        self.parent = parent
        self.dataframe = dataframe.copy()  # Копируем DataFrame
        self.tree = None  # Здесь будет таблица
        self.v_scroll = None  # Вертикальный скролл
        self.h_scroll = None  # Горизонтальный скролл

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

            # Настройка родительского фрейма для растягивания таблицы
            self.parent.grid_rowconfigure(0, weight=1)
            self.parent.grid_columnconfigure(0, weight=1)

        # Настройка колонок
        self.tree["columns"] = list(self.dataframe.columns)
        for col in self.dataframe.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="w", width=100)

            # Определяем, для каких колонок нужно форматировать данные
        columns_to_format_1_decimal = ['instr_height', 'corr_grav', 'std_err']  # Колонки с 1 знаком после запятой
        columns_to_format_9_decimals = ['lat', 'lon']  # Колонки с 9 знаками после запятой

        # Добавляем данные с правильным округлением для чисел с плавающей запятой
        for _, row in self.dataframe.iterrows():
            formatted_row = [
                f'{val:.1f}' if col in columns_to_format_1_decimal and isinstance(val, float) else
                f'{val:.9f}' if col in columns_to_format_9_decimals and isinstance(val, float) else
                val
                for col, val in zip(self.dataframe.columns, row)
            ]
            self.tree.insert("", "end", values=formatted_row)

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
            self.entry_popup = tk.Entry(self.tree, width=width)
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
            self.dataframe.iloc[row_index, column_index] = new_value

            # Закрываем поле редактирования
            self.entry_popup.destroy()
            self.entry_popup = None

    def delete_selected_rows(self, event=None):
        """Удаление выделенных строк."""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        confirm = messagebox.askyesno("Удаление", "Вы уверены, что хотите удалить выбранные строки?")
        if confirm:
            for item in selected_items:
                row_index = self.tree.index(item)
                self.tree.delete(item)
                # Удаляем строку из DataFrame
                self.dataframe.drop(self.dataframe.index[row_index], inplace=True)

    def get_dataframe(self):
        """Возвращаем DataFrame с изменениями."""
        return self.dataframe.copy()
