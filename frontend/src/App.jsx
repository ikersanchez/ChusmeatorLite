import React, { useState } from 'react';
import IntroScreen from './components/IntroScreen';
import ChusmeatorMap from './components/Map/MapContainer';

function App() {
  const [showMap, setShowMap] = useState(false);

  return (
    <div className="App">
      <IntroScreen onComplete={() => setShowMap(true)} />
      {showMap && <ChusmeatorMap />}
    </div>
  );
}

export default App;
