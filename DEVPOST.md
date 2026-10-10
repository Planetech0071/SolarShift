# SolarShift

**Turn any rooftop into solar intelligence.**

Team: Planetech0071 — solo developer.

## One-paragraph description

SolarShift turns overhead photographs into an interactive first look at rooftop solar potential. A pretrained RF-DETR model produces real pixel-level building masks; geometric processing turns them into editable polygons. Users set scale and height assumptions, then move through a day of sunlight calculated with pvlib. Roof-level shadow sampling updates power, heatmaps and comparisons. The result connects an ordinary image to a transparent renewable-energy planning scenario, without paid AI APIs or invented annual production.

## Inspiration

Rooftops are everywhere, but their energy potential is difficult to see from a photograph. A large roof can still be shaded at useful times; a smaller roof may have better exposure per installed kilowatt. We wanted a tool that makes those differences understandable before a detailed site survey.

## Brainstorming and design

The core question was: what if a photograph could become a small solar laboratory? We considered an advice-only image assistant and a full 3D reconstruction, then chose a practical middle ground: real instance segmentation, an editable 2.5D geometric model and physical sunlight calculations. The interaction centers on the image and the time slider. Cyan outlines communicate computer vision; yellow and darker sample cells communicate irradiance and shade. A dark workspace keeps the aerial photograph prominent.

## What it does

SolarShift accepts JPG, PNG and WEBP images, including two public-domain USGS samples. It detects roof candidates, outlines their masks and lets users select or correct them. Location, timezone, date, north direction and scale connect the image to a solar scenario. Heights, panel tilt, coverage and efficiency are editable. Users can drag boundary vertices, add manual roofs/canopy/obstacles, calibrate scale from a known distance, compare roofs and export the complete analysis as JSON.

The day slider changes sun elevation and azimuth, projected shadows, sample exposure, mean panel irradiance and current power. A full-day curve and clear-sky kWh estimate summarize each roof. Nighttime production is zero.

## How it was built

Python and FastAPI serve the interface and analysis endpoints. PyTorch and Hugging Face Transformers run a pinned Apache-licensed RF-DETR building segmentation model on CUDA when available, with CPU fallback. OpenCV traces masks and identifies color-based vegetation candidates. Shapely handles polygon geometry; NumPy and pandas handle sampling and time series. pvlib provides solar position and irradiance. The browser uses modular JavaScript, Canvas, SVG, HTML and CSS, with no frontend build step.

OpenAI Codex assisted implementation, research, debugging, documentation and interface verification. All original SolarShift code was created during this build; pretrained weights and dependencies predate it and are credited separately. No model was trained from scratch.

## Computer vision architecture

Large images are bounded for inference and split into overlapping tiles. The model returns building instance masks and confidence scores. OpenCV vectorizes and simplifies boundaries; overlap deduplication prevents common duplicate detections. Coordinates are transformed back into the original photograph, which stays available at its original display resolution. The application never substitutes hardcoded sample polygons for model output.

Vegetation is extracted with an excess-green/HSV heuristic, clearly labeled for manual review. It is not a pretrained tree detector and may include grass. Rooftop obstacles are manually added rather than falsely claimed as detected. The building masks are candidate roof boundaries, not certified measurements.

## Solar physics and shadow model

pvlib's NREL SPA calculates the sun from coordinates and timezone-aware time. Ineichen clear-sky irradiance is transposed to the selected panel tilt and compass azimuth. Each structure is an opaque extruded polygon with an estimated height. Its shadow on another roof depends on the difference between caster and receiving roof heights: length equals that difference divided by the tangent of sun elevation.

Swept polygons preserve concave footprints. A lattice of sample points determines the shaded direct-light fraction on each roof. Direct irradiance is attenuated; diffuse irradiance remains unshaded in the approximation. Installed capacity follows whole-module count and efficiency, and daily kWh integrates ten-minute power samples with the trapezoidal rule. Timezone and daylight-saving behavior are handled explicitly.

## Engineering challenges

The most consequential challenge was preserving a honest relationship between image pixels and physical claims. Scale changes area quadratically; estimated heights alter shadows; timezones change which sun position corresponds to the timeline. We kept those assumptions visible instead of hiding them behind a single recommendation.

Tiled model inference introduces overlapping masks and cropped boundaries. We added deduplication, coordinate checks and manual correction. Concave shadows also needed a polygon sweep rather than a convex hull, which can over-shade empty parts of an L-shaped footprint. Asynchronous inference progress keeps the image interface usable, and the browser receives precomputed day frames for responsive time changes.

## Results and technical achievements

Both supplied California orthophotos passed upload, real model inference and solar simulation. The model produced 13 roof candidates in Davis and 38 in Sacramento. Measured warm workflows on this machine completed in roughly five seconds, including inference and full-day physics; these are two observed examples, not a general performance guarantee. Automated tests cover cardinal shadows, partial shading, concavity, height and scale effects, location changes, nighttime zero output, polar night, daylight-saving integration and invalid API inputs. Browser verification covers selection, comparisons, timeline behavior and manual geometry correction; see TEST_RESULTS.md for the final record.

The technical contribution is the working connection between pixel masks, editable spatial assumptions, receiving-roof-height shadow geometry and reproducible energy time series. It is more than an image API wrapper and is inspectable through the exported data.

## Lessons learned

Trust improves when users can see and change an assumption. A scientifically grounded approximation is useful when its boundaries are explicit. Visual polish works best when motion and color communicate a calculation rather than decorate a result. Existing image shadows, hidden structures and roof slope still limit what one photograph can establish.

## Future improvements

Add a dedicated canopy model, better tile-edge merging, georeferenced image import, roof-plane geometry, feasible panel placement, weather/TMY data and electrical string modeling. A 3D viewer and persistent projects would follow those accuracy improvements. None of these are claimed as current features.

## Resources

RF-DETR weights: https://huggingface.co/merve/rf-detr-seg-satellite-buildings

Solar library: https://pvlib-python.readthedocs.io/

USGS imagery: https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer

Full credits and licenses: ATTRIBUTION.md.

## Built with

Python · FastAPI · PyTorch · Transformers · RF-DETR · OpenCV · Shapely · NumPy · pandas · pvlib · JavaScript · Canvas · SVG · HTML · CSS · OpenAI Codex
