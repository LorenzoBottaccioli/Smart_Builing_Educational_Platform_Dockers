#!/bin/bash --login
set -euo pipefail

# 1) Cargar Conda y activar el entorno 'backend_env'
set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate backend_env
set -u

# 2) Iniciar Gunicorn apuntando a main:app en puerto 5000
exec gunicorn --workers 4 --bind 0.0.0.0:5000 main:app
