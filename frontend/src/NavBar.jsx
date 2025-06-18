import React from 'react';
import { Link } from 'react-router-dom';
import './NavBar.css';

export default function NavBar() {
  return (
    <nav className="navbar">
      <ul className="nav-links">
        <li className="nav-item">
          <Link to="/" className="nav-link">Home</Link>
        </li>
        <li className="nav-item">
          <Link to="/surrogate_modeling" className="nav-link">Surrogate Modeling</Link>
        </li>
        <li className="nav-item">
          <Link to="/model_editor" className="nav-link">Model Editor</Link>
        </li>
        <li className="nav-item">
          <Link to="/model_converter" className="nav-link">EnergyPlusToFMU</Link>
        </li>
        <li className="nav-item">
          <Link to="/simulator" className="nav-link">Gym Trainer</Link>
        </li>
        <li className="nav-item">
          <Link to="/grafana" className="nav-link">Grafana</Link>
        </li>
        <li className="nav-item">
          <Link to="/openhab" className="nav-link">OpenHAB</Link>
        </li>
        <li className="nav-item">
          <Link to="/controller" className="nav-link">Controller</Link>
        </li>
        <li className="nav-item">
          <Link to="/controlled_simulation" className="nav-link">Controlled Simulation</Link>
        </li>
        <li className="nav-item">
          <Link to="/base_simulation" className="nav-link">Base Simulation</Link>
        </li>
      </ul>
    </nav>
  );
}