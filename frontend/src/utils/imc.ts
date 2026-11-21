/**
 * IMC en kg/m² redondeado a 2 decimales (talla en metros). Sin redondear,
 * 64 kg y 1,60 m dan 24,999999999999996 porque 1,6² no es exacto en coma
 * flotante, y un IMC de 25,0 se clasificaba «Normal» en vez de «Sobrepeso».
 */
export const imcRedondeado = (pesoKg: number, tallaM: number): number =>
  Math.round((pesoKg / (tallaM * tallaM)) * 100) / 100;
