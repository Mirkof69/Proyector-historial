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
import Ecografias from './Ecografias';
import Laboratorio from './Laboratorio';
import Citas from './Citas';
import Partos from './Partos';
import CalculadorasAvanzadas from './CalculadorasAvanzadas';
import Reportes from './Reportes';

const Dashboard: React.FC = () => {
  return (
    <MainLayout>
      <Routes>
        <Route path="/" element={<DashboardHome />} />
        <Route path="/usuarios" element={<Usuarios />} />
        <Route path="/pacientes" element={<PacientesNew />} />
        <Route path="/embarazos" element={<EmbarazosNew />} />
        <Route path="/controles" element={<ControlesNew />} />
        <Route path="/ecografias" element={<Ecografias />} />
        <Route path="/laboratorio" element={<Laboratorio />} />
        <Route path="/citas" element={<Citas />} />
        <Route path="/partos" element={<Partos />} />
        <Route path="/calculadoras" element={<CalculadorasNew />} />
        <Route path="/calculadoras-avanzadas" element={<CalculadorasAvanzadas />} />
        <Route path="/reportes" element={<Reportes />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </MainLayout>
  );
};

export default Dashboard;
