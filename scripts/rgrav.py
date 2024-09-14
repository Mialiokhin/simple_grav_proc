#!/usr/bin/env python
u'''
Read CG-6 data file and calculate ties
'''

# Импортируем необходимые модули для работы с файловыми диалогами, обработкой аргументов, чтением данных,
# расчетами, построением графиков и генерацией отчетов.
from tkinter import filedialog as fd
from grav_proc.arguments import cli_rgrav_arguments, gui_rgrav_arguments
from grav_proc.calculations import make_frame_to_proc, \
    fit_by_meter_created
from grav_proc.loader import read_data, read_scale_factors
from grav_proc.plots import residuals_plot, get_map
from grav_proc.reports import get_report  # , make_vgfit_input


# Главная функция программы
def main():
    # Флаг для определения режима (CLI или GUI)
    gui_mode = False
    args = cli_rgrav_arguments()  # Получаем аргументы через командную строку

    # Если данные не были переданы через командную строку, запускаем графический интерфейс
    if args.input is None:
        gui_mode = True
        args = gui_rgrav_arguments()
        if args.scale_factors:  # Если заданы калибровочные файлы
            calibration_files = []
            # Открываем калибровочные файлы для чтения
            for calibration_file_name in args.scale_factors:
                calibration_files.append(open(calibration_file_name, 'r', encoding='utf-8'))
            args.scale_factors = calibration_files

    # Чтение файлов данных
    data_files = []
    for data_file_name in args.input:
        data_files.append(open(data_file_name, 'r', encoding='utf-8'))
    args.input = data_files

    # Создаем DataFrame из сырых данных для последующей обработки
    raw_data = make_frame_to_proc(read_data(args.input))

    # Если были переданы калибровочные файлы
    if args.scale_factors:
        # Чтение калибровочных коэффициентов и применение их к данным
        scale_factors = read_scale_factors(args.scale_factors)
        group_by_meter = scale_factors.groupby('instrument_serial_number')  # Группировка данных по гравиметрам
        for meter, meter_scale_factors in group_by_meter:
            scale_factors = list(meter_scale_factors['scale_factor'])
            scale_factors_std = list(meter_scale_factors['scale_factor'])
            # Проверяем, если для гравиметра более одного коэффициента, выводим предупреждение
            if len(scale_factors) > 1:
                print('Warning: There is more than one scale factor for a current gravity meter!')
            scale_factor = scale_factors[0]  # Используем первый коэффициент
            scale_factor_std = scale_factors_std[0]
            # Применяем калибровочный коэффициент к данным
            raw_data.loc[raw_data['instrument_serial_number'] == meter, 'scale_factor'] = scale_factor
            raw_data.loc[raw_data['instrument_serial_number'] == meter, 'scale_factor_std'] = scale_factor_std
            raw_data.loc[raw_data['instrument_serial_number'] == meter, 'corr_grav'] = raw_data.loc[raw_data[
                                                                                                        'instrument_serial_number'] == meter, 'corr_grav'] * scale_factor

    # Флаг, указывающий, нужно ли производить расчет по линиям
    by_lines = False
    if args.by_lines:
        by_lines = True

    # Метод расчета (по умолчанию WLS, если указан другой, то используем его)
    method = 'WLS'
    if args.method:
        method = args.method

    # Опорная станция для фиксации
    anchor = None
    if args.anchor:
        anchor = args.anchor

    # Выполняем расчет привязок (ties) на основе сырых данных
    ties = fit_by_meter_created(raw_data, anchor=anchor, method=method, by_lines=by_lines)

    # Генерируем имя файла для отчетов на основе уникальных станций
    basename = '-'.join(str(survey) for survey in raw_data.station.unique())

    # Если указан аргумент для построения графиков, создаем и сохраняем график остатков (residuals)
    if args.plot:
        fig = residuals_plot(raw_data)
        fig.savefig(f'{basename}.png')
        fig.show()

    # Имя файла по умолчанию для сохранения отчета
    default_output_file_report = 'report_' + basename + '.txt'

    # Если программа была запущена в графическом режиме
    if gui_mode:
        # Открываем диалог для сохранения отчета в файл
        output_file_report = open(fd.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[('ACSII text file', '*.txt'), ('All files', '*')],
            initialfile=default_output_file_report,
            title="Save Report"), 'w', encoding='utf-8')
    else:
        # Если файл был передан через командную строку
        if args.output:
            output_file_report = args.output
        else:
            # Если нет, то создаем файл отчета с именем по умолчанию
            output_file_report = open(default_output_file_report, 'w', encoding='utf-8')

    # Генерируем отчет по результатам расчетов
    report = get_report(ties)

    # Сохраняем отчет в файл
    output_file_report.write(report)
    output_file_report.close()

    # Если включен verbose-режим, выводим отчет в консоль
    if args.verbose:
        print(report)

    # Если требуется создание карты, вызываем функцию построения карты
    if args.map:
        fig = get_map(ties)
        fig.savefig(f'{basename}.pdf', bbox_inches='tight')


# Точка входа в программу
if __name__ == '__main__':
    main()
