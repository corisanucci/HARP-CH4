
# Author: Corina Sanucci
# Fecha: 23/03/2021

# Objetivo: 
#           - Aplicar filtros de calidad al producto CH4 L2 de TROPOMI
#           - Generar rasters ortorectificados (producto L3) con los datos filtrados

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

library(harp);library(raster)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

carpeta_salida <- 'D:/Tesina/TROPOMI/TROPOMI_L3/L3_diarios/'
# Guardo todos los archivos en una unica carpeta
setwd(carpeta_salida)

# Path a los archivos:
TROPOfolder <- 'G:/Cori/TROPOMI/'

# Sub-folders con cada anio de datos:
archivo <- dir(TROPOfolder, full.names = T , recursive = T, pattern = '.nc$')


for (i in 1:length(archivo)){
  
  skip_to_next <- FALSE
  
  file <- archivo[i]
  
  tryCatch({TROPO_CH4 = harp::import(file, 
                           operations = 'CH4_column_volume_mixing_ratio_dry_air_validity > 50;
                           keep(latitude_bounds,longitude_bounds,
                           CH4_column_volume_mixing_ratio_dry_air);
                           bin_spatial(4300,-58,0.01,3100,-79,0.01)',
                           options = 'ch4=bias_corrected') # mixing ratio vias correctes
  
  #bin_spatial = en posicion 2 y 5 --> lower-left corner
  # ARGUMENTOS:
  # (extension_lat,latitude_coordinate_lower_left, resolution_lat , 
  #  extension_lon, longitude_coordinate_lower_left, resolution_lon)
  # ¿Como se calcula la extension?
  # (58 - 15)/0.01 = 4300
  # (79 - 48)/0.01 = 3100
  
  
  data <- TROPO_CH4$CH4_column_volume_mixing_ratio_dry_air$data
  
  dat_CH4 <- list()
  dat_CH4$x <- TROPO_CH4$longitude_bounds$data[1,] 
  dat_CH4$y <- TROPO_CH4$latitude_bounds$data[1,]
  dat_CH4$z <- data[,,1]
  
  rm(TROPO_CH4)
  
  if(length(dat_CH4) == 3){   # Puede estar en file sin datos
    
    rCH4 <- raster(dat_CH4)
    
    rm(dat_CH4)
    
    # Hay muchos rasters vacios
    # Guardar unicamente aquellos que tienen datos
    
    if(cellStats(is.na(rCH4), sum) != ncell(rCH4)){
      
      # Primero reemplazo de L2 a CH4 L3:
      filename <- gsub('OFFL_L2__', 'L3_', file)
      # Luego me quedo con la parte que me interesa:
      filename <- substr(filename, 17, nchar(filename) - 29)
      # Guardo el raster:
      writeRaster(rCH4, paste(carpeta_salida, filename, sep=''), 
                  format = 'GTiff',
                  overwrite = TRUE)
    }
    
    rm(rCH4)
    
  }
  }, error = function(e){
    skip_to_next <<- TRUE
  })
  
  if(skip_to_next) { next }
  
}
