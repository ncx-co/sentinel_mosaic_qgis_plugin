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