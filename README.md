# Sentinel Mosaic QGIS Plugin
This repository contains a QGIS python plugin for ordering low-resolution
cloud-free mosaics from Sentinel Hub and loading them into QGIS. It is useful
for determining which combinations of Sentinel orbits can be used for seamless
mosaics and which years/months are necessary to include to get a high quality
mosaic image.

## Installation
To use the plugin you must first install the `sentinelhub` python package (not
in the sequoia virtual environment):

```
pip install sentinelhub
```

Once you have done that, you must authenticate your machine to access our
Sentinel Hub account. The credentials are in the ST LastPass account, you can
find them by searching for 'Sentinel Hub Authentication'. Once you have found
the credentials, you can authenticate your machine from the bash terminal:

```
sentinelhub.config \
  --instance_id '<instance_id>' \
  --sh_client_id '<sh_client_id>' \
  --sh_client_secret '<sh_client_secret>'
```

The plugin can be added to QGIS by downloading the zip file at the v0.1 release
page and installing via the QGIS Plugin Manager (install from zip).

## Usage

1. Open plugin dock widget
    * Click the plugin icon on your toolbar (it is the ST globe logo)
    * This will open a sidebar with the plugin toggles
2. Create a rectangular polygon feature that covers the extent of the area
   for which you want a mosaic preview.
    * From the menu at the top click Layer > Create Layer > Temporary Scratch
      Layer
      * Set it to polygon geometry with WGS84 projection
    * Digitize the feature using the digitization tools
      * the 'Shape Digitization Toolbar' is very helpful for drawing rectangles
3. Specify the years/months to include in the stack of images to be mosaiced
    * The mosaic process will take the median value of all valid pixels in the
    stack (i.e. no clouds/shadows/snow) so ideally we only include the most
    recent possible images.
    * There are places where it is necessary to take the stack all the way back
    to 2018 in order to get enough valid pixels in the stack (e.g. Maine).
    * The more dates that are  
4. Set the maximum proportion of cloud cover for images included in the stack
    * default is 0.2 (20%)
    * we pay for each scene that is included in the processing stack so we can
    reduce processing cost by excluding scenes that are very cloudy
5. Specify the list of Sentinel 2 relative orbits that you want to include in
   this test
    * Sometimes running mosaics across multiple orbits leaves noticeable seams
    along the boundaries between orbits. We can check for this issue using this
    plugin so we don't spend a bunch of money making stripy mosaics!
    * enter a comma-separated list of relative orbits e.g. `112,69`
      * see this [GeoJSON](sentinel_orbits.geojson)
6. Select your temporary scratch layer from the dropdown menu for 'Layer for
   bounding box'
    * The plugin will order an image that covers the bounding box of this layer 
7. Double check your settings then click the 'Order Mosaic Preview' button to
   order the image
    * This will order a low resolution (fixed 512 pixel width) false color
    composite image and load it into your QGIS session when it is done.
    * The process should take less than one minute
    * Review the image for stripes between orbits, or for hazy/cloud spots that
    were not adequately filled in by the cloud filling process.
    * If there are still clouds left behind you may need to include more years
    in the stack.

## Sentinel Orbits

The sentinel orbit geospatial data is helpful to have in QGIS when you are experimenting with different mosaic settings. A GeoJSON of the relative orbits for Sentinel 2 is can be downloaded [here](sentinel_orbits.geojson).

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
