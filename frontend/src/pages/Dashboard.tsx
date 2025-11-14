/**
 * =============================================================================
 * DASHBOARD PRINCIPAL
 * =============================================================================
 * Panel de control con estadísticas en tiempo real
 * =============================================================================
 */

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from '../components/layout/MainLayout';

// Pages
import DashboardHome from './DashboardHome';
import Pacientes from './Pacientes';
import Embarazos from './Embarazos';
import Controles from './Controles';
import Calculadoras from './Calculadoras';

const Dashboard: React.FC = () => {
  return (
    <MainLayout>
      <Routes>
        <Route path="/" element={<DashboardHome />} />
        <Route path="/pacientes" element={<Pacientes />} />
        <Route path="/embarazos" element={<Embarazos />} />
        <Route path="/controles" element={<Controles />} />
        <Route path="/calculadoras" element={<Calculadoras />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </MainLayout>
  );
};

export default Dashboard;
