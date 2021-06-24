import datetime as dt
import parse

from sentinelhub import DataCollection, WebFeatureService

S2_GRANULE_ID_FMT = (
    'S{sat}_{file_class}_{file_category}_' +
    '{level}_{descriptor}_{site_centre}_' +
    '{creation_date}_A{absolute_orbit}_' +
    'T{tile}_{processing_baseline}'
)

PREVIEW_EVALSCRIPT = """
//VERSION=3
// based on this evalscript:
// https://github.com/sentinel-hub/custom-scripts/blob/master/sentinel-2/cloudless_mosaic/L2A-first_quartile_4bands.js
function setup() {
return {
    input: [{
    bands: [
        "B08", // near infrared
        "B03", // green
        "B02", // blue
        "SCL" // pixel classification
    ],
    units: "DN"
    }],
    output: [
    {
        id: "default",
        bands: 3,
        sampleType: SampleType.UINT16
    }
    ],
    mosaicking: "ORBIT"
};
}
// acceptable images are ones collected on specified dates
function filterScenes(availableScenes, inputMetadata) {
var allowedDates = [%s]; // format with python
return availableScenes.filter(function (scene) {
    var sceneDateStr = scene.date.toISOString().split("T")[0]; //converting date and time to string and rounding to day precision
    return allowedDates.includes(sceneDateStr);
});
}
function getValue(values) {
values.sort(function (a, b) {
    return a - b;
});
return getMedian(values);
}
// function for pulling median (second quartile) of values
function getMedian(sortedValues) {
var index = Math.floor(sortedValues.length / 2);
return sortedValues[index];
}
function validate(samples) {
var scl = samples.SCL;
if (scl === 3) { // SC_CLOUD_SHADOW
    return false;
} else if (scl === 9) { // SC_CLOUD_HIGH_PROBA
    return false;
} else if (scl === 8) { // SC_CLOUD_MEDIUM_PROBA
    return false;
} else if (scl === 7) { // SC_CLOUD_LOW_PROBA
    // return false;
} else if (scl === 10) { // SC_THIN_CIRRUS
    return false;
} else if (scl === 11) { // SC_SNOW_ICE
    return false;
} else if (scl === 1) { // SC_SATURATED_DEFECTIVE
    return false;
} else if (scl === 2) { // SC_DARK_FEATURE_SHADOW
    // return false;
}
return true;
}
function evaluatePixel(samples, scenes) {
var clo_b02 = [];
var clo_b03 = [];
var clo_b08 = [];
var clo_b02_invalid = [];
var clo_b03_invalid = [];
var clo_b08_invalid = [];
var a = 0;
var a_invalid = 0;
for (var i = 0; i < samples.length; i++) {
    var sample = samples[i];
    if (sample.B02 > 0 && sample.B03 > 0 && sample.B08 > 0) {
    var isValid = validate(sample);
    if (isValid) {
        clo_b02[a] = sample.B02;
        clo_b03[a] = sample.B03;
        clo_b08[a] = sample.B08;
        a = a + 1;
    } else {
        clo_b02_invalid[a_invalid] = sample.B02;
        clo_b03_invalid[a_invalid] = sample.B03;
        clo_b08_invalid[a_invalid] = sample.B08;
        a_invalid = a_invalid + 1;
    }
    }
}
var gValue;
var bValue;
var nValue;
if (a > 0) {
    gValue = getValue(clo_b03);
    bValue = getValue(clo_b02);
    nValue = getValue(clo_b08);
} else if (a_invalid > 0) {
    gValue = getValue(clo_b03_invalid);
    bValue = getValue(clo_b02_invalid);
    nValue = getValue(clo_b08_invalid);
} else {
    gValue = 0;
    bValue = 0;
    nValue = 0;
}
return {
    default: [nValue, gValue, bValue]
};
}
"""

def absolute_to_relative_orbit(absolute_orbit, sat):
    '''
    Translate Sentinel 2 absolute orbit number to relative orbit number. There
    are 143 relative orbits that are similar to Landsat paths. The relative
    orbit numbers are not readily visible in some Sentinel 2 product IDs so we
    must convert from absolute (number of orbits since some origin point in
    time) to relative orbits (number of orbits since orbit 1).
    '''
    assert sat in ['2A', '2B']
    if sat == '2A':
        adj = -140
    if sat == '2B':
        adj = -26

    return (absolute_orbit + adj) % 143


def get_dates_by_orbit(bbox, start_date, end_date, max_cc, target_orbit, config):
    '''
    For a given bounding box, query Sentinel 2 imagery collection dates between
    two dates (start/end_date) that match a specified list of relative orbits
    and have a maximum cloud cover proportion.

    * bbox is a WGS84 bounding box created by sentinelhub.Geometry.BBox
    * start_date and end_date are date strings formatted as yyyy-mm-dd
    * max_cc is the maximum allowed cloud cover (0-1 scale)
    * target_orbit is a list containing relative orbit numbers to be included
    * config is the Sentinel Hub config object created by sentinelhub.SHConfig()
    '''
    assert target_orbit is not None, "target_orbit must be specified"

    # convert target_orbit to list if just a single orbit
    if type(target_orbit) is int:
        target_orbit = [target_orbit]

    # define time window
    search_time_interval = (f'{start_date}T00:00:00', f'{end_date}T23:59:59')

    # query scenes
    wfs_iterator = WebFeatureService(
        bbox,
        search_time_interval,
        data_collection=DataCollection.SENTINEL2_L2A,
        maxcc=max_cc,
        config=config
    )

    # filter down to dates from specified orbit(s)
    dates = []
    for tile_info in wfs_iterator:
        # raw product ID
        product_id = tile_info['properties']['id']

        # parse the product ID
        product_vals = parse.parse(S2_GRANULE_ID_FMT, product_id)

        # acquisition date
        date = tile_info['properties']['date']

        # absolute orbit is buried in ID after _A string
        absolute_orbit = int(product_vals['absolute_orbit'])

        # which satellite? 2A or 2B
        sat = product_vals['sat']
        assert sat in ('2A', '2B')

        # convert to relative orbit
        relative_orbit = absolute_to_relative_orbit(absolute_orbit, sat)

        if relative_orbit not in target_orbit:
            continue

        # add date if not already added to list
        if date not in dates:
            dates.append(date)

    assert len(dates) > 0, \
        f'No dates available for this bounding box and relative orbit {target_orbit}'

    return dates


def filter_dates(dates, months, years):
    '''
    Filter a list of dates (yyyy-mm-dd format) to only include dates from a list
    of months and years
    '''
    # convert date strings to date objects
    dates = [dt.datetime.strptime(date, '%Y-%m-%d').date() for date in dates]

    # filter down to supplied months/years
    filtered = [date.strftime(
        '%Y-%m-%d') for date in dates if date.month in months and date.year in years]

    assert len(filtered) > 0, \
        'None of supplied dates satisfy desired months/years and maximum cloud coverage.'

    return filtered