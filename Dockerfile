FROM python:3.11-bookworm

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Healthcheck to verify Streamlit is running
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run the dashboard
CMD ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
