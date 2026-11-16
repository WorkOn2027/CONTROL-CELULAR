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
| **Celular** | Android con Chrome |
| **Red** | La PC y el celular conectados a la **misma red** (el WiFi de tu casa, o el hotspot del celular) |
| **Driver** | **ViGEmBus** (gratis): es lo que crea el control de Xbox virtual. Si no lo tenés, el programa te avisa y te abre la página para descargarlo. |

---

## Instalación en la PC

### Opción fácil: descargar el programa (recomendada)

1. Entrá a **[Releases](../../releases/latest)** y descargá **`ControlCelular.exe`**. Es un solo archivo y no hace
   falta instalar Python ni nada más.
2. Abrilo con doble clic. Podés dejarlo en cualquier carpeta, incluso en Descargas.
   - Windows puede mostrar **«Windows protegió su PC»**, porque el programa no está firmado. Tocá **Más información →
     Ejecutar de todas formas**.
   - La primera vez te pregunta si querés **abrir el firewall** (solo para la red de tu casa) y, si tu red está como
     «Pública», si querés marcarla como **privada**. Respondé **S**, solo si es la red de tu casa, y aceptá el
     permiso de Windows.
   - Si falta **ViGEmBus**, te abre la página oficial. Descargá `ViGEmBus_..._x64_x86_arm64.exe`, instalalo y volvé a
     abrir Control Celular.

Tus datos (el certificado y los celulares emparejados) se guardan en `%LOCALAPPDATA%\ControlCelular`.

### Opción con Python (para quien quiera ver o cambiar el código)

1. Instalá **Python 3.10 o más nuevo** desde [python.org/downloads](https://www.python.org/downloads/). Al
   instalarlo, marcá **«Add python.exe to PATH»**.
2. Descargá el proyecto: botón verde **Code → Download ZIP**, y descomprimilo. También podés usar `git clone`.
3. Ejecutá **`iniciar.bat`**. La primera vez instala todo solo (`.venv` y librerías). Después hace las mismas
   preguntas del firewall que el programa.

Para armar tu propio `ControlCelular.exe`, ejecutá **`construir.bat`**. Lo deja en la carpeta `dist\`.

---

## Usarlo

### En la PC (cada vez)

Abrí **Control Celular**: `ControlCelular.exe`, o `iniciar.bat` si usás la opción con Python. La ventana muestra un
**código QR**, la dirección y el código de emparejamiento. Al lado del reloj de Windows aparece el **ícono del
control**, con este menú:

- **Mostrar QR para conectar:** abre el QR en grande, en el navegador de la PC.
- **Mostrar la ventana:** muestra u oculta la ventana negra.
- **Iniciar con Windows:** arranca solo al prender la PC, oculto, sin la ventana.
- **Salir.**

Al pasar el mouse por el ícono, te dice qué jugadores están conectados.

### En el celular (la primera vez)

1. **Escaneá el QR** con la cámara del celular, o abrí en Chrome la dirección `http://…:8765` que muestra la PC.
2. Seguí los pasos de esa página para instalar el **certificado**, necesario para la app y el giroscopio. La página
   reconoce la marca de tu celular (Samsung, Xiaomi, Motorola…) y te muestra el camino exacto en Ajustes. Cuando
   lo instalás, lo detecta sola y te lleva al control.
3. Si llegaste por el QR, **se empareja solo**. Si no, escribí el código de emparejamiento que muestra la PC.
4. Aparece un **tutorial corto**. Después, en el menú **☰** tocá **Instalar app**. Si no aparece, usá el menú de
   Chrome → **Instalar app**.

Después de la primera vez, abrís la app y se conecta sola. Arriba se ve un puntito **verde** cuando está conectada,
tu **número de jugador** (J1, J2…) y la **demora** en milisegundos. Si la demora pasa de 80 ms, se pone en naranja:
el WiFi anda lento.

> **¿No querés instalar el certificado?** Podés usar el control igual, desde la dirección `http://...:8765`, tocando
> «control sin app ni giroscopio». Sin el certificado no hay app instalada ni giroscopio.

### Varios jugadores

Se pueden conectar **hasta 4 celulares a la vez**. Cada uno es un control de Xbox distinto (jugador 1, 2, 3 y 4).
Cada celular, cuando vuelve, recupera siempre su mismo número.

### Tus ajustes quedan en la PC

Las ediciones del control y las opciones se guardan **en la PC**, no solo en el celular. Si cambiás de celular, si
cambia la IP de la PC o si reinstalás la app, al conectarte recuperás todo como lo dejaste.

---

## Qué tiene el menú ☰

- **Elegí el control:**
  - **Completo (Xbox):** dos sticks, cruceta, A/B/X/Y, gatillos y Start/Select.
  - **Alargado:** de una mano y acostado, con cruceta, 1, 2, A, B, + / inicio / − y Derrape.
  - **Por juego (Steam):** muestra tus juegos instalados con su portada. Al tocar uno se arma un control según su
    tipo: carreras, disparos, plataformas, deportes, pelea o completo. Si la opción está prendida, el control
    cambia solo cuando abrís un juego en la PC. En «Control para…» podés elegir otro tipo.
- **Editor de control:**
  - tocá un botón para cambiarle el tamaño, la forma, el color, qué botón manda o el texto, y arrastralo para
    moverlo;
  - podés agregar botones, sticks y crucetas;
  - tiene **Deshacer** y una **Cuadrícula** para alinear los botones;
  - mientras editás, no se manda nada a la PC, y cada control guarda su propia edición.
- **Giroscopio:**
  - **Volante:** inclinás el celular y mueve el stick izquierdo.
  - **Apuntar:** movés el celular y mueve el stick derecho.
  - Se ajusta con sensibilidad e invertir.
- **Vibración:** al tocar los botones, y cuando el juego hace vibrar el control.
- **Ver tutorial:** repite la guía del primer uso.

---

## Problemas comunes

| Pasa esto | Probá esto |
|---|---|
| El celular no abre la página | Fijate que la PC y el celular estén en la **misma red**. Cerrá y volvé a abrir Control Celular, y respondé **S** a abrir el firewall y a marcar la red como privada. También se cambia a mano en Configuración → Red e Internet → tu red → **Privada**. |
| «Falta el driver ViGEmBus» | Instalalo desde [ViGEmBus releases](https://github.com/nefarius/ViGEmBus/releases) y volvé a abrir Control Celular. |
| «Windows protegió su PC» | Es porque el programa no está firmado. Tocá **Más información → Ejecutar de todas formas**. Si no confiás, usá la opción con Python, que es el mismo código a la vista. |
| El antivirus lo bloquea | Pasa a veces con programas armados con PyInstaller. Podés usar la opción con Python, o armar vos el `.exe` con `construir.bat`. |
| «Control Celular ya está abierto» | Ya hay otra ventana del programa abierta. Usá esa, o cerrala antes. |
| La página dice «certificado todavía no está instalado» | Repetí el paso 2. Android puede pedir que tengas un bloqueo de pantalla (PIN o patrón). |
| Cambié de red y la app no abre | La IP de la PC cambió. Abrí la dirección nueva que muestra `iniciar.bat` (el certificado no hace falta reinstalarlo) y volvé a emparejar. |
| El giroscopio va al revés | En ☰, activá «Invertir horizontal» o «Invertir vertical». |
| No anda en el WiFi de un bar, la facu o un hotel | Es normal: esas redes no dejan que los equipos se vean entre sí, y por seguridad el control no abre puertos en redes públicas. Usá el hotspot de tu celular. |
| El juego no reconoce el control | Abrí `iniciar.bat` **antes** que el juego. En Steam: Configuración → Control, tiene que aparecer un «Xbox 360 Controller». |

---

## Seguridad

- Todo funciona **dentro de tu red local**. No se conecta a internet ni manda tu biblioteca de Steam a ningún lado.
- Para conectarse, un celular tiene que conocer el **código de emparejamiento**, que solo aparece en tu pantalla.
  El QR lleva ese código adentro: por eso la página del QR solo se abre desde la propia PC. El código cambia cada
  vez que abrís el programa.
- El certificado lo crea tu propia PC la primera vez (queda en `%LOCALAPPDATA%\ControlCelular\certs`, o en `certs/`
  con la opción de Python). Está **restringido a direcciones de redes
  privadas**: aunque alguien lo robara, no serviría para hacerse pasar por ningún sitio de internet.
- Los puertos se abren solo en redes **privadas**.
- **No compartas** la carpeta `certs/` ni el archivo `tokens.json`: son privados de tu PC y ya están excluidos del repo.

---

## Cómo está hecho (para curiosos)

| Archivo | Qué hace |
|---|---|
| `server.py` | Servidor: crea el control virtual (vgamepad + ViGEmBus), sirve la página y recibe los botones por WebSocket |
| `bandeja.py` | El ícono al lado del reloj (QR, mostrar u ocultar la ventana, iniciar con Windows, salir) |
| `red.py` | Revisa el firewall y si la red es privada; si falta algo, pregunta y lo arregla con permiso de Windows |
| `rutas.py` | Dónde están los archivos, tanto en Python como en el `.exe` |
| `certs.py` | Crea el certificado propio para HTTPS en la red local |
| `steam.py` | Lee la biblioteca de Steam de la PC (juegos, tipo, portadas, juego abierto) |
| `web/index.html` | El control del celular (HTML, CSS y JavaScript puro, sin librerías) |
| `web/plantillas.js` | Los controles: completo, alargado, uno por tipo de juego y perfiles propios por juego |
| `web/configurar.html` | La página de la primera vez (instalar el certificado) |
| `iniciar.bat`, `instalar.bat` | Arrancar con Python (la primera vez instala solo) |
| `construir.bat` | Arma `dist\ControlCelular.exe` con PyInstaller |

Para agregar un control propio para un juego, sumalo en `PERFILES` dentro de `web/plantillas.js` con su número de
Steam (appid).
