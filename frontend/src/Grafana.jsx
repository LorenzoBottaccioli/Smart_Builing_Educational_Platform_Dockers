// src/pages/simulator.jsx
import React, { useContext } from 'react';
import { AppContext } from './AppContext';

export default function Grafana() {
  const { filesUploaded } = useContext(AppContext);

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw' }}>
      <main style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        <iframe
          key={filesUploaded ? 'loaded' : 'empty'}
          title="Grafana"
          src="http://localhost:3000"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            border: 'none',
          }}
        />
      </main>
    </div>
);
}