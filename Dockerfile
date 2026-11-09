FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bridge.py .
RUN useradd --system --no-create-home bridge
USER bridge
CMD ["python", "-u", "bridge.py"]
HEALTHCHECK --interval=60s --timeout=5s --start-period=120s --retries=3 \
  CMD python -c "import os,sys,time; m=os.path.getmtime('/tmp/healthy'); sys.exit(0 if time.time()-m < 3*int(os.environ.get('POLL_INTERVAL','60'))+30 else 1)"
