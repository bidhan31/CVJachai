import React, { useState, useEffect } from 'react';
import { Sparkles } from 'lucide-react';
import Home from './components/Home/Home';
import Shortlisting from './components/Shortlisting/Shortlisting';
import Results from './components/Results/Results';
import Optimization from './components/Optimization/Optimization';
import AnalysisResults from './components/AnalysisResults/AnalysisResults';
import Auth from './components/Auth/Auth';
import JobListing from './components/JobListing/JobListing';
import CreateJob from './components/JobListing/CreateJob';
import JobManagement from './components/JobListing/JobManagement';
import Navbar from './components/Common/Navbar';
import { GoogleOAuthProvider } from '@react-oauth/google';

function App() {
  // Use the Google Client ID from the environment, fallback to the default if not set
  const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || "1036628247859-0o1d664qrn16suiub66j1lv5lm6lle4t.apps.googleusercontent.com";
  const [view, setView] = useState('home'); // 'home', 'shortlisting', 'results', 'personalization', 'analysis_results', 'auth', 'find_job', 'create_job', or 'job_management'
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [authMode, setAuthMode] = useState('login'); // 'login' or 'signup'
  const [user, setUser] = useState(null);

  useEffect(() => {
    const savedUser = localStorage.getItem('cvjachai_user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
      setIsLoggedIn(true);
    }
  }, []);

  const [analysisData, setAnalysisData] = useState(null);

  const handleLogin = (data) => {
    console.log('Login successful, received data:', data);
    setIsLoggedIn(true);
    setUser(data);
    localStorage.setItem('cvjachai_user', JSON.stringify(data));
    setView('home');
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setUser(null);
    localStorage.removeItem('cvjachai_user');
    setView('home');
  };

  const navigateToProtected = (targetView) => {
    if (isLoggedIn) {
      setView(targetView);
    } else {
      setAuthMode('login');
      setView('auth');
    }
  };

  const renderView = () => {
    switch (view) {
      case 'analyzing':
        return (
          <div className="analyzing-screen" style={{ 
            height: '100vh', 
            display: 'flex', 
            flexDirection: 'column', 
            justifyContent: 'center', 
            alignItems: 'center',
            background: 'var(--bg-color)',
            color: 'white',
            textAlign: 'center'
          }}>
            <div className="processing-visual" style={{ marginBottom: '30px', position: 'relative' }}>
              <div className="pulse-ring"></div>
              <div className="pulse-ring" style={{ animationDelay: '0.5s' }}></div>
              <div className="pulse-ring" style={{ animationDelay: '1s' }}></div>
              <div className="ai-icon-large">
                <Sparkles size={60} color="var(--accent-cyan)" fill="var(--accent-cyan)" />
              </div>
            </div>
            <h1 style={{ fontSize: '2.5rem', marginBottom: '15px', letterSpacing: '-1px' }}>AI is analyzing resumes...</h1>
            <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '1.1rem', maxWidth: '500px' }}>
              Our neural networks are scanning for the best matches based on your criteria. This usually takes a few seconds.
            </p>
          </div>
        );
      case 'shortlisting':
        return (
          <Shortlisting
            onBack={() => setView('home')}
            token={user?.access || user?.access_token || user?.token}
            onStartAnalysis={() => setView('analyzing')}
            onAnalyze={(result) => {
              setAnalysisData(result);
              setView('results');
            }}
          />
        );
      case 'results':
        return (
          <Results
            data={analysisData}
            onBackToForm={() => setView('shortlisting')}
            onBackToHome={() => setView('home')}
          />
        );
      case 'personalization':
        return (
          <Optimization
            onBack={() => setView('home')}
            token={user?.access || user?.access_token || user?.token}
            onStartAnalysis={() => setView('analyzing')}
            onAnalyze={(result) => {
              setAnalysisData(result);
              setView('analysis_results');
            }}
          />
        );
      case 'analysis_results':
        return (
          <AnalysisResults
            data={analysisData}
            onBack={() => setView('personalization')}
            onBackToHome={() => setView('home')}
          />
        );
      case 'auth':
        return (
          <Auth
            mode={authMode}
            onToggleMode={() => setAuthMode(authMode === 'login' ? 'signup' : 'login')}
            onSuccess={handleLogin}
            onBack={() => setView('home')}
          />
        );
      case 'find_job':
        return (
          <JobListing 
            onBack={() => setView('home')} 
            onCreateJob={() => navigateToProtected('create_job')} 
          />
        );
      case 'create_job':
        return (
          <CreateJob 
            onBack={() => setView('home')} 
            token={user?.access || user?.access_token || user?.token} 
          />
        );
      case 'job_management':
        return (
          <JobManagement
            onBack={() => setView('home')}
            onPostJob={() => setView('create_job')}
            token={user?.access || user?.access_token || user?.token}
          />
        );
      default:
        return (
          <Home
            isLoggedIn={isLoggedIn}
            onStartShortlisting={() => navigateToProtected('shortlisting')}
            onStartPersonalization={() => navigateToProtected('personalization')}
            onFindJob={() => setView('find_job')}
            onCreateJob={() => navigateToProtected('create_job')}
            onLogin={() => { setAuthMode('login'); setView('auth'); }}
            onSignUp={() => { setAuthMode('signup'); setView('auth'); }}
            onLogout={handleLogout}
          />
        );
    }
  };

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <div className="app-container">
        {view !== 'auth' && (
          <Navbar 
            isLoggedIn={isLoggedIn}
            onLogout={handleLogout}
            onLogin={() => { setAuthMode('login'); setView('auth'); }}
            onSignUp={() => { setAuthMode('signup'); setView('auth'); }}
            onCreateJob={() => navigateToProtected('create_job')}
            onJobManagement={() => navigateToProtected('job_management')}
          />
        )}
        {renderView()}
      </div>
    </GoogleOAuthProvider>
  );
}

export default App;
