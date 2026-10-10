# Deployment

SolarShift is one HTTP service: frontend plus FastAPI analysis. No paid keys are needed. Model weights are public and cached locally.

## Vercel

`app.py`, `pyproject.toml` and `vercel.json` configure FastAPI on Vercel. Python 3.12 and CPU-only PyTorch wheels are used. The build script downloads the pinned public model into the function bundle. The project uses Vercel Fluid Compute and its large-function support; no external paid inference API is involved.

On Vercel, image analysis completes inside its request and returns the result directly. It does not rely on process-local background jobs surviving or subsequent polling reaching the same instance. The local server retains progress polling. The browser supports both responses.

Vercel requests have a 4.5 MB payload limit. Hosted uploads are limited to 4 MB to leave room for multipart headers; local uploads remain limited to 20 MB. Cold CPU inference takes longer than the local warm GPU measurements. The function and browser allow up to 300 seconds for analysis.

Deploy from this directory using a separate SolarShift Vercel project:

```sh
vercel deploy --prod --yes
```

The production URL will be recorded here after a successful deployment and live analysis check.

## Local demonstration

Run `start.ps1` on Windows or the commands in README. Open http://127.0.0.1:8000. The current machine's server is running in the background; process and logs are in ignored `runtime/` files.

## Free persistent hosting: Hugging Face Docker Space

The repository includes a Dockerfile, CPU dependencies, pinned model revision and README metadata for port 7860. A Hugging Face account is required; no credential was available in this environment, so a persistent Space was not published.

1. Sign in to https://huggingface.co/new-space.
2. Create a public Space called **SolarShift**, choose **Docker** and free **CPU Basic** hardware. Review the current free-tier settings before creating it.
3. Copy this repository's tracked files into the Space repository and push. Do not copy `.venv`, `runtime`, credentials or model caches. The Docker build downloads the pinned model.
4. Wait for Running. Visit `/api/health` on the Space's app URL; confirm `vision.ready` is true.
5. Analyze both samples and move the timeline. CPU inference is slower than the measured local GPU examples. Free Spaces can sleep when idle; warm it before judging.
6. Put the Space app URL in README and the submission after successful verification.

Container commands:

```sh
docker build -t solarshift .
docker run --rm -p 7860:7860 solarshift
```

The container configuration was prepared; no Docker build or cloud deployment is claimed unless recorded in TEST_RESULTS.md.

## Temporary live sharing

`localhost.run` can forward the running service without an account:

```sh
ssh -R 80:127.0.0.1:8000 nokey@localhost.run
```

It prints an HTTPS URL. This is a temporary tunnel to this machine, not durable hosting. Keep the computer awake, server running and SSH session alive. Free hostnames can rotate, and service throughput is limited; check the latest URL before sharing. The original Cloudflare quick-tunnel attempt failed certificate verification and was stopped without disabling verification.

Service documentation: https://localhost.run/docs/ and https://localhost.run/docs/forever-free/.

During the initial build, localhost.run established SSH forwarding but the public HTTPS endpoint failed external verification with connection resets/TLS errors. That tunnel was stopped. These temporary tunnels are not the Vercel production deployment.

## GitHub

The source repository is intended to be public at https://github.com/Planetech0071/SolarShift. Public GitHub publication is checked independently of cloud hosting. SolarShift uses its own Vercel project and does not replace the existing Shieldio deployment.
