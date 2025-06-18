from flask import Blueprint, request, jsonify, send_file
from flask_cors import CORS
from methods import *
import os
from config import db
import shutil
import zipfile
import glob
from werkzeug.utils import secure_filename
from eppy.modeleditor import IDF
from models import *
from influxdb import InfluxDBClient as InfluxDBClientV1

UPLOAD_FOLDER='uploads'
SIMULATION_OUTPUTS='simulation_outputs'
IDD_PATH = os.environ.get('IDD_PATH', '/app/EnergyPlus-9-6-0/Energy+.idd')
USER_FILES    = 'user_files'

model_converter_bp = Blueprint('model_converter', __name__)
CORS(model_converter_bp)


@model_converter_bp.route('/get_idf', methods=['GET'])
def get_idf():
    try:
        idf_path_list = glob.glob(os.path.join(UPLOAD_FOLDER, '*.idf'))
        if not idf_path_list:
            return jsonify({'error': 'No IDF file found'}), 404

        idf_path = idf_path_list[0]
        return send_file(idf_path, as_attachment=True, download_name='edited_'+os.path.basename(idf_path))

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# backend/export_model_copies.py
from flask import Blueprint, request, current_app, jsonify, send_file
import os
import glob
import shutil
import zipfile


@model_converter_bp.route('/export_model', methods=['POST'])
def export_model():
    try:
        print("start_export", flush=True)
        data = request.get_json()
        start_time   = data['startTime']
        warmup_time  = data['warmupTime']
        final_time   = data['finalTime']
        timestep     = data['timestep']
        observations = data['observations']
        rewards      = data['rewards']
        actions      = data['actions']
        actionMin    = data['actionMin']
        actionMax    = data['actionMax']

        # 1) Buscar IDF y EPW en ./backend/uploads
        UPLOAD_FOLDER = current_app.config.get('UPLOAD_FOLDER', './backend/uploads')
        idf_list = glob.glob(os.path.join(UPLOAD_FOLDER, '*.idf'))
        epw_list = glob.glob(os.path.join(UPLOAD_FOLDER, '*.epw'))
        if not idf_list or not epw_list:
            return jsonify({'success': False, 'error': 'Missing IDF or EPW file'}), 500
        idf_path = idf_list[0]
        epw_path = epw_list[0]
        idf_filename = os.path.basename(idf_path)
        epw_filename = os.path.basename(epw_path)

        # 2) Ajustar timestep en el IDF
        from eppy.modeleditor import IDF
        IDF.setiddname(IDD_PATH)
        idf = IDF(idf_path)
        timestep_objs = idf.idfobjects.get('Timestep', [])
        if timestep_objs:
            timestep_objs[0].Number_of_Timesteps_per_Hour = timestep
        else:
            idf.newidfobject('Timestep', Number_of_Timesteps_per_Hour=timestep)
        idf.save()

        # 3) Crear archivo de config en ./backend/user_files
        config_content = f"""
import numpy as np

parameter = {{}}
parameter['seed']       = 1
parameter['store_data'] = True

dtype = np.float64
parameter['fmu_step_size']   = 3600 / {timestep}
parameter['fmu_path']        = '{os.path.splitext(idf_filename)[0]}.fmu'
parameter['fmu_start_time']  = {start_time} * 60 * 60 * 24
parameter['fmu_warmup_time'] = {warmup_time} * 60 * 60 * 24
parameter['fmu_final_time']  = {final_time} * 60 * 60 * 24

parameter['action_names']      = {actions}
parameter['action_min']        = np.array({actionMin}, dtype=np.float64)
parameter['action_max']        = np.array({actionMax}, dtype=np.float64)
parameter['observation_names'] = {observations}
parameter['reward_names']      = {rewards}

"""
        config_file_path = os.path.join("user_files", "user-config.txt")
        with open(config_file_path, 'w') as config_file:
            config_file.write(config_content)

        # 4) Copiar EPW a user_files como weather.epw
        weather_epw = os.path.join(USER_FILES, 'weather.epw')
        shutil.copyfile(epw_path, weather_epw)

        # 5) Llamar a la función de conversión

        add_external_interface(idf_path)
        run_conversion(epw_path=weather_epw, idf_path=idf_path)

        # 6) Verificar FMU generado
        generated_fmu = os.path.splitext(idf_filename)[0] + '.fmu'
        fmu_path = os.path.join(USER_FILES, generated_fmu)
        if not os.path.isfile(fmu_path):
            return jsonify({'success': False, 'error': 'FMU not found after conversion'}), 500
        
        output_directory = os.getcwd() 
        
        sim_dir=os.path.join(output_directory, 'simulation_notebooks')
        shutil.copy(fmu_path, sim_dir)
        config_dest = os.path.join(sim_dir, 'parameters.py')
        shutil.copy(config_file_path, config_dest)



        # --- BLOQUE PARA COPIAR A CONTROLLED and BASE SIMULATION ---
        ctrl_dir = os.path.join(current_app.root_path, 'controlled_notebooks')
        base_dir = os.path.join(current_app.root_path, 'base_notebooks')
        os.makedirs(ctrl_dir, exist_ok=True)
        os.makedirs(base_dir, exist_ok=True)
        shutil.copy2(fmu_path,           os.path.join(ctrl_dir, generated_fmu))
        shutil.copy2(config_file_path,   os.path.join(ctrl_dir, 'parameters.py'))
        shutil.copy2(fmu_path,           os.path.join(base_dir, generated_fmu))
        shutil.copy2(config_file_path,   os.path.join(base_dir, 'parameters.py'))
        # ------------------------------------------------------------

        # 7) Crear ZIP con IDF, EPW, FMU y config
        bundle_filename = 'conversion_bundle.zip'
        bundle_path     = os.path.join(USER_FILES, bundle_filename)
        with zipfile.ZipFile(bundle_path, 'w') as bundle_zip:
            bundle_zip.write(idf_path, arcname=idf_filename)
            bundle_zip.write(epw_path, arcname=epw_filename)
            bundle_zip.write(fmu_path, arcname=generated_fmu)
            bundle_zip.write(config_file_path, arcname='parameters.py')

        # 8) Enviar el ZIP al cliente
        return send_file(bundle_path, as_attachment=True, download_name=bundle_filename)

    except Exception as e:
        current_app.logger.error(f"Export error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@model_converter_bp.route('/clear_influx', methods=['POST'])
def clear_influx():
    """
    Limpia (drop & recreate) las bases de datos de InfluxDB 1.x
    para controlled_building y base_building.
    """
    influx_host = current_app.config.get('INFLUX_HOST', 'influxdb')
    influx_port = int(current_app.config.get('INFLUX_PORT', 8086))
    influx_user = current_app.config.get('INFLUX_USERNAME', 'admin')
    influx_pass = current_app.config.get('INFLUX_PASSWORD', 'admin123')
    db1 = current_app.config.get('INFLUX_DATABASE', 'controlled_building')
    db2 = 'base_building'

    try:
        client = InfluxDBClientV1(
            host=influx_host,
            port=influx_port,
            username=influx_user,
            password=influx_pass
        )
        for name in (db1, db2):
            client.drop_database(name)
            client.create_database(name)
        client.close()
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

    return jsonify({'success': True, 'message': 'InfluxDB databases cleared.'}), 200

def _replace_weather_in_fmu(fmu_path: str, new_epw_path: str):
    """
    Desempaqueta el FMU (que es un ZIP), reemplaza el archivo weather.epw
    dentro de resources/ por el new_epw_path, y vuelve a empaquetar.
    """
    tmp_dir = fmu_path + "_tmp"
    # 1) extraer todo
    with zipfile.ZipFile(fmu_path, 'r') as zin:
        zin.extractall(tmp_dir)

    # 2) copia el nuevo EPW dentro de resources/
    res_dir = os.path.join(tmp_dir, 'resources')
    os.makedirs(res_dir, exist_ok=True)
    shutil.copy(new_epw_path, os.path.join(res_dir, 'weather.epw'))

    # 3) reempqtar FMU
    with zipfile.ZipFile(fmu_path, 'w', zipfile.ZIP_DEFLATED) as zout:
        for root, _, files in os.walk(tmp_dir):
            for fname in files:
                full = os.path.join(root, fname)
                rel = os.path.relpath(full, tmp_dir)
                zout.write(full, rel)

    # 4) limpiar temporal
    shutil.rmtree(tmp_dir)

@model_converter_bp.route('/update_epw', methods=['POST'])
def update_epw():
    """
    Recibe un nuevo EPW (form-data key="epw") y lo reemplaza en:
      - ./backend/user_files/*.fmu
      - ./ControlledSimulation (controlled_notebooks)
      - ./BaseSimulation  (base_notebooks)
    """
    # recibe el EPW
    if 'epw' not in request.files:
        return jsonify({'success': False, 'error': 'No EPW file provided'}), 400
    epw = request.files['epw']
    if not epw.filename.lower().endswith('.epw'):
        return jsonify({'success': False, 'error': 'El archivo debe tener extensión .epw'}), 400

    # lo guardamos como weather.epw en user_files
    user_files = current_app.config.get('USER_FILES', './backend/user_files')
    os.makedirs(user_files, exist_ok=True)
    epw_dest = os.path.join(user_files, 'weather.epw')
    epw.save(epw_dest)

    # rutas donde buscar los FMU
    base = current_app.root_path
    dirs = [
        "simulation_notebooks",
        user_files,
        os.path.join(base, 'controlled_notebooks'),
        os.path.join(base, 'base_notebooks')
    ]

    fmus = []
    for d in dirs:
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.lower().endswith('.fmu'):
                    fmus.append(os.path.join(d, f))

    errors = []
    for fmu in fmus:
        try:
            _replace_weather_in_fmu(fmu, epw_dest)
        except Exception as e:
            errors.append(f"{os.path.basename(fmu)}: {e}")

    if errors:
        return jsonify({
            'success': False,
            'updated': len(fmus) - len(errors),
            'errors': errors
        }), 500

    return jsonify({'success': True, 'updated': len(fmus)}), 200

@model_converter_bp.route('/fmu_count', methods=['GET'])
def fmu_count():
    """
    Devuelve el número de archivos .fmu presentes en:
      - backend/user_files
      - controlled_notebooks
      - base_notebooks
    """
    try:
        base = current_app.root_path

        # directorio donde guardas user_files
        user_files_dir = current_app.config.get('USER_FILES', os.path.join(base, 'user_files'))
        # los directorios montados para los contenedores
        ctrl_dir = os.path.join(base, 'controlled_notebooks')
        base_dir = os.path.join(base, 'base_notebooks')

        count = 0
        for d in (user_files_dir, ctrl_dir, base_dir):
            if os.path.isdir(d):
                for f in os.listdir(d):
                    if f.lower().endswith('.fmu'):
                        count += 1

        return jsonify({'count': count}), 200

    except Exception as e:
        current_app.logger.error(f"Error counting FMUs: {e}")
        return jsonify({'error': str(e)}), 500