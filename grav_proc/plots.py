from datetime import timedelta as td  # Импорт функции для работы с временными интервалами
import seaborn as sns  # Библиотека для визуализации данных
from matplotlib.dates import DateFormatter  # Для форматирования дат на графиках
import matplotlib.pyplot as plt  # Основной модуль для построения графиков
import matplotlib.patches as mpatches  # Для создания патчей на графиках (например, легенд)
import geopandas as gpd  # Работа с географическими данными
from shapely.geometry import LineString  # Для создания геометрических объектов, таких как линии
import numpy as np  # Работа с массивами и матричными операциями
import pandas as pd  # Работа с табличными данными (DataFrame)
import contextily as cx  # Добавление базовых карт (например, OpenStreetMap) в визуализации
from cartopy import crs as ccrs  # Координатные системы для карт
import cartopy.io.img_tiles as cimgt  # Модули для работы с картографическими плитками
# from cartopy.io.img_tiles import GoogleTiles
# import ssl
# закомментированный импорт GoogleTiles и модуль ssl используются для загрузки плиток с карт

def get_residuals_plot(raw, readings, ties):
    ''' Get plot of residuals (получение графика остатков) '''

    # Получение списка уникальных номеров приборов
    meters = ties.instrument_serial_number.unique()

    # Для каждого прибора рассчитываются остатки и строится график
    for meter in meters:
        meter_raw = raw[raw.instrument_serial_number == meter]
        meter_readings = readings[readings.instrument_serial_number == meter]
        meter_ties = ties[ties.instrument_serial_number == meter]

        # Перебор строк с данными по связям
        for _, tie_row in meter_ties.iterrows():
            tie_readings = meter_raw[meter_raw.line == tie_row.line]
            first_reading = meter_readings[meter_readings.line == tie_row.line].iloc[0].corr_grav
            tie_station = tie_row.station_to

            # Вычисление остатков для каждой строки измерений
            for reading_index, reading_row in tie_readings.iterrows():
                if reading_row.station == tie_station:
                    raw.loc[
                        reading_index,
                        ['residuals']] = reading_row.corr_grav\
                            - first_reading - tie_row.tie
                else:
                    raw.loc[
                        reading_index,
                        ['residuals']] = reading_row.corr_grav - first_reading

    # delta_time = readings.iloc[-1].date_time - readings.iloc[0].date_time
    # if delta_time < td(hours=24):
    #     date_formatter = DateFormatter('%H:%M')
    # elif delta_time > td(days=2):
    #     date_formatter = DateFormatter('%b %d')
    # else:
    #     date_formatter = DateFormatter('%b %d %H:%M')
    # Установка параметров визуализации (стиль сетки графиков)
    meter_type = raw.iloc[0].meter_type

    with sns.axes_style("whitegrid"):
        # Создание сетки графиков (один график на каждый прибор)
        plots = sns.FacetGrid(
            raw,
            col='instrument_serial_number',
            hue='station',
            col_wrap=1,  # Количество колонок на графике
            aspect=4,
            margin_titles=True,
            sharey=False,  # Не делить ось Y между графиками
            sharex=False  # Не делить ось X между графиками
        )

    # Отображение данных на графиках (ось X - время, ось Y - остатки)
    plots.map(
        sns.scatterplot,
        'date_time',
        'residuals'
    )

    # Установка подписей для осей и заголовков графиков
    plots.set_axis_labels('Date & Time [UTC]', 'Residuals [uGals]')
    plots.set_titles('Residuals of '+meter_type+' {col_name}')
    plots.add_legend(title='Stations')
    # plots.axes[0].xaxis.set_major_formatter(date_formatter)

    return raw  # Возвращаем обновленные данные с рассчитанными остатками


def get_map(ties):
    ''' Get map of ties scheme (получение схемы связей в виде карты) '''

    # Создание таблиц координат станций "откуда" и "куда"
    stations_from = ties[['station_from', 'lat_from', 'lon_from']]
    stations_from.columns = ['station', 'lat', 'lon']  # Переименование столбцов для удобства
    stations_to = ties[['station_to', 'lat_to', 'lon_to']]
    stations_to.columns = ['station', 'lat', 'lon']

    # Объединение данных и группировка по станциям для усреднения координат
    stations = pd.concat([stations_from, stations_to], ignore_index=True).groupby('station').mean()

    # Получение списка уникальных линий связей
    lines = ties[['station_from', 'station_to']].drop_duplicates(ignore_index=True)

    # Создание карты
    fig = plt.figure(figsize=(10, 10))
    xmin, xmax, ymin, ymax = stations.lon.min(), stations.lon.max(), stations.lat.min(), stations.lat.max()
    dx = xmax - xmin
    dy = ymax - ymin

    # Настройка границ карты в зависимости от пропорций
    if dx < 2 * dy:
        offsety = dy * 0.1
        ymin, ymax = ymin - offsety, ymax + offsety
        dy = ymax - ymin
        dx = dy * 16 / 9
        centerx = xmin + (xmax - xmin) / 2
        xmin, xmax = centerx - dx / 2, centerx + dx / 2
    else:
        offsetx = dx * 0.1
        xmin, xmax = xmin - offsetx, xmax + offsetx
        dx = xmax - xmin
        dy = dx * 9 / 16
        centery = ymin + (ymax - ymin) / 2
        ymin, ymax = centery - dy / 2, centery + dy / 2

    extent = [xmin, xmax, ymin, ymax]
    request = cimgt.OSM()  # Использование OpenStreetMap для карт
    ax = plt.axes(projection=request.crs)
    ax.set_extent(extent)

    # Установка уровня детализации карты (zoom) в зависимости от размера области
    if dx < 0.2:
        zoom = 13
    elif dx < 0.3 and dx > 0.2:
        zoom = 12
    elif dx < 0.7 and dx > 0.3:
        zoom = 11
    elif dx < 1 and dx > 0.7:
        zoom = 10
    else:
        zoom = 8

    ax.add_image(request, zoom)

    # Отрисовка линий, соединяющих станции
    for _, row in lines.iterrows():
        x_from = stations.loc[row.station_from, 'lon']
        y_from = stations.loc[row.station_from, 'lat']
        x_to = stations.loc[row.station_to, 'lon']
        y_to = stations.loc[row.station_to, 'lat']

        # tie = ties[
        #     (ties['station_from'] == row.station_from) & \
        #     (ties['station_to'] == row.station_to)
        # ][['tie']].mean()
        ax.plot([x_from, x_to], [y_from, y_to], '-ok', mfc='w', transform=ccrs.PlateCarree())

    # Добавление подписей для станций
    for idx, row in stations.iterrows():
        ax.annotate(idx,
                    xy=(row.lon, row.lat),
                    xycoords='data',
                    xytext=(1.5, 1.5),
                    textcoords='offset points',
                    color='k',
                    fontsize=16,
                    transform=ccrs.PlateCarree())
    # plt.show()

    return fig  # Возвращаем фигуру (карту)


def vg_plot(coeffs, ties, by_meter=False):
    ''' Построение графика зависимости вертикального градиента (VG) от высоты '''

    figs = []
    # Перебор каждой строки с коэффициентами для построения графика
    for _, row in coeffs.iterrows():
        # Если анализируем данные по каждому прибору отдельно
        if by_meter:
            df = ties[(ties.meter == row.meter) & (ties.survey == row.survey)]
        else:
            df = ties[ties.survey == row.survey]

        # Генерация диапазона высот и расчёт полиномиальной функции для VG
        y = np.linspace(0, 1.5, 50)
        b, a = row.b, row.a
        p = np.poly1d([b, a, 0])  # Полиномиальная функция VG
        resid = row.resid.reshape((int(len(row.resid) / 2), 2))
        # h_min = df[['from_height', 'to_height']].min().min() * 1e-3

        h_ref = 1  # Ссылка на стандартную высоту
        # substruct = (p(h_min) - p(h_ref)) / (h_min - h_ref)

        substruct = p(h_ref)  # Коррекция VG относительно стандартной высоты
        gp = lambda x: p(x) - x * substruct

        # Расчет ошибки по коэффициентам
        ua, ub = row.ua, row.ub
        cov = row.covab
        u = abs(h_ref - y) * np.sqrt(ub ** 2 + (y + h_ref) ** 2 * ua ** 2 + 2 * (h_ref + y) * cov)

        x = gp(y)  # Корректированное значение VG
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.plot(x, y)  # Построение графика зависимости
        ax.fill_betweenx(y, x - u, x + u, alpha=0.2)  # Отображение диапазона ошибок

        # Построение отдельных точек высоты для каждой пары измерений
        for height_from, height_to, resid in zip(df.from_height, df.to_height, resid):
            heights = np.array([height_from, height_to]) * 1e-3
            ax.plot(gp(heights) + resid, heights, '.-')

        # Добавление заголовков и подписей осей
        if by_meter:
            plt.title(f'Meter: {row.meter}, survey: {row.survey} (substract {substruct:.1f} uGal/m)')
        else:
            plt.title(f'Survey: {row.survey} (substract {substruct:.1f} uGal/m)')
        plt.xlabel(f'Gravity [uGal]')
        plt.ylabel('Height [m]')

        # Установка пределов для осей
        low, high = plt.xlim()
        bound = max(abs(low), abs(high))
        ax.set(xlim=(-bound, bound), ylim=(0, 1.5))

        fig.tight_layout()
        figs.append((fig, row.survey))  # Добавление графика в список
        plt.close()

    return figs  # Возвращаем список графиков


def residuals_plot(raw_data):
    ''' Построение графика остатков для разных станций и приборов '''

    meters = raw_data['instrument_serial_number'].unique()  # Получение списка приборов
    meter_number = {}

    # Пронумеровываем приборы для построения графиков
    for index, meter in enumerate(meters):
        meter_number[meter] = index

    # Создание графика с количеством строк, равным количеству приборов
    fig, ax = plt.subplots(nrows=len(meters), figsize=(16, 8), layout='constrained')
    fig.supylabel('Residuals [uGal]')  # Общая подпись для оси Y
    fig.supxlabel('Date Time')  # Общая подпись для оси X

    # Построение графиков для каждой станции
    for meter_created, grouped in raw_data.groupby(['instrument_serial_number', 'created']):
        meter, created = meter_created
        for station, grouped_by_station in grouped.groupby('station'):
            if len(meters) > 1:
                ax[meter_number[meter]].set_title(f'CG-6 #{meter}', loc='left')
                ax[meter_number[meter]].plot(grouped_by_station['date_time'], grouped_by_station['resid'], '.', label=station)
                # ax[meter_number[meter]].legend(loc='upper right')
            else:
                ax.set_title(f'CG-6 #{meter}', loc='left')
                ax.plot(grouped_by_station['date_time'], grouped_by_station['resid'], '.', label=station)
                # ax.legend(loc='upper right')
    fig.legend()  # Добавление легенды
    fig.tight_layout()

    return fig  # Возвращаем готовый график
