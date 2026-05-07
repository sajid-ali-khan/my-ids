# Network IDS - Project Structure

This document describes the organized project structure. All files have been reorganized into logical sections for better maintainability and clarity.

## Directory Organization

```
fyp/
├── README.md                    # Main project documentation
├── pyproject.toml              # Python package configuration
├── requirements.txt            # Python dependencies
│
├── src/                         # Core application code
│   ├── ids_api/               # REST API for predictions
│   │   ├── app.py
│   │   ├── routes.py
│   │   ├── dns_utils.py
│   │   └── __init__.py
│   ├── ids_cli/               # Command-line interface
│   │   ├── cli.py
│   │   ├── config.py
│   │   ├── daemon.py
│   │   └── __init__.py
│   ├── ids_core/              # Core detection logic
│   │   ├── pipeline.py
│   │   ├── flow_aggregator.py
│   │   ├── model_loader.py
│   │   ├── store/
│   │   │   ├── db.py
│   │   │   └── __init__.py
│   │   └── __init__.py
│   └── web/                   # Web dashboard
│       ├── index.html
│       ├── style.css
│       ├── script.js
│       └── __init__.py
│
├── scripts/                     # Standalone utility scripts
│   ├── main.py                # Main application entry point
│   ├── run_server.py          # Server launcher
│   ├── flow.py                # Flow analysis utilities
│   ├── capture.py             # Packet capture  
│   └── diagnose_aggregation.py # Diagnostic tools
│
├── tests/                       # Unit and integration tests
│   ├── test_api.py
│   ├── test_pipeline.py
│   ├── test_suspicious_classification.py
│   ├── test_dashboard_integration.py
│   └── test_v2_model.py
│
├── notebooks/                   # Jupyter notebooks for analysis
│   ├── random_forest_cicids2017.ipynb
│   └── random_forest_cicids2017_v2.ipynb
│
├── data/                        # Datasets and data files
│   └── cicids2017_cleaned.csv
│
├── docs/                        # Implementation documentation
│   ├── AGGREGATION_ANALYSIS.md
│   ├── AGGREGATION_LAYER.md
│   ├── API_CONFIG_ENDPOINTS.md
│   ├── BRUTE_FORCE_QUICKSTART.md
│   ├── DASHBOARD_IMPLEMENTATION_SUMMARY.md
│   ├── DIAGNOSTIC_FINDINGS.md
│   ├── FEATURE_COMPLETE_SUMMARY.md
│   ├── IMPLEMENTATION_COMPLETE.md
│   ├── IMPLEMENTATION_SUMMARY.md
│   ├── SUSPICIOUS_CLASSIFICATION_FEATURE.md
│   ├── SUSPICIOUS_CLASSIFICATION_QUICK_REFERENCE.md
│   ├── SUSPICIOUS_CLASSIFICATION_SUMMARY.md
│   └── PIPX_INSTALLATION.md
│
├── model/                       # Pre-trained ML models
│   ├── model_columns_v2.joblib
│   └── model_columns.joblib
│
└── myenv/                       # Python virtual environment
    └── [Python packages and binaries]
```

## What Was Cleaned Up

### ✓ Files Removed
- `memory.md` - Local development notes (not needed)
- `example_doc.md` - Example template file (not relevant)
- `__pycache__/` directories - Python bytecode cache (auto-generated on run)
- `.egg-info/` directories - Build artifacts (auto-generated)

### ✓ Files Organized

**Source Code:**
- Moved `ids_api/`, `ids_cli/`, `ids_core/`, `web/` → `src/`
- Updated `pyproject.toml` to reference new locations

**Tests:**
- Moved all `test_*.py` files → `tests/`

**Scripts:**
- Moved `main.py`, `run_server.py`, `flow.py`, `capture.py`, `diagnose_aggregation.py` → `scripts/`

**Documentation:**
- Moved 13 implementation docs → `docs/`
- Kept main `README.md` at project root

**Notebooks:**
- Moved Jupyter notebooks → `notebooks/`

**Data:**
- Moved CSV dataset → `data/`

## Running the Application

After reorganization, you may need to update imports in some files. For example:

```python
# Old import
from ids_api import app

# New import (if necessary)
from src.ids_api import app
```

Update [run_server.py](scripts/run_server.py) and similar scripts to use the new module paths if needed.

## Benefits of This Structure

- **Clear Separation**: Tests, documentation, and source code are in separate locations
- **Easy Maintenance**: Related files are grouped together logically
- **Scalability**: Easy to add new modules, tests, or documentation
- **Professional Layout**: Follows Python project conventions
- **Cleaner Workspace**: Removed development artifacts and unnecessary files

---

Last organized: April 24, 2026
