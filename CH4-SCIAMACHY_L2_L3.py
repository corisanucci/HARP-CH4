# Autora: Corina Sanucci
# Fecha: 18/03/2021

# Objetivos:
#           - Aplicar filtros de calidad al producto CH4 L2 de SCIAMACHY/ENVISAT
#           - Generar un raster ortorectificado (producto L3) con los datos filtrados

# ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## #

import harp
import coda
import glob
import numpy as np
import rasterio
from rasterio.transform import Affine
import re

# ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## #

# carpeta para guardar los rasters generados:
output_folder = 'D:/Tesina/SCIAMACHY/SCIAMACHY_L3/L3_diarios_py/'

# Los archivos están en multiples subcarpetas año/mes/dia/ adentro de F:/TESINA/SCIAMACHY/
# Genero una lista con los archivos y sus paths:
SCIAfiles = glob.glob('G:/Cori/SCIAMACHY/**/*.N1',
                      recursive=True)
# Con recursive = T uso “**” entre barras ('./**/') para que recorra todas las subcarpetas
# Agrega unicamente los archivos de extensión .N1

print(len(SCIAfiles))  # ¿Cuántos archivos son en total?: 20890

for i in SCIAfiles:
    try:  # Pueden presentarse excepciones/errores, como NoDataError
        SCI_CH4 = harp.import_product(i, options='dataset=nad_ir1_ch4')
        # los archivos contienen mas de un gas: indico el dataset de ch4

        pd = coda.open(i)  # abro el mismo archivo desde coda

        # Agrego al archivo importado con harp tres variables adicionales que me interesa filtrar
        SCI_CH4.err_CH4 = harp.Variable(coda.fetch(pd, "nad_ir1_ch4", -1, "non_linear_fit_param_err",
                                                   0), ["time"])  # error en el factor de escala de CH4
        SCI_CH4.err_CO2 = harp.Variable(coda.fetch(pd, "nad_ir1_ch4", -1, "non_linear_fit_param_err",
                                                   1), ["time"])  # error en el factor de escala de CO2
        SCI_CH4.err_H2O = harp.Variable(coda.fetch(pd, "nad_ir1_ch4", -1, "non_linear_fit_param_err",
                                                   2), ["time"])  # error en el factor de escala de H2O

        coda.close(pd)  # cierro el archivo en coda

        SCI_CH4_filt = harp.execute_operations(SCI_CH4,
                                               operations='scan_direction_type == "forward";'
                                                          # solo mediciones forward
                                                          
                                                          'cloud_fraction < 0.2;'  
                                                          # max cobertura de nubes 20%
                                                          
                                                          # Qualiy flags (16 bits big-endian):
                                                          # bit 15 True: convergencia del modelo
                                                          # bit 14 True: solar zenith angle < 80°
                                                          # Busco: 1100000000000000 = 49152
                                                          'CH4_column_number_density_validity=&49152;'
                                                          
                                                          # los 3 errores del modelo deben ser positivos:
                                                          'err_CH4>=0;err_CO2>=0;err_H2O>=0;'
                                                          # errores maximos recomendados:
                                                          'err_CH4<0.005;err_CO2<0.01;'  
                                                          
                                                          # mantengo solo grilla de lat/lon y [CH4]
                                                          'keep(longitude_bounds, latitude_bounds,'
                                                          'CH4_column_number_density);'
                                                          
                                                          # Genero el producto L3:
                                                          # ARGUMENTOS bin_spatial:
                                                          # (exten_lat,lat_coord_lower_left,res_lat,
                                                          # exten_lon,lon_coord_lower_left,res_lon)
                                                          # ¿Como se calculan los extent?
                                                          # (max lat - min lat)/res_lat
                                                          # (max lon - minlon)/res_lon
                                                          'bin_spatial(86,-58,0.5,62,-79,0.5)')

        # Genero una grilla/array con filas y columnas en la extensión de mi área
        x = np.linspace(-48, -79, 62)  # (lon_left, lon_right, ncols)
        y = np.linspace(-15, -58, 86)  # (lat_bottom, lat_top, nrows)
        X, Y = np.meshgrid(x, y)

        # Guardo los datos de CH4 en un array
        Z = np.array(SCI_CH4_filt.CH4_column_number_density.data)
        # Algunos archivos no tienen esta variable luego del filtro de calidad
        # en esos casos excepción: AttributeError

        # Si no hay datos de CH4 pasar al siguiente archivo:
        is_empty = Z.size == 0
        if is_empty:
            continue

        # Si el array contiene todos NA pasar al siguiente archivo:
        if np.isnan(Z).all():  # True si TODOS los registros son NA
            continue

        # Genero una matriz de transformación para mapear los pixeles: de (row,col) a spatial positions
        res = 0.5  # resolución establecida (en grados)
        transform = Affine.translation(x[-1] - res / 2, y[-1] - res / 2) * Affine.scale(res, res)

        # Genero el path para guardar el raster a partir del nombre del archivo .N1:
        filename = re.sub('_OL__2PYDPA', '_CH4_L3_', i)  # reemplazo 1er término por 2do
        filename = filename[29:55]
        filename = output_folder + filename + '.tif'  # agrego extensión

        # Abrir dataset para guardar la grilla georreferenciada
        with rasterio.open(filename,
                           'w',  # writing mode
                           driver='GTiff',
                           height=Z.shape[1],
                           width=Z.shape[2],
                           count=1,  # numero de bandas
                           dtype=Z.dtype,
                           crs='+proj=latlong +datum=WGS84 +no_defs +ellps=WGS84 +towgs84=0,0,0',
                           # Estoy en coordenadas geográficas WGS84
                           transform=transform,
                           ) as CH4dts:
            CH4dts.write(Z)  # Agrego al dataset los datos de CH4
            CH4dts.close()  # Cierro la conexión con el dataset

    except harp.NoDataError:  # Si se encuentra con NoDataError continua con la siguiente iteracion
        print('archivo sin datos:', i)  # registro los archivos que presentaron error

    except AttributeError:  # Surge al obtener un producto harp vacio luego del filtrado
        print('los datos de', i, 'no tienen la calidad recomendada')

    except harp.CLibraryError:  # Surge porque algunos archivos no tiene la CH4_column_number_density
        print('trying to read beyond the end of:', i)



# ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## # ## #

# Resultados:
# Se procesaron 20890 archivos .N1 con las órbitas completas de SCIAMACHY/ENVISAT entre el 2002 y el 2006
# Se generaron 2285 imágenes diarias de CH4 con la calidad recomendada
