FROM python:3.11-slim

# Cài đặt Lua
RUN apt-get update && apt-get install -y lua5.3 && rm -rf /var/lib/apt/lists/*

# Sao chép requirements.txt và cài đặt các thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ code và file Lua vào container
COPY . .

# Chạy ứng dụng với Uvicorn
CMD uvicorn main:app --host 0.0.0.0 --port $PORT