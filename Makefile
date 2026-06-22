.PHONY: install dev prod test clean

# ==========================================
# Setup
# ==========================================
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt

# ==========================================
# Development — Uvicorn langsung (hot reload)
# ==========================================
dev:
	@echo "Starting Development Server (Uvicorn)..."
	uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level debug

# ==========================================
# Production — Gunicorn + Uvicorn Worker
# ==========================================
prod:
	@echo "Starting Production Server via Configuration File..."
	gunicorn --config gunicorn.conf.py main:app

# ==========================================
# Production — Docker
# ==========================================
dock:
	@echo Menjalankan aplikasi lewat docker
	docker run -p 8000:8000 auth


# ==========================================
# Production custom — override lewat CLI
# ==========================================
prod-custom:
	@echo "Starting Production Server via CLI Override..."
	gunicorn main:app \
	--bind 0.0.0.0:8000\
	--workers 4\
	--worker-class uvicorn.workers.UvicornWorker\
	--timeout 120\
	--log-level info\
	--access-logfile -\
	--error-logfile -

# ==========================================
# Test
# ==========================================
test:
	@echo "Running tests..."
	pytest tests/ -v

# ==========================================
# Bersihkan file cache
# ==========================================
clean:
	@echo "Cleaning up caches and temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -name "*.db" -delete
