# Sentinel Mosaic QGIS Plugin

This repository contains a QGIS python plugin for ordering low-resolution
cloud-free mosaics from Sentinel Hub and loading them into QGIS. It is useful
for determining which combinations of Sentinel orbits can be used for seamless
mosaics and which years/months are necessary to include to get a high quality
mosaic image.

## Installation

To use the plugin you must first install the `sentinelhub` python package.
This can be done in a virtual environment but there are additional steps required
in that case.

### No virtual environment
To install sentinelhub without a virtual environment you can simply run this:
```
pip install sentinelhub
```

### Yes virtual environment
To install sentinelhub package in a virtual environment you need to run this:
```bash
workon {env}
pip install sentinelhub
```

Then in QGIS you need to add your virtual environment to the python path.
You can add a few lines to a script called `startup.py` in your QGIS home
directory:
  1. Locate the QGIS home directory by navigating the menu bar to
     'Settings' > 'User Profiles' > 'Open Active Profile Folder'. This directory
     is located within the QGIS home directory so now you need to navigate up to
     a folder called 'QGIS3'. Once you have found this directory make a file
     called `startup.py` and add these lines:
     ```python
     import sys
     import os
     sys.path = [os.environ['WORKON_HOME'] + '{env}/lib/python3.8/site-packages'] + sys.path
     ```
     This will add the virtualenv to your QGIS python path and you should be
     able to use the `sentinelhub` package from within QGIS.

Once you have done that, you must authenticate your machine to access our
Sentinel Hub account. You can authenticate your machine from the bash terminal:

```
sentinelhub.config \
  --instance_id '<instance_id>' \
  --sh_client_id '<sh_client_id>' \
  --sh_client_secret '<sh_client_secret>'
```

The plugin can be added to QGIS by downloading the
[zip file](https://github.com/SilviaTerra/sentinel_mosaic_qgis_plugin/releases/download/v0.1/SentinelMosaicTester.zip)
at the v0.1 release page and installing via the QGIS Plugin Manager
(install from zip).

Gotcha: if you're getting a `pyproj._network` error, try upgrading your QGIS to 3.16 or above.

## Usage

1. Open plugin dock widget
   - Click the plugin icon on your toolbar (it is the ST globe logo)
   - This will open a sidebar with the plugin toggles
2. Create a rectangular polygon feature that covers the extent of the area
   for which you want a mosaic preview.
   - From the menu at the top click Layer > Create Layer > Temporary Scratch
     Layer
     - Set it to polygon geometry with WGS84 projection
   - Digitize the feature using the digitization tools
     - the 'Shape Digitization Toolbar' is very helpful for drawing rectangles
3. Specify the years/months to include in the stack of images to be mosaiced
   - The mosaic process will take the median value of all valid pixels in the
     stack (i.e. no clouds/shadows/snow) so ideally we only include the most
     recent possible images.
   - There are places where it is necessary to take the stack all the way back
     to 2018 in order to get enough valid pixels in the stack (e.g. Maine).
   - The more dates that are
4. Set the maximum proportion of cloud cover for images included in the stack
   - default is 0.2 (20%)
   - we pay for each scene that is included in the processing stack so we can
     reduce processing cost by excluding scenes that are very cloudy
5. Specify the list of Sentinel 2 relative orbits that you want to include in
   this test
   - Sometimes running mosaics across multiple orbits leaves noticeable seams
     along the boundaries between orbits. We can check for this issue using this
     plugin so we don't spend a bunch of money making stripy mosaics!
   - enter a comma-separated list of relative orbits e.g. `112,69`
     - see this [GeoJSON](sentinel_orbits.geojson)
6. Select your temporary scratch layer from the dropdown menu for 'Layer for
   bounding box'
   - The plugin will order an image that covers the bounding box of this layer
7. Double check your settings then click the 'Order Mosaic Preview' button to
   order the image
   - This will order a low resolution (fixed 512 pixel width) false color
     composite image and load it into your QGIS session when it is done.
   - The process should take less than one minute
   - Review the image for stripes between orbits, or for hazy/cloud spots that
     were not adequately filled in by the cloud filling process.
   - If there are still clouds left behind you may need to include more years
     in the stack.

## Sentinel Orbits

The sentinel orbit geospatial data is helpful to have in QGIS when you are
experimenting with different mosaic settings. A GeoJSON of the relative orbits
for Sentinel 2 is can be downloaded [here](sentinel_orbits.geojson).

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

## Development
If you clone the repo and work on it locally, you can deploy changes to QGIS
using the system package `plugin_build_tool` (`pbt`).

http://g-sherman.github.io/plugin_build_tool/

You will need to modify the file
[SentinelMosaicTester/pb_tool.cfg](./SentinelMosaicTester/pb_tool.cfg) to 
point to the correct QGIS plugin directory on your machine.

```bash
cd sentinel_mosaic_qgis_plugin/SentinelMosaicTester

pbt deploy
```

This will copy the source code into your QGIS plugin folder.
In QGIS you can use the 'Plugin Reloader' plugin to refresh the plugin in your
QGIS session.

## Uploading an installable release
The easiest way to distribute a new release is to zip the contents of the
SentinelMosaicTester directory and upload to GitHub.

1. Zip the package contents
  ```bash
  cd sentinel_mosaic_qgis_plugin
  zip -r SentinelMosaicTester.zip SentinelMosaicTester
  ```

2. Create a tag
  ```bash
  git tag v{version} -m 'SentinelMosaicTester v{version}'
  ```

3. Publish a release via `gh` (GitHub command line interface). This will create
   a release on the specified tag and attach the .zip created in step 1.
  ```bash
  gh release create v{version} SentinelMosaicTester.zip
  ```
  You can also create the release from the GitHub web interface.
