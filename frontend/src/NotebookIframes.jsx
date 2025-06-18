// src/components/NotebookIframes.jsx
import React from 'react';
import { useLocation } from 'react-router-dom';

export default function NotebookIframes() {
  const { pathname } = useLocation();
  const showSurrogate   = pathname === '/surrogate_modeling';
  const showSimulator   = pathname === '/simulator';
  const showControlled  = pathname === '/controlled_simulation';
  const showBase        = pathname === '/base_simulation';
  const showController  = pathname === '/controller';

  const topOffset = 120; // Altura Header + NavBar + FileUploadBar

  return (
    <div style={{
      position:   'absolute',
      top:        topOffset,
      left:       0,
      right:      0,
      bottom:     0,
      zIndex:     0,
      display:    'flex',
    }}>
      {/* Surrogate */}
      {showSurrogate && (
        <div style={{ display: 'flex', width: '100%', height: '100%' }}>
          <div style={{ width: '40%', background: '#f3f3f3', overflow: 'auto' }}>
            {/* SurrogateModeling renderizado vía Routes */}
          </div>
          <iframe
            title="Surrogate Notebook"
            src="http://localhost:8889/tree/SurrogateNotebook.ipynb"
            style={{ width: '60%', height: '100%', border: 'none' }}
          />
        </div>
      )}

      {/* Simulator */}
      {showSimulator && (
        <div style={{ display: 'block', width: '100%', height: '100%' }}>
          <iframe
            title="Simulator Notebook"
            src="http://localhost:8887/notebooks/SimulatorNotebook.ipynb"
            style={{ width: '100%', height: '100%', border: 'none' }}
          />
        </div>
      )}

      {/* Controlled Simulation */}
      {showControlled && (
        <div style={{ display: 'block', width: '100%', height: '100%' }}>
          <iframe
            title="Controlled Simulation Notebook"
            src="http://localhost:8890/notebooks/ControlledSim.ipynb"
            style={{ width: '100%', height: '100%', border: 'none' }}
          />
        </div>
      )}

      {/* Base Simulation */}
      {showBase && (
        <div style={{ display: 'block', width: '100%', height: '100%' }}>
          <iframe
            title="Base Simulation Notebook"
            src="http://localhost:8891/notebooks/BaseSim.ipynb"
            style={{ width: '100%', height: '100%', border: 'none' }}
          />
        </div>
      )}

      {/* Controller */}
      {showController && (
        <div style={{ display: 'block', width: '100%', height: '100%' }}>
          <iframe
            title="Controller Notebook"
            src="http://localhost:8892/notebooks/Controller.ipynb"
            style={{ width: '100%', height: '100%', border: 'none' }}
          />
        </div>
      )}
    </div>
  );
}

