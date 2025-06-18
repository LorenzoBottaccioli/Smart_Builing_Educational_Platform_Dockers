# ./BaseSimulation/Dockerfile

FROM jupyter-simulation:latest

USER root
# 1) Crea y da permisos al directorio de notebooks
RUN mkdir -p /home/jovyan/base_notebooks \
    && chmod -R a+rwX /home/jovyan/base_notebooks

WORKDIR /home/jovyan/base_notebooks

# 2) Copia el notebook vacío
COPY BaseSim.ipynb .

# 3) Exponemos el puerto interno (que luego mapearemos a 8891)
EXPOSE 8891

# 4) ENTRYPOINT al estilo de jupyter_simulation, apuntando a BaseSim.ipynb
ENTRYPOINT ["/bin/bash","-lc", "\
  export PATH=/opt/conda/envs/simulation/bin:/usr/bin:/bin:$PATH && \
  python -m notebook \
    --ip=0.0.0.0 \
    --port=8891 \
    --no-browser \
    --allow-root \
    --NotebookApp.token='' \
    --NotebookApp.password='' \
    --NotebookApp.notebook_dir=/home/jovyan/base_notebooks \
    --NotebookApp.default_url=/notebooks/BaseSim.ipynb \
    --NotebookApp.tornado_settings=\"{'headers':{'Content-Security-Policy':'frame-ancestors *'}}\"\
"]
