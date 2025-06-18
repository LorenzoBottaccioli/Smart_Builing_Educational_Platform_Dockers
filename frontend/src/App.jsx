// src/App.jsx
import React from 'react';
import { BrowserRouter as Router, useLocation } from 'react-router-dom';
import Header from './Header';
import NavBar from './NavBar';
import Footer from './Footer';
import ModelEditor from './ModelEditor';
import ModelConverter from './ModelConverter';
import FileUploadBar from './FileUploadBar';
import WelcomePage from './WelcomePage';
import SurrogateModeling from './SurrogateModeling';
import Simulator from './Simulator';
import Grafana from './Grafana';
import Openhab from './Openhab';
// Importamos los nuevos pages
import ControlledSimulator from './ControlledSimulator';
import BaseSimulation from './BaseSimulation';
import Controller from './Controller';
import { AppProvider } from './AppContext';

function AppContent() {
  const { pathname } = useLocation();

  return (
    <div style={{ position: 'relative', height: 'calc(100vh - 150px)' }}>
      {/* Surrogate Modeling */}
      <div
        style={{
          display: pathname === '/surrogate_modeling' ? 'block' : 'none',
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
        }}
      >
        <SurrogateModeling />
      </div>

      {/* Standard Simulator */}
      <div
        style={{
          display: pathname === '/simulator' ? 'block' : 'none',
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
        }}
      >
        <Simulator />
      </div>

      {/* Base Simulation */}
      <div
        style={{
          display: pathname === '/base_simulation' ? 'block' : 'none',
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
        }}
      >
        <BaseSimulation />
      </div>

      {/* Controlled Simulation */}
      <div
        style={{
          display: pathname === '/controlled_simulation' ? 'block' : 'none',
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
        }}
      >
        <ControlledSimulator />
      </div>

      {/* Controller */}
      <div
        style={{
          display: pathname === '/controller' ? 'block' : 'none',
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
        }}
      >
        <Controller />
      </div>

      {/* Grafana Dashboard */}
      <div
        style={{
          display: pathname === '/grafana' ? 'block' : 'none',
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
        }}
      >
        <Grafana />
      </div>

      {/* openHAB Interface */}
      <div
        style={{
          display: pathname === '/openhab' ? 'block' : 'none',
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
        }}
      >
        <Openhab />
      </div>

      {/* Views without iframe */}
      <div style={{ display: pathname === '/' ? 'block' : 'none' }}>
        <WelcomePage />
      </div>
      <div style={{ display: pathname === '/model_editor' ? 'block' : 'none' }}>
        <ModelEditor />
      </div>
      <div style={{ display: pathname === '/model_converter' ? 'block' : 'none' }}>
        <ModelConverter />
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <Router>
        <Header />
        <NavBar />
        <FileUploadBar />
        <AppContent />
      </Router>
    </AppProvider>
  );
}
