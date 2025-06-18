import React from 'react';
import NavBar from './NavBar';
import './Header.css'; // Make sure to include this CSS file

const Header = () => (
    <header className="header">
        <div className="header-content">
            <img src="/polito_logo.png" alt="Politecnico di Torino Logo" className="logo" />
            <div className="institution-details">
                <h1>Smart Building Educational Platform</h1>
                <h2>ICT in Building Design</h2>
            </div>
        </div>
    </header>
);

export default Header;