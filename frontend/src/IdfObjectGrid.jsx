import React, { useContext, useState, useEffect } from 'react';
import { AppContext } from './AppContext';

// Function to format Output:Variable
function formatOutputVariable(variable) {
    return `Output:Variable,
    ${variable.keyValue},    !- Key Value
    ${variable.variableName},    !- Variable Name
    ${variable.reportingFrequency},    !- Reporting Frequency
    ${variable.scheduleName};    !- Schedule Name`;
}

// Function to format EMS Actuator
function formatEmsActuator(actuator) {
    return `EnergyManagementSystem:Actuator,
    ${actuator.name},    !- Name
    ${actuator.actuatedComponentUniqueName},    !- Actuated Component Unique Name
    ${actuator.actuatedComponentType},    !- Actuated Component Type
    ${actuator.actuatedComponentControlType};    !- Actuated Component Control Type`;
}

// Function to format EMS Sensor
function formatEmsSensor(sensor) {
    return `EnergyManagementSystem:Sensor,
    ${sensor.name},    !- Name
    ${sensor.outputVariableOrOutputMeterIndexKeyName},    !- Output:Variable or Output:Meter Index Key Name
    ${sensor.outputVariableOrOutputMeterName};    !- Output:Variable or Output:Meter Name`;
}

// Function to format FMU Actuator
function formatFmuActuator(actuator) {
    return `ExternalInterface:FunctionalMockupUnitExport:To:Actuator,
    ${actuator.name},    !- Name
    ${actuator.actuatedComponentUniqueName},    !- Actuated Component Unique Name
    ${actuator.actuatedComponentType},    !- Actuated Component Type
    ${actuator.actuatedComponentControlType},    !- Actuated Component Control Type
    ${actuator.fmuVariableName},    !- FMU Variable Name
    ${actuator.initialValue};    !- Initial Value`;
}

// Function to format FMU From Variable
function formatFmuFromVariable(variable) {
    return `ExternalInterface:FunctionalMockupUnitExport:From:Variable,
    ${variable.outputVariableIndexKeyName},    !- Output:Variable Index Key Name
    ${variable.outputVariableName},    !- OutputVariable Name
    ${variable.fmuVariableName};    !- FMU Variable Name`;
}

// Function to format FMU To Variable
function formatFmuToVariable(variable) {
    return `ExternalInterface:FunctionalMockupUnitExport:To:Variable,
    ${variable.name},    !- Name
    ${variable.fmuVariableName},    !- FMU Variable Name
    ${variable.initialValue};    !- Initial Value`;
}

// Function to format FMU Schedule
function formatFmuSchedule(schedule) {
    return `ExternalInterface:FunctionalMockupUnitExport:To:Schedule,
    ${schedule.scheduleName},    !- Schedule Name
    ${schedule.scheduleTypeLimitsNames},    !- Schedule Type Limits Names
    ${schedule.fmuVariableName},    !- FMU Variable Name
    ${schedule.initialValue};    !- Initial Value`;
}

// Function to format EMS Program
function formatEmsProgram(program) {
    let formatted = `EnergyManagementSystem:Program,\n    ${program.name},    !- Name\n`;
    program.programLines.forEach((line, index) => {
        formatted += `    ${line},    !- Program Line ${index + 1}\n`;
    });
    return `${formatted.trim()};`;
}

// Function to format EMS Program Calling Manager
function formatEmsProgramCallingManager(manager) {
    let formatted = `EnergyManagementSystem:ProgramCallingManager,\n    ${manager.name},    !- Name\n    ${manager.energyPlusModelCallingPoint},    !- EnergyPlus Model Calling Point\n`;
    manager.programNames.forEach((programName, index) => {
        formatted += `    ${programName},    !- Program Name ${index + 1}\n`;
    });
    return `${formatted.trim()};`;
}

// Function to format objects based on type
function formatObject(type, obj) {
    switch (type) {
        case 'current_output_variables':
            return formatOutputVariable(obj);
        case 'current_ems_actuators':
            return formatEmsActuator(obj);
        case 'current_ems_sensors':
            return formatEmsSensor(obj);
        case 'current_fmu_actuators':
            return formatFmuActuator(obj);
        case 'current_fmu_from_variables':
            return formatFmuFromVariable(obj);
        case 'current_fmu_to_variables':
            return formatFmuToVariable(obj);
        case 'current_fmu_schedules':
            return formatFmuSchedule(obj);
        case 'current_ems_programs':
            return formatEmsProgram(obj);
        case 'current_ems_program_calling_managers':
            return formatEmsProgramCallingManager(obj);
        default:
            return JSON.stringify(obj, null, 2); // Fallback to JSON display
    }
}

function IdfObjectGrid({ idfObjects, openModal, section, refreshData, removeObject }) {
    const { selection, updateSelection, actionMinMax, updateActionMinMax } = useContext(AppContext);

    const gridTitles = {
        'Output:Variable': 'current_output_variables',
        'EnergyManagementSystem:Actuator': 'current_ems_actuators',
        'EnergyManagementSystem:Sensor': 'current_ems_sensors',
        'EnergyManagementSystem:Program': 'current_ems_programs',
        'EnergyManagementSystem:ProgramCallingManager': 'current_ems_program_calling_managers',
        'ExternalInterface:FunctionalMockupUnitExport:To:Actuator': 'current_fmu_actuators',
        'ExternalInterface:FunctionalMockupUnitExport:From:Variable': 'current_fmu_from_variables',
        'ExternalInterface:FunctionalMockupUnitExport:To:Variable': 'current_fmu_to_variables',
        'ExternalInterface:FunctionalMockupUnitExport:To:Schedule': 'current_fmu_schedules'
    };

    const key = gridTitles[section];
    const sectionObjects = idfObjects ? idfObjects[key] : null;

    const handleSelectionChange = (id, type) => {
        updateSelection(id, type);
    };

    const handleDelete = async (key, obj) => {
        let confirmDelete = true;
        if (key === 'current_output_variables') {
            confirmDelete = window.confirm(
                'Warning: If you delete this variable you will remove the EMS Sensors or the External From Variables that are associated with this variable.'
            );
        } else if (key === 'current_ems_programs') {
            confirmDelete = window.confirm(
                'Warning: If you delete this program you will remove the Program Calling Managers or the other EMS Programs that are associated with this program.'
            );
        } else if (key === 'current_fmu_to_variables' || key === 'current_fmu_actuators') {
            confirmDelete = window.confirm(
                'Warning: If you delete this variable you will remove the Programs that contain this variable and also the calling managers that are associated with these programs.'
            );
        }

        if (!confirmDelete) return;

        try {
            await removeObject(`http://localhost:5000/model_editor/remove_${key.slice(8)}`, obj);
            alert('Object Removed Succesfully')
            refreshData();
        } catch (error) {
            console.error('Error while removing object:', error);
            alert(error);
        }
    };

    const handleActionMinMaxChange = (variable, type, value) => {
        updateActionMinMax(variable, type, value);
    };

    const buttonStyle = {
        marginRight: '10px',
        border: '1px solid red',
        backgroundColor: 'white',
        color: 'red',
        borderRadius: '8px',
        width: '20px',
        height: '20px',
        textAlign: 'center',
        lineHeight: '20px',
        cursor: 'pointer'
    };

    const inputStyle = {
        width: '100px', // Increase the width of the input fields
        marginRight: '10px',
    };

    return (
        <div>
            <h3>
                {section}
                <button style={{ marginLeft: '10px' }} onClick={() => openModal(section)}>
                    Add
                </button>
            </h3>
            <div style={{ border: '1px solid black', padding: '10px' }}>
                {idfObjects ? (
                    sectionObjects && sectionObjects.length > 0 ? (
                        sectionObjects.map((obj) => (
                            <div key={obj.id} style={{ display: 'flex', alignItems: 'center' }}>
                                <button
                                    style={buttonStyle}
                                    onClick={() => handleDelete(key, obj)}
                                >
                                    -
                                </button>
                                <pre style={{ flex: 1 }}>{formatObject(key, obj)}</pre>
                                {key === 'current_fmu_from_variables' && (
                                    <div>
                                        <label>
                                            <input
                                                type="radio"
                                                name={`type_${obj.id}`}
                                                value="observation"
                                                checked={selection[obj.id] === 'observation'}
                                                onChange={() => handleSelectionChange(obj.id, 'observation')}
                                            />
                                            Observation
                                        </label>
                                        <label>
                                            <input
                                                type="radio"
                                                name={`type_${obj.id}`}
                                                value="reward"
                                                checked={selection[obj.id] === 'reward'}
                                                onChange={() => handleSelectionChange(obj.id, 'reward')}
                                            />
                                            Reward
                                        </label>
                                    </div>
                                )}
                                {(key === 'current_fmu_to_variables' || key === 'current_fmu_actuators') && (
                                    <div style={{ display: 'flex', alignItems: 'center' }}>
                                        <label>
                                            Min:
                                            <input
                                                type="number"
                                                value={actionMinMax[obj.fmuVariableName]?.min || ''}
                                                onChange={(e) => handleActionMinMaxChange(obj.fmuVariableName, 'min', e.target.value)}
                                                style={inputStyle}
                                                onBlur={(e) => handleActionMinMaxChange(obj.fmuVariableName, 'min', e.target.value || -1000)}
                                            />
                                        </label>
                                        <label>
                                            Max:
                                            <input
                                                type="number"
                                                value={actionMinMax[obj.fmuVariableName]?.max || ''}
                                                onChange={(e) => handleActionMinMaxChange(obj.fmuVariableName, 'max', e.target.value)}
                                                style={inputStyle}
                                                onBlur={(e) => handleActionMinMaxChange(obj.fmuVariableName, 'max', e.target.value || 1000)}
                                            />
                                        </label>
                                    </div>
                                )}
                            </div>
                        ))
                    ) : (
                        <p>No {section} objects in the IDF</p>
                    )
                ) : (
                    <p>No IDF uploaded</p>
                )}
            </div>
        </div>
    );
}

export default IdfObjectGrid;