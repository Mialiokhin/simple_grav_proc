import tkinter as tk
from tkinter import ttk
from components.survey_data_tab import SurveyDataTab
from components.ties_tab import TiesTab
from components.vg_tab import VGTab


class GravityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SGP")

        # Создаем виджет Notebook для вкладок
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)

        # Создаем вкладки
        self.survey_data_tab = SurveyDataTab(self.notebook)
        self.ties_tab = TiesTab(self.notebook, self.survey_data_tab)
        self.vg_tab = VGTab(self.notebook, self.survey_data_tab)

        # Добавляем вкладки в Notebook
        self.notebook.add(self.survey_data_tab.frame, text="Survey Data")
        self.notebook.add(self.ties_tab.frame, text="Ties")
        self.notebook.add(self.vg_tab.frame, text="Vertical Gradient")

        # Обработка события закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        # Вызываем методы on_closing у вкладок, если они существуют
        if hasattr(self.ties_tab, 'on_closing'):
            self.ties_tab.on_closing()
        if hasattr(self.vg_tab, 'on_closing'):
            self.vg_tab.on_closing()
        if hasattr(self.survey_data_tab, 'on_closing'):
            self.survey_data_tab.on_closing()

        # Закрываем главное окно
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = GravityApp(root)
    root.mainloop()
