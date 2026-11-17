# Novedades

## 1.5.0

- **Instalador:** `ControlCelular-Instalar-1.5.0.exe`. Con un solo permiso de Windows deja todo listo:
  - instala **ViGEmBus**, si falta, sin ventanas extra;
  - abre el firewall para el programa y **saca los bloqueos** que Windows le haya puesto (por ejemplo, si se cerró
    con «Cancelar» el cartel del firewall, el celular no podía conectarse);
  - si la red está como «Pública», ofrece marcarla como privada;
  - crea los íconos (escritorio y menú Inicio) y se desinstala desde «Agregar o quitar programas».
- **Escanear y jugar:** al escanear el QR, el celular entra **directo al control**. El certificado (para instalar la
  app y usar el giroscopio) pasa a ser opcional: menú ☰ → «Activar app y giroscopio».
- El programa instalado arranca más rápido (ya no se descomprime cada vez).
- Sigue estando la versión portátil `ControlCelular.exe`, que no se instala.

## 1.4.1

- **ViGEmBus viene incluido:** ya no hay que bajarlo aparte. Si la PC no tiene el driver, Control Celular pregunta
  «¿Lo instalo ahora?» y abre el instalador oficial (firmado por su autor), que viaja dentro del programa. Al
  terminar, Control Celular se vuelve a abrir solo.
- **Arreglo importante:** en una PC sin ViGEmBus, el programa se cerraba al instante sin mostrar nada. Ya no pasa.
- Si el programa no puede arrancar por cualquier otro motivo, muestra el error, lo guarda en `error.txt` (en
  `%LOCALAPPDATA%\ControlCelular`) y no se cierra solo.

## 1.4.0

- **Control de PS4:** un control nuevo con la forma de uno de PS4: L1/L2/R1/R2, un touchpad grande en el centro
  con Share y Options a los costados, cruceta, botón PS, △ ○ ✕ □ con sus colores y los dos sticks juntos abajo.
  Al elegirlo, la PC lo ve como un DualShock 4. Se puede editar como cualquier otro control.
- Por dentro: el código quedó ordenado en partes y hay más de 50 pruebas automáticas (`probar.bat`).

## 1.3.0

- **iPhone:** versión propia de la página del control y de la guía del certificado (archivos aparte de los de
  Android). La PC elige sola cuál mostrar según el celular, con la misma dirección y el mismo QR. Incluye el permiso
  del giroscopio, «Agregar a inicio» y los pasos del certificado de iPhone (perfil + confianza total). En iPhone no
  hay vibración, porque Safari no la permite. *Todavía no se probó en un iPhone de verdad.*
- **English:** la página del control, la guía del certificado, la ventana del programa, el ícono y un `README.en.md`.
  Sigue el idioma del celular y el de Windows; en ⚙ Opciones → Idioma se puede elegir a mano.

## 1.2.0

- **Modo DualShock 4 (control de PlayStation):** en ⚙ Opciones → «La PC lo ve como» elegís Xbox 360 o
  DualShock 4. Con DualShock 4, los botones se muestran como ✕ ○ □ △, L1/R1, L2/R2, Share, Options y PS, y se puede
  usar el **touchpad** desde el editor.
- **Giroscopio «Movimiento real» (solo DualShock 4):** el celular manda su giroscopio y su acelerómetro como el
  sensor de un control de PlayStation. Lo usan Steam (el giroscopio de Steam Input) y emuladores como Cemu o Yuzu.
- **Modo zurdo:** da vuelta el control como un espejo. Los grupos de botones, como el rombo, mantienen su orden.
- **Opciones más limpias:** un botón ⚙ al lado del ☰ abre una ventana con pestañas (General, Giroscopio y Sticks),
  con interruptores y una explicación corta en cada opción. El ☰ queda para elegir el control y las acciones.

## 1.1.0

**Descargá `ControlCelular.exe`** (abajo, en «Assets»). Es un solo archivo y no hace falta instalar nada más. Si Windows
muestra «Windows protegió su PC», tocá **Más información → Ejecutar de todas formas**: aparece porque el programa no
está firmado.

**Conectarse:**
- **QR al abrir el programa:** lo escaneás con la cámara del celular y entrás emparejado, sin escribir nada.
- **Ícono al lado del reloj:** desde ahí se muestra el QR, se oculta la ventana, se activa el arranque con Windows,
  se ven los celulares emparejados y se puede **desinstalar**.
- **Guía del certificado según la marca del celular:** Samsung, Xiaomi, Motorola, Pixel y otras.

**Jugar:**
- **Hasta 4 celulares a la vez**, cada uno es un control de Xbox distinto (jugador 1 a 4).
- **Botones turbo y fijo** desde el editor: el turbo se repite solo mientras lo mantenés; el fijo queda apretado
  con un toque y se suelta con otro.
- **Ajustes de cada stick:** zona muerta, respuesta (suave, normal o rápida) y recorrido.
- **Demora visible** al lado del número de jugador.
- **Modo noche.**

**Personalizar:**
- **Tus ajustes y controles editados quedan en la PC**, separados por celular, y se pueden copiar de un celular a
  otro.
- **Editor de control** con deshacer y cuadrícula.
- **Tutorial** la primera vez que lo abrís.

**Seguridad:**
- **Límite de intentos** con el código de emparejamiento.
- **Olvidar celulares** desde el ícono: pierden el permiso al instante.

**Además:**
- El programa avisa si hay una **versión nueva**. Se puede apagar.
- Licencia **MIT**.

## 1.0.0

Primera versión: el celular como control de Xbox 360 para la PC, con control completo, alargado y por juego de Steam,
giroscopio, vibración y editor de control.
