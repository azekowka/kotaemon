python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -e "libs/kotaemon[all]"
pip install -e "libs/ktem"
python app.py