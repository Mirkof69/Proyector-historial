"""Límites de tasa de la API.

Por qué existe este módulo
--------------------------
El login ya tenía bloqueo de cuenta: 5 intentos fallidos y la cuenta queda
bloqueada 15 minutos. Eso frena adivinar UNA contraseña, pero por sí solo abre
otra puerta: como no había ningún límite por IP, un atacante podía recorrer la
lista de usuarios haciendo 5 intentos contra cada uno y **dejar sin acceso a
todo el personal del hospital**. En una emergencia obstétrica eso es una
denegación de servicio contra el equipo médico, no una molestia.

Limitar por IP corta ese recorrido antes de que alcance a bloquear cuentas
ajenas. Las dos protecciones son complementarias: el bloqueo de cuenta defiende
la contraseña, el límite por IP defiende la disponibilidad.

Por qué el límite cuenta SOLO los fallos
----------------------------------------
La primera versión contaba todos los intentos, y eso rompía justo el caso para
el que se construyó el sistema. Medido con 100 usuarias simultáneas contra el
servidor real: **23 recibieron 429 y no pudieron entrar**, y como se quedaron
sin sesión, sus 1.249 peticiones siguientes fueron 401.

La causa es la topología de una clínica: todo el personal sale a la red por una
sola IP. Para Django, cien enfermeras en el cambio de turno son cien peticiones
desde la misma dirección. Con 20/min, entraban veinte y ochenta se quedaban
fuera —sin haber hecho nada malo y sin ningún error en los logs, solo un 429
que el personal lee como "el sistema no anda".

Subir la tasa no sirve: devuelve el ataque en la misma proporción. Lo que
distingue al atacante del turno de la mañana no es cuántas veces entra, sino
**si acierta**. Quien recorre una lista de usuarios genera fallos; quien viene
a trabajar genera aciertos. Así que el cupo lo gastan solo los fallos:

  - Cien inicios de sesión correctos consumen cero. La clínica entra entera.
  - Veinte intentos fallidos desde una IP la cortan, igual que antes.

`allow_request` comprueba el cupo sin gastarlo, y la vista llama a
`registrar_fallo()` cuando las credenciales no son válidas.
"""
from __future__ import annotations

from rest_framework.throttling import SimpleRateThrottle


class LoginRateThrottle(SimpleRateThrottle):
    """Limita los intentos FALLIDOS de autenticación por dirección IP.

    La tasa se define en `REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["login"]` y
    queda desactivada en los tests para no volver frágil la suite.

    Por qué NO hereda de `AnonRateThrottle`
    ---------------------------------------
    Parecía la clase natural —quien llama al login no está autenticado— pero su
    `get_cache_key` empieza así:

        if request.user and request.user.is_authenticated:
            return None  # Only throttle unauthenticated requests.

    Devolver `None` desactiva el límite. Y al login se puede llegar con sesión
    ya iniciada, así que bastaba **tener una cuenta cualquiera** para saltarse
    la protección entera: iniciar sesión una vez con credenciales propias y,
    desde ahí, probar contraseñas ajenas sin límite ninguno. Justo el ataque
    que este módulo existe para cortar.

    Lo destapó `test_los_fallos_siguen_gastando_cupo_aunque_haya_aciertos_de_por_medio`:
    el login correcto que hay entre los fallos dejaba autenticado al cliente y
    los intentos siguientes ya no contaban.

    Heredando de `SimpleRateThrottle` y fijando la clave a la IP, el límite se
    aplica siempre, con sesión o sin ella.
    """

    scope = "login"

    def get_cache_key(self, request, view):
        """Siempre la IP de origen, esté o no autenticada la petición."""
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }

    def allow_request(self, request, view):
        """Deja pasar la petición si a esta IP le queda cupo, sin gastarlo.

        Es la única diferencia con `SimpleRateThrottle`: la clase de DRF apunta
        el intento aquí mismo, de modo que un login correcto también gasta. Al
        no apuntarlo, el cupo queda reservado para lo que de verdad hay que
        frenar, y lo consume `registrar_fallo()`.
        """
        if self.rate is None:
            return True

        self.key = self.get_cache_key(request, view)
        if self.key is None:
            return True

        self.history = self.cache.get(self.key, self.cache_format and [])
        if not isinstance(self.history, list):
            self.history = []
        self.now = self.timer()

        # Descartar los intentos que ya salieron de la ventana de tiempo.
        while self.history and self.history[-1] <= self.now - self.duration:
            self.history.pop()

        if len(self.history) >= self.num_requests:
            return self.throttle_failure()
        return True

    def registrar_fallo(self, request, view=None) -> None:
        """Apunta un intento fallido contra el cupo de esta IP.

        La llama la vista de login cuando las credenciales no son válidas. Es
        seguro llamarla aunque `allow_request` no haya llegado a ejecutarse
        —por ejemplo desde un test— porque rellena lo que le falte.

        Nunca lanza excepción: si la caché no está disponible, el login tiene
        que seguir funcionando. Se pierde el límite, no el acceso al sistema.
        """
        if self.rate is None:
            return
        try:
            if getattr(self, "key", None) is None:
                self.key = self.get_cache_key(request, view)
                if self.key is None:
                    return
                self.history = self.cache.get(self.key, [])
                if not isinstance(self.history, list):
                    self.history = []
                self.now = self.timer()
            self.history.insert(0, self.now)
            self.cache.set(self.key, self.history, self.duration)
        except Exception:  # noqa: BLE001 - la caida de la cache no puede tumbar el login
            return


def registrar_intento_fallido(request) -> None:
    """Atajo para las vistas: apunta un fallo de login contra la IP que llama.

    Existe para que la vista no tenga que instanciar el throttle a mano y para
    que, si mañana se añade otro endpoint de autenticación, contar el fallo sea
    una sola línea.
    """
    throttle = LoginRateThrottle()
    throttle.registrar_fallo(request)
