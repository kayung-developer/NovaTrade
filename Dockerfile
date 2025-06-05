FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# IMPORTANT: For production, manage service account key securely (e.g., Secret Manager)
# For now, if you include it in the image (NOT RECOMMENDED FOR PROD):
# COPY path/to/your-service-account-key.json /app/service-account-key.json
# ENV GOOGLE_APPLICATION_CREDENTIALS="/app/service-account-key.json"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]