.PHONY: setup start stop db logs

setup:
	@echo "🔧 Setting up environment..."
	python3 -m venv venv
	. venv/bin/activate && pip install -r backend/requirements.txt

start:
	@echo "🚀 Launching FusonEMS Quantum..."
	cd backend && ./start_dev.sh

stop:
	@echo "🛑 Stopping backend..."
	pkill -f uvicorn || true

db:
	@echo "🗄️  Starting Postgres..."
	brew services start postgresql@16

logs:
	@echo "📜 Viewing logs..."
	mkdir -p logs && tail -f logs/backend_start.log
