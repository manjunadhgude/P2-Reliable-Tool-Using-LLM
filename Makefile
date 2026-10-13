.PHONY: install seed run test lint dataset validate benchmark
install:
	python -m pip install -e ./backend[dev]
seed:
	cd backend && alembic upgrade head && python -c "from app.core.db import SessionLocal; from app.seed import seed_database; db=SessionLocal(); seed_database(db); db.close()"
run:
	cd backend && uvicorn app.main:app --reload
test:
	cd backend && pytest
lint:
	cd backend && ruff check app tests
dataset:
	python experiments/data_generation/generate_dataset.py
validate:
	python experiments/evaluation/validate_dataset.py
benchmark:
	python experiments/evaluation/run_benchmark.py
