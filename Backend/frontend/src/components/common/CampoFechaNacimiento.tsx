import React from 'react';
import { DatePicker } from 'antd';
import type { DatePickerProps } from 'antd';
import type { Rule } from 'antd/es/form';
import dayjs, { Dayjs } from 'dayjs';
import locale from 'antd/es/date-picker/locale/es_ES';

/**
 * Fecha de nacimiento de la paciente.
 *
 * Con máscara: al escribir solo dígitos se completa DD/MM/AAAA y no se puede
 * escribir otra cosa (antes el campo aceptaba «3521651653106» y al salir lo
 * borraba sin avisar). El calendario abre 25 años atrás, no en el mes actual.
 * Mismos límites que el backend (pacientes/serializers.py): ni futura, entre 10 y 100 años.
 * Sin disabledDate a propósito: con él, un año tecleado fuera de rango volvía al
 * valor anterior sin decir nada; así lo explica el validador. El Form.Item usa
 * validateTriggerFechaNacimiento para avisar también al salir del campo.
 */
const EDAD_MINIMA = 10;
const EDAD_MAXIMA = 100;

export const validateTriggerFechaNacimiento = ['onChange', 'onBlur'];

export const reglasFechaNacimiento: Rule[] = [
  { required: true, message: 'Escriba o elija la fecha de nacimiento (DD/MM/AAAA)' },
  {
    validator: (_, valor: Dayjs | null) => {
      if (!valor) return Promise.resolve();
      if (!valor.isValid()) return Promise.reject(new Error('Fecha inválida: use DD/MM/AAAA'));
      if (valor.isAfter(dayjs(), 'day')) return Promise.reject(new Error('La fecha de nacimiento no puede ser futura'));
      const edad = dayjs().diff(valor, 'year');
      if (edad < EDAD_MINIMA) return Promise.reject(new Error(`La paciente debe tener al menos ${EDAD_MINIMA} años`));
      if (edad > EDAD_MAXIMA) return Promise.reject(new Error(`Revise el año: daría ${edad} años`));
      return Promise.resolve();
    },
  },
];

const CampoFechaNacimiento: React.FC<DatePickerProps> = (props) => (
  <DatePicker
    style={{ width: '100%' }}
    format={{ format: 'DD/MM/YYYY', type: 'mask' }}
    placeholder="DD/MM/AAAA"
    locale={locale}
    defaultPickerValue={dayjs().subtract(25, 'year')}
    {...props}
  />
);

export default CampoFechaNacimiento;
