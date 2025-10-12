import React, {useEffect, useState, useImperativeHandle, forwardRef} from 'react';
import Masonry from 'react-masonry-css';
import './MasonryGrid.css';

const MasonryGrid = forwardRef((props, ref) => {
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchImages = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('http://localhost:8000/images');
      if (!res.ok) {
        if (res.status === 503) {
          throw new Error('Backend services not available');
        }
        throw new Error(`Server error: ${res.status}`);
      }
      const data = await res.json();
      setImages(data || []);
    } catch (err) {
      console.error('Failed to fetch images:', err);
      setError(err.message || 'Failed to load images');
      setImages([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchImages();
  }, []);

  useImperativeHandle(ref, () => ({
    refreshImages: fetchImages
  }));

  const breakpointCols = {
    default: 4,
    1100: 3,
    700: 2,
    500: 1
  };

  if (loading) return <div className="masonry-status">Loading images…</div>;
  
  if (error) return (
    <div className="masonry-status error">
      <p>Unable to load images</p>
      <small>{error}</small>
      <button onClick={fetchImages} className="retry-btn">Try Again</button>
    </div>
  );

  if (images.length === 0) return (
    <div className="masonry-status empty">
      <p>No images uploaded yet</p>
      <small>Click "Upload Image" to get started</small>
    </div>
  );

  return (
    <Masonry
      breakpointCols={breakpointCols}
      className="masonry-grid"
      columnClassName="masonry-grid_column"
    >
      {images.map((img, idx) => (
        <div key={idx} className="masonry-item">
          <img
            src={img.object_url}
            alt={img.alt || img.name || `image-${idx}`}
            loading="lazy"
            className="masonry-img"
          />
        </div>
      ))}
    </Masonry>
  );
});

export default MasonryGrid;
