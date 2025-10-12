
import { useRef } from 'react'
import './App.css'
import Header from './components/Header'
import MasonryGrid from './components/MasonryGrid'

function App() {
  const masonryRef = useRef(null);

  const handleImageUploaded = (newImage) => {
    // Refresh the masonry grid when a new image is uploaded
    if (masonryRef.current && masonryRef.current.refreshImages) {
      masonryRef.current.refreshImages();
    }
  };

  return (
    <div className="app">
      <Header onImageUploaded={handleImageUploaded} />
      <main className="main-content">
        <MasonryGrid ref={masonryRef} />
      </main>
    </div>
  )
}

export default App
