import React, { useContext, useState, useEffect, useCallback } from 'react';
import IdfObjectGrid from './IdfObjectGrid';
import ModalComponent from './ModalComponent';
import { AppContext } from './AppContext';

function ModelEditor() {
  const {
    idfObjects,
    fetchIdfObjects,
    filesUploaded,
    removeObject
  } = useContext(AppContext);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalType, setModalType] = useState('');
  const [selectedSection, setSelectedSection] = useState('');

  const gridTitles = {
    'Output:Variable': 'current_output_variables',
    'EnergyManagementSystem:Actuator': 'current_ems_actuators',
    'EnergyManagementSystem:Sensor': 'current_ems_sensors',
    'EnergyManagementSystem:Program': 'current_ems_programs',
    'EnergyManagementSystem:ProgramCallingManager': 'current_ems_program_calling_managers',
    'ExternalInterface:FunctionalMockupUnitExport:From:Variable': 'current_fmu_from_variables',
    'ExternalInterface:FunctionalMockupUnitExport:To:Actuator': 'current_fmu_actuators',
    'ExternalInterface:FunctionalMockupUnitExport:To:Variable': 'current_fmu_to_variables',
    'ExternalInterface:FunctionalMockupUnitExport:To:Schedule': 'current_fmu_schedules',
  };

  useEffect(() => {
    if (!idfObjects) {
      fetchIdfObjects();
    }
  }, [idfObjects, fetchIdfObjects]);

  useEffect(() => {
    if (!idfObjects && filesUploaded) {
      fetchIdfObjects();
    }
  }, [idfObjects, filesUploaded, fetchIdfObjects]);

  const selectSection = (section) => {
    setSelectedSection(section);
  };

  const openModal = (type) => {
    setModalType(type);
    setIsModalOpen(true);
  };

  const closeModal = () => setIsModalOpen(false);

  const refreshData = useCallback(async () => {
    try {
      await fetchIdfObjects();
    } catch (error) {
      console.error('Error refreshing data:', error);
    }
  }, [fetchIdfObjects]);

  return (
      <div style={{ display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex' }}>
        <div style={{ width: '40%', borderRight: '1px solid gray', padding: '10px' }}>
          <h2>Navigation</h2>
          <ul>
            {Object.keys(gridTitles).map((section) => (
              <li
                key={section}
                onClick={() => selectSection(section)}
                style={{ cursor: 'pointer', padding: '5px', listStyleType: 'none' }}
              >
                {section}
              </li>
            ))}
          </ul>
        </div>

        <div style={{ width: '70%', padding: '10px' }}>
          <h1>Model Editor</h1>

          {!filesUploaded ? (
            <p>No IDF uploaded</p>
          ) : selectedSection ? (
            <IdfObjectGrid
              idfObjects={idfObjects}
              openModal={openModal}
              section={selectedSection}
              refreshData={refreshData}
              removeObject={removeObject}
            />
          ) : (
            <p>Please select a section</p>
          )}

          <ModalComponent
            isOpen={isModalOpen}
            closeModal={closeModal}
            type={modalType}
            onSubmitSuccess={refreshData}
            refreshData={refreshData}
            data={idfObjects}
          />
        </div>
      </div>
    </div>
  );
};

export default ModelEditor;