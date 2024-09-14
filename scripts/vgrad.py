#!/usr/bin/env python
u'''
Read CG-6 data file and calculate vertical gradient
'''

# Импортируем необходимые модули для работы с данными, графиками, расчетами вертикального градиента
# и генерацией отчетов.

import numpy as np
from matplotlib import pyplot as plt
import pandas as pd
from grav_proc.vertical_gradient import get_vg
from grav_proc.arguments import cli_vgrad_arguments, gui_vgrad_arguments
from grav_proc.loader import read_data
from grav_proc.calculations import make_frame_to_proc
from grav_proc.plots import vg_plot
from grav_proc.reports import make_vg_ties_report, make_vg_coeffs_report


# Главная функция программы
def main():
    # Получаем аргументы командной строки для работы с вертикальным градиентом
    args = cli_vgrad_arguments()

    # Если не указаны входные файлы, переходим в графический режим
    if args.input is None:
        args = gui_vgrad_arguments()
        if args.scale_factors:  # Проверяем, заданы ли калибровочные файлы
            calibration_files = []
            # Открываем каждый калибровочный файл для чтения
            for calibration_file_name in args.scale_factors:
                calibration_files.append(open(calibration_file_name, 'r', encoding='utf-8'))
            args.scale_factors = calibration_files

    # Чтение файлов данных
    data_files = []
    for data_file_name in args.input:
        data_files.append(open(data_file_name, 'r', encoding='utf-8'))
    args.input = data_files

    # Преобразование сырых данных в формат, пригодный для дальнейшей обработки
    raw_data = make_frame_to_proc(read_data(args.input))

    # Получаем расчетные данные вертикального градиента: привязки (ties) и коэффициенты (coefficients)
    vg_ties, vg_coef = get_vg(raw_data)

    # Сохранение коэффициентов в файл, если указан файл для коэффициентов
    if args.coeffs:
        output_coeffs = args.coeffs.name
    else:
        output_coeffs = 'coeffs.csv'  # Имя файла по умолчанию для сохранения коэффициентов

    # Создание отчета по коэффициентам вертикального градиента
    make_vg_coeffs_report(vg_coef, output_coeffs, args.verbose)

    # Сохранение привязок в файл, если указан файл для привязок
    if args.ties:
        output_file = args.ties.name
    else:
        output_file = 'ties.csv'  # Имя файла по умолчанию для сохранения привязок

    # Создание отчета по привязкам вертикального градиента
    make_vg_ties_report(vg_ties, output_file, args.verbose)

    # Если указан аргумент для построения графиков, создаем и сохраняем графики
    if args.plot:
        figs = vg_plot(vg_coef, vg_ties)
        for fig, filename in figs:
            fig.savefig(filename + '.png')  # Сохранение каждого графика в файл


# Точка входа в программу
if __name__ == '__main__':
    main()
