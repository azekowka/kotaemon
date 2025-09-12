python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -e "libs/kotaemon[all]"
pip install -e "libs/ktem"
python app.py

docker run `
-e GRADIO_SERVER_NAME=0.0.0.0 `
-e GRADIO_SERVER_PORT=7860 `
-v ${PWD}/ktem_app_data:/app/ktem_app_data `
-p 7860:7860 `
-it --rm `
ghcr.io/cinnamon/kotaemon:main-lite