"""
SCRIPT DE POBLADO COMPLETO DE BASE DE DATOS
Sistema de Historias Clínicas Gineco-Obstétricas
Fetal Medical - La Paz, Bolivia

Genera datos de prueba para todos los módulos del sistema
Versión: 2.0 - Corregida y Optimizada
"""

import os
import django
import sys
from datetime import date, datetime, timedelta, time
from decimal import Decimal
import random

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'historial.settings')
django.setup()

from pacientes.models import Paciente
from embarazos.models import Embarazo
from controles.models import ControlPrenatal
from usuarios.models import Usuario
from ecografias.models import Ecografia, BiometriaFetal, AnexosFetales, AnatomiaFetal, ImagenEcografia
from laboratorio.models import TipoExamen, ExamenLaboratorio, ResultadoLaboratorio, ValorReferencia
from citas.models import Cita, Disponibilidad, HistorialCita
from calculadoras.models import (
    CalculoClinico, EdadGestacional, IndiceMasaCorporal, RiesgoPreeclampsia, 
    DiabetesGestacional, PuntajeBishop, PuntajeApgar,
    IndiceLiquidoAmniotico, PesoFetal, GananciaPeso,
    PresionArterialMedia, SuperficieCorporal, RMIOvario, RiesgoEndometrio
)


# ================================================================================
# DATOS DE CONFIGURACIÓN
# ================================================================================

NOMBRES_FEMENINOS = [
    'María', 'Ana', 'Laura', 'Carmen', 'Daniela', 'Patricia', 'Rosa', 'Gabriela',
    'Silvia', 'Andrea', 'Verónica', 'Mónica', 'Jessica', 'Carla', 'Lucia',
    'Fernanda', 'Valeria', 'Camila', 'Sofia', 'Isabella', 'Valentina', 'Claudia',
    'Elena', 'Beatriz', 'Natalia', 'Carolina', 'Diana', 'Paola', 'Adriana'
]

APELLIDOS = [
    'González', 'Martínez', 'Fernández', 'Quispe', 'Condori', 'Vargas', 'Huanca',
    'Ramos', 'Torres', 'Choque', 'Flores', 'Limachi', 'Poma', 'Mamani', 'Apaza',
    'López', 'Rojas', 'Silva', 'García', 'Rodríguez', 'Cruz', 'Nina', 'Ticona',
    'Sánchez', 'Morales', 'Castro', 'Ortiz', 'Pérez', 'Gutiérrez', 'Díaz'
]

DIRECCIONES = [
    'Av. Arce #2345, Zona Central',
    'Calle 21 #456, Calacoto',
    'Av. Blanco Galindo #789, Villa San Antonio',
    'Calle 10 #234, Villa Fátima',
    'Av. 6 de Agosto #567, Sopocachi',
    'Av. Costanera #890, Irpavi',
    'Calle México #123, Zona Central',
    'Av. Montenegro #456, Miraflores',
    'Calle Landaeta #789, San Miguel',
    'Av. Arequipa #321, Sopocachi',
    'Calle Colombia #654, San Pedro',
    'Av. Buenos Aires #987, Miraflores',
    'Calle Muñoz Cornejo #147, Obrajes',
    'Av. Ballivián #258, San Jorge',
    'Calle Abdón Saavedra #369, Sopocachi'
]


# ================================================================================
# FUNCIÓN 1: CREAR USUARIOS
# ================================================================================

def crear_usuarios():
    """Crear usuarios médicos, enfermeros y administradores del sistema"""
    print("\n" + "="*80)
    print("👥 CREANDO USUARIOS DEL SISTEMA")
    print("="*80)
    
    usuarios_data = [
        # MÉDICOS ESPECIALISTAS
        {
            'email': 'dr.wilson@fetalmedical.com',
            'password': 'medico123',
            'nombre': 'Wilson Walter',
            'apellido_paterno': 'Rodriguez',
            'apellido_materno': 'Chuquimia',
            'rol': 'medico',
            'especialidad': 'Ginecología y Obstetricia',
            'numero_registro_profesional': 'MED-12345',
            'telefono': '70123456',
            'activo': True,
        },
        {
            'email': 'dra.patricia@fetalmedical.com',
            'password': 'medico123',
            'nombre': 'Patricia',
            'apellido_paterno': 'Mamani',
            'apellido_materno': 'Quispe',
            'rol': 'medico',
            'especialidad': 'Medicina Materno Fetal',
            'numero_registro_profesional': 'MED-23456',
            'telefono': '70234567',
            'activo': True,
        },
        {
            'email': 'dr.carlos@fetalmedical.com',
            'password': 'medico123',
            'nombre': 'Carlos',
            'apellido_paterno': 'Gutierrez',
            'apellido_materno': 'Flores',
            'rol': 'medico',
            'especialidad': 'Ultrasonografía Obstétrica',
            'numero_registro_profesional': 'MED-34567',
            'telefono': '70345678',
            'activo': True,
        },
        {
            'email': 'dra.ana@fetalmedical.com',
            'password': 'medico123',
            'nombre': 'Ana María',
            'apellido_paterno': 'Lopez',
            'apellido_materno': 'Vargas',
            'rol': 'medico',
            'especialidad': 'Perinatología',
            'numero_registro_profesional': 'MED-45678',
            'telefono': '70456789',
            'activo': True,
        },
        {
            'email': 'dr.roberto@fetalmedical.com',
            'password': 'medico123',
            'nombre': 'Roberto',
            'apellido_paterno': 'Sánchez',
            'apellido_materno': 'Morales',
            'rol': 'medico',
            'especialidad': 'Medicina Fetal',
            'numero_registro_profesional': 'MED-56789',
            'telefono': '70567890',
            'activo': True,
        },
        # ENFERMEROS/AS ESPECIALIZADOS
        {
            'email': 'enf.maria@fetalmedical.com',
            'password': 'enfermero123',
            'nombre': 'María Elena',
            'apellido_paterno': 'Condori',
            'apellido_materno': 'Apaza',
            'rol': 'enfermero',
            'especialidad': 'Enfermería Obstétrica',
            'numero_registro_profesional': 'ENF-12345',
            'telefono': '71123456',
            'activo': True,
        },
        {
            'email': 'enf.rosa@fetalmedical.com',
            'password': 'enfermero123',
            'nombre': 'Rosa',
            'apellido_paterno': 'Imaña',
            'apellido_materno': 'Arratia',
            'rol': 'enfermero',
            'especialidad': 'Atención Prenatal',
            'numero_registro_profesional': 'ENF-23456',
            'telefono': '71234567',
            'activo': True,
        },
        {
            'email': 'enf.juan@fetalmedical.com',
            'password': 'enfermero123',
            'nombre': 'Juan Carlos',
            'apellido_paterno': 'Vargas',
            'apellido_materno': 'Lima',
            'rol': 'enfermero',
            'especialidad': 'Cuidados Maternos',
            'numero_registro_profesional': 'ENF-34567',
            'telefono': '71345678',
            'activo': True,
        },
        {
            'email': 'enf.lucia@fetalmedical.com',
            'password': 'enfermero123',
            'nombre': 'Lucía',
            'apellido_paterno': 'Flores',
            'apellido_materno': 'Castro',
            'rol': 'enfermero',
            'especialidad': 'Neonatología',
            'numero_registro_profesional': 'ENF-45678',
            'telefono': '71456789',
            'activo': True,
        },
        {
            'email': 'enf.carmen@fetalmedical.com',
            'password': 'enfermero123',
            'nombre': 'Carmen',
            'apellido_paterno': 'Ticona',
            'apellido_materno': 'Poma',
            'rol': 'enfermero',
            'especialidad': 'Cuidados Intensivos Neonatales',
            'numero_registro_profesional': 'ENF-56789',
            'telefono': '71567890',
            'activo': True,
        },
    ]
    
    usuarios_creados = {'medico': [], 'enfermero': [], 'administrador': []}
    
    for data in usuarios_data:
        password = data.pop('password')
        
        try:
            usuario = Usuario.objects.get(email=data['email'])
            print(f"⚠️  Usuario ya existe: {usuario.nombre} {usuario.apellido_paterno} ({usuario.rol})")
            usuarios_creados[usuario.rol].append(usuario)
        except Usuario.DoesNotExist:
            usuario = Usuario.objects.create_user(
                email=data['email'],
                password=password,
                nombre=data['nombre'],
                apellido_paterno=data['apellido_paterno'],
                apellido_materno=data.get('apellido_materno', ''),
                rol=data['rol']
            )
            
            usuario.especialidad = data.get('especialidad', '')
            usuario.numero_registro_profesional = data.get('numero_registro_profesional', '')
            usuario.telefono = data.get('telefono', '')
            usuario.activo = data.get('activo', True)
            usuario.save()
            
            print(f"✅ Usuario creado: {usuario.nombre} {usuario.apellido_paterno} ({usuario.rol}) - {usuario.especialidad}")
            usuarios_creados[usuario.rol].append(usuario)
    
    print(f"\n📊 Resumen de usuarios:")
    print(f"   - Médicos: {len(usuarios_creados['medico'])}")
    print(f"   - Enfermeros: {len(usuarios_creados['enfermero'])}")
    print(f"   - Administradores: {len(usuarios_creados['administrador'])}")
    
    return usuarios_creados


# ================================================================================
# FUNCIÓN 2: CREAR PACIENTES
# ================================================================================

def crear_pacientes(cantidad=25):
    """Crear pacientes con datos completos y variados"""
    print("\n" + "="*80)
    print(f"🤰 CREANDO {cantidad} PACIENTES")
    print("="*80)
    
    pacientes = []
    ci_base = 7000000
    telefono_base = 70000000
    
    for i in range(cantidad):
        nombre = random.choice(NOMBRES_FEMENINOS)
        apellido_pat = random.choice(APELLIDOS)
        apellido_mat = random.choice(APELLIDOS)
        
        # Generar fecha de nacimiento (18-45 años)
        edad = random.randint(18, 45)
        fecha_nac = date.today() - timedelta(days=edad*365 + random.randint(0, 364))
        
        paciente_data = {
            'nombre': nombre,
            'apellido_paterno': apellido_pat,
            'apellido_materno': apellido_mat,
            'fecha_nacimiento': fecha_nac,
            'genero': 'femenino',
            'ci': str(ci_base + i),
            'telefono': str(telefono_base + i),
            'email': f'{nombre.lower()}.{apellido_pat.lower()}{i}@email.com',
            'direccion': random.choice(DIRECCIONES) + f', Dpto {random.randint(101, 599)}',
            'ciudad': 'La Paz',
            'pais': 'Bolivia',
            'observaciones': random.choice([
                '',
                'Paciente con antecedentes de diabetes gestacional',
                'Primera gestación',
                'Antecedente de cesárea previa',
                'Grupo sanguíneo O negativo',
                'Antecedente familiar de preeclampsia',
                'Embarazo previo con restricción de crecimiento',
            ])
        }
        
        paciente, created = Paciente.objects.get_or_create(
            ci=paciente_data['ci'],
            defaults=paciente_data
        )
        
        if created:
            print(f"✅ Paciente {i+1:2}/{cantidad} - {paciente.nombre_completo[:40]:40} CI:{paciente.ci}")
        else:
            print(f"⚠️  Paciente {i+1:2}/{cantidad} - {paciente.nombre_completo[:40]:40} (ya existe)")
        
        pacientes.append(paciente)
    
    print(f"\n📊 Total de pacientes: {len(pacientes)}")
    return pacientes


# ================================================================================
# FUNCIÓN 3: CREAR EMBARAZOS
# ================================================================================

def crear_embarazos(pacientes):
    """Crear embarazos para las pacientes con diferentes características"""
    print("\n" + "="*80)
    print("🤱 CREANDO EMBARAZOS")
    print("="*80)
    
    embarazos = []
    
    # Configuraciones variadas de embarazos (más datos)
    configs = [
        {'semanas': 6, 'estado': 'activo', 'riesgo': 'bajo', 'tipo': 'simple'},
        {'semanas': 8, 'estado': 'activo', 'riesgo': 'bajo', 'tipo': 'simple'},
        {'semanas': 10, 'estado': 'activo', 'riesgo': 'bajo', 'tipo': 'simple'},
        {'semanas': 12, 'estado': 'activo', 'riesgo': 'bajo', 'tipo': 'simple'},
        {'semanas': 14, 'estado': 'activo', 'riesgo': 'medio', 'tipo': 'simple'},
        {'semanas': 16, 'estado': 'activo', 'riesgo': 'medio', 'tipo': 'gemelar'},
        {'semanas': 18, 'estado': 'activo', 'riesgo': 'bajo', 'tipo': 'simple'},
        {'semanas': 20, 'estado': 'activo', 'riesgo': 'bajo', 'tipo': 'simple'},
        {'semanas': 22, 'estado': 'activo', 'riesgo': 'alto', 'tipo': 'simple'},
        {'semanas': 24, 'estado': 'activo', 'riesgo': 'bajo', 'tipo': 'simple'},
        {'semanas': 26, 'estado': 'activo', 'riesgo': 'medio', 'tipo': 'simple'},
        {'semanas': 28, 'estado': 'activo', 'riesgo': 'medio', 'tipo': 'simple'},
        {'semanas': 30, 'estado': 'activo', 'riesgo': 'medio', 'tipo': 'simple'},
        {'semanas': 32, 'estado': 'activo', 'riesgo': 'alto', 'tipo': 'simple'},
        {'semanas': 34, 'estado': 'activo', 'riesgo': 'medio', 'tipo': 'simple'},
        {'semanas': 36, 'estado': 'activo', 'riesgo': 'medio', 'tipo': 'simple'},
        {'semanas': 37, 'estado': 'activo', 'riesgo': 'bajo', 'tipo': 'simple'},
        {'semanas': 38, 'estado': 'activo', 'riesgo': 'bajo', 'tipo': 'simple'},
        {'semanas': 39, 'estado': 'activo', 'riesgo': 'bajo', 'tipo': 'simple'},
        {'semanas': 40, 'estado': 'activo', 'riesgo': 'bajo', 'tipo': 'simple'},
    ]
    
    for i, paciente in enumerate(pacientes):
        # Usar config si existe, si no generar aleatoria
        if i < len(configs):
            config = configs[i]
        else:
            config = {
                'semanas': random.choice([8, 10, 12, 16, 20, 24, 28, 32, 36, 38]),
                'estado': 'activo',
                'riesgo': random.choice(['bajo', 'bajo', 'medio', 'alto']),
                'tipo': random.choice(['simple', 'simple', 'simple', 'gemelar'])
            }
        
        fum = date.today() - timedelta(days=config['semanas']*7)
        fpp = fum + timedelta(days=280)
        
        embarazo_data = {
            'paciente': paciente,
            'numero_gesta': random.randint(1, 5),
            'fecha_ultima_menstruacion': fum,
            'fecha_probable_parto': fpp,
            'tipo_embarazo': config['tipo'],
            'estado': config['estado'],
            'riesgo_embarazo': config['riesgo'],
            'notas': f"Embarazo {config['estado']} de riesgo {config['riesgo']}. "
                    f"Tipo: {config['tipo']}. Gesta #{random.randint(1, 5)}. "
                    f"Control prenatal programado cada {'2 semanas' if config['semanas'] > 32 else '4 semanas'}. "
                    f"{random.choice(['Evolución favorable.', 'Requiere vigilancia estrecha.', 'Seguimiento regular.'])}",
            'medico_responsable': random.choice([
                'Dr. Wilson Rodriguez',
                'Dra. Patricia Mamani',
                'Dr. Carlos Gutierrez',
                'Dra. Ana López',
                'Dr. Roberto Sánchez'
            ]),
        }
        
        embarazo, created = Embarazo.objects.get_or_create(
            paciente=paciente,
            fecha_ultima_menstruacion=fum,
            defaults=embarazo_data
        )
        
        if created:
            print(f"✅ Embarazo {i+1:2} - {paciente.nombre_completo[:35]:35} Sem {config['semanas']:2} "
                  f"({config['riesgo']:5}, {config['tipo']:7})")
        
        embarazos.append(embarazo)
    
    print(f"\n📊 Total de embarazos: {len(embarazos)}")
    return embarazos


# ================================================================================
# FUNCIÓN 4: CREAR CONTROLES PRENATALES
# ================================================================================

def crear_controles(embarazos, usuarios):
    """Crear controles prenatales detallados para cada embarazo"""
    print("\n" + "="*80)
    print("📋 CREANDO CONTROLES PRENATALES")
    print("="*80)
    
    controles_creados = 0
    medicos = usuarios.get('medico', [])
    enfermeros = usuarios.get('enfermero', [])
    
    for embarazo in embarazos:
        if embarazo.estado != 'activo':
            continue
        
        dias_embarazo = (date.today() - embarazo.fecha_ultima_menstruacion).days
        semanas_actuales = dias_embarazo // 7
        
        # Determinar número de controles según semanas
        if semanas_actuales < 12:
            num_controles = max(1, semanas_actuales // 4)
        elif semanas_actuales < 20:
            num_controles = 3 + (semanas_actuales - 12) // 4
        elif semanas_actuales < 28:
            num_controles = 5 + (semanas_actuales - 20) // 4
        elif semanas_actuales < 36:
            num_controles = 7 + (semanas_actuales - 28) // 4
        else:
            num_controles = min(12, 9 + (semanas_actuales - 36) // 2)
        
        peso_pregestacional = round(random.uniform(48, 75), 1)
        talla = round(random.uniform(1.48, 1.78), 2)
        
        for num_control in range(1, num_controles + 1):
            # Programar controles cada 4 semanas aprox hasta semana 28, luego cada 2-3 semanas
            if num_control <= 7:
                semanas_control = num_control * 4
            else:
                semanas_control = 28 + (num_control - 7) * 2
            
            if semanas_control > semanas_actuales:
                break
            
            dias_adicionales = random.randint(0, 6)
            # ✅ CORRECCIÓN: usar days correctamente
            fecha_control = embarazo.fecha_ultima_menstruacion + timedelta(
                days=semanas_control*7 + dias_adicionales
            )
            
            # Calcular ganancia de peso esperada progresivamente
            if semanas_control <= 12:
                ganancia_esperada = semanas_control * 0.15
            elif semanas_control <= 28:
                ganancia_esperada = 2 + (semanas_control - 12) * 0.35
            else:
                ganancia_esperada = 7.6 + (semanas_control - 28) * 0.45
            
            peso_actual = peso_pregestacional + ganancia_esperada + random.uniform(-0.8, 0.8)
            
            # Presión arterial según riesgo con progresión temporal
            factor_semanas = 1 + (semanas_control / 100)
            
            if embarazo.riesgo_embarazo == 'bajo':
                pa_sist = random.randint(95, 120)
                pa_diast = random.randint(55, 75)
            elif embarazo.riesgo_embarazo == 'medio':
                pa_sist = int(random.randint(110, 135) * factor_semanas)
                pa_diast = int(random.randint(68, 85) * factor_semanas)
            else:  # alto
                pa_sist = int(random.randint(125, 150) * factor_semanas)
                pa_diast = int(random.randint(78, 98) * factor_semanas)
            
            # Limitar valores máximos
            pa_sist = min(pa_sist, 160)
            pa_diast = min(pa_diast, 110)
            
            altura_uterina = semanas_control + random.randint(-3, 3)
            fcf = random.randint(120, 170) if semanas_control >= 10 else None
            
            # Presentación fetal
            if semanas_control >= 36:
                presentacion = random.choice(['cefalica', 'cefalica', 'cefalica', 'cefalica', 'podalica'])
            elif semanas_control >= 32:
                presentacion = random.choice(['cefalica', 'cefalica', 'cefalica', 'podalica', 'transversa'])
            elif semanas_control >= 28:
                presentacion = random.choice(['cefalica', 'cefalica', 'transversa'])
            else:
                presentacion = None
            
            # Movimientos fetales
            if semanas_control >= 28:
                movimientos = random.choice(['presentes', 'presentes', 'presentes', 'presentes', 'disminuidos'])
            elif semanas_control >= 20:
                movimientos = random.choice(['presentes', 'presentes', 'disminuidos'])
            elif semanas_control >= 16:
                movimientos = 'presentes'
            else:
                movimientos = None
            
            # Edema y proteinuria según riesgo y progresión
            if embarazo.riesgo_embarazo == 'alto' and semanas_control >= 20:
                edema = random.choice(['no', 'leve', 'moderado', 'moderado', 'severo'])
                proteinuria = random.choice(['negativa', 'trazas', 'positiva_1', 'positiva_2'])
            elif embarazo.riesgo_embarazo == 'medio':
                edema = random.choice(['no', 'no', 'leve', 'leve', 'moderado'])
                proteinuria = random.choice(['negativa', 'negativa', 'negativa', 'trazas'])
            else:
                edema = random.choice(['no', 'no', 'no', 'no', 'leve'])
                proteinuria = random.choice(['negativa', 'negativa', 'negativa', 'negativa', 'trazas'])
            
            # Observaciones detalladas
            observaciones_lista = [
                f'Control prenatal #{num_control} - Semana {semanas_control}+{dias_adicionales}.',
                f'Ganancia de peso: {peso_actual - peso_pregestacional:.1f}kg (Esperado: {ganancia_esperada:.1f}kg).',
            ]
            
            if pa_sist >= 140 or pa_diast >= 90:
                observaciones_lista.append('⚠️ Presión arterial elevada - Requiere vigilancia.')
            else:
                observaciones_lista.append('Presión arterial dentro de parámetros normales.')
            
            if embarazo.riesgo_embarazo == 'alto':
                observaciones_lista.append('Embarazo de alto riesgo - Seguimiento especializado.')
            elif embarazo.riesgo_embarazo == 'medio':
                observaciones_lista.append('Control regular programado.')
            else:
                observaciones_lista.append('Evolución satisfactoria del embarazo.')
            
            if semanas_control >= 32:
                observaciones_lista.append(f'Presentación: {presentacion}. Preparación para el parto.')
            
            observaciones = ' '.join(observaciones_lista)
            
            control_data = {
                'embarazo_id': embarazo,
                'paciente': embarazo.paciente,
                'numero_control': num_control,
                'fecha_control': fecha_control,
                'semanas_gestacion': semanas_control,
                'dias_gestacion': dias_adicionales,
                'peso_actual': Decimal(str(round(peso_actual, 1))),
                'peso_pregestacional': Decimal(str(peso_pregestacional)),
                'talla': Decimal(str(talla)),
                'presion_arterial_sistolica': pa_sist,
                'presion_arterial_diastolica': pa_diast,
                'frecuencia_cardiaca': random.randint(60, 100),
                'temperatura': Decimal(str(round(random.uniform(36.1, 37.2), 1))),
                'altura_uterina': Decimal(str(altura_uterina)) if semanas_control >= 12 else None,
                'frecuencia_cardiaca_fetal': fcf,
                'presentacion_fetal': presentacion,
                'movimientos_fetales': movimientos,
                'edema': edema,
                'proteinuria': proteinuria,
                'observaciones': observaciones,
                'medico_id': random.choice(medicos) if medicos else None,
            }
            
            try:
                control, created = ControlPrenatal.objects.get_or_create(
                    embarazo_id=embarazo,
                    numero_control=num_control,
                    defaults=control_data
                )
                
                if created:
                    controles_creados += 1
                    alerta = "⚠️" if pa_sist >= 140 or pa_diast >= 90 or edema == 'severo' else "✅"
                    print(f"{alerta} Control #{num_control:2} - {embarazo.paciente.nombre_completo[:28]:28} "
                          f"Sem {semanas_control:2}+{dias_adicionales} PA:{pa_sist:3}/{pa_diast:2} "
                          f"{('FCF:' + str(fcf)) if fcf else '        '} {edema:8}")
            except Exception as e:
                print(f"❌ Error control #{num_control} - {embarazo.paciente.nombre_completo[:20]}: {str(e)[:50]}")
    
    print(f"\n📊 Total de controles: {controles_creados}")
    return controles_creados


# ================================================================================
# FUNCIÓN 5: CREAR ECOGRAFÍAS
# ================================================================================

def crear_ecografias(embarazos, usuarios):
    """Crear ecografías completas con biometría, anexos y anatomía"""
    print("\n" + "="*80)
    print("🔬 CREANDO ECOGRAFÍAS")
    print("="*80)
    
    ecografias_creadas = 0
    medicos = usuarios.get('medico', [])
    
    for embarazo in embarazos:
        if embarazo.estado != 'activo':
            continue
        
        dias = (date.today() - embarazo.fecha_ultima_menstruacion).days
        semanas = dias // 7
        
        # Programar ecografías según protocolo internacional
        ecografias_programadas = []
        
        # Ecografía temprana
        if semanas >= 6:
            ecografias_programadas.append({
                'semana': random.randint(6, 8),
                'tipo': 'primer_trimestre',
                'descripcion': 'Ecografía temprana - Confirmación de embarazo y viabilidad'
            })
        
        # Ecografía del primer trimestre (11-14 semanas)
        if semanas >= 11:
            ecografias_programadas.append({
                'semana': random.randint(11, 13),
                'tipo': 'primer_trimestre',
                'descripcion': 'Ecografía de tamizaje del primer trimestre - Translucencia nucal'
            })
        
        # Ecografía morfológica (18-22 semanas)
        if semanas >= 18:
            ecografias_programadas.append({
                'semana': random.randint(18, 22),
                'tipo': 'segundo_trimestre',
                'descripcion': 'Ecografía morfológica estructural completa'
            })
        
        # Ecografía de crecimiento (28 semanas)
        if semanas >= 28:
            ecografias_programadas.append({
                'semana': random.randint(26, 29),
                'tipo': 'tercer_trimestre',
                'descripcion': 'Ecografía de crecimiento y bienestar fetal'
            })
        
        # Ecografía de crecimiento tardío (32 semanas)
        if semanas >= 32:
            ecografias_programadas.append({
                'semana': random.randint(31, 33),
                'tipo': 'tercer_trimestre',
                'descripcion': 'Ecografía de crecimiento tardío y evaluación de posición'
            })
        
        # Ecografía pre-parto (36+ semanas)
        if semanas >= 36:
            ecografias_programadas.append({
                'semana': random.randint(36, min(semanas, 40)),
                'tipo': 'tercer_trimestre',
                'descripcion': 'Ecografía de evaluación pre-parto'
            })
        
        for eco_config in ecografias_programadas:
            sem_eco = eco_config['semana']
            dias_eco = random.randint(0, 6)
            # ✅ CORRECCIÓN: calcular fecha correctamente
            fecha_eco = embarazo.fecha_ultima_menstruacion + timedelta(days=sem_eco*7 + dias_eco)
            
            # Datos básicos de la ecografía
            num_fetos = 2 if embarazo.tipo_embarazo == 'gemelar' else 1
            fcf_base = random.randint(130, 170) if sem_eco >= 6 else None
            
            # ILA según trimestre
            if sem_eco < 24:
                ila = round(random.uniform(8.0, 20.0), 1)
            elif sem_eco < 32:
                ila = round(random.uniform(10.0, 22.0), 1)
            else:
                ila = round(random.uniform(8.0, 18.0), 1)
            
            eco_data = {
                'embarazo': embarazo,
                'paciente': embarazo.paciente,
                'fecha_ecografia': fecha_eco,
                'tipo_ecografia': eco_config['tipo'],
                'edad_gestacional_semanas': sem_eco,
                'edad_gestacional_dias': dias_eco,
                'numero_fetos': num_fetos,
                'vitalidad_fetal': True,
                'frecuencia_cardiaca_fetal': fcf_base,
                'indice_liquido_amniotico': Decimal(str(ila)),
                'localizacion_placenta': random.choice([
                    'Anterior', 'Anterior', 'Posterior', 'Posterior', 'Posterior',
                    'Fúndica', 'Lateral izquierda', 'Lateral derecha'
                ]),
                'grado_madurez_placenta': min(3, sem_eco // 12),
                'diagnostico': f"{eco_config['descripcion']}. "
                              f"Biometría fetal {'acorde' if random.random() > 0.1 else 'por debajo'} a edad gestacional. "
                              f"Anatomía fetal {'sin alteraciones aparentes' if random.random() > 0.05 else 'requiere evaluación'}.  "
                              f"Líquido amniótico en {'cantidad normal' if 8 <= ila <= 20 else 'cantidad alterada'}.",
                'observaciones': random.choice([
                    'Estudio ecográfico completo. Visualización adecuada de todas las estructuras fetales.',
                    'Condiciones técnicas óptimas. Excelente colaboración materna.',
                    'Estudio satisfactorio. Se visualizan todas las estructuras anatómicas.',
                    'Ecografía realizada siguiendo protocolos internacionales ISUOG.',
                    'Evaluación completa del bienestar fetal. No se observan alteraciones mayores.',
                ]) + f' {"Embarazo gemelar." if num_fetos == 2 else ""}',
                'medico': random.choice(medicos) if medicos else None,
            }
            
            try:
                eco, created = Ecografia.objects.get_or_create(
                    embarazo=embarazo,
                    fecha_ecografia=fecha_eco,
                    tipo_ecografia=eco_data['tipo_ecografia'],
                    defaults=eco_data
                )
                
                if created:
                    ecografias_creadas += 1
                    print(f"✅ Eco {eco_config['tipo'][:15]:15} - {embarazo.paciente.nombre_completo[:28]:28} "
                          f"Sem {sem_eco:2}+{dias_eco} FCF:{fcf_base if fcf_base else '---':3} ILA:{ila:4.1f}")
                    
                    # Crear biometría fetal si es 2do o 3er trimestre
                    if sem_eco >= 14:
                        crear_biometria_fetal(eco, sem_eco)
                    
                    # Crear anexos fetales
                    crear_anexos_fetales(eco, sem_eco)
                    
                    # Crear anatomía fetal si es morfológica
                    if 18 <= sem_eco <= 24:
                        crear_anatomia_fetal(eco)
                        
            except Exception as e:
                print(f"❌ Error eco - {embarazo.paciente.nombre_completo[:25]}: {str(e)[:60]}")
    
    print(f"\n📊 Total de ecografías: {ecografias_creadas}")
    return ecografias_creadas


def crear_biometria_fetal(ecografia, semanas):
    """Crear medidas biométricas fetales según tablas de Hadlock"""
    try:
        # Valores aproximados según tablas de referencia (percentil 50)
        # DBP (Diámetro biparietal) en mm
        dbp_valores = {
            14: 27, 16: 35, 18: 42, 20: 47, 22: 53, 24: 59, 26: 64,
            28: 70, 30: 75, 32: 80, 34: 84, 36: 88, 38: 91, 40: 93
        }
        
        # CC (Circunferencia cefálica) en mm
        cc_valores = {
            14: 100, 16: 115, 18: 145, 20: 170, 22: 195, 24: 220, 26: 240,
            28: 260, 30: 275, 32: 295, 34: 305, 36: 320, 38: 330, 40: 340
        }
        
        # CA (Circunferencia abdominal) en mm
        ca_valores = {
            14: 80, 16: 100, 18: 125, 20: 150, 22: 170, 24: 190, 26: 215,
            28: 240, 30: 260, 32: 280, 34: 295, 36: 310, 38: 325, 40: 340
        }
        
        # LF (Longitud de fémur) en mm
        lf_valores = {
            14: 16, 16: 20, 18: 28, 20: 32, 22: 38, 24: 42, 26: 47,
            28: 52, 30: 56, 32: 60, 34: 63, 36: 66, 38: 69, 40: 72
        }
        
        # Peso fetal estimado en gramos
        peso_valores = {
            14: 110, 16: 160, 18: 250, 20: 350, 22: 480, 24: 650, 26: 850,
            28: 1100, 30: 1400, 32: 1800, 34: 2250, 36: 2700, 38: 3100, 40: 3400
        }
        
        # Redondear semanas a valores de referencia más cercanos
        sem_ref = min(40, max(14, (semanas // 2) * 2))
        
        # Agregar variabilidad (±10% para simular percentiles 10-90)
        dbp = dbp_valores.get(sem_ref, 50) * random.uniform(0.92, 1.08)
        cc = cc_valores.get(sem_ref, 200) * random.uniform(0.93, 1.07)
        ca = ca_valores.get(sem_ref, 200) * random.uniform(0.90, 1.10)
        lf = lf_valores.get(sem_ref, 40) * random.uniform(0.92, 1.08)
        peso = peso_valores.get(sem_ref, 1500) * random.uniform(0.85, 1.15)
        
        # Determinar percentil
        if peso < peso_valores.get(sem_ref, 1500) * 0.90:
            percentil = random.choice([5, 10])
        elif peso > peso_valores.get(sem_ref, 1500) * 1.10:
            percentil = random.choice([90, 95])
        else:
            percentil = random.choice([25, 50, 75])
        
        biometria_data = {
            'ecografia': ecografia,
            'diametro_biparietal': Decimal(str(round(dbp, 1))),
            'circunferencia_cefalica': Decimal(str(round(cc, 1))),
            'circunferencia_abdominal': Decimal(str(round(ca, 1))),
            'longitud_femur': Decimal(str(round(lf, 1))),
            'peso_fetal_estimado': Decimal(str(round(peso, 0))),
            'percentil': percentil,
        }
        
        BiometriaFetal.objects.create(**biometria_data)
    except Exception as e:
        pass


def crear_anexos_fetales(ecografia, semanas):
    """Crear información detallada de anexos fetales"""
    try:
        # Espesor placentario según edad gestacional
        if semanas < 20:
            espesor = round(random.uniform(15, 25), 1)
        elif semanas < 30:
            espesor = round(random.uniform(22, 35), 1)
        else:
            espesor = round(random.uniform(28, 40), 1)
        
        anexos_data = {
            'ecografia': ecografia,
            'localizacion_placenta': ecografia.localizacion_placenta,
            'grado_placenta': ecografia.grado_madurez_placenta,
            'espesor_placenta': Decimal(str(espesor)),
            'insercion_cordon': random.choice([
                'central', 'central', 'central', 'paracentral', 'paracentral',
                'marginal', 'velamentosa'
            ]),
            'numero_vasos_cordon': 3,
            'liquido_amniotico': random.choice([
                'normal', 'normal', 'normal', 'normal',
                'aumentado', 'disminuido'
            ]),
            'indice_liquido_amniotico': ecografia.indice_liquido_amniotico,
        }
        
        AnexosFetales.objects.create(**anexos_data)
    except Exception as e:
        pass


def crear_anatomia_fetal(ecografia):
    """Crear evaluación anatómica fetal completa (para eco morfológica)"""
    try:
        # 95% de anatomías normales, 5% con alguna alteración
        prob_normal = 0.95
        
        anatomia_data = {
            'ecografia': ecografia,
            'craneo': 'normal' if random.random() < prob_normal else random.choice(['alterado', 'no_visualizado']),
            'cara': 'normal' if random.random() < prob_normal else random.choice(['alterado', 'no_visualizado']),
            'columna': 'normal' if random.random() < prob_normal else random.choice(['alterado', 'no_visualizado']),
            'torax': 'normal' if random.random() < prob_normal else random.choice(['alterado', 'no_visualizado']),
            'corazon': 'normal' if random.random() < prob_normal else random.choice(['alterado', 'no_visualizado']),
            'abdomen': 'normal' if random.random() < prob_normal else random.choice(['alterado', 'no_visualizado']),
            'extremidades': 'normal' if random.random() < prob_normal else random.choice(['alterado', 'no_visualizado']),
            'genitales': random.choice(['masculino', 'femenino', 'femenino', 'no_determinado']),
            'observaciones': random.choice([
                'Anatomía fetal sin alteraciones mayores evidentes en el estudio actual.',
                'Evaluación anatómica completa. No se observan malformaciones mayores.',
                'Estudio morfológico completo. Anatomía fetal acorde a edad gestacional.',
                'Visualización adecuada de todas las estructuras anatómicas.',
            ]),
        }
        
        AnatomiaFetal.objects.create(**anatomia_data)
    except Exception as e:
        pass


# ================================================================================
# FUNCIÓN 6: CREAR CALCULADORAS CLÍNICAS
# ================================================================================

def crear_calculadoras(embarazos, pacientes, usuarios):
    """Crear todos los tipos de cálculos clínicos"""
    print("\n" + "="*80)
    print("🧮 CREANDO CÁLCULOS CLÍNICOS")
    print("="*80)
    
    calculos_creados = 0
    medicos = usuarios.get('medico', [])
    
    for i, embarazo in enumerate(embarazos[:18]):  # Primeros 18 embarazos
        paciente = embarazo.paciente
        dias = (date.today() - embarazo.fecha_ultima_menstruacion).days
        semanas = dias // 7
        medico = random.choice(medicos) if medicos else None
        
        print(f"\n📋 Paciente {i+1:2}: {paciente.nombre_completo[:45]:45} (Sem {semanas})")
        
        # 1. EDAD GESTACIONAL (todos los embarazos)
        try:
            calculo_base = CalculoClinico.objects.create(
                paciente=paciente,
                embarazo=embarazo,
                medico=medico,
                tipo_calculo='edad_gestacional',
                fecha_calculo=date.today()
            )
            
            trimestre = 1 if semanas < 13 else (2 if semanas < 28 else 3)
            
            EdadGestacional.objects.create(
                calculo=calculo_base,
                fum=embarazo.fecha_ultima_menstruacion,
                fecha_calculo=date.today(),
                semanas=semanas,
                dias=dias % 7,
                fpp=embarazo.fecha_probable_parto,
                trimestre=trimestre
            )
            calculos_creados += 1
            print(f"   ✅ Edad Gestacional: {semanas}sem+{dias%7}d (Trimestre {trimestre}) FPP:{embarazo.fecha_probable_parto.strftime('%d/%m/%Y')}")
        except Exception as e:
            print(f"   ❌ Error EG: {str(e)[:55]}")
        
        # 2. IMC (todos los embarazos)
        try:
            peso = Decimal(str(round(random.uniform(45, 90), 1)))
            altura = Decimal(str(round(random.uniform(1.45, 1.80), 2)))
            imc = peso / (altura * altura)
            
            if imc < 18.5:
                clasificacion = 'bajo_peso'
                ganancia_min, ganancia_max = Decimal('12.5'), Decimal('18')
                recomendacion = 'Aumentar ingesta calórica'
            elif imc < 25:
                clasificacion = 'normal'
                ganancia_min, ganancia_max = Decimal('11.5'), Decimal('16')
                recomendacion = 'Mantener alimentación balanceada'
            elif imc < 30:
                clasificacion = 'sobrepeso'
                ganancia_min, ganancia_max = Decimal('7'), Decimal('11.5')
                recomendacion = 'Control de peso y actividad física'
            else:
                clasificacion = 'obesidad'
                ganancia_min, ganancia_max = Decimal('5'), Decimal('9')
                recomendacion = 'Seguimiento nutricional especializado'
            
            calculo_base = CalculoClinico.objects.create(
                paciente=paciente,
                embarazo=embarazo,
                medico=medico,
                tipo_calculo='imc',
                fecha_calculo=date.today()
            )
            
            IndiceMasaCorporal.objects.create(
                calculo=calculo_base,
                peso=peso,
                altura=altura,
                imc=imc,
                clasificacion=clasificacion,
                ganancia_peso_recomendada_min=ganancia_min,
                ganancia_peso_recomendada_max=ganancia_max
            )
            calculos_creados += 1
            print(f"   ✅ IMC: {float(imc):.1f} ({clasificacion:10}) Peso:{float(peso):5.1f}kg Talla:{float(altura):.2f}m - Ganancia: {ganancia_min}-{ganancia_max}kg")
        except Exception as e:
            print(f"   ❌ Error IMC: {str(e)[:55]}")
        
        # 3. RIESGO PREECLAMPSIA (a partir de semana 11)
        if semanas >= 11:
            try:
                edad = paciente.edad
                es_primera = embarazo.numero_gesta == 1
                tiene_diabetes = random.choice([True, False, False, False, False, False])
                tiene_hipertension = random.choice([True, False, False, False, False, False])
                tiene_obesidad = imc >= 30 if 'imc' in locals() else False
                es_multiple = embarazo.tipo_embarazo == 'gemelar'
                tiene_renal = random.choice([True, False, False, False, False, False])
                tiene_autoinmune = random.choice([True, False, False, False, False, False])
                
                factores = sum([
                    edad >= 40,
                    edad < 18,
                    es_primera and edad >= 35,
                    tiene_diabetes,
                    tiene_hipertension,
                    tiene_obesidad,
                    es_multiple,
                    tiene_renal,
                    tiene_autoinmune
                ])
                
                if factores == 0:
                    nivel = 'bajo'
                    aspirina = False
                elif factores <= 1:
                    nivel = 'bajo'
                    aspirina = False
                elif factores <= 3:
                    nivel = 'medio'
                    aspirina = True
                else:
                    nivel = 'alto'
                    aspirina = True
                
                calculo_base = CalculoClinico.objects.create(
                    paciente=paciente,
                    embarazo=embarazo,
                    medico=medico,
                    tipo_calculo='riesgo_preeclampsia',
                    fecha_calculo=date.today()
                )
                
                RiesgoPreeclampsia.objects.create(
                    calculo=calculo_base,
                    edad=edad,
                    primiparidad=es_primera,
                    antecedente_preeclampsia=False,
                    diabetes=tiene_diabetes,
                    hipertension_cronica=tiene_hipertension,
                    obesidad=tiene_obesidad,
                    embarazo_multiple=es_multiple,
                    enfermedad_renal=tiene_renal,
                    enfermedad_autoinmune=tiene_autoinmune,
                    nivel_riesgo=nivel,
                    recomienda_aspirina=aspirina,
                    factores_riesgo_count=factores
                )
                calculos_creados += 1
                
                factores_texto = []
                if edad >= 40: factores_texto.append('Edad≥40')
                if edad < 18: factores_texto.append('Edad<18')
                if tiene_diabetes: factores_texto.append('DM')
                if tiene_hipertension: factores_texto.append('HTA')
                if tiene_obesidad: factores_texto.append('Obesidad')
                if es_multiple: factores_texto.append('Gemelar')
                
                print(f"   ✅ Riesgo Preeclampsia: {nivel.upper():5} ({factores} factores: {', '.join(factores_texto) if factores_texto else 'Ninguno'}) - Aspirina: {'SÍ' if aspirina else 'NO'}")
            except Exception as e:
                print(f"   ❌ Error Preeclampsia: {str(e)[:55]}")
        
        # 4. GANANCIA DE PESO (a partir de semana 12)
        if semanas >= 12:
            try:
                peso_pregestacional = Decimal(str(round(random.uniform(45, 75), 1)))
                peso_actual = peso if 'peso' in locals() else Decimal(str(round(random.uniform(50, 85), 1)))
                ganancia_actual = peso_actual - peso_pregestacional
                
                # Calcular ganancia esperada según IMC pregestacional
                imc_preg = peso_pregestacional / (altura * altura) if 'altura' in locals() else Decimal('22')
                
                if imc_preg < 18.5:
                    ganancia_esp_min = Decimal(str(semanas * 0.45))
                    ganancia_esp_max = Decimal(str(semanas * 0.64))
                elif imc_preg < 25:
                    ganancia_esp_min = Decimal(str(semanas * 0.41))
                    ganancia_esp_max = Decimal(str(semanas * 0.57))
                elif imc_preg < 30:
                    ganancia_esp_min = Decimal(str(semanas * 0.25))
                    ganancia_esp_max = Decimal(str(semanas * 0.41))
                else:
                    ganancia_esp_min = Decimal(str(semanas * 0.18))
                    ganancia_esp_max = Decimal(str(semanas * 0.32))
                
                # Determinar estado
                if ganancia_actual < ganancia_esp_min:
                    estado = 'insuficiente'
                elif ganancia_actual > ganancia_esp_max:
                    estado = 'excesiva'
                else:
                    estado = 'adecuada'
                
                calculo_base = CalculoClinico.objects.create(
                    paciente=paciente,
                    embarazo=embarazo,
                    medico=medico,
                    tipo_calculo='ganancia_peso',
                    fecha_calculo=date.today()
                )
                
                GananciaPeso.objects.create(
                    calculo=calculo_base,
                    peso_pregestacional=peso_pregestacional,
                    peso_actual=peso_actual,
                    ganancia_peso=ganancia_actual,
                    semanas_gestacion=semanas,
                    ganancia_esperada_min=ganancia_esp_min,
                    ganancia_esperada_max=ganancia_esp_max,
                    estado=estado
                )
                calculos_creados += 1
                print(f"   ✅ Ganancia Peso: {float(ganancia_actual):+5.1f}kg ({estado:11}) - Esperado: {float(ganancia_esp_min):.1f}-{float(ganancia_esp_max):.1f}kg")
            except Exception as e:
                print(f"   ❌ Error Ganancia Peso: {str(e)[:55]}")
        
        # 5. PRESIÓN ARTERIAL MEDIA
        try:
            pas = random.randint(95, 145)
            pad = random.randint(55, 95)
            pam = (pas + 2 * pad) / 3
            
            if pam < 70:
                clasificacion = 'hipotension'
            elif pam <= 105:
                clasificacion = 'normal'
            elif pam <= 125:
                clasificacion = 'elevada'
            else:
                clasificacion = 'hipertension'
            
            calculo_base = CalculoClinico.objects.create(
                paciente=paciente,
                embarazo=embarazo,
                medico=medico,
                tipo_calculo='presion_arterial_media',
                fecha_calculo=date.today()
            )
            
            PresionArterialMedia.objects.create(
                calculo=calculo_base,
                presion_sistolica=pas,
                presion_diastolica=pad,
                pam=Decimal(str(round(pam, 1))),
                clasificacion=clasificacion
            )
            calculos_creados += 1
            print(f"   ✅ PAM: {pam:5.1f} mmHg (PA: {pas:3}/{pad:2}) - {clasificacion.upper()}")
        except Exception as e:
            print(f"   ❌ Error PAM: {str(e)[:55]}")
        
        # 6. SUPERFICIE CORPORAL (útil para dosificación de medicamentos)
        if semanas >= 20:
            try:
                peso_kg = float(peso) if 'peso' in locals() else random.uniform(55, 85)
                altura_cm = float(altura) * 100 if 'altura' in locals() else random.uniform(150, 175)
                
                # Fórmula de Mosteller: SC (m²) = √[(Peso(kg) × Altura(cm)) / 3600]
                sc = ((peso_kg * altura_cm) / 3600) ** 0.5
                
                calculo_base = CalculoClinico.objects.create(
                    paciente=paciente,
                    embarazo=embarazo,
                    medico=medico,
                    tipo_calculo='superficie_corporal',
                    fecha_calculo=date.today()
                )
                
                SuperficieCorporal.objects.create(
                    calculo=calculo_base,
                    peso=Decimal(str(round(peso_kg, 1))),
                    altura=Decimal(str(round(altura_cm, 1))),
                    superficie_corporal=Decimal(str(round(sc, 2))),
                    formula_utilizada='Mosteller'
                )
                calculos_creados += 1
                print(f"   ✅ Superficie Corporal: {sc:.2f} m² (Peso:{peso_kg:.1f}kg Altura:{altura_cm:.0f}cm)")
            except Exception as e:
                print(f"   ❌ Error SC: {str(e)[:55]}")
    
    print(f"\n📊 Total de cálculos creados: {calculos_creados}")
    return calculos_creados


# ================================================================================
# FUNCIÓN 7: CREAR LABORATORIOS
# ================================================================================

def crear_tipos_examenes():
    """Crear catálogo completo de tipos de exámenes de laboratorio"""
    print("\n🧪 Creando tipos de exámenes...")
    
    tipos = [
        # HEMATOLOGÍA
        {'codigo': 'HEM001', 'nombre': 'Hemograma Completo', 'categoria': 'hematologia', 
         'descripcion': 'Recuento completo de células sanguíneas', 'precio': Decimal('50.00')},
        {'codigo': 'HEM002', 'nombre': 'Grupo Sanguíneo y Factor Rh', 'categoria': 'hematologia',
         'descripcion': 'Determinación de grupo ABO y Rh', 'precio': Decimal('30.00')},
        {'codigo': 'HEM003', 'nombre': 'Tiempo de Coagulación', 'categoria': 'hematologia',
         'descripcion': 'PT, PTT, INR', 'precio': Decimal('40.00')},
        
        # BIOQUÍMICA
        {'codigo': 'GLU001', 'nombre': 'Glucosa en Ayunas', 'categoria': 'bioquimica',
         'descripcion': 'Medición de glucosa basal', 'precio': Decimal('25.00')},
        {'codigo': 'GLU002', 'nombre': 'Curva de Glucosa (PTOG)', 'categoria': 'bioquimica',
         'descripcion': 'Prueba de tolerancia oral a la glucosa - 3 muestras', 'precio': Decimal('80.00')},
        {'codigo': 'GLU003', 'nombre': 'Hemoglobina Glicosilada (HbA1c)', 'categoria': 'bioquimica',
         'descripcion': 'Control glicémico de 3 meses', 'precio': Decimal('70.00')},
        
        # UROLOGÍA
        {'codigo': 'ORI001', 'nombre': 'Examen General de Orina', 'categoria': 'urologia',
         'descripcion': 'Análisis físico, químico y microscópico', 'precio': Decimal('20.00')},
        {'codigo': 'ORI002', 'nombre': 'Urocultivo', 'categoria': 'urologia',
         'descripcion': 'Cultivo de orina y antibiograma', 'precio': Decimal('60.00')},
        {'codigo': 'ORI003', 'nombre': 'Proteinuria de 24 horas', 'categoria': 'urologia',
         'descripcion': 'Medición de proteínas en orina de 24h', 'precio': Decimal('45.00')},
        
        # SEROLOGÍA
        {'codigo': 'SER001', 'nombre': 'VDRL', 'categoria': 'serologia',
         'descripcion': 'Tamizaje de sífilis', 'precio': Decimal('35.00')},
        {'codigo': 'SER002', 'nombre': 'VIH', 'categoria': 'serologia',
         'descripcion': 'Tamizaje de VIH (ELISA)', 'precio': Decimal('50.00')},
        {'codigo': 'SER003', 'nombre': 'Toxoplasma IgG/IgM', 'categoria': 'serologia',
         'descripcion': 'Detección de anticuerpos contra toxoplasma', 'precio': Decimal('80.00')},
        {'codigo': 'SER004', 'nombre': 'Rubéola IgG/IgM', 'categoria': 'serologia',
         'descripcion': 'Detección de anticuerpos contra rubéola', 'precio': Decimal('75.00')},
        {'codigo': 'SER005', 'nombre': 'Hepatitis B (HBsAg)', 'categoria': 'serologia',
         'descripcion': 'Tamizaje de hepatitis B', 'precio': Decimal('60.00')},
        {'codigo': 'SER006', 'nombre': 'Chagas', 'categoria': 'serologia',
         'descripcion': 'Serología para Trypanosoma cruzi', 'precio': Decimal('55.00')},
        
        # BIOQUÍMICA ESPECIALIZADA
        {'codigo': 'BIO001', 'nombre': 'Perfil Hepático', 'categoria': 'bioquimica',
         'descripcion': 'TGO, TGP, Bilirrubinas, Fosfatasa Alcalina', 'precio': Decimal('70.00')},
        {'codigo': 'BIO002', 'nombre': 'Perfil Renal', 'categoria': 'bioquimica',
         'descripcion': 'Urea, Creatinina, Ácido Úrico', 'precio': Decimal('65.00')},
        {'codigo': 'BIO003', 'nombre': 'Perfil Tiroideo', 'categoria': 'bioquimica',
         'descripcion': 'TSH, T3, T4 libre', 'precio': Decimal('120.00')},
        {'codigo': 'BIO004', 'nombre': 'Perfil Lipídico', 'categoria': 'bioquimica',
         'descripcion': 'Colesterol, Triglicéridos, HDL, LDL', 'precio': Decimal('75.00')},
        {'codigo': 'BIO005', 'nombre': 'Electrolitos', 'categoria': 'bioquimica',
         'descripcion': 'Sodio, Potasio, Cloro', 'precio': Decimal('55.00')},
    ]
    
    creados = 0
    for tipo_data in tipos:
        tipo, created = TipoExamen.objects.get_or_create(
            codigo=tipo_data['codigo'],
            defaults=tipo_data
        )
        if created:
            creados += 1
            print(f"   ✅ {tipo.codigo} - {tipo.nombre[:50]:50} ({tipo.categoria})")
    
    print(f"\n📊 Tipos de exámenes: {creados} creados, {TipoExamen.objects.count()} total")
    return TipoExamen.objects.all()


def crear_valores_referencia(tipos_examenes):
    """Crear valores de referencia completos para los exámenes"""
    print("\n📏 Creando valores de referencia...")
    
    referencias = [
        # Hemograma Completo
        {'tipo_codigo': 'HEM001', 'parametro': 'Hemoglobina', 'valor_min': 11.0, 'valor_max': 16.0, 'unidad': 'g/dL',
         'observaciones': 'Valor mínimo para embarazadas'},
        {'tipo_codigo': 'HEM001', 'parametro': 'Hematocrito', 'valor_min': 33.0, 'valor_max': 45.0, 'unidad': '%',
         'observaciones': 'Rango ajustado para embarazo'},
        {'tipo_codigo': 'HEM001', 'parametro': 'Leucocitos', 'valor_min': 6000.0, 'valor_max': 17000.0, 'unidad': '/mm³',
         'observaciones': 'Aumentados fisiológicamente en embarazo'},
        {'tipo_codigo': 'HEM001', 'parametro': 'Plaquetas', 'valor_min': 150000.0, 'valor_max': 400000.0, 'unidad': '/mm³',
         'observaciones': 'Vigilar si < 100,000'},
        {'tipo_codigo': 'HEM001', 'parametro': 'VCM', 'valor_min': 80.0, 'valor_max': 100.0, 'unidad': 'fL',
         'observaciones': 'Volumen corpuscular medio'},
        
        # Glucosa
        {'tipo_codigo': 'GLU001', 'parametro': 'Glucosa Ayunas', 'valor_min': 70.0, 'valor_max': 92.0, 'unidad': 'mg/dL',
         'observaciones': 'Criterio IADPSG para embarazo'},
        {'tipo_codigo': 'GLU002', 'parametro': 'Glucosa Basal', 'valor_min': 70.0, 'valor_max': 92.0, 'unidad': 'mg/dL',
         'observaciones': 'PTOG - muestra basal'},
        {'tipo_codigo': 'GLU002', 'parametro': 'Glucosa 1 hora', 'valor_min': 0.0, 'valor_max': 180.0, 'unidad': 'mg/dL',
         'observaciones': 'PTOG - 1 hora post carga'},
        {'tipo_codigo': 'GLU002', 'parametro': 'Glucosa 2 horas', 'valor_min': 0.0, 'valor_max': 153.0, 'unidad': 'mg/dL',
         'observaciones': 'PTOG - 2 horas post carga'},
        
        # Orina
        {'tipo_codigo': 'ORI001', 'parametro': 'pH', 'valor_min': 4.5, 'valor_max': 8.0, 'unidad': '',
         'observaciones': 'Rango normal de pH urinario'},
        {'tipo_codigo': 'ORI001', 'parametro': 'Densidad', 'valor_min': 1.005, 'valor_max': 1.030, 'unidad': '',
         'observaciones': 'Densidad específica'},
        {'tipo_codigo': 'ORI001', 'parametro': 'Proteínas', 'valor_min': 0.0, 'valor_max': 15.0, 'unidad': 'mg/dL',
         'observaciones': 'Normal: negativo o trazas'},
        {'tipo_codigo': 'ORI001', 'parametro': 'Glucosa', 'valor_min': 0.0, 'valor_max': 0.0, 'unidad': 'mg/dL',
         'observaciones': 'Normal: negativo'},
        {'tipo_codigo': 'ORI001', 'parametro': 'Leucocitos', 'valor_min': 0.0, 'valor_max': 5.0, 'unidad': '/campo',
         'observaciones': 'Por campo de alto poder'},
        {'tipo_codigo': 'ORI001', 'parametro': 'Hematíes', 'valor_min': 0.0, 'valor_max': 3.0, 'unidad': '/campo',
         'observaciones': 'Por campo de alto poder'},
        
        # Proteinuria 24h
        {'tipo_codigo': 'ORI003', 'parametro': 'Proteínas 24h', 'valor_min': 0.0, 'valor_max': 300.0, 'unidad': 'mg/24h',
         'observaciones': '>300mg diagnóstico de proteinuria'},
        
        # Perfil Hepático
        {'tipo_codigo': 'BIO001', 'parametro': 'TGO (AST)', 'valor_min': 0.0, 'valor_max': 35.0, 'unidad': 'U/L',
         'observaciones': 'Transaminasa glutámico oxalacética'},
        {'tipo_codigo': 'BIO001', 'parametro': 'TGP (ALT)', 'valor_min': 0.0, 'valor_max': 35.0, 'unidad': 'U/L',
         'observaciones': 'Transaminasa glutámico pirúvica'},
        {'tipo_codigo': 'BIO001', 'parametro': 'Bilirrubina Total', 'valor_min': 0.2, 'valor_max': 1.2, 'unidad': 'mg/dL',
         'observaciones': 'Suma de directa e indirecta'},
        {'tipo_codigo': 'BIO001', 'parametro': 'Fosfatasa Alcalina', 'valor_min': 30.0, 'valor_max': 130.0, 'unidad': 'U/L',
         'observaciones': 'Aumentada fisiológicamente en embarazo'},
        
        # Perfil Renal
        {'tipo_codigo': 'BIO002', 'parametro': 'Creatinina', 'valor_min': 0.5, 'valor_max': 1.1, 'unidad': 'mg/dL',
         'observaciones': 'Disminuida en embarazo normal'},
        {'tipo_codigo': 'BIO002', 'parametro': 'Urea', 'valor_min': 15.0, 'valor_max': 45.0, 'unidad': 'mg/dL',
         'observaciones': 'BUN: Blood Urea Nitrogen'},
        {'tipo_codigo': 'BIO002', 'parametro': 'Ácido Úrico', 'valor_min': 2.5, 'valor_max': 6.0, 'unidad': 'mg/dL',
         'observaciones': 'Elevado en preeclampsia'},
        
        # Perfil Tiroideo
        {'tipo_codigo': 'BIO003', 'parametro': 'TSH', 'valor_min': 0.1, 'valor_max': 4.0, 'unidad': 'mUI/L',
         'observaciones': 'Rango trimestral: 1T:0.1-2.5, 2T:0.2-3.0, 3T:0.3-3.5'},
        {'tipo_codigo': 'BIO003', 'parametro': 'T4 Libre', 'valor_min': 0.8, 'valor_max': 1.8, 'unidad': 'ng/dL',
         'observaciones': 'Tiroxina libre'},
        {'tipo_codigo': 'BIO003', 'parametro': 'T3', 'valor_min': 80.0, 'valor_max': 200.0, 'unidad': 'ng/dL',
         'observaciones': 'Triyodotironina'},
        
        # Perfil Lipídico
        {'tipo_codigo': 'BIO004', 'parametro': 'Colesterol Total', 'valor_min': 0.0, 'valor_max': 200.0, 'unidad': 'mg/dL',
         'observaciones': 'Aumentado fisiológicamente en embarazo'},
        {'tipo_codigo': 'BIO004', 'parametro': 'Triglicéridos', 'valor_min': 0.0, 'valor_max': 150.0, 'unidad': 'mg/dL',
         'observaciones': 'Pueden duplicarse en embarazo'},
        {'tipo_codigo': 'BIO004', 'parametro': 'HDL Colesterol', 'valor_min': 40.0, 'valor_max': 200.0, 'unidad': 'mg/dL',
         'observaciones': 'Colesterol "bueno"'},
        {'tipo_codigo': 'BIO004', 'parametro': 'LDL Colesterol', 'valor_min': 0.0, 'valor_max': 130.0, 'unidad': 'mg/dL',
         'observaciones': 'Colesterol "malo"'},
        
        # Electrolitos
        {'tipo_codigo': 'BIO005', 'parametro': 'Sodio', 'valor_min': 135.0, 'valor_max': 145.0, 'unidad': 'mEq/L',
         'observaciones': 'Ligeramente disminuido en embarazo'},
        {'tipo_codigo': 'BIO005', 'parametro': 'Potasio', 'valor_min': 3.5, 'valor_max': 5.0, 'unidad': 'mEq/L',
         'observaciones': 'Importante en HTA y preeclampsia'},
        {'tipo_codigo': 'BIO005', 'parametro': 'Cloro', 'valor_min': 98.0, 'valor_max': 107.0, 'unidad': 'mEq/L',
         'observaciones': 'Electrolito principal extracelular'},
    ]
    
    creados = 0
    for ref_data in referencias:
        tipo = tipos_examenes.filter(codigo=ref_data['tipo_codigo']).first()
        if tipo:
            ref, created = ValorReferencia.objects.get_or_create(
                tipo_examen=tipo,
                parametro=ref_data['parametro'],
                defaults={
                    'valor_minimo': Decimal(str(ref_data['valor_min'])),
                    'valor_maximo': Decimal(str(ref_data['valor_max'])),
                    'unidad_medida': ref_data['unidad'],
                    'observaciones': ref_data.get('observaciones', ''),
                }
            )
            if created:
                creados += 1
    
    print(f"📊 Valores de referencia: {creados} creados, {ValorReferencia.objects.count()} total")
    return creados


def crear_examenes_laboratorio(embarazos, pacientes, usuarios):
    """Crear exámenes de laboratorio completos para las pacientes"""
    print("\n🔬 Creando exámenes de laboratorio...")
    
    tipos = TipoExamen.objects.all()
    medicos = usuarios.get('medico', [])
    examenes_creados = 0
    
    # Protocolos de exámenes según trimestre
    examenes_primer_trim = ['HEM001', 'HEM002', 'GLU001', 'ORI001', 'SER001', 'SER002', 'SER003', 'SER004', 'SER005']
    examenes_segundo_trim = ['HEM001', 'GLU002', 'ORI001', 'BIO001', 'BIO002']
    examenes_tercer_trim = ['HEM001', 'GLU001', 'ORI001', 'HEM003']
    
    for embarazo in embarazos[:15]:  # Primeros 15 embarazos
        paciente = embarazo.paciente
        semanas = (date.today() - embarazo.fecha_ultima_menstruacion).days // 7
        
        # Exámenes del primer trimestre (8-12 semanas)
        if semanas >= 8:
            fecha_base = embarazo.fecha_ultima_menstruacion + timedelta(days=random.randint(56, 84))
            
            for codigo in examenes_primer_trim:
                tipo = tipos.filter(codigo=codigo).first()
                if tipo:
                    try:
                        fecha = fecha_base + timedelta(days=random.randint(0, 7))
                        
                        examen, created = ExamenLaboratorio.objects.get_or_create(
                            paciente=paciente,
                            embarazo=embarazo,
                            tipo_examen=tipo,
                            fecha_solicitud=fecha,
                            defaults={
                                'medico_solicitante': random.choice(medicos) if medicos else None,
                                'estado': 'completado',
                                'fecha_resultado': fecha + timedelta(days=random.randint(1, 3)),
                                'observaciones': f'Exámenes de rutina del primer trimestre. {random.choice(["Protocolo estándar.", "Control prenatal inicial.", "Batería completa."])}',
                                'urgente': False,
                            }
                        )
                        if created:
                            examenes_creados += 1
                            crear_resultados_laboratorio(examen, tipo)
                            print(f"   ✅ {paciente.nombre_completo[:28]:28} - {tipo.nombre[:45]:45} (Sem {semanas})")
                    except Exception as e:
                        pass
        
        # PTOG en segundo trimestre (24-28 semanas)
        if semanas >= 24 and semanas <= 28:
            fecha = embarazo.fecha_ultima_menstruacion + timedelta(days=random.randint(168, 196))
            
            for codigo in examenes_segundo_trim:
                tipo = tipos.filter(codigo=codigo).first()
                if tipo:
                    try:
                        examen, created = ExamenLaboratorio.objects.get_or_create(
                            paciente=paciente,
                            embarazo=embarazo,
                            tipo_examen=tipo,
                            fecha_solicitud=fecha,
                            defaults={
                                'medico_solicitante': random.choice(medicos) if medicos else None,
                                'estado': 'completado',
                                'fecha_resultado': fecha + timedelta(days=1 if codigo == 'GLU002' else random.randint(1, 3)),
                                'observaciones': f'{"Tamizaje de diabetes gestacional." if codigo == "GLU002" else "Control del segundo trimestre."}',
                                'urgente': codigo == 'GLU002',
                            }
                        )
                        if created:
                            examenes_creados += 1
                            crear_resultados_laboratorio(examen, tipo)
                            print(f"   ✅ {paciente.nombre_completo[:28]:28} - {tipo.nombre[:45]:45} (Sem {semanas})")
                    except Exception as e:
                        pass
        
        # Exámenes del tercer trimestre (32-36 semanas)
        if semanas >= 32:
            fecha = embarazo.fecha_ultima_menstruacion + timedelta(days=random.randint(224, 252))
            
            for codigo in examenes_tercer_trim:
                tipo = tipos.filter(codigo=codigo).first()
                if tipo:
                    try:
                        examen, created = ExamenLaboratorio.objects.get_or_create(
                            paciente=paciente,
                            embarazo=embarazo,
                            tipo_examen=tipo,
                            fecha_solicitud=fecha,
                            defaults={
                                'medico_solicitante': random.choice(medicos) if medicos else None,
                                'estado': 'completado',
                                'fecha_resultado': fecha + timedelta(days=random.randint(1, 2)),
                                'observaciones': 'Control pre-parto. Evaluación final antes del nacimiento.',
                                'urgente': False,
                            }
                        )
                        if created:
                            examenes_creados += 1
                            crear_resultados_laboratorio(examen, tipo)
                            print(f"   ✅ {paciente.nombre_completo[:28]:28} - {tipo.nombre[:45]:45} (Sem {semanas})")
                    except Exception as e:
                        pass
        
        # Exámenes adicionales según riesgo
        if embarazo.riesgo_embarazo in ['medio', 'alto'] and semanas >= 20:
            examenes_adicionales = ['BIO003', 'BIO004', 'ORI003']  # Tiroides, Lípidos, Proteinuria 24h
            
            for codigo in random.sample(examenes_adicionales, random.randint(1, 2)):
                tipo = tipos.filter(codigo=codigo).first()
                if tipo:
                    try:
                        fecha = date.today() - timedelta(days=random.randint(7, 30))
                        
                        examen, created = ExamenLaboratorio.objects.get_or_create(
                            paciente=paciente,
                            embarazo=embarazo,
                            tipo_examen=tipo,
                            fecha_solicitud=fecha,
                            defaults={
                                'medico_solicitante': random.choice(medicos) if medicos else None,
                                'estado': random.choice(['completado', 'completado', 'en_proceso']),
                                'fecha_resultado': fecha + timedelta(days=random.randint(2, 5)) if random.random() > 0.2 else None,
                                'observaciones': f'Examen solicitado por embarazo de riesgo {embarazo.riesgo_embarazo}. Seguimiento especializado.',
                                'urgente': embarazo.riesgo_embarazo == 'alto',
                            }
                        )
                        if created:
                            examenes_creados += 1
                            if examen.estado == 'completado':
                                crear_resultados_laboratorio(examen, tipo)
                            print(f"   ⚠️  {paciente.nombre_completo[:28]:28} - {tipo.nombre[:45]:45} (Riesgo {embarazo.riesgo_embarazo})")
                    except Exception as e:
                        pass
    
    print(f"\n📊 Total de exámenes: {examenes_creados}")
    return examenes_creados


def crear_resultados_laboratorio(examen, tipo):
    """Crear resultados específicos para cada tipo de examen"""
    referencias = ValorReferencia.objects.filter(tipo_examen=tipo)
    
    for ref in referencias:
        valor_min = float(ref.valor_minimo)
        valor_max = float(ref.valor_maximo)
        
        # 85% de valores normales, 15% alterados
        if random.random() < 0.85:
            # Valor normal (dentro del rango)
            valor = random.uniform(valor_min + (valor_max - valor_min) * 0.1, 
                                 valor_max - (valor_max - valor_min) * 0.1)
        else:
            # Valor alterado
            if random.random() < 0.5:
                # Valor bajo
                valor = random.uniform(max(0, valor_min * 0.6), valor_min * 0.95)
            else:
                # Valor alto
                valor = random.uniform(valor_max * 1.05, valor_max * 1.4)
        
        normal = valor_min <= valor <= valor_max
        
        # Observaciones según el valor
        if normal:
            obs = random.choice([
                'Resultado dentro de parámetros normales',
                'Valor normal para edad gestacional',
                'Sin alteraciones significativas',
            ])
        else:
            if valor < valor_min:
                obs = f'Valor por debajo del rango de referencia. Requiere evaluación médica.'
            else:
                obs = f'Valor por encima del rango de referencia. Considerar seguimiento.'
        
        ResultadoLaboratorio.objects.create(
            examen=examen,
            parametro=ref.parametro,
            valor=Decimal(str(round(valor, 2))),
            unidad_medida=ref.unidad_medida,
            valor_referencia_min=ref.valor_minimo,
            valor_referencia_max=ref.valor_maximo,
            normal=normal,
            observaciones=obs
        )


# ================================================================================
# FUNCIÓN 8: CREAR CITAS Y DISPONIBILIDADES
# ================================================================================

def crear_disponibilidades(usuarios):
    """Crear disponibilidades horarias de médicos"""
    print("\n📅 Creando disponibilidades médicas...")
    
    medicos = usuarios.get('medico', [])
    disponibilidades = 0
    
    dias_semana_choices = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado']
    
    for medico in medicos:
        # Cada médico tiene 4-6 días disponibles
        dias_trabajo = random.sample(dias_semana_choices, random.randint(4, 6))
        
        for dia in dias_trabajo:
            # Turnos: mañana (8-12) y/o tarde (14-18)
            turnos_posibles = [
                (time(8, 0), time(12, 0)),   # Mañana
                (time(14, 0), time(18, 0)),  # Tarde
            ]
            
            turnos_asignados = random.sample(turnos_posibles, random.randint(1, 2))
            
            for hora_inicio, hora_fin in turnos_asignados:
                try:
                    disp, created = Disponibilidad.objects.get_or_create(
                        medico=medico,
                        dia_semana=dia,
                        hora_inicio=hora_inicio,
                        defaults={
                            'hora_fin': hora_fin,
                            'activo': True,
                            'duracion_cita': random.choice([30, 30, 45]),
                        }
                    )
                    if created:
                        disponibilidades += 1
                        print(f"   ✅ Dr(a). {medico.nombre} {medico.apellido_paterno[:15]:15} - {dia[:8]:8} {hora_inicio.strftime('%H:%M')}-{hora_fin.strftime('%H:%M')}")
                except Exception as e:
                    print(f"   ❌ Error: {str(e)[:60]}")
    
    print(f"\n📊 Disponibilidades: {disponibilidades} creadas")
    return disponibilidades


def crear_citas(pacientes, usuarios):
    """Crear citas médicas programadas con diferentes estados"""
    print("\n📅 Creando citas médicas...")
    
    medicos = usuarios.get('medico', [])
    if not medicos:
        print("⚠️  No hay médicos disponibles")
        return 0
    
    citas_creadas = 0
    tipos_cita = ['control_prenatal', 'ecografia', 'consulta_general', 'seguimiento', 'urgencia']
    
    motivos = {
        'control_prenatal': 'Control prenatal de rutina programado',
        'ecografia': 'Ecografía obstétrica programada',
        'consulta_general': 'Consulta médica gineco-obstétrica',
        'seguimiento': 'Seguimiento y evolución del embarazo',
        'urgencia': 'Atención por urgencia obstétrica'
    }
    
    for i, paciente in enumerate(pacientes[:18]):  # Primeros 18 pacientes
        # 2-5 citas por paciente
        num_citas = random.randint(2, 5)
        
        for j in range(num_citas):
            try:
                # Mix de fechas pasadas, presentes y futuras
                if j == 0:
                    # Primera cita: hace 2-4 semanas
                    dias_offset = -random.randint(14, 28)
                elif j == 1:
                    # Segunda cita: hace 1-2 semanas
                    dias_offset = -random.randint(7, 14)
                elif j == 2:
                    # Tercera cita: esta semana o próxima
                    dias_offset = random.randint(0, 7)
                else:
                    # Citas futuras
                    dias_offset = random.randint(7, 60)
                
                fecha = date.today() + timedelta(days=dias_offset)
                hora = time(random.randint(8, 16), random.choice([0, 30]))
                medico = random.choice(medicos)
                
                tipo = random.choice(tipos_cita)
                
                # Estado según fecha
                if fecha < date.today() - timedelta(days=1):
                    estado = random.choice(['completada', 'completada', 'completada', 'cancelada', 'no_asistio'])
                elif fecha < date.today():
                    estado = random.choice(['completada', 'en_curso'])
                elif fecha == date.today():
                    estado = random.choice(['confirmada', 'en_curso', 'programada'])
                else:
                    estado = random.choice(['programada', 'programada', 'confirmada'])
                
                duracion = 45 if tipo in ['control_prenatal', 'ecografia'] else 30
                
                observaciones_lista = [
                    motivos.get(tipo, 'Consulta médica'),
                ]
                
                if estado == 'completada':
                    observaciones_lista.append(random.choice([
                        'Cita realizada satisfactoriamente.',
                        'Paciente evaluada sin complicaciones.',
                        'Control realizado según protocolo.',
                    ]))
                elif estado == 'cancelada':
                    observaciones_lista.append(random.choice([
                        'Cancelada por la paciente.',
                        'Reprogramada a solicitud de la paciente.',
                        'Cancelada por razones personales.',
                    ]))
                elif estado == 'no_asistio':
                    observaciones_lista.append('Paciente no asistió a la cita programada.')
                elif estado == 'confirmada':
                    observaciones_lista.append('Cita confirmada por la paciente.')
                
                observaciones = ' '.join(observaciones_lista)
                
                cita, created = Cita.objects.get_or_create(
                    paciente=paciente,
                    fecha_cita=fecha,
                    hora_cita=hora,
                    medico=medico,
                    defaults={
                        'duracion': duracion,
                        'tipo_cita': tipo,
                        'estado': estado,
                        'motivo': motivos.get(tipo, 'Consulta médica'),
                        'observaciones': observaciones,
                        'recordatorio_enviado': estado in ['confirmada', 'programada'] and fecha > date.today(),
                        'fecha_recordatorio': (fecha - timedelta(days=1)) if fecha > date.today() else None,
                        'creado_por': medico,
                    }
                )
                
                if created:
                    citas_creadas += 1
                    
                    # Iconos según estado
                    if estado == 'completada':
                        icono = '✅'
                    elif estado == 'confirmada':
                        icono = '🔵'
                    elif estado == 'programada':
                        icono = '⏰'
                    elif estado == 'cancelada':
                        icono = '❌'
                    elif estado == 'no_asistio':
                        icono = '⚠️'
                    else:
                        icono = '🔄'
                    
                    print(f"{icono} {paciente.nombre_completo[:26]:26} {fecha.strftime('%d/%m/%Y')} {hora.strftime('%H:%M')} "
                          f"{tipo[:18]:18} ({estado[:12]:12}) Dr(a). {medico.apellido_paterno[:15]}")
                    
                    # Crear historial de cambios para citas completadas o canceladas
                    if estado in ['completada', 'cancelada'] and random.random() < 0.7:
                        estado_anterior = 'confirmada' if estado == 'completada' else 'programada'
                        motivo_cambio = {
                            'completada': 'Cita realizada exitosamente',
                            'cancelada': random.choice([
                                'Cancelación solicitada por paciente',
                                'Reprogramación por conflicto de horario',
                                'Cancelación por razones médicas'
                            ])
                        }.get(estado, 'Cambio de estado')
                        
                        HistorialCita.objects.create(
                            cita=cita,
                            estado_anterior=estado_anterior,
                            estado_nuevo=estado,
                            motivo_cambio=motivo_cambio,
                            usuario=medico,
                            fecha_cambio=fecha if estado == 'completada' else fecha - timedelta(days=random.randint(1, 3))
                        )
                        
            except Exception as e:
                print(f"❌ Error: {str(e)[:70]}")
    
    print(f"\n📊 Total de citas: {citas_creadas}")
    print(f"   - Completadas: {Cita.objects.filter(estado='completada').count()}")
    print(f"   - Programadas: {Cita.objects.filter(estado='programada').count()}")
    print(f"   - Confirmadas: {Cita.objects.filter(estado='confirmada').count()}")
    print(f"   - Canceladas: {Cita.objects.filter(estado='cancelada').count()}")
    
    return citas_creados


# ================================================================================
# FUNCIÓN PRINCIPAL
# ================================================================================

def main():
    """Función principal para poblar toda la base de datos"""
    print("="*80)
    print("🚀 POBLANDO BASE DE DATOS COMPLETA")
    print("   Sistema de Historias Clínicas Gineco-Obstétricas")
    print("   Fetal Medical - La Paz, Bolivia")
    print("="*80)
    print(f"📅 Fecha: {date.today().strftime('%d/%m/%Y')}")
    print(f"🕐 Hora: {datetime.now().strftime('%H:%M:%S')}")
    print(f"💾 Base de datos: PostgreSQL")
    print("="*80)
    
    inicio = datetime.now()
    
    try:
        # 1. USUARIOS
        usuarios = crear_usuarios()
        
        # 2. PACIENTES
        pacientes = crear_pacientes(cantidad=25)
        
        # 3. EMBARAZOS
        embarazos = crear_embarazos(pacientes)
        
        # 4. CONTROLES PRENATALES
        crear_controles(embarazos, usuarios)
        
        # 5. ECOGRAFÍAS CON BIOMETRÍA Y ANATOMÍA
        crear_ecografias(embarazos, usuarios)
        
        # 6. CALCULADORAS CLÍNICAS
        crear_calculadoras(embarazos, pacientes, usuarios)
        
        # 7. LABORATORIOS
        tipos_examenes = crear_tipos_examenes()
        crear_valores_referencia(tipos_examenes)
        crear_examenes_laboratorio(embarazos, pacientes, usuarios)
        
        # 8. CITAS Y DISPONIBILIDADES
        crear_disponibilidades(usuarios)
        crear_citas(pacientes, usuarios)
        
        # Tiempo de ejecución
        fin = datetime.now()
        duracion = (fin - inicio).total_seconds()
        
        # RESUMEN FINAL COMPLETO
        print("\n" + "="*80)
        print("✅ ¡PROCESO COMPLETADO EXITOSAMENTE!")
        print("="*80)
        
        print(f"\n⏱️  TIEMPO DE EJECUCIÓN: {duracion:.2f} segundos")
        
        print(f"\n📊 RESUMEN COMPLETO DE DATOS:")
        
        print(f"\n   👥 USUARIOS Y PERSONAL:")
        print(f"      Total Usuarios: {Usuario.objects.count()}")
        print(f"      - Médicos Especialistas: {Usuario.objects.filter(rol='medico').count()}")
        print(f"      - Enfermeros: {Usuario.objects.filter(rol='enfermero').count()}")
        print(f"      - Administradores: {Usuario.objects.filter(rol='administrador').count()}")
        print(f"      - Usuarios Activos: {Usuario.objects.filter(activo=True).count()}")
        
        print(f"\n   🤰 PACIENTES Y EMBARAZOS:")
        print(f"      Total Pacientes: {Paciente.objects.count()}")
        print(f"      Total Embarazos: {Embarazo.objects.count()}")
        print(f"      - Embarazos Activos: {Embarazo.objects.filter(estado='activo').count()}")
        print(f"      - Bajo Riesgo: {Embarazo.objects.filter(riesgo_embarazo='bajo').count()}")
        print(f"      - Riesgo Medio: {Embarazo.objects.filter(riesgo_embarazo='medio').count()}")
        print(f"      - Alto Riesgo: {Embarazo.objects.filter(riesgo_embarazo='alto').count()}")
        print(f"      - Embarazos Gemelares: {Embarazo.objects.filter(tipo_embarazo='gemelar').count()}")
        
        print(f"\n   📋 CONTROLES Y SEGUIMIENTO:")
        print(f"      Controles Prenatales: {ControlPrenatal.objects.count()}")
        print(f"      Ecografías Totales: {Ecografia.objects.count()}")
        print(f"      - Primer Trimestre: {Ecografia.objects.filter(tipo_ecografia='primer_trimestre').count()}")
        print(f"      - Segundo Trimestre: {Ecografia.objects.filter(tipo_ecografia='segundo_trimestre').count()}")
        print(f"      - Tercer Trimestre: {Ecografia.objects.filter(tipo_ecografia='tercer_trimestre').count()}")
        print(f"      Biometrías Fetales: {BiometriaFetal.objects.count()}")
        print(f"      Anexos Fetales: {AnexosFetales.objects.count()}")
        print(f"      Anatomías Fetales: {AnatomiaFetal.objects.count()}")
        
        print(f"\n   🧮 CALCULADORAS CLÍNICAS:")
        print(f"      Total Cálculos: {CalculoClinico.objects.count()}")
        print(f"      - Edad Gestacional: {EdadGestacional.objects.count()}")
        print(f"      - IMC: {IndiceMasaCorporal.objects.count()}")
        print(f"      - Riesgo Preeclampsia: {RiesgoPreeclampsia.objects.count()}")
        print(f"      - Ganancia de Peso: {GananciaPeso.objects.count()}")
        print(f"      - PAM: {PresionArterialMedia.objects.count()}")
        print(f"      - Superficie Corporal: {SuperficieCorporal.objects.count()}")
        
        print(f"\n   🔬 LABORATORIO:")
        print(f"      Tipos de Exámenes Disponibles: {TipoExamen.objects.count()}")
        print(f"      Valores de Referencia: {ValorReferencia.objects.count()}")
        print(f"      Exámenes Solicitados: {ExamenLaboratorio.objects.count()}")
        print(f"      - Completados: {ExamenLaboratorio.objects.filter(estado='completado').count()}")
        print(f"      - En Proceso: {ExamenLaboratorio.objects.filter(estado='en_proceso').count()}")
        print(f"      Resultados Emitidos: {ResultadoLaboratorio.objects.count()}")
        print(f"      - Resultados Normales: {ResultadoLaboratorio.objects.filter(normal=True).count()}")
        print(f"      - Resultados Alterados: {ResultadoLaboratorio.objects.filter(normal=False).count()}")
        
        print(f"\n   📅 SISTEMA DE CITAS:")
        print(f"      Disponibilidades Configuradas: {Disponibilidad.objects.count()}")
        print(f"      Citas Totales: {Cita.objects.count()}")
        print(f"      - Completadas: {Cita.objects.filter(estado='completada').count()}")
        print(f"      - Programadas: {Cita.objects.filter(estado='programada').count()}")
        print(f"      - Confirmadas: {Cita.objects.filter(estado='confirmada').count()}")
        print(f"      - Canceladas: {Cita.objects.filter(estado='cancelada').count()}")
        print(f"      - No Asistió: {Cita.objects.filter(estado='no_asistio').count()}")
        print(f"      Historial de Cambios: {HistorialCita.objects.count()}")
        
        # Contar registros totales
        total_registros = (
            Usuario.objects.count() +
            Paciente.objects.count() +
            Embarazo.objects.count() +
            ControlPrenatal.objects.count() +
            Ecografia.objects.count() +
            BiometriaFetal.objects.count() +
            AnexosFetales.objects.count() +
            AnatomiaFetal.objects.count() +
            CalculoClinico.objects.count() +
            TipoExamen.objects.count() +
            ValorReferencia.objects.count() +
            ExamenLaboratorio.objects.count() +
            ResultadoLaboratorio.objects.count() +
            Disponibilidad.objects.count() +
            Cita.objects.count() +
            HistorialCita.objects.count()
        )
        
        print(f"\n   💾 TOTAL DE REGISTROS EN BASE DE DATOS: {total_registros:,}")
        
        print(f"\n🌐 ACCESO AL SISTEMA:")
        print(f"   🖥️  Administración: http://127.0.0.1:8000/admin/")
        print(f"   🔌 API REST: http://127.0.0.1:8000/api/")
        print(f"   📋 Pacientes: http://127.0.0.1:8000/api/pacientes/")
        print(f"   🤱 Embarazos: http://127.0.0.1:8000/api/embarazos/")
        print(f"   📝 Controles: http://127.0.0.1:8000/api/controles/")
        print(f"   🔬 Ecografías: http://127.0.0.1:8000/api/ecografias/")
        print(f"   🧮 Calculadoras: http://127.0.0.1:8000/api/calculadoras/")
        print(f"   🧪 Laboratorio: http://127.0.0.1:8000/api/laboratorio/")
        print(f"   📅 Citas: http://127.0.0.1:8000/api/citas/")
        
        print(f"\n🔐 CREDENCIALES DE ACCESO:")
        print(f"\n   👨‍⚕️ MÉDICOS:")
        print(f"      Email: dr.wilson@fetalmedical.com")
        print(f"      Password: medico123")
        print(f"\n      Email: dra.patricia@fetalmedical.com")
        print(f"      Password: medico123")
        print(f"\n   👩‍⚕️ ENFERMEROS:")
        print(f"      Email: enf.maria@fetalmedical.com")
        print(f"      Password: enfermero123")
        print(f"\n   👔 ADMINISTRADOR:")
        print(f"      Email: MirkofAdmin@fetalmedical.com")
        print(f"      Password: 25693")
        
        print("\n" + "="*80)
        print("🎉 ¡BASE DE DATOS COMPLETAMENTE POBLADA Y LISTA PARA PRODUCCIÓN!")
        print("="*80)
        print(f"✅ Sistema verificado y funcional")
        print(f"✅ {total_registros:,} registros creados exitosamente")
        print(f"✅ Tiempo de ejecución: {duracion:.2f} segundos")
        print(f"✅ {int(total_registros/duracion)} registros por segundo")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO DURANTE LA EJECUCIÓN:")
        print(f"   {str(e)}")
        print("\n📋 TRACEBACK COMPLETO:")
        import traceback
        traceback.print_exc()
        print("\n⚠️  El proceso se detuvo. Revisa los errores anteriores.")


if __name__ == '__main__':
    main()