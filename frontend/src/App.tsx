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

function App() {
  return (
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
  );
}

export default App;