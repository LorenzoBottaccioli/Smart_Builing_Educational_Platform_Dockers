import React, { createContext, useState, useEffect } from 'react';
import axios from 'axios';

const AppContext = createContext();

const AppProvider = ({ children }) => {
  const [idfObjects, setIdfObjects] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState({ idf: '', epw: '' });
  const [filesUploaded, setFilesUploaded] = useState(false);
  const [selection, setSelection] = useState({});
  const [actionMinMax, setActionMinMax] = useState({});
  const [scheduleTypeLimits, setScheduleTypeLimits] = useState({});
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  useEffect(() => {
    const storedFiles = localStorage.getItem('uploadedFiles');
    if (storedFiles) {
      setUploadedFiles(JSON.parse(storedFiles));
      setFilesUploaded(true);
    }
  }, []);

  const fetchIdfObjects = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:5000/model_editor/get_objects');
      const data = response.data;
      setIdfObjects(data);

      // Extract and set schedule type limits
      const limits = {};
      data.existing_schedule_type_limits.forEach(limit => {
        limits[limit.name] = {
          min: parseFloat(limit.lowerLimitValue),
          max: parseFloat(limit.upperLimitValue)
        };
      });
      setScheduleTypeLimits(limits);

    } catch (error) {
      console.error('Error fetching objects:', error);
      setIdfObjects({});
    } finally {
      setLoading(false);
    }
  };

  const resetSession = async () => {
    try {
      const response = await axios.delete('http://localhost:5000/model_editor/reset_session');
      const data = response.data;
      alert(data.message || 'Session Reset Done.');
      setFilesUploaded(false);
      setUploadedFiles({ idf: '', epw: '' });
      setIdfObjects('');
      setSelection({});
      setActionMinMax({});
      setScheduleTypeLimits({});
      localStorage.removeItem('uploadedFiles');
    } catch (error) {
      console.error('Error resetting session:', error);
      alert('Failed to reset session');
    }
  };

  const updateUploadedFiles = (files) => {
    setUploadedFiles(files);
    setFilesUploaded(true);
    localStorage.setItem('uploadedFiles', JSON.stringify(files));
    fetchIdfObjects(); // Fetch objects after uploading files
  };

  const removeObject = async (url, data) => {
    try {
      await axios.delete(url, { data });
      fetchIdfObjects(); // Refresh the data after deletion
    } catch (error) {
      console.error('Error removing object:', error);
      alert('Failed to remove object');
    }
  };

  const updateSelection = (id, type) => {
    setSelection((prevSelection) => ({
      ...prevSelection,
      [id]: type,
    }));
  };

  const updateActionMinMax = (variable, type, value) => {
    setActionMinMax(prevState => ({
      ...prevState,
      [variable]: {
        ...prevState[variable],
        [type]: value
      }
    }));
  };

  return (
    <AppContext.Provider value={{ 
      idfObjects, 
      uploadedFiles, 
      fetchIdfObjects, 
      resetSession, 
      filesUploaded, 
      updateUploadedFiles, 
      removeObject, 
      selection, 
      updateSelection, 
      actionMinMax, 
      updateActionMinMax,
      scheduleTypeLimits,
      loading, 
      uploadProgress, 
      setUploadProgress
    }}>
      {children}
    </AppContext.Provider>
  );
};

export { AppProvider, AppContext };
