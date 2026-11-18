# Control Celular

*[Read in English](README.en.md)*

Usá tu celular Android o tu iPhone como **control de juegos para la PC**. Windows, Steam y los emuladores lo reconocen como un
**control de Xbox 360 de verdad**, enchufado por USB.

- Funciona por el **WiFi de tu casa**, con poca demora y sin internet.
- Es una página web liviana que se instala como app. Anda bien en celulares poco potentes.
- Trae tres tipos de control:
  - **completo** (estilo Xbox);
  - **alargado** (de una mano, acostado);
  - **por juego**: lee tu biblioteca de Steam y arma un control según el tipo de juego.
- Tiene **giroscopio** (volante, apuntar y movimiento real de DualShock 4), **vibración** (Android), **hasta 4
  jugadores** y un **editor** para mover, agrandar, pintar y cambiar cualquier botón.
- Está en **español e inglés**: sigue el idioma del celular y el de Windows.

---

## Qué necesitás

| | |
|---|---|
| **PC** | Windows 10 u 11 |
| **Celular** | Android con Chrome, o iPhone con Safari |
| **Red** | La PC y el celular conectados a la **misma red** (el WiFi de tu casa, o el hotspot del celular) |
| **Driver** | **ViGEmBus**: es lo que crea el control virtual. **Viene incluido**: si no lo tenés, el programa te ofrece instalarlo. |

---

## Instalación en la PC

### Opción fácil: el instalador (recomendada)

1. Entrá a **[Releases](../../releases/latest)** y descargá **`ControlCelular-Instalar-….exe`**.
2. Abrilo y tocá **Siguiente → Instalar**. Windows pide permiso una sola vez, y el instalador deja todo listo:
   - instala **ViGEmBus**, el driver del control virtual, si falta;
   - abre el firewall solo para Control Celular y solo para la red de tu casa (ande la red como «Privada» o como
     «Pública»), y saca cualquier bloqueo de Windows;
   - crea el ícono en el escritorio y en el menú Inicio;
   - si ya tenías una versión anterior, la reemplaza y (casilla marcada) borra los instaladores y versiones
     portátiles viejas de Descargas y Escritorio. Tus ajustes no se tocan.
3. Al terminar, Control Celular se abre solo y muestra el QR: **escanealo con el celular y listo**.

Para desinstalarlo: «Agregar o quitar programas» → Control Celular. Saca también el firewall y el arranque con
Windows.

Si Windows muestra **«Windows protegió su PC»**, es porque el programa no está firmado: tocá **Más información →
Ejecutar de todas formas**.

### Opción portátil: sin instalar

1. En **[Releases](../../releases/latest)** descargá **`ControlCelular.exe`**: es un solo archivo.
2. Abrilo con doble clic. Podés dejarlo en cualquier carpeta, incluso en Descargas.
   - Windows puede mostrar **«Windows protegió su PC»**, porque el programa no está firmado. Tocá **Más información →
     Ejecutar de todas formas**.
   - La primera vez te pregunta si querés **abrir el firewall** (solo para la red de tu casa). Tocá **Sí** y aceptá
     el permiso de Windows.
   - Si falta **ViGEmBus**, el driver del control virtual, te pregunta **«¿Lo instalo ahora?»**. Tocá **Sí**,
     aceptá el permiso de Windows y tocá **Instalar** en su instalador. Viene incluido: es el instalador oficial,
     firmado por su autor. Al terminar, Control Celular se vuelve a abrir solo.

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

Abrí **Control Celular** (o `iniciar.bat` si usás la opción con Python). El control de neón se enciende en el
centro de la pantalla y después se abre la **ventana de Control Celular**:

- el **código QR** para escanear, el código de emparejamiento y la dirección (con botón para copiarla);
- los **4 lugares de jugador**: qué celular está en cada uno y si la PC lo ve como Xbox 360 o DualShock 4;
- el **juego de Steam** que está abierto;
- los **celulares emparejados**, con **Olvidar** para sacarle el permiso a uno o a todos;
- la **actividad**: quién se conectó, quién se fue, etc.;
- **⚙ Opciones:** abrir al prender la PC, avisar si hay una versión nueva (y descargarla) y **Apagar**.

Si cerrás la ventana, Control Celular **sigue funcionando** en el **ícono del control** al lado del reloj de
Windows. Un toque en el ícono vuelve a abrir la ventana (y si abrís el programa otra vez, también). El menú del
ícono tiene:

- **Abrir Control Celular:** la ventana.
- **Iniciar con Windows:** arranca solo al prender la PC, oculto, sin la ventana.
- **Celulares emparejados:** la lista de celulares con permiso para conectarse, para **olvidar** uno o todos. Un
  celular olvidado pierde el permiso y sus ajustes, y para volver a usarlo hay que emparejarlo con el QR.
- **Versión y desinstalar:**
  - la versión instalada y el aviso de **versión nueva** (con «Buscar versiones nuevas» lo apagás);
  - **Desinstalar…**: saca la regla del firewall, el arranque con Windows y tus datos, y te dice qué queda por
    borrar a mano.
- **Salir.**

Al pasar el mouse por el ícono, te dice qué jugadores están conectados.

### En el celular (la primera vez)

1. **Escaneá el QR** con la cámara del celular, o abrí en Chrome la dirección `http://…:8765` que muestra la PC.
   **Entrás directo al control** y se empareja solo: ya podés jugar.
2. **Opcional:** para instalarlo como app y usar el giroscopio, en el menú **☰** tocá **Activar app y
   giroscopio** y seguí los pasos para instalar el **certificado**. Cada celular tiene los suyos:
   - **Android:** la página reconoce la marca (Samsung, Xiaomi, Motorola…) y te muestra el camino exacto en Ajustes.
   - **iPhone:** usá **Safari**. El certificado se instala como un **perfil** y después hay que **activar la
     confianza** en Ajustes → General → Información → Configuración de confianza de certificados.
3. Si llegaste por el QR, **se empareja solo**. Si no, escribí el código de emparejamiento que muestra la PC.
4. Aparece un **tutorial corto**. Después instalala como app:
   - **Android:** en el menú **☰** tocá **Instalar app**. Si no aparece, usá el menú de Chrome → **Instalar app**.
   - **iPhone:** en Safari tocá **Compartir** → **Agregar a inicio**.

Después de la primera vez, abrís la app y se conecta sola. Arriba se ve un puntito **verde** cuando está conectada,
tu **número de jugador** (J1, J2…) y la **demora** en milisegundos. Si la demora pasa de 80 ms, se pone en naranja:
el WiFi anda lento.

> **¿No querés instalar el certificado?** Podés usar el control igual, desde la dirección `http://...:8765`, tocando
> «control sin app ni giroscopio». Sin el certificado no hay app instalada ni giroscopio.

### Lo distinto en iPhone

El iPhone tiene su propia versión de la página del control, en archivos aparte, así nunca se mezcla con la de Android:

- **No vibra:** Safari no deja que una página web vibre.
- **Giroscopio:** el iPhone pide permiso. Tocá **Permitir** en ⚙ Opciones → Giroscopio.
- **Instalar:** con **Agregar a inicio**. No hay botón de pantalla completa, porque la app instalada ya se abre así.

> La versión de iPhone está hecha siguiendo cómo funciona Safari, pero **todavía no se probó en un iPhone de
> verdad**. Si algo no anda, avisá.

### Varios jugadores

Se pueden conectar **hasta 4 celulares a la vez**. Cada uno es un control de Xbox distinto (jugador 1, 2, 3 y 4).
Cada celular, cuando vuelve, recupera siempre su mismo número.

### Tus ajustes quedan en la PC

Las ediciones del control y las opciones se guardan **en la PC**, separadas por celular: cada jugador tiene las
suyas. Si cambia la IP de la PC o reinstalás la app, al conectarte recuperás todo como lo dejaste.

¿Celular nuevo? En **☰ → Copiar ajustes de otro celular** elegís de cuál copiar (aparecen por su modelo) y te quedan
iguales.

---

## Los botones de arriba: ⚙ Opciones y ☰ Menú

Arriba al centro del control están el puntito de conexión y dos botones.

### ☰ Menú: elegir y hacer

- **Elegí el control:**
  - **Completo (Xbox):** dos sticks, cruceta, A/B/X/Y, gatillos y Start/Select.
  - **Alargado:** de una mano y acostado, con cruceta, 1, 2, A, B, + / inicio / − y Derrape.
  - **PS4 (DualShock 4):** con la forma de un control de PS4: touchpad grande, Share/Options, botón PS,
    △ ○ ✕ □ y los dos sticks juntos abajo. Al elegirlo, la PC lo ve como un DualShock 4.
  - **Por juego (Steam):** muestra tus juegos instalados con su portada. Al tocar uno se arma un control según su
    tipo: carreras, disparos, plataformas, deportes, pelea o completo. Si la opción está prendida, el control
    cambia solo cuando abrís un juego en la PC. En «Control para…» podés elegir otro tipo.
- **Editor de control:**
  - tocá un botón para cambiarle el tamaño, la forma, el color, qué botón manda o el texto, y arrastralo para
    moverlo;
  - podés agregar botones, sticks y crucetas;
  - tiene **Deshacer** y una **Cuadrícula** para alinear los botones;
  - cada botón puede ser **normal**, **⚡ turbo** (se aprieta y suelta solo, 10 veces por segundo, mientras lo
    mantenés) o **📌 fijo** (un toque lo deja apretado y otro lo suelta; sirve, por ejemplo, para acelerar sin
    tener el dedo encima);
  - mientras editás, no se manda nada a la PC, y cada control guarda su propia edición.
- **Copiar ajustes de otro celular:** trae los controles editados y las opciones de otro celular emparejado.
- **Ver tutorial**, **Pantalla completa** e **Instalar app**.

### ⚙ Opciones: una ventana con tres pestañas

- **General:**
  - **Vibrar al tocar** y **Vibración del juego**.
  - **Modo noche:** colores oscuros en todo, para jugar con poca luz. Apagado, el control es blanco.
  - **Modo zurdo:** da vuelta el control como un espejo. Los grupos de botones, como el rombo, mantienen su orden.
    El editor muestra el control al derecho.
  - **La PC lo ve como:** **Xbox 360**, o **DualShock 4** de PlayStation, para juegos y emuladores que lo
    prefieren. Con DualShock 4 los botones se muestran como ✕ ○ □ △, y el editor permite usar el touchpad.
- **Giroscopio:**
  - **Volante:** inclinás el celular y mueve el stick izquierdo. Tiene «Centrar».
  - **Apuntar:** movés el celular y mueve el stick derecho.
  - **Movimiento real** (solo DualShock 4): el celular funciona como el sensor de movimiento de un control de
    PlayStation. Lo usan Steam (el giroscopio de Steam Input) y emuladores como Cemu o Yuzu.
  - **Sensibilidad**, **invertir horizontal** e **invertir vertical**.
- **Sticks:** para cada stick, por separado:
  - **zona muerta:** cuánto hay que mover antes de que responda, para que no se mueva solo;
  - **respuesta:** suave (más precisa en movimientos chicos, ideal para apuntar), normal o rápida;
  - **recorrido:** cuánto hay que mover el dedo para llegar al máximo.

Todo se guarda para cada celular, también en la PC.

---

## Problemas comunes

| Pasa esto | Probá esto |
|---|---|
| El celular no abre la página | Fijate que la PC y el celular estén en la **misma red** (no la de «invitados») y apagá los datos móviles. Cerrá y volvé a abrir Control Celular y tocá **Sí** para abrir el firewall. |
| El celular dice `ERR_CONNECTION_TIMED_OUT` | Algo bloquea la conexión entre el celular y la PC: casi siempre un **antivirus con firewall propio** (Avast, AVG, Norton, McAfee, Kaspersky, ESET…). Permití Control Celular en su firewall, o probá con el antivirus en pausa un momento para confirmarlo. Si no hay antivirus, puede ser el router: probá con el hotspot del celular. |
| «Una directiva de Control de aplicaciones bloqueó este archivo» (código 4551) | Es el **Control inteligente de aplicaciones** de Windows 11: bloquea los programas sin firma digital y no tiene botón para abrirlos igual. Se apaga en Seguridad de Windows → Control de aplicaciones y navegador → Control inteligente de aplicaciones → **Desactivado**. Ojo: después Windows no deja volver a activarlo (salvo reinstalando Windows); la PC sigue protegida por el antivirus de Windows. |
| «Falta el driver ViGEmBus» | Tocá **Sí** cuando el programa ofrezca instalarlo. Si preferís hacerlo a mano: [ViGEmBus releases](https://github.com/nefarius/ViGEmBus/releases). Si después de instalarlo sigue sin reconocerlo, reiniciá la PC. |
| «Windows protegió su PC» | Es porque el programa no está firmado. Tocá **Más información → Ejecutar de todas formas**. Si no confiás, usá la opción con Python, que es el mismo código a la vista. |
| El antivirus lo bloquea | Pasa a veces con programas armados con PyInstaller. Podés usar la opción con Python, o armar vos el `.exe` con `construir.bat`. |
| No veo la ventana | Control Celular sigue abierto al lado del reloj: tocá su ícono, o volvé a abrir el programa (trae la misma ventana). |
| La página dice «certificado todavía no está instalado» | Repetí el paso 2. Android puede pedir que tengas un bloqueo de pantalla (PIN o patrón). |
| Cambié de red y la app no abre | La IP de la PC cambió. Abrí la dirección nueva que muestra la ventana de Control Celular (el certificado no hace falta reinstalarlo) y volvé a emparejar. |
| El giroscopio va al revés | En ☰, activá «Invertir horizontal» o «Invertir vertical». |
| No anda en el WiFi de un bar, la facu o un hotel | Es normal: esas redes no dejan que los equipos se vean entre sí. Usá el hotspot de tu celular. |
| El juego no reconoce el control | Abrí `iniciar.bat` **antes** que el juego. En Steam: Configuración → Control, tiene que aparecer un «Xbox 360 Controller». |

---

## Seguridad

- Todo funciona **dentro de tu red local**. No manda tu biblioteca de Steam ni ningún dato tuyo a ningún lado. Lo
  único que hace en internet es consultar la página pública de Releases de este proyecto en GitHub, para avisarte si
  hay una versión nueva; se apaga desde el ícono, en «Buscar versiones nuevas».
- Para conectarse, un celular tiene que conocer el **código de emparejamiento**, que solo aparece en tu pantalla.
  El QR lleva ese código adentro: por eso la página del QR solo se abre desde la propia PC. El código cambia cada
  vez que abrís el programa.
- **Límite de intentos:** cada 5 códigos equivocados desde un mismo equipo, queda bloqueado un rato, y el bloqueo se
  duplica cada vez (30 s, 1 min, 2 min… hasta 1 hora). Si hay muchos intentos fallidos en total, el código cambia
  solo y el nuevo aparece en la ventana y en el QR del ícono.
- Podés **olvidar** cualquier celular emparejado desde el ícono: pierde el permiso al instante.
- El certificado lo crea tu propia PC la primera vez (queda en `%LOCALAPPDATA%\ControlCelular\certs`, o en `certs/`
  con la opción de Python). Está **restringido a direcciones de redes
  privadas**: aunque alguien lo robara, no serviría para hacerse pasar por ningún sitio de internet.
- Los puertos se abren **solo para tu red local**: nadie de afuera (internet) puede llegar. Valen aunque Windows
  tenga tu red como «Pública», porque así marca casi toda red nueva; en una red ajena (un bar, un hotel), alguien
  de esa misma red podría ver la página, pero sin el código de emparejamiento no puede usar el control.
- **No compartas** la carpeta `certs/` ni el archivo `tokens.json`: son privados de tu PC y ya están excluidos del repo.

---

## Cómo está hecho (para curiosos)

| Archivo | Qué hace |
|---|---|
| `arranque.py` | El punto de entrada: si algo falla al arrancar (por ejemplo, falta ViGEmBus), lo explica en vez de cerrarse |
| `server.py` | Arma todo y atiende la conexión de cada celular |
| `mandos.py` | Los controles virtuales (Xbox 360 y DualShock 4) y la traducción de botones |
| `celulares.py` | Celulares emparejados, sus ajustes, el código y el límite de intentos |
| `paginas.py` | Las páginas web y el QR |
| `certs.py` | El certificado propio para HTTPS en la red local |
| `steam.py` | Lee la biblioteca de Steam de la PC (juegos, tipo, portadas, juego abierto) |
| `red.py` | Revisa la regla del firewall (solo red local, ande la red como privada o pública); si falta, pregunta y la crea con permiso de Windows |
| `bandeja.py` | El ícono al lado del reloj |
| `idioma.py`, `web/i18n.js` | El inglés, en la PC y en la página del control |
| `version.py`, `rutas.py` | La versión y el aviso de versión nueva; dónde están los archivos (Python o `.exe`) |
| `web/index.html`, `web/configurar.html` | El control y la guía del certificado (Android) |
| `web/iphone.html`, `web/configurar-iphone.html` | La versión de iPhone: **se generan solos**, no se editan a mano |
| `web/plantillas.js` | Los controles: completo, alargado, uno por tipo de juego y perfiles por juego |

### Para cambiar algo

1. Cambiá la versión de Android (`web/index.html` o `web/configurar.html`).
2. Corré `python herramientas/hacer_iphone.py`: genera la versión de iPhone con sus cambios propios. Así cada cambio
   se hace una sola vez y las dos versiones nunca quedan distintas.
3. Corré **`probar.bat`**: son más de 50 pruebas automáticas en unos 20 segundos. Prueban el servidor con controles
   de mentira, así que no hace falta ViGEmBus, y las páginas de Android e iPhone en un Chrome invisible. También
   revisan que ningún control tenga botones encimados. No tocan tus datos ni tus puertos.
4. `construir.bat` arma el instalador (`herramientas/instalador.iss`, necesita [Inno Setup 6](https://jrsoftware.org/isinfo.php))
   y la versión portátil. Antes corre las pruebas: si algo falla, no arma nada.

Para agregar un control propio para un juego, sumalo en `PERFILES` dentro de `web/plantillas.js` con su número de
Steam (appid).

## Software de terceros

Control Celular incluye, sin cambios, el instalador oficial de **[ViGEmBus](https://github.com/nefarius/ViGEmBus)**,
de Nefarius Software Solutions e.U., con licencia BSD de 3 cláusulas. El aviso completo está en
[`terceros/LICENCIA-ViGEmBus.txt`](terceros/LICENCIA-ViGEmBus.txt).

## Licencia

[MIT](LICENSE): podés usarlo, cambiarlo y compartirlo, manteniendo el aviso de autoría. Las novedades de cada versión están en [NOVEDADES.md](NOVEDADES.md).
