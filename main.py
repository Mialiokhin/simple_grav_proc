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


if __name__ == "__main__":
    root = tk.Tk()
    app = GravityApp(root)
    root.mainloop()
