import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import Demo from './pages/Demo';
import DemoProcess from './pages/DemoProcess';
import DemoTryOn from './pages/DemoTryOn';
import DemoRecommendations from './pages/DemoRecommendations';
import ColorPalettePage from './pages/ColorPalettePage';
import MonkColorPalettePage from './pages/MonkColorPalettePage';
import ResourcesPage from './pages/ResourcesPage';
import BlogPage from './pages/BlogPage';
import AboutPage from './pages/AboutPage';
import ContactPage from './pages/ContactPage';
import ErrorBoundary from './components/ErrorBoundary';
import useNetworkRecovery from './hooks/useNetworkRecovery';

function App() {
  const { isOnline, isRecovering } = useNetworkRecovery({
    onNetworkRestore: () => console.log('Network restored'),
    onNetworkLost: () => console.log('Network connection lost'),
  });

  return (
    <ErrorBoundary>
      {!isOnline && (
        <div className="fixed top-0 left-0 w-full p-4 bg-red-600 text-white text-center z-50">
          Network connection lost. {isRecovering ? 'Trying to reconnect...' : 'You are offline.'}
        </div>
      )}
      <Router future={{ v7_relativeSplatPath: true }}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/demo">
            <Route index element={<Demo />} />
            <Route path="process" element={<DemoProcess />} />
            <Route path="try-on" element={<DemoTryOn />} />
            <Route path="recommendations" element={<DemoRecommendations />} />
          </Route>
          <Route path="/colors/:skinTone" element={<ColorPalettePage />} />
          <Route path="/monk-colors/:monkId" element={<MonkColorPalettePage />} />
          <Route path="/resources" element={<ResourcesPage />} />
          <Route path="/blog" element={<BlogPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/contact" element={<ContactPage />} />
          <Route path="*" element={<LandingPage />} />
        </Routes>
      </Router>
    </ErrorBoundary>
  );
}

export default App;