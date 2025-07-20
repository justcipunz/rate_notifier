# 1. Берем официальный образ Python
FROM python:3.10-slim

# 2. Устанавливаем рабочую директорию на уровень ВЫШЕ кода приложения
WORKDIR /code

# 3. Копируем файл с зависимостями и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Копируем папку app целиком внутрь /code
COPY ./app ./app

# 5. Запускаем uvicorn, указывая ему путь до приложения в виде пакета: app.main:app
# Python теперь будет искать пакет 'app', в нем модуль 'main', а в нем объект 'app'
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
