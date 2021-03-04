
## Sentinel Orbits

The sentinel orbit geospatial data is helpful to have in QGIS when you are experimenting with different mosaic settings. A GeoJSON of the relative orbits for Sentinel 2 is can be downloaded [here]("sentinel_orbits.geojson").

Here is the R code used to scrape the data and create the GeoJSON:
```r
library(magrittr)
url <- "https://sentinels.copernicus.eu/documents/247904/4584266/Sentinel-2A_MP_ACQ_KML_20210225T120000_20210315T150000.kml"

orbits_raw <- sf::st_read(url, layer = "NOMINAL") 

orbits_dissolved <- orbits_raw %>%
  dplyr::group_by(OrbitRelative) %>%
  dplyr::filter(OrbitAbsolute == max(OrbitAbsolute)) %>%
  dplyr::summarize(
    .groups = "drop"
  )

sf::st_write(orbits_dissolved, "sentinel_orbits.geojson")
```
