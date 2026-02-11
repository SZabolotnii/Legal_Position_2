# Dockerfile для Local Position AI Analyzer (опціонально для HF Spaces)
FROM python:3.10-slim

WORKDIR /app

# Встановлюємо системні залежності
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Копіюємо requirements
COPY requirements.txt .

# Встановлюємо Python залежності
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо код проєкту
COPY . .

# Відкриваємо порт для Gradio
EXPOSE 7860

# Запускаємо додаток
CMD ["python", "app.py"]
