from flask import Blueprint, request, session, jsonify
from flask_cors import CORS
from methods import *
import os
from config import db
import shutil
import glob
from werkzeug.utils import secure_filename
from eppy.modeleditor import IDF
from models import *
import re

UPLOAD_FOLDER='Uploads'
SIMULATION_OUTPUTS='simulation_outputs'
IDD_PATH='EnergyPlusV9-6-0\Energy+.idd'

surrogate_modeling_bp = Blueprint('surrogate_modeling', __name__)
CORS(surrogate_modeling_bp)

@surrogate_modeling_bp.route('/get_surrogate_objects', methods=['GET'])
def get_surrogate_objects():
    """
    Endpoint para obtener todos los objetos de surrogate modeling en formato JSON.
    """
    materials    = idf_Material.query.all()
    constructions = idf_Construction.query.all()
    fenestrations = idf_FenestrationSurfaceDetailed.query.all()
    ventilations = idf_ZoneVentilationDesignFlowRate.query.all()
    lights       = idf_Lights.query.all()
    shadings     = idf_WindowShadingControl.query.all()

    response = {
        'materials': [m.to_json() for m in materials],
        'constructions': [c.to_json() for c in constructions],
        'fenestration_surfaces': [f.to_json() for f in fenestrations],
        'zone_ventilations': [v.to_json() for v in ventilations],
        'lights': [l.to_json() for l in lights],
        'window_shading_controls': [s.to_json() for s in shadings]
    }
    return jsonify(response), 200

# Para registrar este blueprint, en tu app principal:
# from surrogate_modeling import surrogate_bp
# app.register_blueprint(surrogate_bp, url_prefix='/api')