import React, { useReducer, useEffect, useMemo, useCallback } from 'react';
import { Button, Space, Card, Typography, Badge, Drawer } from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import { PlusOutlined, UserOutlined } from '@ant-design/icons';
import { usuariosService, Usuario } from '../../services/usuariosService';
import FormularioUsuario from './FormularioUsuario';
import ModalCambiarPassword from './ModalCambiarPassword';
import UsuariosTable from './components/UsuariosTable';
import UsuarioDetailDrawer from './components/UsuarioDetailDrawer';
import UsuariosStatsCards from './components/UsuariosStatsCards';
import UsuariosFilterBar from './components/UsuariosFilterBar';
import './Usuarios.css';
import { incluyeTexto } from '../../utils/texto';
import { contarPorRol } from '../../config/roles';

const { Title } = Typography;

// El mapa de roles vive ahora en `config/roles`: estaba copiado aqui, en la
// tabla y en el detalle, y las tres copias se habian quedado atras respecto a
// los cinco roles del backend.
const plusIcon = <PlusOutlined />;

interface UsuariosState {
  usuarios: Usuario[];
  loading: boolean;
  searchText: string;
  filtroRol?: string;
  filtroEstado?: boolean;
  drawerVisible: boolean;
  modalPasswordVisible: boolean;
  usuarioEditando: Usuario | null;
  usuarioVisualizando: Usuario | null;
  modoEdicion: boolean;
}

type UsuariosAction =
  | { type: 'SET_USUARIOS'; payload: Usuario[] }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_SEARCH_TEXT'; payload: string }
  | { type: 'SET_FILTRO_ROL'; payload: string | undefined }
  | { type: 'SET_FILTRO_ESTADO'; payload: boolean | undefined }
  | { type: 'OPEN_DRAWER'; payload: { usuario?: Usuario | null; modoEdicion?: boolean } }
  | { type: 'CLOSE_DRAWER' }
  | { type: 'OPEN_PASSWORD_MODAL'; payload: Usuario }
  | { type: 'CLOSE_PASSWORD_MODAL' }
  | { type: 'SET_VIEW_USER'; payload: Usuario | null }
  | { type: 'CLEAR_FILTERS' };

const initialState: UsuariosState = {
  usuarios: [],
  loading: false,
  searchText: '',
  filtroRol: undefined,
  filtroEstado: undefined,
  drawerVisible: false,
  modalPasswordVisible: false,
  usuarioEditando: null,
  usuarioVisualizando: null,
  modoEdicion: false,
};

function usuariosReducer(state: UsuariosState, action: UsuariosAction): UsuariosState {
  switch (action.type) {
    case 'SET_USUARIOS': return { ...state, usuarios: action.payload };
    case 'SET_LOADING': return { ...state, loading: action.payload };
    case 'SET_SEARCH_TEXT': return { ...state, searchText: action.payload };
    case 'SET_FILTRO_ROL': return { ...state, filtroRol: action.payload };
    case 'SET_FILTRO_ESTADO': return { ...state, filtroEstado: action.payload };
    case 'OPEN_DRAWER': return { ...state, drawerVisible: true, usuarioEditando: action.payload.usuario || null, modoEdicion: action.payload.modoEdicion || false };
    case 'CLOSE_DRAWER': return { ...state, drawerVisible: false, usuarioEditando: null };
    case 'OPEN_PASSWORD_MODAL': return { ...state, modalPasswordVisible: true, usuarioEditando: action.payload };
    case 'CLOSE_PASSWORD_MODAL': return { ...state, modalPasswordVisible: false, usuarioEditando: null };
    case 'SET_VIEW_USER': return { ...state, usuarioVisualizando: action.payload };
    case 'CLEAR_FILTERS': return { ...state, searchText: '', filtroRol: undefined, filtroEstado: undefined };
    default: return state;
  }
}

const Usuarios: React.FC = () => {
  const { message: antdMessage } = useAntdApp();
  const [state, dispatch] = useReducer(usuariosReducer, initialState);
  const { usuarios, loading, searchText, filtroRol, filtroEstado, drawerVisible, modalPasswordVisible, usuarioEditando, usuarioVisualizando, modoEdicion } = state;

  const cargarUsuarios = useCallback(async () => {
    dispatch({ type: 'SET_LOADING', payload: true });
    try {
      const params: any = {};
      if (filtroRol) params.rol = filtroRol;
      if (filtroEstado !== undefined) params.activo = filtroEstado;
      if (searchText) params.search = searchText;

      const data = await usuariosService.getAll(params);
      dispatch({ type: 'SET_USUARIOS', payload: data });
      antdMessage.success(`${data.length} usuarios cargados correctamente`);
    } catch (error: any) {
      antdMessage.error('Error al cargar usuarios');
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [filtroRol, filtroEstado, searchText, antdMessage]);

  useEffect(() => { cargarUsuarios(); }, [cargarUsuarios]);

  // Las cuentas por rol salen del catalogo unico. Antes estaban escritas a
  // mano y una de ellas comparaba con 'enfermero', que el backend no usa
  // nunca: la tarjeta de enfermeras marcaba 0 hubiera las que hubiera.
  const estadisticas = useMemo(() => ({
    total: usuarios.length,
    activos: usuarios.filter(u => u.activo).length,
    porRol: contarPorRol(usuarios),
  }), [usuarios]);

  const handleNuevoUsuario = useCallback(() => { dispatch({ type: 'OPEN_DRAWER', payload: { usuario: null, modoEdicion: false } }); }, []);
  const handleEditarUsuario = useCallback((usuario: Usuario) => { dispatch({ type: 'OPEN_DRAWER', payload: { usuario, modoEdicion: true } }); }, []);
  const handleVisualizarUsuario = useCallback((usuario: Usuario) => { dispatch({ type: 'SET_VIEW_USER', payload: usuario }); }, []);
  const handleEliminarUsuario = useCallback(async (id: number) => {
    try { await usuariosService.delete(id); antdMessage.success('Usuario eliminado correctamente'); cargarUsuarios(); }
    catch (error: any) { antdMessage.error('Error al eliminar usuario'); }
  }, [cargarUsuarios, antdMessage]);
  const handleToggleActivo = useCallback(async (usuario: Usuario) => {
    try {
      if (usuario.activo) { await usuariosService.desactivar(usuario.id!); antdMessage.success('Usuario desactivado correctamente'); }
      else { await usuariosService.activar(usuario.id!); antdMessage.success('Usuario activado correctamente'); }
      cargarUsuarios();
    } catch (error: any) { antdMessage.error('Error al cambiar estado del usuario'); }
  }, [cargarUsuarios, antdMessage]);
  const handleRestablecerMfa = useCallback(async (usuario: Usuario) => {
    try { const r = await usuariosService.restablecerMfa(usuario.id!); antdMessage.success(r.mensaje); }
    catch (error: any) { antdMessage.error('No se pudo restablecer el MFA'); }
  }, [antdMessage]);
  const handleCambiarPassword = useCallback((usuario: Usuario) => { dispatch({ type: 'OPEN_PASSWORD_MODAL', payload: usuario }); }, []);
  const handleCloseDrawer = useCallback((reload?: boolean) => { dispatch({ type: 'CLOSE_DRAWER' }); if (reload) cargarUsuarios(); }, [cargarUsuarios]);
  const handleClosePasswordModal = useCallback((reload?: boolean) => { dispatch({ type: 'CLOSE_PASSWORD_MODAL' }); if (reload) cargarUsuarios(); }, [cargarUsuarios]);
  const handleBuscar = useCallback(() => { cargarUsuarios(); }, [cargarUsuarios]);
  const handleLimpiarFiltros = useCallback(() => { dispatch({ type: 'SET_SEARCH_TEXT', payload: '' }); dispatch({ type: 'SET_FILTRO_ROL', payload: undefined }); dispatch({ type: 'SET_FILTRO_ESTADO', payload: undefined }); }, []);

  const usuariosFiltrados = useMemo(() => {
    return usuarios.filter(usuario => {
      const matchSearch = !searchText || incluyeTexto(usuario.nombre, searchText) || incluyeTexto(usuario.email, searchText) || incluyeTexto(usuario.apellido_paterno, searchText);
      const matchRol = !filtroRol || usuario.rol === filtroRol;
      const matchEstado = filtroEstado === undefined || usuario.activo === filtroEstado;
      return matchSearch && matchRol && matchEstado;
    });
  }, [usuarios, searchText, filtroRol, filtroEstado]);

  return (
    <div className="usuarios-container page-container" style={{ padding: 24 }}>
      <UsuariosStatsCards estadisticas={estadisticas} />

      <UsuariosFilterBar
        searchText={searchText}
        filtroRol={filtroRol}
        filtroEstado={filtroEstado}
        onSearchChange={(val) => dispatch({ type: 'SET_SEARCH_TEXT', payload: val })}
        onFiltroRolChange={(val) => dispatch({ type: 'SET_FILTRO_ROL', payload: val })}
        onFiltroEstadoChange={(val) => dispatch({ type: 'SET_FILTRO_ESTADO', payload: val })}
        onBuscar={handleBuscar}
        onLimpiar={handleLimpiarFiltros}
      />

      <Card
        title={<Space><UserOutlined /><Title level={4} style={{ margin: 0 }}>Gestión de Usuarios</Title><Badge count={usuariosFiltrados.length} showZero color="#1890ff" /></Space>}
        extra={<Button type="primary" icon={plusIcon} onClick={handleNuevoUsuario}>Nuevo Usuario</Button>}
      >
        <UsuariosTable
          usuarios={usuariosFiltrados}
          loading={loading}
          onVisualizar={handleVisualizarUsuario}
          onEditar={handleEditarUsuario}
          onCambiarPassword={handleCambiarPassword}
          onEliminar={handleEliminarUsuario}
          onToggleActivo={handleToggleActivo}
          onRestablecerMfa={handleRestablecerMfa}
        />
      </Card>

      <Drawer title={modoEdicion ? 'Editar Usuario' : 'Nuevo Usuario'} width={720} open={drawerVisible} onClose={() => handleCloseDrawer(false)} destroyOnHidden>
        <FormularioUsuario usuario={usuarioEditando} onClose={handleCloseDrawer} />
      </Drawer>

      {usuarioEditando && (
        <ModalCambiarPassword open={modalPasswordVisible} usuario={usuarioEditando} onClose={handleClosePasswordModal} />
      )}

      <UsuarioDetailDrawer usuario={usuarioVisualizando} open={!!usuarioVisualizando} onClose={() => dispatch({ type: 'SET_VIEW_USER', payload: null })} />
    </div>
  );
};

export default Usuarios;
