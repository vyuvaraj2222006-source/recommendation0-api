#!/usr/bin/env python3
"""
INSTALLATION VERIFICATION TEST
===============================
Run this script to verify your installation is working correctly
"""

import sys
import importlib

print("=" * 60)
print("  RECOMMENDATION SYSTEM - INSTALLATION TEST")
print("=" * 60)
print()

# Required packages
required_packages = {
    'flask': 'Flask',
    'numpy': 'NumPy',
    'pandas': 'Pandas',
    'sklearn': 'scikit-learn',
    'redis': 'Redis',
    'flask_cors': 'Flask-CORS',
    'scipy': 'SciPy',
    'prometheus_flask_exporter': 'Prometheus Flask Exporter'
}

print("Step 1: Checking Python Version...")
print("-" * 60)
python_version = sys.version
print(f"✓ Python version: {python_version}")
if sys.version_info < (3, 8):
    print("✗ ERROR: Python 3.8 or higher required!")
    sys.exit(1)
print()

print("Step 2: Checking Required Packages...")
print("-" * 60)

missing_packages = []
installed_packages = []

for package, display_name in required_packages.items():
    try:
        module = importlib.import_module(package)
        version = getattr(module, '__version__', 'unknown')
        print(f"✓ {display_name:30} - Version {version}")
        installed_packages.append(display_name)
    except ImportError:
        print(f"✗ {display_name:30} - NOT INSTALLED")
        missing_packages.append(package)

print()

if missing_packages:
    print("=" * 60)
    print("  MISSING PACKAGES DETECTED")
    print("=" * 60)
    print()
    print("The following packages need to be installed:")
    for pkg in missing_packages:
        print(f"  - {pkg}")
    print()
    print("To install, run:")
    print(f"  pip install {' '.join(missing_packages)}")
    print()
    print("Or install all requirements:")
    print("  pip install -r requirements.txt")
    print()
    sys.exit(1)
else:
    print("=" * 60)
    print("  ✓ ALL REQUIRED PACKAGES INSTALLED!")
    print("=" * 60)
    print()

print("Step 3: Checking File Structure...")
print("-" * 60)

import os

required_files = [
    'step1_model_preparation.py',
    'step2_api_service.py',
    'requirements.txt',
    'README.md'
]

optional_files = [
    'Dockerfile',
    'docker-compose.yml',
    'step4_cloud_deployment_aws.py',
    'step5_frontend_integration.js',
    'step6_performance_testing.py',
    'step7_monitoring_logging.py',
    'step8_deployment_checklist.py'
]

all_present = True
for filename in required_files:
    if os.path.exists(filename):
        print(f"✓ {filename}")
    else:
        print(f"✗ {filename} - MISSING")
        all_present = False

print()
print("Optional files:")
for filename in optional_files:
    if os.path.exists(filename):
        print(f"✓ {filename}")
    else:
        print(f"  {filename} - not found (optional)")

print()

if not all_present:
    print("⚠ Some required files are missing!")
    print()
else:
    print("✓ All required files present!")
    print()

print("Step 4: Testing Basic Functionality...")
print("-" * 60)

try:
    import numpy as np
    test_array = np.array([1, 2, 3, 4, 5])
    print(f"✓ NumPy test: {test_array.mean()}")
except Exception as e:
    print(f"✗ NumPy test failed: {e}")

try:
    import pandas as pd
    test_df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    print(f"✓ Pandas test: DataFrame shape {test_df.shape}")
except Exception as e:
    print(f"✗ Pandas test failed: {e}")

try:
    from sklearn.neighbors import NearestNeighbors
    print(f"✓ scikit-learn test: Successfully imported NearestNeighbors")
except Exception as e:
    print(f"✗ scikit-learn test failed: {e}")

try:
    from flask import Flask
    test_app = Flask(__name__)
    print(f"✓ Flask test: Successfully created Flask app")
except Exception as e:
    print(f"✗ Flask test failed: {e}")

print()

print("Step 5: Checking Directories...")
print("-" * 60)

directories = ['models', 'logs']
for directory in directories:
    if os.path.exists(directory):
        print(f"✓ {directory}/ directory exists")
    else:
        print(f"  {directory}/ directory not found (will be created automatically)")

print()

print("=" * 60)
print("  INSTALLATION VERIFICATION COMPLETE!")
print("=" * 60)
print()

if missing_packages:
    print("❌ Status: INCOMPLETE - Missing packages")
    print()
    print("Next step: Install missing packages")
    print("  pip install -r requirements.txt")
elif not all_present:
    print("⚠ Status: PARTIAL - Some files missing")
    print()
    print("Next step: Ensure all required files are in current directory")
else:
    print("✅ Status: READY TO GO!")
    print()
    print("Next steps:")
    print("  1. Prepare your model:")
    print("     python step1_model_preparation.py")
    print()
    print("  2. Start the API server:")
    print("     python step2_api_service.py")
    print()
    print("  3. Test the API (in another terminal):")
    print("     curl http://localhost:5000/health")
    print()

print("=" * 60)
