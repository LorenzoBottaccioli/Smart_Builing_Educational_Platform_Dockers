// SurrogateModeling.jsx
import React, { useState, useEffect, useContext } from 'react';
import { Plus, Minus, Menu } from 'lucide-react';
import SurrogateObjectGrid from './SurrogateObjectGrid';
import { AppContext } from './AppContext';

const surrogateTypes = [
  { key: 'materials', label: 'Material' },
  { key: 'constructions', label: 'Construction' },
  { key: 'fenestration_surfaces', label: 'FenestrationSurface:Detailed' },
  { key: 'zone_ventilations', label: 'ZoneVentilation:DesignFlowRate' },
  { key: 'lights', label: 'Lights' },
  { key: 'window_shading_controls', label: 'WindowShadingControl' }
];

export default function SurrogateModeling() {
  const { filesUploaded } = useContext(AppContext);
  const [data, setData] = useState({});
  const [openSections, setOpenSections] = useState({});
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // initialize collapse state
  useEffect(() => {
    const init = {};
    surrogateTypes.forEach(t => (init[t.key] = false));
    setOpenSections(init);
  }, []);

  // fetch data on mount and whenever filesUploaded toggles
  useEffect(() => {
    fetch('http://localhost:5000/surrogate_modeling/get_surrogate_objects')
      .then(res => res.json())
      .then(json => setData(json))
      .catch(err => console.error(err));

    // reset collapse & sidebar
    const init = {};
    surrogateTypes.forEach(t => (init[t.key] = false));
    setOpenSections(init);
    setSidebarOpen(true);
  }, [filesUploaded]);

  const toggleSection = key =>
    setOpenSections(prev => ({ ...prev, [key]: !prev[key] }));
  const toggleSidebar = () => setSidebarOpen(open => !open);

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw' }}>
      {sidebarOpen && (
        <aside
          style={{
            width: '40%',
            minWidth: '200px',
            maxWidth: '600px',
            background: '#f3f3f3',
            borderRight: '1px solid #ddd',
            padding: '1rem',
            overflowY: 'auto'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 style={{ margin: 0 }}>Surrogate Objects</h2>
            <button onClick={toggleSidebar} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
              <Minus size={20} />
            </button>
          </div>

          {surrogateTypes.map(t => (
            <div key={t.key} style={{ marginTop: '1rem' }}>
              <div
                onClick={() => toggleSection(t.key)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  cursor: 'pointer',
                  padding: '0.5rem',
                  borderRadius: '4px'
                }}
              >
                {openSections[t.key] ? (
                  <Minus style={{ marginRight: 8 }} />
                ) : (
                  <Plus style={{ marginRight: 8 }} />
                )}
                <span>{t.label}</span>
              </div>
              {openSections[t.key] && (
                <div style={{ marginTop: '0.5rem' }}>
                  <SurrogateObjectGrid objects={data[t.key] || []} type={t.key} />
                </div>
              )}
            </div>
          ))}
        </aside>
      )}

      <main style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        {!sidebarOpen && (
          <button
            onClick={toggleSidebar}
            style={{
              position: 'absolute',
              top: 10,
              left: 10,
              zIndex: 10,
              background: 'white',
              border: '1px solid #ccc',
              borderRadius: '4px',
              padding: '4px',
              cursor: 'pointer'
            }}
          >
            <Menu size={20} />
          </button>
        )}
        {/* El key here hace que el iframe se remonte cada vez que filesUploaded cambie */}
        <iframe
          key={filesUploaded ? 'loaded' : 'empty'}
          title="Surrogate Notebook"
          src="http://localhost:8889/notebooks/SurrogateNotebook.ipynb"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            border: 'none'
          }}
        />
      </main>
    </div>
  );
}


