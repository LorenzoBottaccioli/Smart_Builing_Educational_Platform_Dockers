from eppy.modeleditor import IDF
import subprocess
import os
from models import (
    idf_Material,
    idf_Construction,
    idf_FenestrationSurfaceDetailed,
    idf_ZoneVentilationDesignFlowRate,
    idf_Lights,
    idf_WindowShadingControl
)

#ENERGY_PLUS_EXECUTABLE_PATH = 'EnergyPlusV9-6-0\energyplus.exe'
IDD_PATH='/app/EnergyPlus-9-6-0/Energy+.idd'
#CONVERTER_PATH='EnergyPlusToFMU-v3.1.0\Scripts\EnergyPlusToFMU.py'
SIMULATION_OUTPUTS='simulation_outputs'
IDF_EXTENSION={'idf'}
EPW_EXTENSION=['epw']

def run_energyplus_simulation(idf_path, epw_path):
    """
    Run an EnergyPlus simulation by executing the EnergyPlus binary
    inside a separate Docker container named 'energyplus'.

    Parameters:
        idf_path (str): Path to the IDF file relative to the local project root,
                        e.g. 'uploads/my_model.idf'.
        epw_path (str): Path to the EPW weather file relative to the local project root,
                        e.g. 'uploads/my_weather.epw'.

    Returns:
        bool: True if the simulation completed successfully, False otherwise.
    """
    # Ensure the local output folder exists
    os.makedirs(SIMULATION_OUTPUTS, exist_ok=True)

    # Absolute path to the EnergyPlus binary inside the energyplus container
    ENERGYPLUS_BIN = "/EnergyPlus-9.6.0-4b123cf80f-Linux-Ubuntu20.04-x86_64/energyplus-9.6.0"

    # Build the 'docker exec' command as a list of arguments:
    # - '-u root'            : run inside the container as 'root'
    # - 'energyplus'         : name of the container (matches container_name in docker-compose)
    # - ENERGYPLUS_BIN       : calls the executable inside that container
    # - '-r'                  : request standard results files (.csv, .eso, etc.)
    # - '-d /workspace/...'   : directory inside the container where results are placed
    # - '-w /workspace/...'   : EPW file path inside the container
    # - '/workspace/...'      : IDF file path inside the container
    cmd = [
        "docker", "exec", "-u", "root", "energyplus",
        ENERGYPLUS_BIN,
        "-r",
        "-d", f"/workspace/{SIMULATION_OUTPUTS}",
        "-w", f"/workspace/{epw_path.replace(os.sep, '/')}",
        f"/workspace/{idf_path.replace(os.sep, '/')}"
    ]

    try:
        # Run the command, capturing stdout and stderr as text
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            # If the return code is non-zero, EnergyPlus failed
            print("EnergyPlus did not run successfully.")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
        else:
            print("EnergyPlus simulation completed successfully.")
            return True

    except Exception as e:
        # Catch any exception raised by subprocess.run or building the command
        print(f"An error occurred while trying to run EnergyPlus: {e}", flush=1)
        return False

def idf_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in IDF_EXTENSION

def epw_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in EPW_EXTENSION

def modify_idf_for_one_day_simulation(idf_path):
    IDF.setiddname(IDD_PATH)
    idf = IDF(idf_path)

    run_periods = idf.idfobjects['RUNPERIOD']
    
    if run_periods:
        run_period = run_periods[0]
    else:
        run_period = idf.newidfobject('RUNPERIOD')

    run_period.Begin_Month = 1
    run_period.Begin_Day_of_Month = 1
    run_period.End_Month = 1
    run_period.End_Day_of_Month = 1

    idf.save()

def modify_simulation_parameters(idf_path, begin_month, begin_day_of_month, end_month, end_day_of_month, timestep):
    IDF.setiddname(IDD_PATH)
    idf = IDF(idf_path)

    run_periods = idf.idfobjects['RUNPERIOD']
    
    if run_periods:
        run_period = run_periods[0]
    else:
        run_period = idf.newidfobject('RUNPERIOD')

    run_period.Begin_Month = begin_month
    run_period.Begin_Day_of_Month = begin_day_of_month
    run_period.End_Month = end_month
    run_period.End_Day_of_Month = end_day_of_month

    timesteps = idf.idfobjects['Timestep']

    if timesteps:
        timestep_obj=timesteps[0]
    else:
        timestep_obj = idf.newidfobject('Timestep')
    
    timestep_obj.Number_of_Timesteps_per_Hour=timestep

    idf.save()

def add_verbose(idf_path):
    IDF.setiddname(IDD_PATH)
    idf = IDF(idf_path)

    ems_outputs = idf.idfobjects['OUTPUT:ENERGYMANAGEMENTSYSTEM']
    variable_outputs = idf.idfobjects['OUTPUT:VARIABLEDICTIONARY']

    if ems_outputs:
        for ems_output in ems_outputs:
            ems_output['Actuator_Availability_Dictionary_Reporting'] = 'Verbose'
            ems_output['Internal_Variable_Availability_Dictionary_Reporting'] = 'Verbose'
    else:
        ems_output = idf.newidfobject('OUTPUT:ENERGYMANAGEMENTSYSTEM')
        ems_output['Actuator_Availability_Dictionary_Reporting'] = 'Verbose'
        ems_output['Internal_Variable_Availability_Dictionary_Reporting'] = 'Verbose'

    if variable_outputs:
        for variable_output in variable_outputs:
            variable_output.Key_Field = 'regular'
            variable_output.Sort_Option= 'Name'
    else:

        variable_output=idf.newidfobject('OUTPUT:VARIABLEDICTIONARY')
        variable_output.Key_Field = 'regular'
        variable_output.Sort_Option= 'Name'

    idf.save()

def add_external_interface(idf_path):
    IDF.setiddname(IDD_PATH)
    idf = IDF(idf_path)

    external_interface = idf.idfobjects['ExternalInterface']

    if external_interface:
        external_exist = external_interface[0]
    else:
        external_exist = idf.newidfobject('ExternalInterface')

    external_exist.Name_of_External_Interface = 'FunctionalMockupUnitExport'

    idf.save()

def parse_edd_file(edd_file_path):
    available_actuators = []

    with open(edd_file_path, 'r') as file:
        lines = file.readlines()

    for line in lines:
        if "EnergyManagementSystem:Actuator Available" in line:
            parts = line.split(',')
            if len(parts) >= 4:
                actuator_info = {
                    'Component_Unique_Name': parts[1].strip(),
                    'Component_Type': parts[2].strip(),
                    'Control_Type': parts[3].strip().split(']')[0]
                }
                available_actuators.append(actuator_info)
    
    first_actuator = available_actuators.pop(0)

    return available_actuators

def parse_rdd_file(rdd_file_path):
    available_variables = []
    with open(rdd_file_path, 'r') as file:
        rdd_lines = file.readlines()
    
    start_reading = False
    for line in rdd_lines:
        if line.strip().startswith("Var Type (reported time step)"):
            start_reading = True
            continue
        if start_reading:
            parts = line.strip().split(',')
            if len(parts) > 2:
                var_type = parts[0].strip()
                var_name = parts[2].strip()
                if '[' in var_name:
                    var_name, units = var_name.split('[')
                    var_name = var_name.strip()
                    units = units.replace(']', '').strip()
                else:
                    units = None
                variable = {
                    'Var_Type': var_type,
                    'Variable_Name': var_name
                }
                if variable not in available_variables:
                    available_variables.append(variable)
    
    return available_variables

def get_output_variables(idf_path):
    IDF.setiddname(IDD_PATH)
    idf=IDF(idf_path)

    variables=idf.idfobjects['Output:Variable']

    available_variables=[]

    for variable in variables:
        available_variables.append({
            'Key_Value': variable.Key_Value,
            'Variable_Name': variable.Variable_Name,
            'Reporting_Frequency': variable.Reporting_Frequency,
            'Schedule_Name': variable.Schedule_Name
        })

    return available_variables

def get_zone_names(idf_path):
    IDF.setiddname(IDD_PATH)
    idf=IDF(idf_path)

    zones=idf.idfobjects['Zone']

    zone_names=[]

    for zone in zones:
        zone_names.append(zone.Name)

    return zone_names

def get_schedule_limits(idf_path):
    IDF.setiddname(IDD_PATH)
    idf = IDF(idf_path)

    available_limits = []
    limits_array = idf.idfobjects['ScheduleTypeLimits']

    for limit in limits_array:
        lower_limit = -1000 if limit.Lower_Limit_Value is None else limit.Lower_Limit_Value
        upper_limit = 1000 if limit.Upper_Limit_Value is None else limit.Upper_Limit_Value

        available_limits.append({
            'Name': limit.Name,
            'Lower_Limit_Value': lower_limit,
            'Upper_Limit_Value': upper_limit
        })

    for limit in available_limits:
        if limit['Lower_Limit_Value']=='':
            limit['Lower_Limit_Value']=-1000
        
        if limit['Upper_Limit_Value']=='':
            limit['Upper_Limit_Value']=1000

    return available_limits

def get_schedule_names(idf_path):
    IDF.setiddname(IDD_PATH)
    idf = IDF(idf_path)

    available_schedule_names = []
    schedule_types = ['Schedule:Day:Hourly', 'Schedule:Day:Interval', 'Schedule:Day:List',
                      'Schedule:Week:Daily', 'Schedule:Week:Compact', 'Schedule:Year',
                      'Schedule:Compact', 'Schedule:Constant', 'Schedule:File:Shading', 'Schedule:File']

    for schedule_type in schedule_types:
        schedules = idf.idfobjects[schedule_type]
        for schedule in schedules:
            available_schedule_names.append(schedule.Name)
        
    external_schedules = idf.idfobjects['ExternalInterface:FunctionalMockupUnitExport:To:Schedule']
    for schedule in external_schedules:
        available_schedule_names.append(schedule.Schedule_Name)

    return available_schedule_names

def get_ems_actuators(idf_path):
    IDF.setiddname(IDD_PATH)
    idf=IDF(idf_path)

    available_ems_actuators=[]
    actuators=idf.idfobjects['EnergyManagementSystem:Actuator']
    for actuator in actuators:
        available_ems_actuators.append({
            'Name': actuator.Name,
            'Actuated_Component_Unique_Name': actuator.Actuated_Component_Unique_Name,
            'Actuated_Component_Type': actuator.Actuated_Component_Type,
            'Actuated_Component_Control_Type': actuator.Actuated_Component_Control_Type
        })

    return available_ems_actuators

def get_ems_sensors(idf_path):
    IDF.setiddname(IDD_PATH)
    idf=IDF(idf_path)

    available_ems_sensors=[]
    sensors=idf.idfobjects['EnergyManagementSystem:Sensor']
    for sensor in sensors:
        available_ems_sensors.append({
            'Name': sensor.Name,
            'OutputVariable_or_OutputMeter_Index_Key_Name': sensor.OutputVariable_or_OutputMeter_Index_Key_Name,
            'OutputVariable_or_OutputMeter_Name': sensor.OutputVariable_or_OutputMeter_Name
        })

    return available_ems_sensors

def get_ems_programs(idf_path):
    IDF.setiddname(IDD_PATH)
    idf=IDF(idf_path)

    available_ems_programs=[]
    programs=idf.idfobjects['EnergyManagementSystem:Program']
    for program in programs:
        program_info = {'Name': program.Name, 'ProgramLines': []}
        for fieldname in program.fieldnames[2:]:  # Skip the 'Name' field
            line = getattr(program, fieldname)  # Only add the line if it is not empty
            if line:
                program_info['ProgramLines'].append(line)
            
        available_ems_programs.append(program_info)

    return available_ems_programs

def get_ems_program_calling_managers(idf_path):
    IDF.setiddname(IDD_PATH)
    idf = IDF(idf_path)
    
    available_ems_program_calling_managers = []

    calling_managers = idf.idfobjects['EnergyManagementSystem:ProgramCallingManager']
    
    for manager in calling_managers:
        manager_details = {
            'Name': manager.Name,
            'EnergyPlus Model Calling Point': manager.EnergyPlus_Model_Calling_Point,
            'Program Names': []
        }
        
        for i in range(1, 26):
            program_name_field = f'Program_Name_{i}'
            program_name = getattr(manager, program_name_field, None)
            if program_name:
                manager_details['Program Names'].append(program_name)
        
        available_ems_program_calling_managers.append(manager_details)
    
    return available_ems_program_calling_managers

def get_fmu_actuators(idf_path):
    IDF.setiddname(IDD_PATH)
    idf=IDF(idf_path)

    available_fmu_actuators=[]
    actuators=idf.idfobjects['ExternalInterface:FunctionalMockupUnitExport:To:Actuator']
    for actuator in actuators:
        available_fmu_actuators.append({
            'Name': actuator.Name,
            'Actuated_Component_Unique_Name': actuator.Actuated_Component_Unique_Name,
            'Actuated_Component_Type': actuator.Actuated_Component_Type,
            'Actuated_Component_Control_Type': actuator.Actuated_Component_Control_Type,
            'FMU_Variable_Name': actuator.FMU_Variable_Name,
            'Initial_Value': actuator.Initial_Value
        })

    return available_fmu_actuators

def get_fmu_schedules(idf_path):
    IDF.setiddname(IDD_PATH)
    idf=IDF(idf_path)

    available_fmu_schedules=[]
    schedules=idf.idfobjects['ExternalInterface:FunctionalMockupUnitExport:To:Schedule']
    for schedule in schedules:
        available_fmu_schedules.append({
            'Schedule_Name': schedule.Schedule_Name,
            'Schedule_Type_Limits_Names': schedule.Schedule_Type_Limits_Names,
            'FMU_Variable_Name': schedule.FMU_Variable_Name,
            'Initial_Value': schedule.Initial_Value
        })
    return available_fmu_schedules

def get_fmu_to_variables(idf_path):
    IDF.setiddname(IDD_PATH)
    idf=IDF(idf_path)

    available_fmu_to_variables=[]
    variables=idf.idfobjects['ExternalInterface:FunctionalMockupUnitExport:To:Variable']
    for variable in variables:
        available_fmu_to_variables.append({
            'Name': variable.Name,
            'FMU_Variable_Name': variable.FMU_Variable_Name,
            'Initial_Value':variable.Initial_Value
        })
    return available_fmu_to_variables

def get_fmu_from_variables(idf_path):
    IDF.setiddname(IDD_PATH)
    idf=IDF(idf_path)

    available_fmu_from_variables=[]
    variables=idf.idfobjects['ExternalInterface:FunctionalMockupUnitExport:From:Variable']
    for variable in variables:
        available_fmu_from_variables.append({
            'OutputVariable_Index_Key_Name':variable.OutputVariable_Index_Key_Name,
            'OutputVariable_Name': variable.OutputVariable_Name,
            'FMU_Variable_Name': variable.FMU_Variable_Name
            })
    return available_fmu_from_variables

def extract_year_from_epw(epw_path):
    with open(epw_path, 'r') as file:
        for line in file:
            parts = line.strip().split(',')
            # Check if the first element is a year (four digits long and all digits)
            if parts[0].isdigit() and len(parts[0]) == 4:
                return parts[0]
    return 'Year not found'

def run_conversion(epw_path, idf_path):
    """
    Ejecuta la conversión a FMU haciendo `docker exec` sobre el contenedor eptofmu,
    que está corriendo en “idle” (con `tail -f /dev/null`). 
    - epw_path: ruta absoluta al archivo .epw en el host (ej. './backend/user_files/weather.epw')
    - idf_path: ruta absoluta al archivo .idf  en el host (ej. './backend/uploads/mi_modelo.idf')
    """
    idf_fname = os.path.basename(idf_path)   # p.ej. 'mi_modelo.idf'
    epw_fname = os.path.basename(epw_path)   # p.ej. 'weather.epw'

    cmd = [
        "docker", "exec", "-u", "root", "eptofmu",
        "bash", "/opt/EnergyPlusToFMU/entrypoint.sh",
        idf_fname,
        epw_fname
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            # Mostrar stdout/ stderr para depurar
            print("----- eptofmu STDOUT -----", flush=1)
            print(result.stdout, flush=1)
            print("----- eptofmu STDERR -----", flush=1)
            print(result.stderr, flush=1)
            raise RuntimeError(f"eptofmu falló con código {result.returncode}")
        return "success"
    except FileNotFoundError:
        raise RuntimeError("No se encontró el comando 'docker'. Asegúrate de tener Docker instalado.")
    except Exception as e:
        raise RuntimeError(f"Error al ejecutar eptofmu: {e}")

def parse_materials(idf):
    materials = []
    for obj in idf.idfobjects['MATERIAL']:
        materials.append(idf_Material(
            Name=obj.Name,
            Roughness=obj.Roughness,
            Thickness=obj.Thickness,
            Conductivity=obj.Conductivity,
            Density=obj.Density,
            Specific_Heat=obj.Specific_Heat,
            Thermal_Absorptance=obj.Thermal_Absorptance,
            Solar_Absorptance=obj.Solar_Absorptance,
            Visible_Absorptance=obj.Visible_Absorptance
        ))
    return materials

def parse_constructions(idf):
    constructions = []
    for obj in idf.idfobjects['CONSTRUCTION']:
        constructions.append(idf_Construction(
            Name=obj.Name,
            Outside_Layer=obj.Outside_Layer,
            Layer_2=getattr(obj, 'Layer_2', ''),
            Layer_3=getattr(obj, 'Layer_3', ''),
            Layer_4=getattr(obj, 'Layer_4', ''),
            Layer_5=getattr(obj, 'Layer_5', ''),
            Layer_6=getattr(obj, 'Layer_6', ''),
            Layer_7=getattr(obj, 'Layer_7', ''),
            Layer_8=getattr(obj, 'Layer_8', ''),
            Layer_9=getattr(obj, 'Layer_9', ''),
            Layer_10=getattr(obj, 'Layer_10', '')
        ))
    return constructions

def parse_fenestration_surfaces(idf):
    surfaces = []
    for obj in idf.idfobjects['FENESTRATIONSURFACE:DETAILED']:
        surfaces.append(idf_FenestrationSurfaceDetailed(
            Name=obj.Name,
            Surface_Type=obj.Surface_Type,
            Construction_Name=obj.Construction_Name,
            Building_Surface_Name=obj.Building_Surface_Name,
            Outside_Boundary_Condition_Object=obj.Outside_Boundary_Condition_Object,
            View_Factor_to_Ground=obj.View_Factor_to_Ground,
            Frame_and_Divider_Name=getattr(obj, 'Frame_and_Divider_Name', ''),
            Multiplier=obj.Multiplier,
            Number_of_Vertices=obj.Number_of_Vertices,
            Vertex_1_X=getattr(obj, 'Vertex_1_X', ''),
            Vertex_1_Y=getattr(obj, 'Vertex_1_Y', ''),
            Vertex_1_Z=getattr(obj, 'Vertex_1_Z', ''),
            Vertex_2_X=getattr(obj, 'Vertex_2_X', ''),
            Vertex_2_Y=getattr(obj, 'Vertex_2_Y', ''),
            Vertex_2_Z=getattr(obj, 'Vertex_2_Z', ''),
            Vertex_3_X=getattr(obj, 'Vertex_3_X', ''),
            Vertex_3_Y=getattr(obj, 'Vertex_3_Y', ''),
            Vertex_3_Z=getattr(obj, 'Vertex_3_Z', ''),
            Vertex_4_X=getattr(obj, 'Vertex_4_X', ''),
            Vertex_4_Y=getattr(obj, 'Vertex_4_Y', ''),
            Vertex_4_Z=getattr(obj, 'Vertex_4_Z', '')
        ))
    return surfaces

def parse_zone_ventilation(idf):
    vents = []
    for obj in idf.idfobjects['ZONEVENTILATION:DESIGNFLOWRATE']:
        vents.append(idf_ZoneVentilationDesignFlowRate(
            Name=obj.Name,
            Zone_Name=obj.Zone_or_ZoneList_Name,
            Schedule_Name=obj.Schedule_Name,
            Design_Flow_Rate_Calculation_Method=obj.Design_Flow_Rate_Calculation_Method,
            Design_Flow_Rate=getattr(obj, 'Design_Flow_Rate', ''),
            Flow_per_Zone_Floor_Area=getattr(obj, 'Flow_per_Zone_Floor_Area', ''),
            Flow_Rate_per_Person=getattr(obj, 'Flow_Rate_per_Person', ''),
            Air_Changes_per_Hour=getattr(obj, 'Air_Changes_per_Hour', ''),
            Ventilation_Type=obj.Ventilation_Type,
            Fan_Pressure_Rise=getattr(obj, 'Fan_Pressure_Rise', ''),
            Fan_Total_Efficiency=getattr(obj, 'Fan_Total_Efficiency', ''),
            Constant_Term_Coefficient=getattr(obj, 'Constant_Term_Coefficient', ''),
            Temperature_Term_Coefficient=getattr(obj, 'Temperature_Term_Coefficient', ''),
            Velocity_Term_Coefficient=getattr(obj, 'Velocity_Term_Coefficient', ''),
            Velocity_Squared_Term_Coefficient=getattr(obj, 'Velocity_Squared_Term_Coefficient', ''),
            Minimum_Indoor_Temperature=getattr(obj, 'Minimum_Indoor_Temperature', ''),
            Minimum_Indoor_Temp_Schedule=getattr(obj, 'Minimum_Indoor_Temperature_Schedule_Name', ''),
            Maximum_Indoor_Temperature=getattr(obj, 'Maximum_Indoor_Temperature', ''),
            Maximum_Indoor_Temp_Schedule=getattr(obj, 'Maximum_Indoor_Temperature_Schedule_Name', ''),
            Delta_Temperature=getattr(obj, 'Delta_Temperature', ''),
            Delta_Temp_Schedule=getattr(obj, 'Delta_Temperature_Schedule_Name', ''),
            Minimum_Outdoor_Temperature=getattr(obj, 'Minimum_Outdoor_Temperature', ''),
            Minimum_Outdoor_Temp_Schedule=getattr(obj, 'Minimum_Outdoor_Temperature_Schedule_Name', ''),
            Maximum_Outdoor_Temperature=getattr(obj, 'Maximum_Outdoor_Temperature', ''),
            Maximum_Outdoor_Temp_Schedule=getattr(obj, 'Maximum_Outdoor_Temperature_Schedule_Name', ''),
            Maximum_Wind_Speed=getattr(obj, 'Maximum_Wind_Speed', '')
        ))
    return vents

def parse_lights(idf):
    lights = []
    for obj in idf.idfobjects['LIGHTS']:
        lights.append(idf_Lights(
            Name=obj.Name,
            Zone_or_Space_Name=obj.Zone_or_ZoneList_or_Space_or_SpaceList_Name,
            Schedule_Name=obj.Schedule_Name,
            Design_Level_Calculation_Method=obj.Design_Level_Calculation_Method,
            Lighting_Level=getattr(obj, 'Lighting_Level', ''),
            Watts_per_Zone_Floor_Area=getattr(obj, 'Watts_per_Zone_Floor_Area', ''),
            Watts_per_Person=getattr(obj, 'Watts_per_Person', ''),
            Return_Air_Fraction=getattr(obj, 'Return_Air_Fraction', ''),
            Fraction_Radiant=getattr(obj, 'Fraction_Radiant', ''),
            Fraction_Visible=getattr(obj, 'Fraction_Visible', ''),
            Fraction_Replaceable=getattr(obj, 'Fraction_Replaceable', ''),
            End_Use_Subcategory=getattr(obj, 'End_Use_Subcategory', '')
        ))
    return lights

def parse_window_shading(idf):
    controls = []
    for obj in idf.idfobjects['WINDOWSHADINGCONTROL']:
        controls.append(idf_WindowShadingControl(
            Name=obj.Name,
            Zone_Name=obj.Zone_Name,
            Shading_Control_Sequence=getattr(obj, 'Shading_Control_Sequence_Number', ''),
            Shading_Type=obj.Shading_Type,
            Construction_with_Shading_Name=getattr(obj, 'Construction_with_Shading_Name', ''),
            Shading_Control_Type=obj.Shading_Control_Type,
            Schedule_Name=getattr(obj, 'Schedule_Name', ''),
            Setpoint=getattr(obj, 'Setpoint', ''),
            Shading_Control_Is_Scheduled=getattr(obj, 'Shading_Control_Is_Scheduled', ''),
            Glare_Control_Is_Active=getattr(obj, 'Glare_Control_Is_Active', ''),
            Shading_Device_Material_Name=getattr(obj, 'Shading_Device_Material_Name', ''),
            Slat_Angle_Control_Type=obj.Type_of_Slat_Angle_Control_for_Blinds,
            Slat_Angle_Schedule_Name=getattr(obj, 'Slat_Angle_Schedule_Name', ''),
            Setpoint_2=getattr(obj, 'Setpoint_2', ''),
            Daylighting_Control_Object_Name=getattr(obj, 'Daylighting_Control_Object_Name', ''),
            Multiple_Surface_Control_Type=obj.Multiple_Surface_Control_Type,
            Fenestration_Surface_1_Name=getattr(obj, 'Fenestration_Surface_1_Name', ''),
            Fenestration_Surface_2_Name=getattr(obj, 'Fenestration_Surface_2_Name', ''),
            Fenestration_Surface_3_Name=getattr(obj, 'Fenestration_Surface_3_Name', ''),
            Fenestration_Surface_4_Name=getattr(obj, 'Fenestration_Surface_4_Name', ''),
            Fenestration_Surface_5_Name=getattr(obj, 'Fenestration_Surface_5_Name', ''),
            Fenestration_Surface_6_Name=getattr(obj, 'Fenestration_Surface_6_Name', ''),
            Fenestration_Surface_7_Name=getattr(obj, 'Fenestration_Surface_7_Name', ''),
            Fenestration_Surface_8_Name=getattr(obj, 'Fenestration_Surface_8_Name', ''),
            Fenestration_Surface_9_Name=getattr(obj, 'Fenestration_Surface_9_Name', ''),
            Fenestration_Surface_10_Name=getattr(obj, 'Fenestration_Surface_10_Name', '')
        ))
    return controls

def delete_external_interface(idf_path):
    IDF.setiddname(IDD_PATH)
    idf = IDF(idf_path)

    external_interface = idf.idfobjects['ExternalInterface']

    if external_interface:
        external_exist = external_interface[0]
        idf.removeidfobject(external_exist)

    idf.save()