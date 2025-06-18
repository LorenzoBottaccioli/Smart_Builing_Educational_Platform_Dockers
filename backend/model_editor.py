from flask import Blueprint, request, session, jsonify, current_app
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
import nbformat
from influxdb import InfluxDBClient as InfluxDBClientV1
from datetime import datetime
from traceback import format_exc
from nbformat import read, write


UPLOAD_FOLDER='uploads'
SIMULATION_OUTPUTS='simulation_outputs'
IDD_PATH = os.environ.get('IDD_PATH', '/app/EnergyPlus-9-6-0/Energy+.idd')

NOTEBOOK_DIR = os.path.join(
    os.getcwd(),
    "surrogate_notebooks"
)
NOTEBOOK_NAME = "SurrogateNotebook.ipynb"

def restore_notebook():
    nb_path = os.path.join(NOTEBOOK_DIR, NOTEBOOK_NAME)
    if not os.path.exists(nb_path):
        return
    nb = nbformat.read(nb_path, as_version=4)
    # Remove any injected “Rutas de archivos subidos” cell
    nb.cells = [
        cell for cell in nb.cells
        if not cell.source.startswith("# 🔧 Rutas de archivos subidos")
    ]
    nbformat.write(nb, nb_path)

model_editor_bp = Blueprint('model_editor', __name__)
CORS(model_editor_bp)

@model_editor_bp.route('/get_objects', methods=['GET'])
def get_objects():
    idf_path = glob.glob(os.path.join(UPLOAD_FOLDER, '*.idf'))    
    edd_actuators = edd_Actuator.query.all()
    rdd_variables = rdd_Variable.query.all()

    current_idf_runperiod = current_runperiod.query.all()
    
    current_output_variables = current_output_variable.query.all()
    current_ems_actuators = current_ems_actuator.query.all()
    current_ems_sensors = current_ems_sensor.query.all()
    current_fmu_actuators = current_fmu_actuator.query.all()
    current_fmu_from_variables = current_fmu_from_variable.query.all()
    current_fmu_to_variables = current_fmu_to_variable.query.all()
    current_fmu_schedules = current_fmu_schedule.query.all()
    current_ems_programs = CurrentEMSProgram.query.all()
    current_ems_program_calling_managers = CurrentEMSProgramCallingManager.query.all()

    existing_schedule_type_limits = existing_shedule_type_limit.query.all()
    existing_schedule_names = existing_schedule_name.query.all()

    edd_actuators_json = [actuator.to_json() for actuator in edd_actuators]
    rdd_variables_json = [variable.to_json() for variable in rdd_variables]

    current_idf_runperiod_json = [runperiod.to_json() for runperiod in current_idf_runperiod]

    current_output_variables_json = [variable.to_json() for variable in current_output_variables]
    current_ems_actuators_json = [actuator.to_json() for actuator in current_ems_actuators]
    current_ems_sensors_json = [sensor.to_json() for sensor in current_ems_sensors]
    current_fmu_actuators_json = [actuator.to_json() for actuator in current_fmu_actuators]
    current_fmu_from_variables_json = [variable.to_json() for variable in current_fmu_from_variables]
    current_fmu_to_variables_json = [variable.to_json() for variable in current_fmu_to_variables]
    current_fmu_schedules_json = [schedule.to_json() for schedule in current_fmu_schedules]
    current_ems_programs_json = [program.to_json() for program in current_ems_programs]
    current_ems_program_calling_managers_json = [manager.to_json() for manager in current_ems_program_calling_managers]

    existing_schedule_type_limits_json = [limit.to_json() for limit in existing_schedule_type_limits]
    existing_schedule_names_json = [name.to_json() for name in existing_schedule_names]
    if idf_path:
        idf_zone_names = get_zone_names(idf_path[0])

        return jsonify({
            'edd_actuators': edd_actuators_json,
            'rdd_variables': rdd_variables_json,
            'current_idf_runperiod': current_idf_runperiod_json,
            'current_output_variables': current_output_variables_json,
            'current_ems_actuators': current_ems_actuators_json,
            'current_ems_sensors': current_ems_sensors_json,
            'current_ems_programs': current_ems_programs_json,
            'current_ems_program_calling_managers': current_ems_program_calling_managers_json,
            'current_fmu_actuators': current_fmu_actuators_json,
            'current_fmu_from_variables': current_fmu_from_variables_json,
            'current_fmu_to_variables': current_fmu_to_variables_json,
            'current_fmu_schedules': current_fmu_schedules_json,
            'existing_schedule_type_limits': existing_schedule_type_limits_json,
            'existing_schedule_names': existing_schedule_names_json,
            'zone_names': idf_zone_names
        }), 200
    
    else: 
        return jsonify({
            'edd_actuators': edd_actuators_json,
            'rdd_variables': rdd_variables_json,
            'current_idf_runperiod': current_idf_runperiod_json,
            'current_output_variables': current_output_variables_json,
            'current_ems_actuators': current_ems_actuators_json,
            'current_ems_sensors': current_ems_sensors_json,
            'current_ems_programs': current_ems_programs_json,
            'current_ems_program_calling_managers': current_ems_program_calling_managers_json,
            'current_fmu_actuators': current_fmu_actuators_json,
            'current_fmu_from_variables': current_fmu_from_variables_json,
            'current_fmu_to_variables': current_fmu_to_variables_json,
            'current_fmu_schedules': current_fmu_schedules_json,
            'existing_schedule_type_limits': existing_schedule_type_limits_json,
            'existing_schedule_names': existing_schedule_names_json
        }), 200

@model_editor_bp.route('/upload_files', methods=['POST'])
def upload_files():
    try:
        idf_file = request.files.get('idf_file')
        epw_file = request.files.get('epw_file')

        if not idf_file:
            return jsonify({'error': 'No IDF file provided.'}), 400
        if not epw_file:
            return jsonify({'error': 'No EPW file provided.'}), 400
        
        if not idf_allowed_file(idf_file.filename):
            return jsonify({'error': 'Invalid IDF file type.'}), 400
        if not epw_allowed_file(epw_file.filename):
            return jsonify({'error': 'Invalid EPW file type.'}), 400
        
        original_idf_filename = secure_filename(idf_file.filename)
        epw_filename = secure_filename(epw_file.filename)

        original_idf_filepath = os.path.join(UPLOAD_FOLDER, original_idf_filename)
        epw_filepath = os.path.join(UPLOAD_FOLDER, epw_filename)

        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)

        idf_file.save(original_idf_filepath)
        epw_file.save(epw_filepath)

        copy_idf_filepath = os.path.join(SIMULATION_OUTPUTS, f"ems_{original_idf_filename}")
        shutil.copyfile(original_idf_filepath, copy_idf_filepath)
        
        add_verbose(original_idf_filepath)

        modify_idf_for_one_day_simulation(copy_idf_filepath)
        add_verbose(copy_idf_filepath)

        delete_external_interface(copy_idf_filepath)

        session["progress"] = 10
        session.modified = True

        simulation_success = run_energyplus_simulation(copy_idf_filepath, epw_filepath)

        session["progress"] = 25
        session.modified = True

        if not simulation_success:
            return jsonify({'error': 'Simulation failed. Please check the simulation inputs.'}), 500
        
        else:
            edd_files = glob.glob(os.path.join(SIMULATION_OUTPUTS, '*.edd'))
            rdd_files = glob.glob(os.path.join(SIMULATION_OUTPUTS, '*.rdd'))

            if edd_files:
                edd_Actuators = parse_edd_file(edd_files[0])
                for actuator in edd_Actuators:
                    new_edd_actuator = edd_Actuator(
                        Component_Unique_Name=actuator['Component_Unique_Name'],
                        Component_Type=actuator['Component_Type'],
                        Control_Type=actuator['Control_Type']
                    )
                    db.session.add(new_edd_actuator)
                    db.session.commit()

                session["progress"] = 50
                session.modified = True

            else:
                return jsonify({'error': 'No EDD file found after simulation.'}), 404
            
            if rdd_files:
                rdd_Variables = parse_rdd_file(rdd_files[0])
                for variable in rdd_Variables:
                    new_rdd_variable = rdd_Variable(
                        Var_Type=variable['Var_Type'],
                        Variable_Name=variable['Variable_Name']
                    )
                    db.session.add(new_rdd_variable)
                    db.session.commit()
                session["progress"] = 75
                session.modified = True
            else:
                return jsonify({'error': 'No RDD file found after simulation.'}), 404
            
            idf_path = glob.glob(os.path.join(UPLOAD_FOLDER, '*.idf'))
            IDF.setiddname(IDD_PATH)
            idf = IDF(idf_path[0])

            zones=get_zone_names(idf_path[0])

            idf_runperiods = idf.idfobjects['Runperiod']
            idf_runperiod = idf_runperiods[0]

            new_current_runperiod = current_runperiod(
                Begin_Month=idf_runperiod.Begin_Month,
                Begin_Day_of_Month=idf_runperiod.Begin_Day_of_Month
            )
            db.session.add(new_current_runperiod)
            db.session.commit()
            
            idf_ems_sensors = idf.idfobjects['EnergyManagementSystem:Sensor']

            if idf_ems_sensors:
                for sensor in idf_ems_sensors:
                    new_current_ems_sensor = current_ems_sensor(
                        Name=sensor.Name,
                        OutputVariable_or_OutputMeter_Index_Key_Name=sensor.OutputVariable_or_OutputMeter_Index_Key_Name,
                        OutputVariable_or_OutputMeter_Name=sensor.OutputVariable_or_OutputMeter_Name
                    )
                    db.session.add(new_current_ems_sensor)
                    db.session.commit()
            
            idf_ems_actuators = idf.idfobjects['EnergyManagementSystem:Actuator']

            if idf_ems_actuators:
                for actuator in idf_ems_actuators:
                    new_current_ems_actuator = current_ems_actuator(
                        Name=actuator.Name,
                        Actuated_Component_Unique_Name=actuator.Actuated_Component_Unique_Name,
                        Actuated_Component_Type=actuator.Actuated_Component_Type,
                        Actuated_Component_Control_Type=actuator.Actuated_Component_Control_Type
                    )
                    db.session.add(new_current_ems_actuator)
                    db.session.commit()

            idf_ems_programs = get_ems_programs(original_idf_filepath)

            if idf_ems_programs:
                for program in idf_ems_programs:
                    new_ems_program = CurrentEMSProgram(name=program['Name'])

                    # Add each program line to the program
                    for line_text in program['ProgramLines']:
                        new_ems_program.program_lines.append(ProgramLine(line_text=line_text))

                    db.session.add(new_ems_program)
                    db.session.commit()

            idf_ems_program_calling_managers = get_ems_program_calling_managers(original_idf_filepath)

            if idf_ems_program_calling_managers:
                for manager in idf_ems_program_calling_managers:
                    new_manager = CurrentEMSProgramCallingManager(
                        name=manager['Name'],
                        energy_plus_model_calling_point=manager['EnergyPlus Model Calling Point']
                    )

                    # Add each program name to the calling manager
                    for program_name in manager['Program Names']:
                        new_manager.program_names.append(ProgramName(line_text=program_name))

                    db.session.add(new_manager)
                    db.session.commit()

            idf_fmu_actuators = idf.idfobjects['ExternalInterface:FunctionalMockupUnitExport:To:Actuator']

            if idf_fmu_actuators:
                for actuator in idf_fmu_actuators:
                    new_current_fmu_actuator = current_fmu_actuator(
                        Name=actuator.Name,
                        Actuated_Component_Unique_Name=actuator.Actuated_Component_Unique_Name,
                        Actuated_Component_Type=actuator.Actuated_Component_Type,
                        Actuated_Component_Control_Type=actuator.Actuated_Component_Control_Type,
                        FMU_Variable_Name=actuator.FMU_Variable_Name,
                        Initial_Value=actuator.Initial_Value
                    )
                    db.session.add(new_current_fmu_actuator)
                    db.session.commit()

            idf_fmu_from_variables = idf.idfobjects['ExternalInterface:FunctionalMockupUnitExport:From:Variable']

            if idf_fmu_from_variables:
                for variable in idf_fmu_from_variables:
                    new_current_fmu_from_variable = current_fmu_from_variable(
                        OutputVariable_Index_Key_Name=variable.OutputVariable_Index_Key_Name,
                        OutputVariable_Name=variable.OutputVariable_Name,
                        FMU_Variable_Name=variable.FMU_Variable_Name
                    )
                    db.session.add(new_current_fmu_from_variable)
                    db.session.commit()

            idf_fmu_to_variables = idf.idfobjects['ExternalInterface:FunctionalMockupUnitExport:To:Variable']
            if idf_fmu_to_variables:
                for variable in idf_fmu_to_variables:
                    new_current_fmu_to_variable = current_fmu_to_variable(
                        Name=variable.Name,
                        FMU_Variable_Name=variable.FMU_Variable_Name,
                        Initial_Value=variable.Initial_Value
                    )
                    db.session.add(new_current_fmu_to_variable)
                    db.session.commit()

            idf_fmu_schedules = idf.idfobjects['ExternalInterface:FunctionalMockupUnitExport:To:Schedule']

            if idf_fmu_schedules:
                for schedule in idf_fmu_schedules:
                    new_current_fmu_schedule = current_fmu_schedule(
                        Schedule_Name=schedule.Schedule_Name,
                        Schedule_Type_Limits_Names=schedule.Schedule_Type_Limits_Names,
                        FMU_Variable_Name=schedule.FMU_Variable_Name,
                        Initial_Value=schedule.Initial_Value
                    )
                    db.session.add(new_current_fmu_schedule)
                    db.session.commit()

            idf_schedule_type_limits = get_schedule_limits(original_idf_filepath)

            if idf_schedule_type_limits:
                for limit in idf_schedule_type_limits:
                    new_existing_schedule_type_limit = existing_shedule_type_limit(
                        Name=limit['Name'],
                        Lower_Limit_Value=limit['Lower_Limit_Value'],
                        Upper_Limit_Value=limit['Upper_Limit_Value']
                    )
                    db.session.add(new_existing_schedule_type_limit)
                    db.session.commit()

            idf_schedule_names = get_schedule_names(original_idf_filepath)

            if idf_schedule_names:
                for name in idf_schedule_names:
                    new_existing_schedule_name = existing_schedule_name(
                        Schedule_Name=name
                    )
                    db.session.add(new_existing_schedule_name)
                    db.session.commit()

            idf_output_variables = idf.idfobjects['Output:Variable']

            if idf_output_variables:
                for variable in idf_output_variables:
                    new_current_output_variable = current_output_variable(
                        Key_Value=variable.Key_Value,
                        Variable_Name=variable.Variable_Name,
                        Reporting_Frequency=variable.Reporting_Frequency,
                        Schedule_Name=variable.Schedule_Name
                    )
                    db.session.add(new_current_output_variable)
                    db.session.commit()
                
            session["progress"] = 100
            session.modified = True

            materials = parse_materials(idf)
            for m in materials:
                db.session.add(m)

            constructions = parse_constructions(idf)
            for c in constructions:
                db.session.add(c)

            fenestrations = parse_fenestration_surfaces(idf)
            for f in fenestrations:
                db.session.add(f)

            ventilations = parse_zone_ventilation(idf)
            for v in ventilations:
                db.session.add(v)

            lights = parse_lights(idf)
            for l in lights:
                db.session.add(l)

            shadings = parse_window_shading(idf)
            for s in shadings:
                db.session.add(s)

            db.session.commit()
            session['progress'] = 100

            subprocess.run(["python", "inject_data.py"], check=True)

            return jsonify({'message': 'Files Processed and Simulation Completed Successfully.'}), 200
    except Exception as e:
        print(f"ERROR en /upload_files: {e}", flush=1)
        print(format_exc(), flush=1)
        return {"error": str(e)}, 500

@model_editor_bp.route('/progress', methods=['GET'])
def get_progress():
    progress_1 = session.get("progress", 75)  # Usar get para manejar sesiones no inicializadas
    return jsonify({'progress': progress_1}), 200

@model_editor_bp.route('/add_output_variable', methods=['POST'])
def add_output_variable():
    idf_path = glob.glob(os.path.join(UPLOAD_FOLDER, '*.idf'))
    IDF.setiddname(IDD_PATH)
    idf = IDF(idf_path[0])
    try:
        data = request.get_json()
        new_output_variable_info=current_output_variable(
            Key_Value=data['keyValue'],
            Variable_Name=data['oVariableName'],
            Reporting_Frequency=data['reportingFrequency'],
            Schedule_Name=data['scheduleName']
        )
        db.session.add(new_output_variable_info)
        db.session.commit()
        # Add the Output:Variable object
        new_output_variable = idf.newidfobject('Output:Variable')
        new_output_variable.Key_Value = data['keyValue']
        new_output_variable.Variable_Name = data['oVariableName']
        new_output_variable.Reporting_Frequency = data['reportingFrequency']

        if data['scheduleName'] != '':
            new_output_variable.Schedule_Name=data['scheduleName']

        # Add additional objects based on addType
        if data.get('addType') == 'output_variable_with_ems_sensor' or data.get('addType') == 'output_variable_with_both':
            new_ems_sensor_info= current_ems_sensor(
                Name=data['name'],
                OutputVariable_or_OutputMeter_Index_Key_Name=data['keyValue'],
                OutputVariable_or_OutputMeter_Name=data['oVariableName']
            )
            db.session.add(new_ems_sensor_info)
            db.session.commit()

            new_ems_sensor = idf.newidfobject('EnergyManagementSystem:Sensor')
            new_ems_sensor.Name = data['name']
            new_ems_sensor.OutputVariable_or_OutputMeter_Index_Key_Name = data['keyValue']
            new_ems_sensor.OutputVariable_or_OutputMeter_Name = data['oVariableName']

        if data.get('addType') == 'output_variable_with_external_from_variable' or data.get('addType') == 'output_variable_with_both':
            new_fmu_from_variable_info= current_fmu_from_variable(
                OutputVariable_Index_Key_Name=data['keyValue'],
                OutputVariable_Name=data['oVariableName'],
                FMU_Variable_Name=data['fmuVariableName']
            )
            db.session.add(new_fmu_from_variable_info)
            db.session.commit()

            new_fmu_from_variable = idf.newidfobject('ExternalInterface:FunctionalMockupUnitExport:From:Variable')
            new_fmu_from_variable.OutputVariable_Index_Key_Name = data['keyValue']
            new_fmu_from_variable.OutputVariable_Name = data['oVariableName']
            new_fmu_from_variable.FMU_Variable_Name = data['fmuVariableName']

        idf.save()

        return jsonify({'message': 'Variable added successfully'}), 200

    except Exception as e:
        return jsonify({'error': 'Failed to Add Object.', 'details': str(e)}), 500

@model_editor_bp.route('/add_ems_sensor', methods=['POST'])
def add_ems_sensor():
    idf_path=glob.glob(os.path.join(UPLOAD_FOLDER, '*.idf'))
    IDF.setiddname(IDD_PATH)
    idf=IDF(idf_path[0])
    try:
        data = request.get_json()
        new_ems_sensor_info= current_ems_sensor(
            Name=data['name'],
            OutputVariable_or_OutputMeter_Index_Key_Name=data['outputVariableOrOutputMeterIndexKeyName'],
            OutputVariable_or_OutputMeter_Name=data['outputVariableOrOutputMeterName']
        )
        db.session.add(new_ems_sensor_info)
        db.session.commit()

        new_output_variable_info=current_output_variable(
            Key_Value=data['outputVariableOrOutputMeterIndexKeyName'],
            Variable_Name=data['outputVariableOrOutputMeterName'],
            Reporting_Frequency='Timestep',
            Schedule_Name=''
        )
        db.session.add(new_output_variable_info)
        db.session.commit()

        new_ems_sensor=idf.newidfobject('EnergyManagementSystem:Sensor')
        new_ems_sensor.Name=data['name']
        new_ems_sensor.OutputVariable_or_OutputMeter_Index_Key_Name=data['outputVariableOrOutputMeterIndexKeyName']
        new_ems_sensor.OutputVariable_or_OutputMeter_Name=data['outputVariableOrOutputMeterName']

        new_output_variable=idf.newidfobject('Output:Variable')
        new_output_variable.Key_Value=data['outputVariableOrOutputMeterIndexKeyName']
        new_output_variable.Variable_Name=data['outputVariableOrOutputMeterName']
        new_output_variable.Reporting_Frequency='Timestep'

        idf.save()

        return jsonify({'message': 'Sensor Added cuccesfully'}), 200
    
    except Exception as e:
        return jsonify({'error': 'Failed to Add Object.', 'details': str(e)}), 500

@model_editor_bp.route('/add_ems_actuator', methods=['POST'])
def add_ems_actuator():
    idf_path=glob.glob(os.path.join(UPLOAD_FOLDER, '*.idf'))
    IDF.setiddname(IDD_PATH)
    idf=IDF(idf_path[0])
    try:
        data = request.get_json()
        new_ems_actuator_info= current_ems_actuator(
            Name=data['name'],
            Actuated_Component_Unique_Name=data['actuatedComponentUniqueName'],
            Actuated_Component_Type=data['actuatedComponentType'],
            Actuated_Component_Control_Type=data['actuatedComponentControlType']
        )
        db.session.add(new_ems_actuator_info)
        db.session.commit()

        new_ems_actuator=idf.newidfobject('EnergyManagementSystem:Actuator')
        new_ems_actuator.Name=data['name']
        new_ems_actuator.Actuated_Component_Unique_Name=data['actuatedComponentUniqueName']
        new_ems_actuator.Actuated_Component_Type=data['actuatedComponentType']
        new_ems_actuator.Actuated_Component_Control_Type=data['actuatedComponentControlType']

        idf.save()

        return jsonify({'message': 'Actuator Added Successfully'}), 200
    
    except Exception as e:
         return jsonify({'error': 'Failed to Add Object.', 'details': str(e)}), 500

@model_editor_bp.route('/add_fmu_actuator', methods=['POST'])
def add_fmu_actuator():
    idf_path=glob.glob(os.path.join(UPLOAD_FOLDER, '*.idf'))
    IDF.setiddname(IDD_PATH)
    idf=IDF(idf_path[0])
    try:
        data = request.get_json()
        new_fmu_actuator_info= current_fmu_actuator(
            Name=data['name'],
            Actuated_Component_Unique_Name=data['actuatedComponentUniqueName'],
            Actuated_Component_Type=data['actuatedComponentType'],
            Actuated_Component_Control_Type=data['actuatedComponentControlType'],
            FMU_Variable_Name=data['fmuVariableName'],
            Initial_Value=data['initialValue']
        )
        db.session.add(new_fmu_actuator_info)
        db.session.commit()

        new_fmu_actuator=idf.newidfobject('ExternalInterface:FunctionalMockupUnitExport:To:Actuator')
        new_fmu_actuator.Name=data['name']
        new_fmu_actuator.Actuated_Component_Unique_Name=data['actuatedComponentUniqueName']
        new_fmu_actuator.Actuated_Component_Type=data['actuatedComponentType']
        new_fmu_actuator.Actuated_Component_Control_Type=data['actuatedComponentControlType']
        new_fmu_actuator.FMU_Variable_Name=data['fmuVariableName']
        new_fmu_actuator.Initial_Value=data['initialValue']

        idf.save()

        return jsonify({'message': 'FMU Actuator Added Successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': 'Failed to Add Object.', 'details': str(e)}), 500
    
@model_editor_bp.route('/add_fmu_from_variable', methods=['POST'])
def add_fmu_from_variable():
    idf_path=glob.glob(os.path.join(UPLOAD_FOLDER, '*.idf'))
    IDF.setiddname(IDD_PATH)
    idf=IDF(idf_path[0])
    try:
        data = request.get_json()
        new_fmu_from_variable_info= current_fmu_from_variable(
            OutputVariable_Index_Key_Name=data['outputVariableIndexKeyName'],
            OutputVariable_Name=data['outputVariableName'],
            FMU_Variable_Name=data['fmuVariableName']
        )
        db.session.add(new_fmu_from_variable_info)
        db.session.commit()

        new_output_variable_info = current_output_variable(
            Key_Value=data['outputVariableIndexKeyName'],
            Variable_Name=data['outputVariableName'],
            Reporting_Frequency='Timestep',
            Schedule_Name=''
        )
        db.session.add(new_output_variable_info)
        db.session.commit()

        new_fmu_from_variable=idf.newidfobject('ExternalInterface:FunctionalMockupUnitExport:From:Variable')
        new_fmu_from_variable.OutputVariable_Index_Key_Name=data['outputVariableIndexKeyName']
        new_fmu_from_variable.OutputVariable_Name=data['outputVariableName']
        new_fmu_from_variable.FMU_Variable_Name=data['fmuVariableName']

        new_output_variable=idf.newidfobject('Output:Variable')
        new_output_variable.Key_Value=data['outputVariableIndexKeyName']
        new_output_variable.Variable_Name=data['outputVariableName']
        new_output_variable.Reporting_Frequency='Timestep'

        idf.save()

        return jsonify({'message': 'FMU From Variable Added Succesfully'}), 200
    
    except Exception as e:
        return jsonify({'error': 'Failed to Add Object.', 'details': str(e)}), 500
    
@model_editor_bp.route('/add_fmu_to_variable', methods=['POST'])
def add_fmu_to_variable():
    idf_path=glob.glob(os.path.join(UPLOAD_FOLDER, '*.idf'))
    IDF.setiddname(IDD_PATH)
    idf=IDF(idf_path[0])
    try:
        data = request.get_json()
        new_fmu_to_variable_info= current_fmu_to_variable(
            Name=data['name'],
            FMU_Variable_Name=data['fmuVariableName'],
            Initial_Value=data['initialValue']
        )
        db.session.add(new_fmu_to_variable_info)
        db.session.commit()

        new_fmu_to_variable=idf.newidfobject('ExternalInterface:FunctionalMockupUnitExport:To:Variable')
        new_fmu_to_variable.Name=data['name']
        new_fmu_to_variable.FMU_Variable_Name=data['fmuVariableName']
        new_fmu_to_variable.Initial_Value=data['initialValue']

        idf.save()

        return jsonify({'message': 'FMU To Variable Added Successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': 'Failed to Add Object.', 'details': str(e)}), 500
    
@model_editor_bp.route('/add_fmu_schedule', methods=['POST'])
def add_fmu_schedule():
    idf_path = glob.glob(os.path.join(UPLOAD_FOLDER, '*.idf'))
    IDF.setiddname(IDD_PATH)
    idf = IDF(idf_path[0])
    try:
        data = request.get_json()
        schedule_name = data['scheduleName']

        # Check if the name type is existing_schedule and remove existing schedules with the same name
        if data.get('nameType') == 'existing_schedule':
            schedule_types = ['Schedule:Day:Hourly', 'Schedule:Day:Interval', 'Schedule:Day:List',
                              'Schedule:Week:Daily', 'Schedule:Week:Compact', 'Schedule:Year',
                              'Schedule:Compact', 'Schedule:Constant', 'Schedule:File:Shading', 'Schedule:File']

            for schedule_type in schedule_types:
                schedules = idf.idfobjects[schedule_type]
                for schedule in schedules:
                    if schedule.Name == schedule_name:
                        idf.removeidfobject(schedule)

        # Now, add the new schedule to the IDF
        new_fmu_schedule = idf.newidfobject('ExternalInterface:FunctionalMockupUnitExport:To:Schedule')
        new_fmu_schedule.Schedule_Name = schedule_name
        new_fmu_schedule.Schedule_Type_Limits_Names = data['scheduleTypeLimitsNames']
        new_fmu_schedule.FMU_Variable_Name = data['fmuVariableName']
        new_fmu_schedule.Initial_Value = data['initialValue']

        idf.save()

        # Add the new schedule information to the database
        new_fmu_schedule_info = current_fmu_schedule(
            Schedule_Name=schedule_name,
            Schedule_Type_Limits_Names=data['scheduleTypeLimitsNames'],
            FMU_Variable_Name=data['fmuVariableName'],
            Initial_Value=data['initialValue']
        )
        db.session.add(new_fmu_schedule_info)
        db.session.commit()

        return jsonify({'message': 'FMU Schedule Added Successfully'}), 200

    except Exception as e:
        return jsonify({'error': 'Failed to Add Object.', 'details': str(e)}), 500
    
@model_editor_bp.route('/add_ems_program_calling_manager', methods=['POST'])
def add_ems_program_calling_manager():
    idf_path=glob.glob(os.path.join(UPLOAD_FOLDER, '*.idf'))
    IDF.setiddname(IDD_PATH)
    idf=IDF(idf_path[0])
    try: 
        data = request.get_json()
        new_program_calling_manager_info = CurrentEMSProgramCallingManager (
            name=data['name'],
            energy_plus_model_calling_point=data['energyPlusModelCallingPoint']
        )
        for program_name in data['programNames']:
            new_program_calling_manager_info.program_names.append(ProgramName(line_text=program_name))
            
        db.session.add(new_program_calling_manager_info)
        db.session.commit()

        new_program_calling_manager=idf.newidfobject('EnergyManagementSystem:ProgramCallingManager')
        new_program_calling_manager.Name=data['name']
        new_program_calling_manager.EnergyPlus_Model_Calling_Point=data['energyPlusModelCallingPoint']

        for i, program in enumerate(data['programNames'], start=1):
            setattr(new_program_calling_manager, f'Program_Name_{i}', program)
            
        idf.save()

        return jsonify({'message': 'Program Calling Manager Added Successfully'}), 200

    except Exception as e:
        return jsonify({'error': 'Failed to Add Object', 'details': str(e)}), 500
    
@model_editor_bp.route('/add_ems_program', methods=['POST'])
def add_ems_program():
    idf_path=glob.glob(os.path.join(UPLOAD_FOLDER, '*.idf'))
    IDF.setiddname(IDD_PATH)
    idf=IDF(idf_path[0])
    try:
        data = request.get_json()
        new_program_info = CurrentEMSProgram(
            name=data['name']
        )
        for program_line in data['programLines']:
            new_program_info.program_lines.append(ProgramLine(line_text=program_line))

        db.session.add(new_program_info)
        db.session.commit()
        
        new_program=idf.newidfobject('EnergyManagementSystem:Program')
        new_program.Name=data['name']

        for i, line in enumerate(data['programLines'], start=1):
            setattr(new_program, f'Program_Line_{i}', line)
            
        idf.save()

        return jsonify({'message': 'Program Added Successfylly'}), 200
    
    except Exception as e:
        return jsonify({'error': 'Failed to Add Object', 'details': str(e)}), 500

@model_editor_bp.route('/add_ems_output_variable', methods=['POST'])
def add_ems_output_variable():
    idf_path = glob.glob(os.path.join(UPLOAD_FOLDER, '*.idf'))[0]
    IDF.setiddname(IDD_PATH)
    idf = IDF(idf_path[0])
    try:
        data = request.get_json()

        # 1) Persistir en BD
        new = current_ems_output_variable(
            Name=data['name'],
            Variable_Name=data['variableName'],
            Type_of_Data=data['typeOfData'],
            Update_Frequency=data['updateFrequency'],
            EMS_Program_or_Sub=data.get('emsProgramOrSub', ''),
            Units=data.get('units', '')
        )
        db.session.add(new)
        db.session.commit()

        # 2) Añadir al IDF
        obj = idf.newidfobject('EnergyManagementSystem:OutputVariable')
        obj.Name = data['name']
        obj.EMS_Variable_Name = data['variableName']
        obj.Type_of_Data_in_Variable = data['typeOfData']
        obj.Update_Frequency = data['updateFrequency']
        if data.get('emsProgramOrSub'):
            obj.EMS_Program_or_Subroutine_Name = data['emsProgramOrSub']
        if data.get('units'):
            obj.Units = data['units']
        idf.save()

        return jsonify({'message': 'EMS Output Variable added'}), 200
    
    except Exception as e:
        return jsonify({'error': 'Failed to Add Object', 'details': str(e)}), 500
    
@model_editor_bp.route('/remove_output_variables', methods=['DELETE'])
def remove_output_variables():
    idf_path = glob.glob(os.path.join(UPLOAD_FOLDER, '*.idf'))
    IDF.setiddname(IDD_PATH)
    idf = IDF(idf_path[0])
    try:
        data = request.get_json()

        current_output_variables = idf.idfobjects['Output:Variable']
        for variable in current_output_variables:
            if variable.Key_Value == data['keyValue'] and variable.Variable_Name == data['variableName'] and variable.Reporting_Frequency == data['reportingFrequency']:
                idf.removeidfobject(variable)
                break

            # Remove associated EMS Sensors
        current_ems_sensors = idf.idfobjects['EnergyManagementSystem:Sensor']
        sensors_to_remove = [sensor for sensor in current_ems_sensors if sensor.OutputVariable_or_OutputMeter_Index_Key_Name == data['keyValue'] and sensor.OutputVariable_or_OutputMeter_Name == data['variableName']]
        for sensor in sensors_to_remove:
            idf.removeidfobject(sensor)

            # Remove associated FMU From Variables
        current_fmu_from_variables = idf.idfobjects['ExternalInterface:FunctionalMockupUnitExport:From:Variable']
        from_vars_to_remove = [var for var in current_fmu_from_variables if var.OutputVariable_Index_Key_Name == data['keyValue'] and var.OutputVariable_Name == data['variableName']]
        for var in from_vars_to_remove:
            idf.removeidfobject(var)

        idf.save()

            # Remove from database
        current_output_variable.query.filter_by(Key_Value=data['keyValue'], Variable_Name=data['variableName'], Reporting_Frequency=data['reportingFrequency']).delete()
        db.session.commit()
        current_ems_sensor.query.filter_by(OutputVariable_or_OutputMeter_Index_Key_Name=data['keyValue'], OutputVariable_or_OutputMeter_Name=data['variableName']).delete()
        db.session.commit()
        current_fmu_from_variable.query.filter_by(OutputVariable_Index_Key_Name=data['keyValue'], OutputVariable_Name=data['variableName']).delete()
        db.session.commit()

        return jsonify({'message': 'Output Variable and associated objects removed successfully'}), 200

    except Exception as e:
        return jsonify({'error': 'Failed to remove Output Variable and associated objects.', 'details': str(e)}), 500

@model_editor_bp.route('/remove_ems_sensors', methods=['DELETE'])
def remove_ems_sensors():
    idf_path = glob.glob(os.path.join(UPLOAD_FOLDER, '*.idf'))
    IDF.setiddname(IDD_PATH)
    idf = IDF(idf_path[0])
    try:
        data = request.get_json()

        current_ems_sensors = idf.idfobjects['EnergyManagementSystem:Sensor']
        for sensor in current_ems_sensors:
            if sensor.Name == data['name']:
                idf.removeidfobject(sensor)
                break

        current_output_variables = idf.idfobjects['Output:Variable']
        for variable in current_output_variables:
            if variable.Key_Value==data['outputVariableOrOutputMeterIndexKeyName'] and variable.Variable_Name==data['outputVariableOrOutputMeterName']:
                idf.removeidfobject(variable)
        
        idf.save()

        # Remove from database
        db_sensor = current_ems_sensor.query.filter_by(Name=data['name']).first()
        if db_sensor:
            db.session.delete(db_sensor)
            db.session.commit()

        db_output_variables = current_output_variable.query.filter_by(Key_Value=data['outputVariableOrOutputMeterIndexKeyName'], Variable_Name=data['outputVariableOrOutputMeterName'])
        if db_output_variables:
            for variable in db_output_variables:
                db.session.delete(variable)
                db.session.commit()

        return jsonify({'message': 'Sensor Removed Successfully'}), 200

    except Exception as e:
        return jsonify({'error': 'Failed to Remove Sensor', 'details': str(e)}), 500

@model_editor_bp.route('/remove_ems_actuators', methods=['DELETE'])
def remove_ems_actuators():
    idf_path = glob.glob(os.path.join(UPLOAD_FOLDER, '*.idf'))
    IDF.setiddname(IDD_PATH)
    idf = IDF(idf_path[0])
    try:
        data = request.get_json()

        current_ems_actuators = idf.idfobjects['EnergyManagementSystem:Actuator']
        for actuator in current_ems_actuators:
            if actuator.Name == data['name']:
                idf.removeidfobject(actuator)
                break
        
        idf.save()

        # Remove from database
        db_actuator = current_ems_actuator.query.filter_by(Name=data['name']).first()
        if db_actuator:
            db.session.delete(db_actuator)
            db.session.commit()

        return jsonify({'message': 'Actuator Removed Successfully'}), 200

    except Exception as e:
        return jsonify({'error': 'Failed to Remove Actuator', 'details': str(e)}), 500

@model_editor_bp.route('/remove_ems_program_calling_managers', methods=['DELETE'])
def remove_ems_program_calling_managers():
    idf_path = glob.glob(os.path.join(UPLOAD_FOLDER, '*.idf'))
    IDF.setiddname(IDD_PATH)
    idf = IDF(idf_path[0])
    try:
        data = request.get_json()

        current_ems_program_calling_managers = idf.idfobjects['EnergyManagementSystem:ProgramCallingManager']
        for manager in current_ems_program_calling_managers:
            if manager.Name == data['name']:
                idf.removeidfobject(manager)
                break
        
        idf.save()

        # Remove from database
        db_manager = CurrentEMSProgramCallingManager.query.filter_by(name=data['name']).first()
        if db_manager:
            db.session.delete(db_manager)
            db.session.commit()

        return jsonify({'message': 'Program Calling Manager Removed Successfully'}), 200

    except Exception as e:
        return jsonify({'error': 'Failed to Remove Program Calling Manager', 'details': str(e)}), 500

@model_editor_bp.route('/remove_ems_programs', methods=['DELETE'])
def remove_ems_programs():
    idf_path = glob.glob(os.path.join(UPLOAD_FOLDER, '*.idf'))
    IDF.setiddname(IDD_PATH)
    idf = IDF(idf_path[0])
    try:
        data = request.get_json()
        program_name = data['name']

        # Remove from IDF
        current_ems_programs = idf.idfobjects['EnergyManagementSystem:Program']
        programs_to_remove = set()

        for program in current_ems_programs:
            if program.Name == program_name:
                idf.removeidfobject(program)
                programs_to_remove.add(program_name)

        # Regex pattern to match exact program names
        program_pattern = re.compile(r'\b' + re.escape(program_name) + r'\b')

        # Find and remove programs that reference the deleted program in their lines
        for program in current_ems_programs:
            program_lines = []
            for i in range(1, 500):  # Assuming there won't be more than 500 lines in a program
                line_attr = f'Program_Line_{i}'
                if hasattr(program, line_attr):
                    line = getattr(program, line_attr)
                    program_lines.append(line)
                else:
                    break

            # Use regex to match exact program names
            if any(program_pattern.search(line) for line in program_lines):
                programs_to_remove.add(program.Name)
                idf.removeidfobject(program)

        # Remove related entries in ProgramCallingManagers
        current_program_calling_managers = idf.idfobjects['EnergyManagementSystem:ProgramCallingManager']
        for manager in current_program_calling_managers:
            manager_programs = [getattr(manager, f'Program_Name_{i}') for i in range(1, 500) if hasattr(manager, f'Program_Name_{i}')]
            if any(prog in manager_programs for prog in programs_to_remove):
                idf.removeidfobject(manager)

        idf.save()

        # Remove from database
        for prog in programs_to_remove:
            db_program = CurrentEMSProgram.query.filter_by(name=prog).first()
            if db_program:
                db.session.delete(db_program)
                db.session.commit()

        # Remove related entries in CurrentEMSProgramCallingManager
        db_managers = CurrentEMSProgramCallingManager.query.all()
        for manager in db_managers:
            manager_programs = [name.line_text for name in manager.program_names]
            if any(prog in manager_programs for prog in programs_to_remove):
                db.session.delete(manager)
                db.session.commit()

        return jsonify({'message': 'Program and related entries removed successfully'}), 200

    except Exception as e:
        return jsonify({'error': 'Failed to remove program', 'details': str(e)}), 500

@model_editor_bp.route('/remove_fmu_actuators', methods=['DELETE'])
def remove_fmu_actuators():
    idf_path = glob.glob(os.path.join(UPLOAD_FOLDER, '*.idf'))
    IDF.setiddname(IDD_PATH)
    idf = IDF(idf_path[0])

    try:
        data = request.get_json()

        current_fmu_actuators = idf.idfobjects['ExternalInterface:FunctionalMockupUnitExport:To:Actuator']
        for actuator in current_fmu_actuators:
            if actuator.Name == data['name']:
                idf.removeidfobject(actuator)
                break
        
        idf.save()

        # Remove from database
        db_actuator = current_fmu_actuator.query.filter_by(Name=data['name']).first()
        if db_actuator:
            db.session.delete(db_actuator)
            db.session.commit()

        return jsonify({'message': 'FMU Actuator Removed Successfully'}), 200

    except Exception as e:
        return jsonify({'error': 'Failed to Remove FMU Actuator', 'details': str(e)}), 500

@model_editor_bp.route('/remove_fmu_from_variables', methods=['DELETE'])
def remove_fmu_from_variables():
    idf_path = glob.glob(os.path.join(UPLOAD_FOLDER, '*.idf'))
    IDF.setiddname(IDD_PATH)
    idf = IDF(idf_path[0])
    try:
        data = request.get_json()

        current_fmu_from_variables = idf.idfobjects['ExternalInterface:FunctionalMockupUnitExport:From:Variable']
        for variable in current_fmu_from_variables:
            if variable.FMU_Variable_Name == data['fmuVariableName']:
                idf.removeidfobject(variable)
                break

        current_output_variables = idf.idfobjects['Output:Variable']
        for variable in current_output_variables:
            if variable.Key_Value==data['outputVariableIndexKeyName'] and variable.Variable_Name==data['outputVariableName']:
                idf.removeidfobject(variable)
        
        idf.save()

        # Remove from database
        db_variable = current_fmu_from_variable.query.filter_by(FMU_Variable_Name=data['fmuVariableName']).first()
        if db_variable:
            db.session.delete(db_variable)
            db.session.commit()

        db_output_variables = current_output_variable.query.filter_by(Key_Value=data['outputVariableIndexKeyName'], Variable_Name=data['outputVariableName'])
        if db_output_variables:
            for variable in db_output_variables:
                db.session.delete(variable)
                db.session.commit()

        return jsonify({'message': 'From:Variable Removed Successfully'}), 200

    except Exception as e:
        return jsonify({'error': 'Failed to Remove From:Variable', 'details': str(e)}), 500

@model_editor_bp.route('/remove_fmu_to_variables', methods=['DELETE'])
def remove_fmu_to_variables():
    idf_path = glob.glob(os.path.join(UPLOAD_FOLDER, '*.idf'))
    IDF.setiddname(IDD_PATH)
    idf = IDF(idf_path[0])
    try:
        data = request.get_json()
        variable_name = data['name']

        # Remove from IDF
        current_fmu_to_variables = idf.idfobjects['ExternalInterface:FunctionalMockupUnitExport:To:Variable']
        variables_to_remove = set()

        for variable in current_fmu_to_variables:
            if variable.Name == variable_name:
                variables_to_remove.add(variable.Name)
                idf.removeidfobject(variable)
                break

        # Regex pattern to match exact variable names
        variable_pattern = re.compile(r'\b' + re.escape(variable_name) + r'\b')

        # Find and remove programs that reference the deleted variable in their lines
        current_ems_programs = idf.idfobjects['EnergyManagementSystem:Program']
        programs_to_remove = set()

        for program in current_ems_programs:
            program_lines = []
            for i in range(1, 500):  # Assuming there won't be more than 500 lines in a program
                line_attr = f'Program_Line_{i}'
                if hasattr(program, line_attr):
                    line = getattr(program, line_attr)
                    program_lines.append(line)
                else:
                    break

            # Use regex to match exact variable names
            if any(variable_pattern.search(line) for line in program_lines):
                programs_to_remove.add(program.Name)
                idf.removeidfobject(program)

        # Remove related entries in ProgramCallingManagers
        current_program_calling_managers = idf.idfobjects['EnergyManagementSystem:ProgramCallingManager']
        for manager in current_program_calling_managers:
            manager_programs = [getattr(manager, f'Program_Name_{i}') for i in range(1, 500) if hasattr(manager, f'Program_Name_{i}')]
            if any(prog in programs_to_remove for prog in manager_programs):
                idf.removeidfobject(manager)

        idf.save()

        # Remove from database
        db_variable = current_fmu_to_variable.query.filter_by(Name=variable_name).first()
        if db_variable:
            db.session.delete(db_variable)
            db.session.commit()

        for prog in programs_to_remove:
            db_program = CurrentEMSProgram.query.filter_by(name=prog).first()
            if db_program:
                db.session.delete(db_program)
                db.session.commit()

        # Remove related entries in CurrentEMSProgramCallingManager
        db_managers = CurrentEMSProgramCallingManager.query.all()
        for manager in db_managers:
            manager_programs = [name.line_text for name in manager.program_names]
            if any(prog in manager_programs for prog in programs_to_remove):
                db.session.delete(manager)
                db.session.commit()

        return jsonify({'message': 'To:Variable and related entries removed successfully'}), 200

    except Exception as e:
        return jsonify({'error': 'Failed to remove To:Variable', 'details': str(e)}), 500

@model_editor_bp.route('/remove_fmu_schedules', methods=['DELETE'])
def remove_fmu_schedules():
    idf_path = glob.glob(os.path.join(UPLOAD_FOLDER, '*.idf'))
    IDF.setiddname(IDD_PATH)
    idf = IDF(idf_path[0])
    try:
        data = request.get_json()

        current_fmu_schedules = idf.idfobjects['ExternalInterface:FunctionalMockupUnitExport:To:Schedule']
        for schedule in current_fmu_schedules:
            if schedule.Schedule_Name == data['scheduleName']:
                idf.removeidfobject(schedule)
                break
        
        idf.save()

        # Remove from database
        db_schedule = current_fmu_schedule.query.filter_by(Schedule_Name=data['scheduleName']).first()
        if db_schedule:
            db.session.delete(db_schedule)
            db.session.commit()

        return jsonify({'message': 'Schedule Removed Successfully'}), 200

    except Exception as e:
        return jsonify({'error': 'Failed to Remove FMU Schedule', 'details': str(e)}), 500
    
@model_editor_bp.route('/remove_ems_output_variable', methods=['POST'])
def remove_ems_output_variable():
    data = request.get_json()
    # eliminar de BD
    o = current_ems_output_variable.query.get(data['id'])
    db.session.delete(o); db.session.commit()
    # eliminar en IDF
    idf_path = glob.glob(...)[0]
    IDF.setiddname(IDD_PATH); idf = IDF(idf_path)
    for eo in idf.idfobjects['EnergyManagementSystem:OutputVariable']:
        if eo.Name == data['name']:
            idf.removeidfobject(eo)
            break
    idf.save()
    return jsonify({'message': 'Removed'}), 200


def clean_dir(path):
    """
    Limpia un directorio borrando subdirectorios y archivos, pero preserva cualquier Dockerfile.
    """
    if os.path.isdir(path):
        for entry in os.listdir(path):
            # No borramos Dockerfile
            if entry == 'Dockerfile':
                continue
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
            elif os.path.isfile(full_path) or os.path.islink(full_path):
                os.remove(full_path)

@model_editor_bp.route('/reset_session', methods=['DELETE'])
def reset_session():
    try:
        # 1) Clear Flask session
        session.clear()

        # 2) Delete all relevant DB entries (SQLAlchemy models)
        models = [
            edd_Actuator, rdd_Variable,
            current_ems_sensor, current_ems_actuator,
            CurrentEMSProgram, ProgramLine,
            CurrentEMSProgramCallingManager, ProgramName,
            current_fmu_actuator, current_fmu_from_variable,
            current_fmu_to_variable, current_fmu_schedule,
            existing_schedule_name, existing_shedule_type_limit,
            current_output_variable,
            idf_Material, idf_Construction,
            idf_FenestrationSurfaceDetailed,
            idf_ZoneVentilationDesignFlowRate,
            idf_Lights, idf_WindowShadingControl
        ]
        for model in models:
            model.query.delete()
        db.session.commit()

        # 3) Remove and recreate core directories
        core_dirs = ['simulation_outputs', 'uploads', 'user_files']
        for directory in core_dirs:
            shutil.rmtree(directory, ignore_errors=True)
            os.makedirs(directory, exist_ok=True)

        # 4) Remove stray files in workspace
        for ext in ['*.fmu', '*.exe', '*.zip']:
            for fpath in glob.glob(ext):
                try:
                    os.remove(fpath)
                except OSError:
                    pass

        # 5) Strip outputs from notebooks or delete if unparsable
        nb_dirs = ['simulation_notebooks', 'surrogate_notebooks']
        for nb_dir in nb_dirs:
            if not os.path.isdir(nb_dir):
                os.makedirs(nb_dir, exist_ok=True)
            for entry in os.listdir(nb_dir):
                full_path = os.path.join(nb_dir, entry)
                if os.path.isdir(full_path):
                    shutil.rmtree(full_path, ignore_errors=True)
                elif entry.endswith('.ipynb'):
                    try:
                        nb = read(full_path, as_version=4)
                        for cell in nb.cells:
                            cell.pop('outputs', None)
                            cell.pop('execution_count', None)
                        write(nb, full_path)
                    except Exception:
                        os.remove(full_path)
                else:
                    try:
                        os.remove(full_path)
                    except OSError:
                        pass

        # 5.1) Restore notebook templates for simulation and surrogate
        templates = {
            'Surrogate_template.ipynb': 'surrogate_notebooks/SurrogateNotebook.ipynb',
            'Simulation_template.ipynb': 'simulation_notebooks/SimulationNotebook.ipynb'
        }
        for src_name, target_rel in templates.items():
            src = os.path.join(os.getcwd(), 'notebook_templates', src_name)
            dst = os.path.join(os.getcwd(), target_rel)
            shutil.copy(src, dst)

        # 6) Reset InfluxDB databases
        influx_host = 'influxdb'
        influx_port = 8086
        influx_user = os.getenv('INFLUX_USERNAME', 'admin')
        influx_pass = os.getenv('INFLUX_PASSWORD', 'admin123')
        db1 = os.getenv('INFLUX_BUCKET', 'controlled_building')
        db2 = 'base_building'
        client_v1 = InfluxDBClientV1(
            host=influx_host,
            port=influx_port,
            username=influx_user,
            password=influx_pass
        )
        client_v1.drop_database(db1)
        client_v1.create_database(db1)
        client_v1.drop_database(db2)
        client_v1.create_database(db2)
        client_v1.close()

        # 7) Clean shared notebook dirs for ControlledSimulation, BaseSimulation, Controller
        base = current_app.root_path
        shared_dirs = [
            os.path.join(base, 'controlled_notebooks'),
            os.path.join(base, 'base_notebooks'),
            os.path.join(base, 'controller_notebooks')
        ]
        for path in shared_dirs:
            clean_dir(path)

        # 8) Restore notebook templates for these three
        extra_templates = {
            'ControlledSim_template.ipynb': 'controlled_notebooks/ControlledSim.ipynb',
            'BaseSim_template.ipynb':       'base_notebooks/BaseSim.ipynb',
            'Controller_template.ipynb':    'controller_notebooks/Controller.ipynb'
        }
        for src_name, target_rel in extra_templates.items():
            src = os.path.join(os.getcwd(), 'notebook_templates', src_name)
            dst = os.path.join(os.getcwd(), target_rel)
            shutil.copy(src, dst)

        # 9) Return success
        return jsonify({'success': True, 'message': 'Session Reset Done.'}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error resetting session: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500