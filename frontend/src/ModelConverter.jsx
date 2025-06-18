import React, { useState, useContext, useEffect } from 'react';
import { AppContext } from './AppContext';
import axios from 'axios';
import { ProgressBar } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';

const ModelConverter = () => {
  const { idfObjects, fetchIdfObjects, selection, uploadedFiles, actionMinMax, scheduleTypeLimits, filesUploaded } = useContext(AppContext);
  const [startTime, setStartTime] = useState(0);
  const [warmupTime, setWarmupTime] = useState(3);
  const [finalTime, setFinalTime] = useState(24);
  const [timestep, setTimestep] = useState(6); // Default to 4 (15-minute intervals)

  const [observations, setObservations] = useState([]);
  const [rewards, setRewards] = useState([]);
  const [actions, setActions] = useState([]);
  const [exportProgress, setExportProgress] = useState(0);

  useEffect(() => {
    if (!idfObjects) {
      fetchIdfObjects();
    }
  }, [idfObjects, fetchIdfObjects]);

  useEffect(() => {
    if (idfObjects) {
      const fmuFromVariables = idfObjects.current_fmu_from_variables || [];
      const fmuToActuators = idfObjects.current_fmu_actuators || [];
      const fmuToVariables = idfObjects.current_fmu_to_variables || [];
      const fmuToSchedules = idfObjects.current_fmu_schedules || [];

      const obs = fmuFromVariables
        .filter(v => selection[v.id] === 'observation')
        .map(v => v.fmuVariableName);
      const rew = fmuFromVariables
        .filter(v => selection[v.id] === 'reward')
        .map(v => v.fmuVariableName);
      const act = [
        ...fmuToActuators.map(a => a.fmuVariableName),
        ...fmuToVariables.map(v => v.fmuVariableName),
        ...fmuToSchedules.map(s => s.fmuVariableName)
      ];

      setObservations(obs);
      setRewards(rew);
      setActions(act);
    }
  }, [idfObjects, selection]);

  const generateConfigPreview = () => {
  const dtype = 'np.float64';
  const stepSize = 3600 / timestep;
  const fmuPath = uploadedFiles.idf.replace('.idf', '.fmu');

  // Obtén el primer runperiod con seguridad
  const runperiod = (idfObjects.current_idf_runperiod && idfObjects.current_idf_runperiod[0]) || {};

  // Calcula actionMin y actionMax igual que antes...
  const actionMinArray = actions.map(a => {
    const sched = idfObjects.current_fmu_schedules?.find(s => s.fmuVariableName === a);
    const limitName = sched?.scheduleTypeLimitsNames;
    return limitName && scheduleTypeLimits[limitName]
      ? scheduleTypeLimits[limitName].min
      : actionMinMax[a]?.min ?? -1000;
  });
  const actionMaxArray = actions.map(a => {
    const sched = idfObjects.current_fmu_schedules?.find(s => s.fmuVariableName === a);
    const limitName = sched?.scheduleTypeLimitsNames;
    return limitName && scheduleTypeLimits[limitName]
      ? scheduleTypeLimits[limitName].max
      : actionMinMax[a]?.max ?? 1000;
  });

  return `
import numpy as np

parameter = {}
# fmi_gym parameter
parameter['seed'] = 1
parameter['store_data'] = True

# fmu parameter
dtype = ${dtype}
parameter['fmu_step_size'] = ${stepSize}
parameter['fmu_path'] = '${fmuPath}'
parameter['fmu_start_time'] = ${startTime} * 60 * 60 * 24
parameter['fmu_warmup_time'] = ${warmupTime} * 60 * 60 * 24
parameter['fmu_final_time'] = ${finalTime} * 60 * 60 * 24

# data exchange parameter
parameter['action_names'] = ${JSON.stringify(actions)}
parameter['action_min'] = np.array(${JSON.stringify(actionMinArray)}, dtype=${dtype})
parameter['action_max'] = np.array(${JSON.stringify(actionMaxArray)}, dtype=${dtype})
parameter['observation_names'] = ${JSON.stringify(observations)}
parameter['reward_names'] = ${JSON.stringify(rewards)}

`.trim();
};


  const handleExport = async () => {
    setExportProgress(10); // Start export progress
    try {
      const response = await axios.post('http://localhost:5000/model_converter/export_model', {
        startTime,
        warmupTime,
        finalTime,
        timestep,
        observations,
        rewards,
        actions,
        actionMin: actions.map(a => actionMinMax[a]?.min ?? -1000),
        actionMax: actions.map(a => actionMinMax[a]?.max ?? 1000)
      }, { 
        responseType: 'blob',
        onDownloadProgress: progressEvent => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setExportProgress(percentCompleted);
        }
      });

      if (response.data) {
        const blob = new Blob([response.data], { type: 'application/zip' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'conversion_bundle.zip';
        document.body.appendChild(a);
        a.click();
        a.remove();
        setExportProgress(100); // Complete export progress
        setTimeout(() => setExportProgress(0), 1000); // Reset progress after a short delay
        alert('Model exported successfully');
      } else {
        alert('Failed to export model');
        setExportProgress(0); // Reset progress if failed
      }
    } catch (error) {
      console.error('Error exporting model:', error);
      alert('Failed to export model');
      setExportProgress(0); // Reset progress if error occurs
    }
  };

  return (
    <div style={{ display: 'flex' }}>
      <div style={{ width: '30%', borderRight: '1px solid gray', padding: '10px' }}>
        <h2>Model Converter</h2>
        <label>
          Timestep (number of measurements per hour):
          <input type="number" value={timestep} onChange={(e) => setTimestep(e.target.value)} />
        </label>
        <br />
        <label>
          Start Time (days):
          <input type="number" value={startTime} onChange={(e) => setStartTime(e.target.value)} />
        </label>
        <br />
        <label>
          Warmup Time (days):
          <input type="number" value={warmupTime} onChange={(e) => setWarmupTime(e.target.value)} />
        </label>
        <br />
        <label>
          Final Time (days):
          <input type="number" value={finalTime} onChange={(e) => setFinalTime(e.target.value)} />
        </label>
        <br />
        {filesUploaded && (
          <button onClick={handleExport}>Export Model</button>
        )}
        {exportProgress > 0 && (
          <div style={{ marginTop: '10px', width: '100%' }}>
            <ProgressBar now={exportProgress} label={`${exportProgress}%`} />
          </div>
        )}
      </div>
      <div style={{ width: '70%', padding: '10px' }}>
        <h2>Config Preview</h2>
        {uploadedFiles.idf ? (
          <pre>{generateConfigPreview()}</pre>
        ) : (
          <p>No IDF uploaded</p>
        )}
      </div>
    </div>
  );
};

export default ModelConverter;