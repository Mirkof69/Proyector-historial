import React from 'react';

const Auditoria: React.FC = () => {

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold mb-4">Auditoría del Sistema</h1>
      <div className="bg-white dark:bg-zinc-800 rounded-lg p-6 shadow">
        <p className="text-zinc-600 dark:text-zinc-400">
          Módulo de auditoría. Conecta con la API de auditoría del backend para visualizar
          los registros de actividad, cambios y accesos del sistema.
        </p>
      </div>
    </div>
  );
};

export default Auditoria;
