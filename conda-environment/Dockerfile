###############################################
# Dockerfile base unificado para todos       #
# los notebooks (surrogate + simulation)     #
# Incluye librería custom fmi_mlc            #
###############################################

FROM nrel/energyplus:9.6.0

# Miniconda
RUN apt-get update && \
    apt-get install -y --no-install-recommends wget bzip2 ca-certificates curl git && \
    rm -rf /var/lib/apt/lists/*

ENV CONDA_DIR=/opt/conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh && \
    bash /tmp/miniconda.sh -b -p ${CONDA_DIR} && \
    rm /tmp/miniconda.sh && \
    ${CONDA_DIR}/bin/conda clean -afy

ENV PATH=${CONDA_DIR}/bin:$PATH

# Copiar y crear entorno Conda
COPY conda_environment.yml /tmp/conda_environment.yml
RUN conda env create -f /tmp/conda_environment.yml && \
    conda clean -afy

# Symlink para EnergyPlus
RUN ln -sf /EnergyPlus-9.6.0-4b123cf80f-Linux-Ubuntu20.04-x86_64 /usr/local/EnergyPlus-9-6-0
ENV ENERGYPLUS_HOME=/usr/local/EnergyPlus-9-6-0
ENV EPLUS_PATH=/usr/local/EnergyPlus-9-6-0/energyplus
ENV PATH=/usr/local/EnergyPlus-9-6-0:$PATH

# Activar entorno y registrar kernel Jupyter
SHELL ["/opt/conda/bin/conda", "run", "-n", "conda_environment", "/bin/bash", "-lc"]
RUN python -m ipykernel install --user --name conda_environment --display-name "Python (SmartBuilding RL)"

# Copiar librería custom fmi_mlc al site-packages del entorno
COPY fmi_mlc /opt/conda/envs/conda_environment/lib/python3.9/site-packages/fmi_mlc

# Crear carpeta de notebooks
USER root
RUN mkdir -p /home/jovyan/notebooks && chown -R root:root /home/jovyan
WORKDIR /home/jovyan/notebooks

EXPOSE 8888

# Jupyter Notebook como entrypoint
ENTRYPOINT ["/bin/bash", "-lc", \
    "/opt/conda/envs/conda_environment/bin/jupyter notebook \
     --ip=0.0.0.0 \
     --port=8888 \
     --no-browser \
     --allow-root \
     --NotebookApp.token='' \
     --NotebookApp.password='' \
     --NotebookApp.notebook_dir=/home/jovyan/notebooks \
     --NotebookApp.tornado_settings=\"{'headers':{'Content-Security-Policy':'frame-ancestors *'}}\""]
