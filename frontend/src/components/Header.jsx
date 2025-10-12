import React, { useState } from 'react';
import UploadModal from './UploadModal';
import './Header.css';

export default function Header({ onImageUploaded }) {
  const [showUploadModal, setShowUploadModal] = useState(false);

  const handleUploadSuccess = (newImage) => {
    setShowUploadModal(false);
    if (onImageUploaded) {
      onImageUploaded(newImage);
    }
  };

  return (
    <>
      <header className="app-header">
        <div className="header-content">
          <h1 className="site-title">NEIL Gallery</h1>
          <button 
            className="upload-btn"
            onClick={() => setShowUploadModal(true)}
          >
            Upload Image
          </button>
        </div>
      </header>
      
      {showUploadModal && (
        <UploadModal 
          onClose={() => setShowUploadModal(false)}
          onUploadSuccess={handleUploadSuccess}
        />
      )}
    </>
  );
}