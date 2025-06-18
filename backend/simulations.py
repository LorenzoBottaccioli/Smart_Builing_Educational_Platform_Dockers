from flask import Blueprint, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import subprocess
import uuid

# Folder paths
dirpath = os.getcwd()
UPLOAD_FOLDER = os.path.join(dirpath, 'uploads')
SIMULATION_OUTPUTS = os.path.join(dirpath, 'simulation_outputs')

# Containers
default_rl_container = 'RLSimulation'
default_base_container = 'BaseSimulation'

simulations_bp = Blueprint('simulations', __name__)
CORS(simulations_bp)

# Ensure folder exists
def _ensure_folder(path):
    os.makedirs(path, exist_ok=True)

# Common file save + copy helper
def _save_and_copy(file_obj, filename, container_name):
    _ensure_folder(UPLOAD_FOLDER)
    host_path = os.path.join(UPLOAD_FOLDER, filename)
    file_obj.save(host_path)
    subprocess.check_call([
        'docker', 'cp', host_path,
        f"{container_name}:/home/jovyan/uploads/{filename}"
    ])
    return filename

@simulations_bp.route('/upload_rl_script', methods=['POST'])
def upload_rl_script():
    """
    Upload RL script and FMU to RLSimulation container.
    Expects 'script' and optional 'fmu' in files.
    """
    try:
        if 'script' not in request.files:
            return jsonify({'error': 'No script file provided'}), 400
        script = request.files['script']
        script_name = secure_filename(script.filename)
        _save_and_copy(script, script_name, default_rl_container)

        if 'fmu' in request.files:
            fmu = request.files['fmu']
            fmu_name = secure_filename(fmu.filename)
            _save_and_copy(fmu, fmu_name, default_rl_container)
        else:
            fmu_name = request.form.get('fmu', 'model.fmu')

        return jsonify({
            'script': script_name,
            'fmu': fmu_name,
            'message': 'Files uploaded to RLSimulation'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@simulations_bp.route('/upload_base_script', methods=['POST'])
def upload_base_script():
    """
    Upload base simulation script and FMU to BaseSimulation container.
    Expects 'script' and optional 'fmu' in files.
    """
    try:
        if 'script' not in request.files:
            return jsonify({'error': 'No script file provided'}), 400
        script = request.files['script']
        script_name = secure_filename(script.filename)
        _save_and_copy(script, script_name, default_base_container)

        if 'fmu' in request.files:
            fmu = request.files['fmu']
            fmu_name = secure_filename(fmu.filename)
            _save_and_copy(fmu, fmu_name, default_base_container)
        else:
            fmu_name = request.form.get('fmu', 'model.fmu')

        return jsonify({
            'script': script_name,
            'fmu': fmu_name,
            'message': 'Files uploaded to BaseSimulation'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@simulations_bp.route('/execute_rl_simulation', methods=['POST'])
def execute_rl_simulation():
    """
    Execute previously uploaded RL script inside RLSimulation container.
    Expects JSON with 'script' and 'fmu' names (or defaults).
    Returns jobId for tracking.
    """
    try:
        data = request.get_json() or {}
        script_name = secure_filename(data.get('script', ''))
        fmu_name = secure_filename(data.get('fmu', 'model.fmu'))
        job_id = str(uuid.uuid4())
        cmd = [
            'docker', 'exec', '-d', default_rl_container,
            'bash', '-lc',
            f"python /home/jovyan/uploads/{script_name} --fmu /home/jovyan/uploads/{fmu_name} --job-id {job_id}"
        ]
        subprocess.check_call(cmd)
        return jsonify({'jobId': job_id}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@simulations_bp.route('/execute_base_simulation', methods=['POST'])
def execute_base_simulation():
    """
    Execute previously uploaded base simulation script inside BaseSimulation container.
    Expects JSON with 'script' and 'fmu' names (or defaults).
    Returns jobId for tracking.
    """
    try:
        data = request.get_json() or {}
        script_name = secure_filename(data.get('script', ''))
        fmu_name = secure_filename(data.get('fmu', 'model.fmu'))
        job_id = str(uuid.uuid4())
        cmd = [
            'docker', 'exec', '-d', default_base_container,
            'bash', '-lc',
            f"python /home/jovyan/uploads/{script_name} --fmu /home/jovyan/uploads/{fmu_name} --job-id {job_id}"
        ]
        subprocess.check_call(cmd)
        return jsonify({'jobId': job_id}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
