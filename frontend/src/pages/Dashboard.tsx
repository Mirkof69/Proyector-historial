/**
 * =============================================================================
 * DASHBOARD PRINCIPAL
 * =============================================================================
 */

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from '../components/layout/MainLayout';

// Pages
import DashboardHome from './DashboardHome';
import Usuarios from './Usuarios';
import PacientesNew from './PacientesNew';
import EmbarazosNew from './EmbarazosNew';
import ControlesNew from './ControlesNew';
import CalculadorasNew from './CalculadorasNew';

const Dashboard: React.FC = () => {
  return (
    <MainLayout>
      <Routes>
        <Route path="/" element={<DashboardHome />} />
        <Route path="/usuarios" element={<Usuarios />} />
        <Route path="/pacientes" element={<PacientesNew />} />
        <Route path="/embarazos" element={<EmbarazosNew />} />
        <Route path="/controles" element={<ControlesNew />} />
        <Route path="/calculadoras" element={<CalculadorasNew />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </MainLayout>
  );
};

export default Dashboard;
