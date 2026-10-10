---
title: SolarShift
emoji: ☀️
colorFrom: yellow
colorTo: gray
sdk: docker
app_port: 7860
license: mit
---

# SolarShift

**Turn any rooftop into solar intelligence.**

An AI-assisted preliminary solar-planning workspace for Banana Hacks 2026. Upload overhead imagery, extract real building instance masks, correct the geometry, and explore a full day of computed sunlight, shadows and clear-sky energy.

Solo developer: **Planetech0071**. Original project code created on October 11, 2026 (Europe/Rome). Open-source dependencies and the pretrained model are credited in [ATTRIBUTION.md](ATTRIBUTION.md).

## Try it

**Live app:** https://solarshift-seven.vercel.app  
**Source:** https://github.com/Planetech0071/SolarShift

1. Choose Davis or Sacramento, or upload a JPG, PNG or WEBP aerial photograph.
2. Click **Analyze location**. The backend runs actual RF-DETR instance segmentation; no sample polygons are substituted.
3. Select a rooftop on the image or from the ranked list. Move the timeline from morning to evening.
4. Set image scale, latitude, longitude, IANA timezone, date and image north direction. Set building/canopy heights and panel tilt/azimuth.
5. Use **Edit boundary** to drag polygon vertices, or **Draw a new region** to add a roof, canopy or obstacle. Enter finishes drawing; Escape cancels. Use **Calibrate a known distance** to mark two image points.
6. Compare roofs, including generation per installed kWp. Export all geometry, assumptions and time-series results as JSON.

## Start on Windows

Requires Python 3.12. The current workspace has an installed virtual environment and downloaded model:

```powershell
.\start.ps1
```

Open http://127.0.0.1:8000. Alternatively:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

For a fresh checkout, `start.ps1` creates a virtual environment and installs CPU PyTorch plus the pinned dependencies. CUDA is optional; if a compatible GPU build of PyTorch is already installed in your environment, SolarShift selects it automatically. Set `SOLARSHIFT_CPU=1` to force CPU. No keys or accounts are needed to run the app. The first run downloads approximately 142 MB of publicly available model weights; wait for **Vision engine ready** before recording.

## Start on Linux / macOS

```sh
python3.12 -m venv .venv
. .venv/bin/activate
pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
python -m scripts.download_model
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

There is no frontend build step. The modular browser application uses JavaScript ES modules, semantic HTML, CSS, Canvas and SVG. This keeps the demo deployable as one Python service. For development, add `--reload`. For a public container:

```sh
docker build -t solarshift .
docker run --rm -p 7860:7860 solarshift
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for free hosting and the current live-demo state.

## Architecture

```text
image → validation / EXIF transpose → overlapping RF-DETR tiles
      → instance masks → OpenCV contours → simplified roof candidates
      → overlap deduplication → original image coordinates
      → editable extruded polygons + vegetation heuristic
      → pvlib solar position / clear-sky irradiance
      → roof-plane swept shadows / lattice point tests
      → panel power + daily integration → interactive canvas + charts
```

- `backend/vision.py`: pretrained model loading, tiled inference, polygon extraction, deduplication and color-based vegetation.
- `backend/physics.py`: sun, irradiance, concavity-preserving shadow projection, rooftop sampling and energy.
- `backend/contracts.py`: Pydantic API validation.
- `backend/app.py`: FastAPI upload, asynchronous inference jobs, progress and simulation endpoints.
- `public/app.js`: application state, viewer, editing, calibration, charts and comparisons.
- `tests/`: focused physics, geometry and API tests.
- `scripts/verify_api.py`: real-image integration test against a running server.

## Computer vision

**RF-DETR Seg Medium**, pretrained and fine-tuned for satellite buildings by Merve Noyan. The model revision is pinned. Images are bounded to 1800 px on the longest side for inference, tiled at 640 px with 512 px stride, then normalized/resized by the model processor. The original image remains the display source. Detection threshold is 0.45, instance-mask threshold 0.5. OpenCV extracts contours, simplifies vertices and maps coordinates back to the original image. Overlapping candidates are removed using intersection-over-smaller-area greater than 0.5, preferring masks away from tile edges.

Vegetation uses an explicitly labeled excess-green/HSV heuristic, morphology and compact-region filtering. It can mistake grass for canopy or miss dark trees. **It is not a tree AI model.** Visible rooftop equipment is not automatically detected; users add shading obstacles manually. Review low-confidence and cropped roofs. Model scores are not calibrated correctness probabilities.

## Solar methodology

- Solar position: pvlib `nrel_numpy`, NREL Solar Position Algorithm, based on location and timezone-aware date/time.
- Clear sky: Ineichen model; default Linke turbidity 3, altitude 0 m.
- Plane-of-array irradiance: isotropic sky transposition, panel tilt and compass azimuth, albedo 0.2.
- Shadows: opaque vertical prisms. At receiving roof height, caster height difference `Δh` gives shadow length `Δh / tan(elevation)`. Direction is opposite solar azimuth, with image north rotation. The swept footprint is the union of the original polygon, translated polygon and edge quadrilaterals, preserving concavity.
- Approximately 180 lattice samples per roof determine the shaded fraction. Objects at or below the receiving roof height do not shade it. Vegetation is modeled as an opaque prism and requires manual height confirmation.
- Direct POA is reduced by shaded fraction. Diffuse sky and ground irradiance stay unshaded; electrical string mismatch is omitted.
- Below the horizon, irradiance, direct sunlight and power are explicitly zero.
- 10-minute samples span the actual local civil day, including daylight-saving changes. Trapezoidal integration gives daily kWh and equivalent sunlit hours. Sunrise/sunset labels are approximate first/last positive-elevation samples.

Default capacity assumptions: 65% usable coverage, 2 m² modules, 22% module efficiency, performance ratio 0.80. Panel count is floored to a whole number. `capacity_kWp = panel_count × module_area × efficiency`. `power_kW = capacity_kWp × mean_POA_Wm2 / 1000 × performance_ratio`. No arbitrary roof score or invented annual energy is used. Roofs rank by total daily clear-sky generation; specific yield provides a size-normalized comparison. Coverage and panel count are area estimates, not a feasible panel layout.

## Tests and evidence

```sh
python -m pytest tests -q
python scripts/verify_api.py
```

See [TEST_RESULTS.md](TEST_RESULTS.md) for measured results, browser checks and limits. Screenshots in [DEMO_ASSETS](DEMO_ASSETS/) show the running application. The end-to-end test needs the server running and downloads no new imagery.

## Limitations

This is a preliminary planning tool. One image does not establish heights, roof slope, hidden obstacles, legal setbacks or load-bearing capacity. Building masks may cover only part of a roof or extend onto a facade. Small buildings and structures crossing tile/image edges may be incomplete. Large inputs are downsampled for inference. The first photograph's real shadows are baked into its pixels; the colored and shaded overlays show a new scenario, not a reconstructed shadow-free photograph.

The clear-sky scenario excludes clouds, terrain horizon, module temperature, diffuse occlusion, string-level electrical losses and annual weather. Heights are absolute above an assumed level ground plane; tilted panel orientation changes irradiance, while shade sampling uses a flat receiving roof plane. Objects beyond the image extent are unknown. Existing panels are not subtracted. No engineering or financial accuracy is claimed. Two real scenes were exercised; no ground-truth segmentation benchmark or broad generalization study was performed.

Uploads are processed in memory. The browser keeps the original image locally; local server job results expire after one hour. There are no paid runtime API calls, persistent image database, authentication or multi-user project storage.

The Vercel deployment uses CPU inference and returns analysis directly in its request, so no background job state needs to survive between requests. Hosted uploads are limited to 4 MB; local uploads support 20 MB. The model is bundled during the build. See `DEPLOYMENT.md` for the hosting configuration and verification record.

## Submission materials

- [DEVPOST.md](DEVPOST.md): reusable project description.
- [DEMO_SCRIPT.md](DEMO_SCRIPT.md): 2:40 narration and live recording actions.
- [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md): completed and manual steps.
- [DEMO_ASSETS](DEMO_ASSETS/): real source imagery, logo, screenshots and demo video when rendered.
