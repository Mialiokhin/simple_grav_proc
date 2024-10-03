import numpy as np
import pandas as pd
from grav_proc.calculations import get_ties_sum  # Импорт функции для подсчета суммы связей


# Функция для генерации отчета на основе связей (ties)
def get_report(ties):
    # Указываем необходимые столбцы для отчета
    columns = [
        'station_from',  # * Начальная станция
        'station_to',  # * Конечная станция
        'date_time',  # Время
        'survey_name',  # Имя измерения
        'operator',  # Оператор
        'meter_type',  # Тип прибора
        'instrument_serial_number',  # * Серийный номер прибора
        # 'line',                     # * Линия (не используется, закомментировано)
        'instr_height_from',  # Высота начальной точки
        'instr_height_to',  # Высота конечной точки
        'tie',  # * Связь между станциями
        'err'  # * Ошибка измерения
    ]
    # Заголовки для итогового отчета
    headers = [
        'From',  # Начальная станция
        'To',  # Конечная станция
        'Date',  # Время измерения
        'Survey',  # Имя измерения
        'Operator',  # Оператор
        'Meter',  # Тип прибора
        'S/N',  # Серийный номер прибора
        # 'Line',                   # Линия (закомментировано)
        'Height From (mm)',  # Высота начальной станции (в мм)
        'Height To (mm)',  # Высота конечной станции (в мм)
        'Tie (uGal)',  # Значение связи (в микрогалах)
        'SErr (uGal)'  # Стандартная ошибка (в микрогалах)
    ]

    # Начальная строка для отчета
    report = f'\nThe mean ties between the stations:\n==================================='

    # Замена NaN на None для корректной обработки
    ties = ties.replace(np.nan, None)

    # Преобразование DataFrame в таблицу с форматированием
    ties_table = ties[columns].to_markdown(
        index=False,  # Без индексов
        headers=headers,  # Указание заголовков таблицы
        tablefmt="simple",  # Формат таблицы
        floatfmt=".1f")  # Формат для числовых значений

    # Добавление таблицы в отчет
    report = f'{report}\n{ties_table}'

    # Инициализация DataFrame для хранения сумм
    ties_sums = pd.DataFrame()

    # Группировка данных по серийному номеру прибора
    group_by_meters = ties.groupby('instrument_serial_number')

    # Для каждого прибора вычисляем сумму связей
    for meter, meter_ties in group_by_meters:
        meter_ties_sums = get_ties_sum(meter_ties)
        if len(meter_ties_sums):
            ties_sums = pd.concat([ties_sums, meter_ties_sums])

    # Если есть данные по суммам, добавляем их в отчет
    if len(ties_sums):
        report = f'{report}\n\nSum of the cicle ties:\n======================\n'
        headers = ['Meter', 'Cicles', 'Sum (uGal)']  # Заголовки для сумм
        sums_table = ties_sums.to_markdown(
            index=False,
            headers=headers,
            tablefmt="simple",
            floatfmt=".2f")  # Формат для числовых значений с двумя знаками после запятой
        report = report + sums_table

    return report  # Возвращаем итоговый отчет


# Функция для создания CSV файла для утилиты vg_fit
def make_vgfit_input(means, filename):
    ''' Make CSV file for vg_fit utilite '''
    columns = [
        'created_date',  # Дата создания
        'survey',  # Имя измерения
        'operator',  # Оператор
        'meter',  # Прибор
        'line',  # Линия
        'from_height',  # Высота начальной точки
        'to_height',  # Высота конечной точки
        'gravity',  # Значение гравитации
        'std_gravity',  # Стандартная ошибка для гравитации
        'data_file'  # Имя файла данных
    ]

    # Преобразование DataFrame для записи в CSV
    means_to_vgfit = means[columns]
    means_to_vgfit.columns = [
        'date',  # Дата
        'station',  # Станция
        'observer',  # Наблюдатель
        'gravimeter',  # Гравиметр
        'runn',  # Линия
        'level_1',  # Высота 1
        'level_2',  # Высота 2
        'delta_g',  # Дельта гравитации
        'err',  # Ошибка
        'source'  # Источник данных
    ]

    # Сохранение данных в CSV файл
    means_to_vgfit.to_csv(filename, index=False)

    return means_to_vgfit


# Функция для создания отчета по связям для вертикальных градиентов (VG)
def make_vg_ties_report(ties, output_file, verbose=False):
    columns = [
        'created_date',  # Дата создания
        'survey',  # Имя измерения
        'operator',  # Оператор
        'meter',  # Прибор
        'line',  # Линия
        'from_point',  # Начальная точка
        'to_point',  # Конечная точка
        'from_height',  # Высота начальной точки
        'to_height',  # Высота конечной точки
        'gravity',  # Значение гравитации
        'std_gravity',  # Стандартная ошибка для гравитации
    ]

    # Заголовки для CSV файла
    header = [
        'date',  # Дата
        'station',  # Станция
        'observer',  # Наблюдатель
        'gravimeter',  # Гравиметр
        'line',  # Линия
        'from_point',  # Начальная точка
        'to_point',  # Конечная точка
        'level_1',  # Высота 1
        'level_2',  # Высота 2
        'delta_g',  # Дельта гравитации
        'std',  # Ошибка
    ]

    # Сохранение данных в CSV файл
    ties.to_csv(
        output_file,
        columns=columns,  # Выбор столбцов для сохранения
        header=header,  # Заголовки для CSV файла
        index=False,  # Без индексов
        date_format='%Y-%m-%d'  # Формат для дат
    )

    # Если включен подробный вывод, выводим данные в консоль
    if verbose:
        print()
        print(ties[columns].to_markdown(index=False, tablefmt='simple', floatfmt='.3f'))
        print()


# Функция для создания отчета по коэффициентам для вертикальных градиентов (VG)
def make_vg_coeffs_report(coeffs, output_file, verbose=False):
    # Сохраняем только нужные столбцы
    # coeffs[['meter', 'survey', 'a', 'b', 'ua', 'ub', 'covab']].to_csv(
    coeffs[['survey', 'a', 'b', 'ua', 'ub', 'covab']].to_csv(
        output_file,
        index=False,
        float_format='%.3f'  # Формат для числовых данных с тремя знаками после запятой
    )

    # Если включен подробный вывод, выводим данные в консоль
    if verbose:
        print()
        # print(coeffs[['meter', 'survey', 'a', 'b', 'ua', 'ub', 'covab']].to_markdown(
        print(coeffs[['survey', 'a', 'b', 'ua', 'ub', 'covab']].to_markdown(
            index=False,
            tablefmt='simple',
            floatfmt='.1f'  # Формат для числовых данных с одним знаком после запятой
        ))
        print()
