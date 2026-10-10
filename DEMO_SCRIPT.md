# SolarShift — 2:40 demo

Target length: **160 seconds**, strictly below three minutes. Record the actual application. The prepared captioned MP4 uses captured live UI states and time-series frames; no detection or solar output is painted into screenshots. If using that recording-ready file, add your narration or present it as a captioned walkthrough. It is not a continuous raw screen recording.

Before recording: start SolarShift, wait for Vision engine ready, open Davis, keep the June 21 scenario, and use a desktop viewport. Initial sample heights are estimates. Avoid suggesting that installed panels in the photograph are new additional capacity. When displaying an edited or taller-building scenario, say that an assumption was changed.

| Time | On-screen action | Voiceover |
|---|---|---|
| 00:00–00:15 | Show the unanalysed aerial image and product name. | “This is SolarShift: turn any rooftop into solar intelligence. An aerial photograph shows buildings, but it doesn't tell us how much useful sunlight reaches them. SolarShift connects that image to a first solar-planning scenario.” |
| 00:15–00:30 | Click Analyze location. Show the actual scan/progress and AI outlines. | “We start with real USGS aerial imagery. A pretrained RF-DETR model performs pixel-level building segmentation. OpenCV converts its masks into roof candidates. These boundaries come from inference on this image, and the confidence scores come from the model.” |
| 00:30–00:48 | Select two roofs and show capacity, area and the day curve. | “Each polygon becomes an editable spatial footprint. Scale turns pixels into square meters. Coverage, module size and efficiency determine estimated capacity. The right panel shows a calculated clear-sky day, rather than an invented annual forecast.” |
| 00:48–01:13 | Move from sunrise through midday to evening. Keep the sun and power values visible. | “Now move time. pvlib calculates the sun's azimuth and elevation from location, date and timezone. Shadows change direction and length with that sun position. Rooftop sample cells show which parts receive direct light, and the power curve tracks the same calculation.” |
| 01:13–01:25 | Move just before sunrise, then after sunset. Show zero power. | “Below the horizon, sunlight and modeled production fall to zero. These are physical inputs to the energy calculation, not arbitrary animations.” |
| 01:25–01:45 | Open boundary editing. Drag a vertex. Change a neighboring building height; wait for recomputation. | “A photograph cannot reliably measure height or roof slope. Here I can correct a boundary or change a height assumption. The receiving roof's height matters too: only a taller obstacle casts a shadow onto it. The energy estimate updates after the geometry changes.” |
| 01:45–02:05 | Show the roof comparison. Compare another pair. | “The comparison separates total generation from generation per installed kilowatt. A larger roof can produce more total energy, while another roof has better exposure per unit of capacity. Both comparisons use the same area, irradiance and shadow model.” |
| 02:05–02:25 | Open How it works. Show the shadow and energy method. | “Underneath, the system sweeps extruded polygons along the computed shadow vector, then tests roof sample points. Ineichen clear-sky irradiance is transposed to panel orientation. Direct light is reduced by shading, and ten-minute power samples are integrated into daily kilowatt-hours.” |
| 02:25–02:40 | Close methodology, play the day, finish on the solar map and GitHub link. | “We tested two real aerial scenes, geometry and nighttime behavior. SolarShift is a preliminary planning tool: clouds, terrain and unknown structures still require better data. But the complete pipeline works today: real segmentation, editable geometry, solar physics and interactive energy analysis.” |

## Publishing on YouTube

1. Review the entire `DEMO_ASSETS/SolarShift-demo.mp4` after rendering. It is a captioned recording-ready walkthrough assembled from actual UI captures; add narration if desired. Check final duration with `ffprobe` and keep it below 180 seconds after any edits.
2. Open YouTube Studio in your account → Create → Upload videos.
3. Choose the finished MP4. Title: **SolarShift — Turn any rooftop into solar intelligence | Banana Hacks 2026**.
4. Description: “AI-assisted preliminary rooftop solar planning with RF-DETR building segmentation, editable geometry, pvlib solar position, geometric shadows and clear-sky energy estimates. Source: https://github.com/Planetech0071/SolarShift. Credits and limitations are in the repository.”
5. Set the truthful audience and copyright fields, choose **Public**, and publish. No third-party music is required.
6. Copy the public watch URL into the submission. Open it signed out and confirm it plays.

YouTube publication and the final submission need your account. They are not performed automatically.
