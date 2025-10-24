import React, { useState, useEffect } from 'react';
import { ConfigProvider } from 'antd';
import esES from 'antd/locale/es_ES';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import { authService } from './services/authService';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    setIsAuthenticated(authService.isAuthenticated());
  }, []);

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
  };

  return (
    <ConfigProvider locale={esES}>
      {isAuthenticated ? (
        <Dashboard onLogout={handleLogout} />
      ) : (
        <Login onLoginSuccess={handleLoginSuccess} />
      )}
    </ConfigProvider>
  );
}

export default App;