import auditoriaService from './auditoriaService';

// Alias para compatibilidad con DashboardHome y otros componentes
const activityLogsService = {
  getAccessLogs: async (filters?: any, page = 1, pageSize = 20) => {
    return auditoriaService.getAuditRecords(filters, page, pageSize);
  },
  getRegistros: async (filters?: any, page = 1, pageSize = 20) => {
    return auditoriaService.getAuditRecords(filters, page, pageSize);
  },
  getActividadReciente: async (filters?: any, page = 1, pageSize = 10) => {
    return auditoriaService.getAuditRecords(filters, page, pageSize);
  },
};

export default activityLogsService;
