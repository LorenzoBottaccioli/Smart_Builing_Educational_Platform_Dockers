import React from 'react';

const WelcomePage = () => {
  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h1>Welcome to the Smart Building Educational Platform</h1>
      <p>
        This application allows you to upload EnergyPlus IDF and EPW files, and convert them into FMU models.
        Follow the instructions below to get started:
      </p>
      <ol style={{ textAlign: 'left', maxWidth: '600px', margin: '0 auto' }}>
        <li>Upload your IDF and EPW files using the file upload section.</li>
        <li>After uploading, you can edit the model in the model editor section as you want.</li>
        <li>After having made all the modifications download your new file or fill the configuration parameters as needed</li>
        <li>Use the model converter section to export the model.</li>
        <li>Verify that your config file is set as desired</li>
        <li>Click the "Export Model" button to convert the model and use it as needed.</li>
      </ol>
      <p>
        Remember to check all your parameters before exporting the model, click the reset session button if you want to start over
      </p>
      <p>
        Please ensure your files are correctly formatted and follow the EnergyPlus standards. If you encounter any issues,
        refer to the documentation or contact support.
      </p>
    </div>
  );
};

export default WelcomePage;