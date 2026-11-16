# Control Celular

Usá tu celular Android como **control de juegos para la PC**. Windows, Steam y los emuladores lo reconocen como un
**control de Xbox 360 de verdad**, enchufado por USB.

- Funciona por el **WiFi de tu casa**, con poca demora y sin internet.
- Es una página web liviana que se instala como app. Anda bien en celulares poco potentes.
- Trae tres tipos de control:
  - **completo** (estilo Xbox);
  - **alargado** (de una mano, acostado);
  - **por juego**: lee tu biblioteca de Steam y arma un control según el tipo de juego.
- Tiene **giroscopio** (volante y apuntar), **vibración** y un **editor** para mover, agrandar, pintar y cambiar
  cualquier botón.

---

## Qué necesitás

| | |
|---|---|
| **PC** | Windows 10 u 11 |
| **Python** | 3.10 o más nuevo: [python.org/downloads](https://www.python.org/downloads/). Al instalarlo, marcá **«Add python.exe to PATH»**. |
| **Celular** | Android con Chrome |
| **Red** | La PC y el celular conectados a la **misma red** (el WiFi de tu casa, o el hotspot del celular) |

---

## Instalación en la PC (una sola vez)

1. **Descargá el proyecto.** En GitHub, tocá el botón verde **Code → Download ZIP** y descomprimilo en una carpeta.
   Si usás git, también podés clonarlo.
2. **Ejecutá `instalar.bat`** con doble clic.
   - Crea un entorno de Python propio del proyecto (`.venv`) e instala las librerías.
   - Si se abre el instalador de **ViGEmBus** (el driver del control virtual), aceptá y seguí los pasos.
3. **Ejecutá `permitir-firewall.bat`** con doble clic y aceptá el permiso de administrador.
   - Abre los puertos **8765** y **8443** solo en redes **privadas** y solo para los equipos de tu red.
   - Te pregunta si querés marcar tu red como **privada**. Decí que sí **solo si es la red de tu casa**.

> **Si al iniciar aparece «Falta el driver ViGEmBus»**, instalalo a mano desde
> [github.com/nefarius/ViGEmBus/releases](https://github.com/nefarius/ViGEmBus/releases) (el archivo
> `ViGEmBus_..._x64_x86_arm64.exe`) y volvé a abrir `iniciar.bat`.

---

## Usarlo

### En la PC (cada vez)

Ejecutá **`iniciar.bat`**. Se abre una ventana como esta:

```
  CONTROL CELULAR listo
  Control (app):         https://192.168.0.10:8443
  Primera vez / ayuda:   http://192.168.0.10:8765
  Código de emparejamiento:  1234
```

Dejá esa ventana abierta mientras juegues. Para cerrar el control, cerrala o apretá `Ctrl+C`.

### En el celular (la primera vez)

1. Abrí en Chrome la dirección de **«Primera vez / ayuda»**: la de `http://` con el puerto `:8765`.
2. Seguí los 3 pasos de esa página para instalar el **certificado**. Esto es necesario para la app y el giroscopio.
   - Tocá **Descargar certificado**.
   - En **Ajustes** del celular, buscá «certificado de CA» → **Instalar certificado → Certificado de CA** → elegí
     `control-celular-ca.crt`.
   - Volvé a la página: detecta sola que el certificado está instalado y te lleva al control.
3. Escribí el **código de emparejamiento** que aparece en la PC. Se pide solo la primera vez.
4. En el menú **☰**, tocá **Instalar app**. Si no aparece, usá el menú de Chrome → **Instalar app**.

Después de la primera vez, abrís la app y se conecta sola. El puntito de arriba se pone **verde** cuando está
conectada.

> **¿No querés instalar el certificado?** Podés usar el control igual, desde la dirección `http://...:8765`, tocando
> «control sin app ni giroscopio». Sin el certificado no hay app instalada ni giroscopio.

---

## Qué tiene el menú ☰

- **Elegí el control:**
  - **Completo (Xbox):** dos sticks, cruceta, A/B/X/Y, gatillos y Start/Select.
  - **Alargado:** de una mano y acostado, con cruceta, 1, 2, A, B, + / inicio / − y Derrape.
  - **Por juego (Steam):** muestra tus juegos instalados con su portada. Al tocar uno se arma un control según su
    tipo: carreras, disparos, plataformas, deportes, pelea o completo. Si la opción está prendida, el control
    cambia solo cuando abrís un juego en la PC. En «Control para…» podés elegir otro tipo.
- **Editor de control:** tocá un botón para cambiarle el tamaño, la forma, el color, qué botón manda o el texto,
  y arrastralo para moverlo. También podés agregar botones, sticks y crucetas. Mientras editás, no se manda nada
  a la PC. Cada control guarda su propia edición.
- **Giroscopio:**
  - **Volante:** inclinás el celular y mueve el stick izquierdo.
  - **Apuntar:** movés el celular y mueve el stick derecho.
  - Se ajusta con sensibilidad e invertir.
- **Vibración:** al tocar los botones, y cuando el juego hace vibrar el control.

---

## Problemas comunes

| Pasa esto | Probá esto |
|---|---|
| El celular no abre la página | Fijate que la PC y el celular estén en la **misma red**, que hayas ejecutado `permitir-firewall.bat` y que la red sea **Privada** (Configuración → Red e Internet → tu red). |
| «Falta el driver ViGEmBus» | Instalalo desde [ViGEmBus releases](https://github.com/nefarius/ViGEmBus/releases) y volvé a abrir `iniciar.bat`. |
| La página dice «certificado todavía no está instalado» | Repetí el paso 2. Android puede pedir que tengas un bloqueo de pantalla (PIN o patrón). |
| Cambié de red y la app no abre | La IP de la PC cambió. Abrí la dirección nueva que muestra `iniciar.bat` (el certificado no hace falta reinstalarlo) y volvé a emparejar. |
| El giroscopio va al revés | En ☰, activá «Invertir horizontal» o «Invertir vertical». |
| No anda en el WiFi de un bar, la facu o un hotel | Es normal: esas redes no dejan que los equipos se vean entre sí, y por seguridad el control no abre puertos en redes públicas. Usá el hotspot de tu celular. |
| El juego no reconoce el control | Abrí `iniciar.bat` **antes** que el juego. En Steam: Configuración → Control, tiene que aparecer un «Xbox 360 Controller». |

---

## Seguridad

- Todo funciona **dentro de tu red local**. No se conecta a internet ni manda tu biblioteca de Steam a ningún lado.
- Para conectarse, un celular tiene que conocer el **código de emparejamiento**, que solo aparece en tu pantalla.
- El certificado lo crea tu propia PC la primera vez (queda en `certs/`). Está **restringido a direcciones de redes
  privadas**: aunque alguien lo robara, no serviría para hacerse pasar por ningún sitio de internet.
- Los puertos se abren solo en redes **privadas**.
- **No compartas** la carpeta `certs/` ni el archivo `tokens.json`: son privados de tu PC y ya están excluidos del repo.

---

## Cómo está hecho (para curiosos)

| Archivo | Qué hace |
|---|---|
| `server.py` | Servidor: crea el control virtual (vgamepad + ViGEmBus), sirve la página y recibe los botones por WebSocket |
| `certs.py` | Crea el certificado propio para HTTPS en la red local |
| `steam.py` | Lee la biblioteca de Steam de la PC (juegos, tipo, portadas, juego abierto) |
| `web/index.html` | El control del celular (HTML, CSS y JavaScript puro, sin librerías) |
| `web/plantillas.js` | Los controles: completo, alargado, uno por tipo de juego y perfiles propios por juego |
| `web/configurar.html` | La página de la primera vez (instalar el certificado) |
| `instalar.bat`, `permitir-firewall.bat`, `iniciar.bat` | Instalar, abrir el firewall y arrancar |

Para agregar un control propio para un juego, sumalo en `PERFILES` dentro de `web/plantillas.js` con su número de
Steam (appid).
