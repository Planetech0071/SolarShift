# Verification record

## Automated checks

- 28 tests passed with Python 3.12. Tests cover cardinal shadow directions, image north rotation, concave footprints, partial shading, height and scale changes, location changes, nighttime zero production, polar night, daylight-saving day length, polygon validation, upload validation and unknown jobs.
- Three hosting checks exercise the serverless result response, its 4 MB upload limit and retryable inference failure.
- `node --check public/app.js` passes.

## Real model and physics

Both public-domain USGS/NAIP samples were uploaded to the running local service and processed by the actual pinned RF-DETR model. Davis produced 13 rooftop candidates and Sacramento produced 38. No hardcoded polygons were substituted. Warm GPU workflows on the development machine took approximately five seconds including full-day solar calculations. These measurements are two examples, not a general speed or accuracy benchmark.

PNG and WEBP uploads also passed real inference. A 2400 × 1800 WEBP was reduced to 1800 × 1350 for inference; returned polygon coordinates stayed within the original image bounds. Invalid uploads and invalid simulation inputs returned errors.

`python -m scripts.verify_serverless` exercises both samples with actual CPU inference and the stateless Vercel request path. `python scripts/verify_api.py --base <deployed-url> --prefix vercel-` verifies the hosted sample files, real inference, full-day physics and nighttime behavior. Measured reports are kept in ignored `runtime/` files.

The stateless CPU check passed for both samples: Davis returned 13 rooftops in an 18.10-second workflow including initial model loading; Sacramento returned 38 rooftops in a 6.22-second warm workflow. These were local CPU checks, not Vercel latency measurements.

## Browser checks

The running interface was exercised for image loading, rooftop selection, two-roof comparisons, morning/noon/night timeline changes, play/pause, vertex editing, height changes, location changes, known-distance calibration, manual roof drawing and JSON export. Changes triggered recalculation and changed calculated results.

A 390 px wide same-origin iframe checked the narrow layout and sample analysis. Its content had no horizontal overflow. This was a responsive layout check, not native phone emulation. Desktop browser console checks reported no warnings or errors during the recorded checks.

## Public Vercel verification

Verified on October 11, 2026 (Europe/Rome) at https://solarshift-seven.vercel.app without an authentication header. The production page, sample manifest, sample images and health endpoint were accessible. Corrupt upload returned 422.

| Sample | Actual roof candidates | CPU inference | Full hosted workflow |
| --- | ---: | ---: | ---: |
| Davis | 13 | 10.91 s | 16.91 s |
| Sacramento | 38 | 7.46 s | 13.30 s |

Both workflows ran real model inference, full-day physics and nighttime zero-output assertions. These are measured examples, not general latency guarantees.

The public browser interface also analyzed Davis successfully. At 07:00, selected roof R01 showed 2.82 kW and 87% direct sunlight; at 12:00, 24.59 kW and 100%; at 21:00, 0.00 kW and 0%. Its daily clear-sky estimate was 208.7 kWh. Roof comparison and charts displayed calculated results. A screenshot is saved as `DEMO_ASSETS/live-vercel.jpg`.

The first deployment exposed a missing runtime `public/` directory. The fix lets Vercel serve those files through its CDN and redirects the sample manifest when needed. The production deployment was rebuilt from GitHub and all checks above passed afterward.

## Demo

`DEMO_ASSETS/SolarShift-demo.mp4` is a 160-second, captioned silent walkthrough assembled from actual captured application states. It is not a continuous screen recording. Source aerial images, screenshots, exported analysis, chart, subtitles and narration script are included. ffprobe confirmed the MP4 duration.

## Limits

No ground-truth segmentation accuracy, rooftop engineering accuracy, annual energy accuracy or broad generalization benchmark was measured. Weather, electrical string mismatch and roof slope are outside the current model. Review `README.md` for assumptions and `DEPLOYMENT.md` for hosting state.
