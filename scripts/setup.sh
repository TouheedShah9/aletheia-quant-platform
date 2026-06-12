#!/bin/bash
echo "ALETHEIA SETUP"
pip install -r requirements.txt
python database/schema.py
python tests/test_suite.py
echo "Done. Run: python -m streamlit run dashboard/app.py"