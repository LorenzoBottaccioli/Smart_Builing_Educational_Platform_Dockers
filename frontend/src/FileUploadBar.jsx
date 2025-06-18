import React, { useState, useContext, useEffect } from 'react';
import { AppContext } from './AppContext';
import axios from 'axios';
import { ProgressBar } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';

function FileUploadBar() {
  const {
    updateUploadedFiles,
    uploadedFiles,
    filesUploaded,
    resetSession,
    setUploadProgress,
    uploadProgress,
  } = useContext(AppContext);

  const [idfFile, setIdfFile] = useState(null);
  const [epwFile, setEpwFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  // New state for updating EPW
  const [newEpwFile, setNewEpwFile] = useState(null);
  const [epwUpdating, setEpwUpdating] = useState(false);

  const handleFileChange = (e, setFile) => {
    setFile(e.target.files[0]);
  };

  const checkProgress = async () => {
    try {
      const { data } = await axios.get('http://localhost:5000/model_editor/progress');
      setUploadProgress(data.progress);
      if (data.progress >= 100) {
        setUploading(false);
      }
    } catch (err) {
      console.error('Error fetching progress:', err);
    }
  };

  useEffect(() => {
    let interval = null;
    if (uploading) {
      interval = setInterval(checkProgress, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [uploading]);

  const handleSubmit = async e => {
    e.preventDefault();
    if (!idfFile || !epwFile) {
      alert('Please select both IDF and EPW files.');
      return;
    }
    const formData = new FormData();
    formData.append('idf_file', idfFile);
    formData.append('epw_file', epwFile);

    setUploading(true);
    setUploadProgress(10);

    try {
      const { data } = await axios.post(
        'http://localhost:5000/model_editor/upload_files',
        formData
      );
      if (data.message) {
        updateUploadedFiles({ idf: idfFile.name, epw: epwFile.name });
        setUploadProgress(100);
        alert(data.message);
      } else {
        throw new Error(data.error || 'Unknown error');
      }
    } catch (err) {
      console.error(err);
      alert('Upload failed.');
      setUploadProgress(0);
    } finally {
      setUploading(false);
      setTimeout(() => setUploadProgress(0), 1000);
    }
  };

  const handleResetSession = async () => {
    try {
      await resetSession();
    } catch (err) {
      console.error('Error resetting session:', err);
      alert('Failed to reset session');
    }
  };

  const handleDownloadIdf = () => {
    window.open('http://localhost:5000/model_converter/get_idf', '_blank');
  };

  // New: update EPW in all FMUs
  const handleUpdateEpw = async () => {
    if (!newEpwFile) {
      alert('Please select a new EPW file first.');
      return;
    }
    const formData = new FormData();
    formData.append('epw', newEpwFile);

    setEpwUpdating(true);
    try {
      const { data } = await axios.post(
        'http://localhost:5000/model_converter/update_epw',
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      if (data.success) {
        alert(`EPW updated in ${data.updated} FMUs`);
      } else {
        throw new Error(data.error || 'Unknown error');
      }
    } catch (err) {
      console.error('Error updating EPW:', err);
      alert('Failed to update EPW');
    } finally {
      setEpwUpdating(false);
      setNewEpwFile(null);
    }
  };

  // New: clear InfluxDB
  const handleClearInflux = async () => {
    if (!window.confirm('Are you sure you want to clear InfluxDB?')) return;
    try {
      const { data } = await axios.post('http://localhost:5000/model_converter/clear_influx');
      if (data.success) {
        alert('InfluxDB databases cleared.');
      } else {
        throw new Error(data.error || 'Unknown error');
      }
    } catch (err) {
      console.error('Error clearing InfluxDB:', err);
      alert('Failed to clear InfluxDB');
    }
  };

  return (
    <div style={{ backgroundColor: '#f8f9fa', padding: '10px', borderBottom: '1px solid #dee2e6' }}>
      {filesUploaded ? (
        <>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <p>IDF File: {uploadedFiles.idf}</p>
              <p>EPW File: {uploadedFiles.epw}</p>
            </div>
            <div>
              <button onClick={handleResetSession} style={{ marginRight: '10px' }}>
                Reset Session
              </button>
              <button onClick={handleDownloadIdf} style={{ marginRight: '10px' }}>
                Download IDF
              </button>
            </div>
          </div>

          {/* New EPW update section */}
          <div style={{ marginTop: '10px', display: 'flex', alignItems: 'center' }}>
            <input
              type="file"
              accept=".epw"
              onChange={e => handleFileChange(e, setNewEpwFile)}
            />
            <button
              onClick={handleUpdateEpw}
              disabled={epwUpdating}
              style={{ marginLeft: '10px', marginRight: '10px' }}
            >
              {epwUpdating ? 'Updating EPW…' : 'Update EPW in FMUs'}
            </button>
            <button onClick={handleClearInflux}>
              Clear InfluxDB
            </button>
          </div>
        </>
      ) : (
        <form
          onSubmit={handleSubmit}
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
        >
          <label>
            IDF File:
            <input type="file" accept=".idf" onChange={e => handleFileChange(e, setIdfFile)} />
          </label>
          <label>
            EPW File:
            <input type="file" accept=".epw" onChange={e => handleFileChange(e, setEpwFile)} />
          </label>
          <button type="submit">Upload Files</button>
        </form>
      )}

      {uploading && (
        <div style={{ marginTop: '10px', width: '100%' }}>
          <ProgressBar now={uploadProgress} label={`${Math.round(uploadProgress)}%`} />
        </div>
      )}
    </div>
  );
}

export default FileUploadBar;
