
Render is building with your repo's Dockerfile and ignoring render.yaml.
Exit 128 is happening because the container starts and exits immediately with the existing start command.
Fix: replace your Dockerfile with the one in this patch or edit your Dockerfile's CMD to run `python app_fast.py`.
