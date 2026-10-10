# 🚀 Deploying Reality Sculptor to Render.com

This guide provides end-to-end instructions for deploying **Reality Sculptor** to [Render.com](https://render.com).

Reality Sculptor includes a self-contained FastAPI backend, Three.js 3D WebGL Digital Twin frontend, and 10 production ML intelligence models.

---

## 📋 Prerequisites
1. A [GitHub](https://github.com) account.
2. A free [Render.com](https://render.com) account.
3. Git installed on your computer.

---

## ⚡ Option 1: 1-Click Blueprint Deploy (Recommended)

1. **Push your code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Reality Sculptor: Production Build Ready for Render"
   git branch -M main
   git remote add origin https://github.com/<your-username>/reality-sculptor.git
   git push -u origin main
   ```

2. **Open Render**:
   - Go to [dashboard.render.com](https://dashboard.render.com).
   - Click **New +** in the top right and select **Blueprint**.
   - Connect your GitHub repository (`reality-sculptor`).
   - Render will automatically read [`render.yaml`](file:///C:/Users/Aryan%20kumar/Downloads/reality-sculptor/render.yaml) and configure:
     - **Service Name**: `reality-sculptor`
     - **Runtime**: Python 3.11
     - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
     - **Start Command**: `python run.py`
     - **Health Check Path**: `/health`
   - Click **Apply**. Render will build and deploy your app in 2–3 minutes.

---

## 🐳 Option 2: Docker Web Service Deploy (Zero Dependency Issues)

Render also supports building directly from the included [`Dockerfile`](file:///C:/Users/Aryan%20kumar/Downloads/reality-sculptor/Dockerfile). This option packages all Linux C-libraries (`libgomp1`, `libglib2.0-0`) in a container.

1. In Render Dashboard, click **New +** &rarr; **Web Service**.
2. Select your GitHub repository.
3. Choose **Docker** as the environment.
4. Render will automatically detect the root `Dockerfile`.
5. Under **Environment Variables**, ensure:
   - `DEMO_MODE`: `true`
6. Click **Create Web Service**.

---

## 🛠 Option 3: Manual Python Web Service

If setting up manually without Blueprint:
1. Click **New +** &rarr; **Web Service**.
2. Select your repository.
3. Configure settings:
   - **Name**: `reality-sculptor`
   - **Language**: `Python 3`
   - **Region**: `Oregon (US West)` (or your preferred region)
   - **Branch**: `main`
   - **Root Directory**: *(leave blank for root)*
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `python run.py`
4. Expand **Advanced**:
   - **Health Check Path**: `/health`
   - **Auto-Deploy**: `Yes`
   - **Environment Variables**:
     - `PYTHON_VERSION`: `3.11.9`
     - `DEMO_MODE`: `true`
     - `LOG_LEVEL`: `INFO`
5. Click **Create Web Service**.

---

## ✅ Verifying Your Live Deployment

Once Render finishes the build:
1. **Interactive 3D Digital Twin**:
   ```
   https://<your-app-name>.onrender.com/
   ```
   Open in your browser to interact with the 3D city, trigger simulations (Flood, Heat, Wildfire, Traffic), click on buildings/pipes, and click **Implement in 3D** to watch solutions physically fix problems in real time.

2. **System Health & Node Status**:
   ```
   https://<your-app-name>.onrender.com/health
   ```
   Returns HTTP 200 with loaded node count (17,057 nodes) and status of all 8 core intelligence engines.

3. **Interactive OpenAPI / Swagger Documentation**:
   ```
   https://<your-app-name>.onrender.com/docs
   ```
   Test all 25+ verified REST endpoints.

4. **Real-Time WebSocket Stream**:
   ```
   wss://<your-app-name>.onrender.com/ws/state
   ```
