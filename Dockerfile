# 1. Use a lightweight version of Python
FROM python:3.9-slim

# 2. Create a folder inside the server called 'app'
WORKDIR /app

# 3. Install the tools in your requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy all your code (app.py, generator_logic.py, etc.) into the server
COPY . .

# 5. Tell the server to listen on port 8080 (Required by Google Cloud)
ENV PORT=8080

# 6. Run the app
CMD streamlit run app.py --server.port 8080 --server.address 0.0.0.0