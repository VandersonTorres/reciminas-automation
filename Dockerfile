FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

# Avoid .pyc files and buffering issues
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh

# Create media folder
RUN mkdir -p /app/server/downloads

# Collect static files
RUN python server/manage.py collectstatic --noinput

# Expose port for the application
EXPOSE 8000

# Startup command
ENTRYPOINT [ "./entrypoint.sh" ]
