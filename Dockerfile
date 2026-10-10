FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 SOLARSHIFT_CPU=1 HF_HOME=/app/.cache/huggingface
WORKDIR /app
RUN useradd -m -u 1000 appuser
COPY requirements.txt .
RUN pip install --no-cache-dir torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cpu && pip install --no-cache-dir -r requirements.txt
COPY --chown=appuser:appuser backend ./backend
COPY --chown=appuser:appuser public ./public
RUN mkdir -p models .cache && chown -R appuser:appuser /app
USER appuser
RUN python -c "from backend.vision import warmup,status; warmup(); assert status['ready'],status"
EXPOSE 7860
CMD ["python","-m","uvicorn","backend.app:app","--host","0.0.0.0","--port","7860"]
