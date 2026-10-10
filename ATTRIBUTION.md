# Resources and licenses

SolarShift's original source code is MIT licensed. That license does not replace third-party licenses.

## Building model

- **merve/rf-detr-seg-satellite-buildings**, by Merve Noyan; model card declares **Apache 2.0**. Fine-tuned from Roboflow RF-DETR Seg Medium on the merve/satellite-building-segmentation dataset.
- Model: https://huggingface.co/merve/rf-detr-seg-satellite-buildings
- Pinned revision: `05b80dce9a57701724ad6a0fc052827c8b724257`.
- RF-DETR: https://github.com/roboflow/rf-detr
- Transformers: https://github.com/huggingface/transformers — Apache 2.0.
- Weights are downloaded at setup/startup and are excluded from Git. No model was trained by this project. The publisher's reported metrics are not SolarShift benchmark results.

## Aerial samples

`public/samples/davis.jpg` and `sacramento.jpg` are actual California orthophotos downloaded from the **USGS National Map USGSNAIPImagery ImageServer** on October 11, 2026, Europe/Rome time. Imagery: USDA National Agriculture Imagery Program / USGS. California imagery from this service is public domain.

- Service: https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer
- Public-domain information: https://www.usgs.gov/national-map-supporting-themes
- Usage FAQ: https://www.usgs.gov/faqs/are-there-any-costs-or-restrictions-usage-data-downloaded-national-map
- Exact URLs, centers, projected bounding boxes, dimensions and ground scales: `public/samples/index.json`.
- `scripts/fetch_samples.py` reproduces downloads. Both scenes span approximately 220 × 165 ground meters, are north-up and contain 1200 × 900 display pixels. Export resampling does not improve the imagery's native resolution. The physical ground scale uses the local Web Mercator cosine correction; small-area distortion is negligible for this preliminary example.
- These scenes can contain existing panels. SolarShift estimates total potential capacity under coverage assumptions, not additional capacity after subtracting an existing installation.

No AI-generated aerial photograph or manually supplied building detection is used. Screenshots show actual app output.

## Other dependencies and assets

- pvlib: BSD 3-Clause; https://github.com/pvlib/pvlib-python
- PyTorch / torchvision: BSD-style licenses; https://github.com/pytorch/pytorch
- OpenCV: Apache 2.0; https://github.com/opencv/opencv
- NumPy: BSD 3-Clause; pandas: BSD 3-Clause; Shapely: BSD 3-Clause.
- FastAPI: MIT; Uvicorn: BSD 3-Clause; Pillow: HPND; Pydantic: MIT.
- DM Sans and Space Grotesk: SIL Open Font License, served by Google Fonts with system-font fallbacks.
- SolarShift SVG logo: original code-created asset, MIT.
- OpenAI Codex assisted source creation, research, debugging, documentation and UI verification. No paid image-analysis or multimodal API is used at runtime.
