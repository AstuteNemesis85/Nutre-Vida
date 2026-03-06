import { AnimatePresence, motion } from 'framer-motion';
import { createContext, useContext, useEffect, useState } from 'react';
import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import styled from 'styled-components';

// Components
import AIHealthCoach from './components/AIHealthCoach/AIHealthCoach';
import FoodAnalysis from './components/Analysis/FoodAnalysis';
import Login from './components/Auth/Login';
import ConnectionStatus from './components/Common/ConnectionStatus';
import ErrorBoundary from './components/Common/ErrorBoundary';
import Toast from './components/Common/Toast';
import Dashboard from './components/Dashboard/Dashboard';
import MealHistory from './components/History/MealHistory';
import MealPlan from './components/MealPlan/MealPlan';
import Navigation from './components/Navigation/Navigation';

// Context
const AppContext = createContext();

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
};

// Styled Components
const AppContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
  position: relative;
  overflow-x: hidden;
`;

const MainContent = styled(motion.main)`
  min-height: 100vh;
  padding-top: ${props => props.isAuthenticated ? '80px' : '0'};
  transition: padding-top 0.3s ease;
`;

const BackgroundEffects = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: -1;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: 
      radial-gradient(circle at 20% 80%, rgba(102, 126, 234, 0.1) 0%, transparent 50%),
      radial-gradient(circle at 80% 20%, rgba(118, 75, 162, 0.1) 0%, transparent 50%),
      radial-gradient(circle at 40% 40%, rgba(72, 187, 120, 0.05) 0%, transparent 50%);
    animation: backgroundShift 20s ease-in-out infinite;
  }
  
  @keyframes backgroundShift {
    0%, 100% { transform: translateX(0) translateY(0); }
    25% { transform: translateX(-10px) translateY(-10px); }
    50% { transform: translateX(10px) translateY(10px); }
    75% { transform: translateX(-5px) translateY(15px); }
  }
`;

// Configuration
const GOOGLE_CLIENT_ID = "710741263207-6c73gn9lsqt9b109dglhmis5r5nte9vd.apps.googleusercontent.com";
const BASE_URL = window.location.hostname === 'localhost'
  ? "http://localhost:8000"
  : "http://127.0.0.1:8000";

function App() {
  // State
  const [user, setUser] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('offline');
  const [toast, setToast] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Toast function
  const showToast = (message, type = 'info', duration = 5000) => {
    setToast({ message, type, id: Date.now() });
    setTimeout(() => setToast(null), duration);
  };

  // Connection management
  const testConnection = async () => {
    try {
      const response = await fetch(`${BASE_URL}/health`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
        signal: AbortSignal.timeout(5000)
      });

      if (response.ok) {
        setConnectionStatus('online');
        return true;
      } else {
        throw new Error(`Server responded with ${response.status}`);
      }
    } catch (error) {
      setConnectionStatus('offline');
      console.warn('Connection test failed:', error.message);
      return false;
    }
  };

  // Session management
  const initSession = async () => {
    if (connectionStatus === 'offline') {
      showToast("Cannot create session while offline", 'error');
      return false;
    }

    try {
      const response = await fetch(`${BASE_URL}/sessions/`, {
        method: "POST",
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) {
        throw new Error(`Session creation failed: ${response.status}`);
      }

      const data = await response.json();
      setSessionId(data.session_id);
      localStorage.setItem('sessionId', data.session_id);
      return true;
    } catch (error) {
      console.error("Session creation error:", error);
      showToast("Failed to create session: " + error.message, 'error');
      return false;
    }
  };

  // Authentication
  const login = async (userData) => {
    if (connectionStatus === 'offline') {
      showToast("Cannot sign in while offline. Please check your connection.", 'error');
      return false;
    }

    try {
      const response = await fetch(`${BASE_URL}/users/google`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(userData)
      });

      if (!response.ok) {
        throw new Error(`Authentication failed: ${response.status}`);
      }

      const userResponse = await response.json();
      setUser(userResponse);
      localStorage.setItem('userId', userResponse.id);
      showToast(`Welcome, ${userData.name || userData.email}!`, 'success');
      return true;
    } catch (error) {
      console.error("Authentication error:", error);
      showToast("Authentication failed: " + error.message, 'error');
      return false;
    }
  };

  const logout = () => {
    setUser(null);
    setSessionId(null);
    localStorage.removeItem('userId');
    localStorage.removeItem('sessionId');
    showToast("Logged out successfully", 'info');
  };

  const updateUser = (updatedUserData) => {
    setUser(updatedUserData);
  };

  // Initialize app
  useEffect(() => {
    const initializeApp = async () => {
      setIsLoading(true);
      
      // Test connection
      const connected = await testConnection();
      
      if (connected) {
        // Initialize session
        const storedSessionId = localStorage.getItem('sessionId');
        if (storedSessionId) {
          setSessionId(storedSessionId);
        } else {
          await initSession();
        }

        // Restore user session
        const storedUserId = localStorage.getItem('userId');
        if (storedUserId) {
          try {
            const response = await fetch(`${BASE_URL}/users/${storedUserId}`);
            if (response.ok) {
              const userData = await response.json();
              setUser(userData);
            } else {
              localStorage.removeItem('userId');
            }
          } catch (error) {
            console.error("Failed to restore user session:", error);
            localStorage.removeItem('userId');
          }
        }
      }
      
      setIsLoading(false);
    };

    initializeApp();

    // Set up periodic connection check
    const connectionInterval = setInterval(testConnection, 30000);
    return () => clearInterval(connectionInterval);
  }, []);

  // Context value
  const contextValue = {
    user,
    sessionId,
    connectionStatus,
    showToast,
    login,
    logout,
    updateUser,
    initSession,
    BASE_URL,
    GOOGLE_CLIENT_ID
  };

  if (isLoading) {
    return (
      <AppContainer>
        <BackgroundEffects />
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          flexDirection: 'column',
          gap: '20px'
        }}>
          <div className="spinner"></div>
          <motion.h2
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="gradient-text"
            style={{ fontFamily: 'Orbitron, monospace' }}
          >
            INITIALIZING FITKIT
          </motion.h2>
        </div>
      </AppContainer>
    );
  }

  return (
    <AppContext.Provider value={contextValue}>
      <Router>
        <AppContainer>
          <BackgroundEffects />
          <ConnectionStatus status={connectionStatus} />
          
          {user && <Navigation />}
          
          <ErrorBoundary>
            <MainContent
              isAuthenticated={!!user}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5 }}
            >
              <AnimatePresence mode="wait">
                <Routes>
                  <Route 
                    path="/login" 
                    element={!user ? <Login /> : <Navigate to="/dashboard" replace />} 
                  />
                  <Route 
                    path="/dashboard" 
                    element={user ? <Dashboard /> : <Navigate to="/login" replace />} 
                  />
                  <Route 
                    path="/analyze" 
                    element={user ? <FoodAnalysis /> : <Navigate to="/login" replace />} 
                  />
                  <Route 
                    path="/history" 
                    element={user ? <MealHistory /> : <Navigate to="/login" replace />} 
                  />
                  <Route 
                    path="/meal-plan" 
                    element={user ? <MealPlan /> : <Navigate to="/login" replace />} 
                  />
                  <Route 
                    path="/" 
                    element={<Navigate to={user ? "/dashboard" : "/login"} replace />} 
                  />
                </Routes>
              </AnimatePresence>
            </MainContent>

            {user && <AIHealthCoach />}
          </ErrorBoundary>
          
          <AnimatePresence>
            {toast && (
              <Toast
                key={toast.id}
                message={toast.message}
                type={toast.type}
                onClose={() => setToast(null)}
              />
            )}
          </AnimatePresence>
        </AppContainer>
      </Router>
    </AppContext.Provider>
  );
}

export default App;
