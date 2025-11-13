from django.core.management.base import BaseCommand
from citas.models import Disponibilidad, Cita
from usuarios.models import Usuario
from pacientes.models import Paciente
from datetime import time, date, timedelta, datetime
from django.utils import timezone


class Command(BaseCommand):
    help = 'Crea datos iniciales de citas y disponibilidades'
    
    def handle(self, *args, **kwargs):
        self.stdout.write('Creando datos de citas...')
        
        # Obtener médicos
        medicos = Usuario.objects.filter(rol='medico')
        
        if not medicos.exists():
            self.stdout.write(self.style.ERROR('No hay médicos en el sistema'))
            return
        
        # Crear disponibilidades para cada médico
        for medico in medicos:
            # Lunes a Viernes: 8:00 - 12:00
            for dia in range(5):  # 0-4 (Lunes a Viernes)
                Disponibilidad.objects.get_or_create(
                    medico=medico,
                    dia_semana=dia,
                    hora_inicio=time(8, 0),
                    hora_fin=time(12, 0),
                    defaults={
                        'duracion_cita': 30,
                        'activo': True,
                    }
                )
            
            # Lunes, Miércoles, Viernes: 14:00 - 18:00
            for dia in [0, 2, 4]:
                Disponibilidad.objects.get_or_create(
                    medico=medico,
                    dia_semana=dia,
                    hora_inicio=time(14, 0),
                    hora_fin=time(18, 0),
                    defaults={
                        'duracion_cita': 30,
                        'activo': True,
                    }
                )
        
        self.stdout.write(self.style.SUCCESS('✅ Disponibilidades creadas'))
        
        # Crear algunas citas de ejemplo
        pacientes = Paciente.objects.filter(activo=True)[:5]
        medico = medicos.first()
        
        if pacientes.exists() and len(pacientes) >= 3:
            # Usar timezone.now() para obtener fecha/hora actual con zona horaria
            ahora = timezone.now()
            hoy = ahora.date()
            
            # Calcular próxima fecha disponible (mañana si hoy es fin de semana)
            manana = hoy + timedelta(days=1)
            while manana.weekday() >= 5:  # Si es sábado o domingo
                manana += timedelta(days=1)
            
            # Próxima semana
            proxima_semana = hoy + timedelta(days=7)
            while proxima_semana.weekday() >= 5:  # Si es sábado o domingo
                proxima_semana += timedelta(days=1)
            
            # Solo crear citas si no existen
            try:
                # Cita para mañana a las 9:00
                cita1, created1 = Cita.objects.get_or_create(
                    paciente=pacientes[0],
                    medico=medico,
                    fecha_cita=manana,
                    hora_cita=time(9, 0),
                    defaults={
                        'duracion': 30,
                        'tipo_cita': 'control',
                        'estado': 'confirmada',
                        'motivo': 'Control prenatal rutinario',
                    }
                )
                if created1:
                    self.stdout.write(self.style.SUCCESS(f'✅ Cita creada para {manana}'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠️ No se pudo crear cita 1: {e}'))
            
            try:
                # Cita para mañana a las 10:00
                cita2, created2 = Cita.objects.get_or_create(
                    paciente=pacientes[1],
                    medico=medico,
                    fecha_cita=manana,
                    hora_cita=time(10, 0),
                    defaults={
                        'duracion': 30,
                        'tipo_cita': 'primera_vez',
                        'estado': 'agendada',
                        'motivo': 'Primera consulta',
                    }
                )
                if created2:
                    self.stdout.write(self.style.SUCCESS(f'✅ Cita creada para {manana}'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠️ No se pudo crear cita 2: {e}'))
            
            try:
                # Cita para la próxima semana
                cita3, created3 = Cita.objects.get_or_create(
                    paciente=pacientes[2],
                    medico=medico,
                    fecha_cita=proxima_semana,
                    hora_cita=time(11, 0),
                    defaults={
                        'duracion': 30,
                        'tipo_cita': 'seguimiento',
                        'estado': 'agendada',
                        'motivo': 'Seguimiento de tratamiento',
                    }
                )
                if created3:
                    self.stdout.write(self.style.SUCCESS(f'✅ Cita creada para {proxima_semana}'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠️ No se pudo crear cita 3: {e}'))
            
            self.stdout.write(self.style.SUCCESS('✅ Citas de ejemplo procesadas'))
        else:
            self.stdout.write(self.style.WARNING('⚠️ No hay suficientes pacientes para crear citas de ejemplo'))
        
        self.stdout.write(self.style.SUCCESS('✅ Datos de citas creados exitosamente'))