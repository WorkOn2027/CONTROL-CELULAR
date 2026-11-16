"""Genera la versión de iPhone de las páginas a partir de las de Android.

Las de iPhone son archivos aparte (web/iphone.html y web/configurar-iphone.html), así nunca se mezclan con las de
Android. Pero NO se editan a mano: se cambia web/index.html o web/configurar.html y se corre este script, que les
aplica los cambios propios de iPhone. Así cada cambio del control se hace una sola vez.

  python herramientas/hacer_iphone.py               genera los archivos de iPhone
  python herramientas/hacer_iphone.py --comprobar   solo revisa que estén al día (lo usan las pruebas)

Si un cambio de iPhone no encuentra su lugar en la página de Android (porque esa parte cambió), el script frena
con un error en vez de seguir: hay que actualizar ese cambio acá.
"""

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
WEB = RAIZ / "web"

# ---------- Cambios de iPhone para la página del control (web/index.html -> web/iphone.html) ----------
CAMBIOS_CONTROL = [
    # Encabezado: app de pantalla de inicio en iPhone
    ('<link rel="icon" href="/icono-192.png">',
     '<link rel="icon" href="/icono-192.png">\n<link rel="apple-touch-icon" href="/icono-192.png">\n'
     '<meta name="apple-mobile-web-app-capable" content="yes">\n'
     '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">\n'
     '<meta name="apple-mobile-web-app-title" content="Control">'),
    ('<title>Control Celular</title>', '<title>Control Celular (iPhone)</title>'),
    # Opciones: sin vibración (Safari no la permite) -> aviso; permiso del giroscopio
    ('        <label class="fila"><span class="txt"><b>Vibrar al tocar</b>',
     '        <div class="fila"><span class="txt"><b>Vibración</b><small>En iPhone, Safari no deja que una página web '
     'vibre.</small></span></div>\n        <label class="fila" hidden><span class="txt"><b>Vibrar al tocar</b>'),
    ('        <label class="fila"><span class="txt"><b>Vibración del juego</b>',
     '        <label class="fila" hidden><span class="txt"><b>Vibración del juego</b>'),
    ('      <section class="ajPanel" data-panel="giro" id="giroOpts">',
     '      <section class="ajPanel" data-panel="giro" id="giroOpts">\n'
     '        <div class="fila" id="filaPermiso"><span class="txt"><b>Permitir el giroscopio (iPhone)</b>'
     '<small>El iPhone pide permiso para usar el movimiento.</small></span>\n'
     '          <button id="permisoGiro">Permitir</button></div>'),
    # Menú: instalar = "Agregar a inicio"; sin pantalla completa (Safari en iPhone no la tiene)
    ('    <button id="pantalla">Pantalla completa</button>\n',
     '    <button id="pantalla" hidden>Pantalla completa</button>\n'
     '    <button id="agregarInicio">Agregar a inicio (iPhone)</button>\n'),
    ('href="/configurar.html" hidden>Activar app y giroscopio</a>',
     'href="/configurar-iphone.html" hidden>Activar app y giroscopio</a>'),
    # Arranque: lo propio de iPhone
    ('  traducirDOM(document.body); // inglés si el celular está en inglés (o si se eligió en ⚙ → Idioma)',
     '''  traducirDOM(document.body); // inglés si el celular está en inglés (o si se eligió en ⚙ → Idioma)

  // ---------- Lo propio de iPhone (Safari) ----------
  // · No hay vibración. · El giroscopio pide permiso con un toque. · El acelerómetro mide al revés que en Android.
  // · Se instala con Compartir → «Agregar a inicio». · Se evita el zoom con dos dedos.
  try { localStorage.setItem("toque", "0"); localStorage.setItem("juego", "0"); } catch (e) {}
  document.addEventListener("gesturestart", (e) => e.preventDefault());
  const gIOS = (g) => (g && g.x !== null ? { x: -g.x, y: -g.y, z: -g.z } : g);
  const pidePermiso = typeof DeviceMotionEvent !== "undefined" && typeof DeviceMotionEvent.requestPermission === "function";
  function pedirPermisoGiro() {
    if (!pidePermiso) return Promise.resolve(true);
    return DeviceMotionEvent.requestPermission().then((r) => r === "granted").catch(() => false);
  }'''),
    ('const g = e.accelerationIncludingGravity;\n      if (!g || g.x === null) return;\n      if (!hayFiltro)',
     'const g = gIOS(e.accelerationIncludingGravity);\n      if (!g || g.x === null) return;\n      if (!hayFiltro)'),
    ('const r = e.rotationRate, g = e.accelerationIncludingGravity;',
     'const r = e.rotationRate, g = gIOS(e.accelerationIncludingGravity);'),
    ('  $("optGiro").onchange = (e) => { opt.giro = e.target.value; guardar("giro", opt.giro); aplicarGiro(); };',
     '''  $("optGiro").onchange = (e) => {
    opt.giro = e.target.value; guardar("giro", opt.giro);
    if (opt.giro !== "0") pedirPermisoGiro().then(() => aplicarGiro()); else aplicarGiro();
  };
  $("filaPermiso").hidden = !pidePermiso;
  $("permisoGiro").onclick = () => pedirPermisoGiro().then((ok) => {
    $("permisoGiro").textContent = ok ? "✓" : "✗"; aplicarGiro();
  });
  $("agregarInicio").hidden = !!navigator.standalone; // ya está instalada
  $("agregarInicio").onclick = () => alert(tr("Para instalarla: en Safari tocá Compartir (el cuadrado con la flecha) → «Agregar a inicio». Después abrila desde el ícono."));'''),
    ('''    const m = navigator.userAgent.match(/Android [\\d.]+; ([^;)]+)/);
    return m && m[1] !== "K" ? m[1].replace(/ Build.*/, "").trim() : "Celular";''',
     '''    return /iPad/.test(navigator.userAgent) ? "iPad" : "iPhone";'''),
]

# ---------- Guía del certificado de iPhone (web/configurar.html -> web/configurar-iphone.html) ----------
GUIA_IPHONE = '''    <ol>
      <li data-en="Use <b>Safari</b> (in other browsers the iPhone doesn't install certificates). Tapping <b>Download certificate</b> shows <b>“This website is trying to download a configuration profile”</b>: tap <b>Allow</b>.">Usá <b>Safari</b> (en otros navegadores el iPhone no instala certificados). Al tocar <b>Descargar certificado</b> aparece <b>«Este sitio web intenta descargar un perfil de configuración»</b>: tocá <b>Permitir</b>.</li>
      <li data-en="Open <b>Settings</b>: at the top you'll see <b>Profile Downloaded</b> (or go to <b>General</b> → <b>VPN &amp; Device Management</b>). Tap <b>CONTROL CELULAR</b> → <b>Install</b>, enter your passcode and tap <b>Install</b> again.">Abrí <b>Ajustes</b>: arriba aparece <b>Perfil descargado</b> (o entrá a <b>General</b> → <b>VPN y gestión de dispositivos</b>). Tocá <b>CONTROL CELULAR</b> → <b>Instalar</b>, poné tu código y tocá <b>Instalar</b> otra vez.</li>
      <li data-en="<b>Turn on trust</b> (iPhone asks for this extra step): <b>Settings</b> → <b>General</b> → <b>About</b> → at the bottom, <b>Certificate Trust Settings</b> → turn on <b>CONTROL CELULAR (solo red local)</b>."><b>Activá la confianza</b> (el iPhone pide este paso extra): <b>Ajustes</b> → <b>General</b> → <b>Información</b> → abajo de todo, <b>Configuración de confianza de certificados</b> → activá <b>CONTROL CELULAR (solo red local)</b>.</li>
    </ol>
'''
AVISO_IPHONE = ('    <small data-en="The certificate only works for addresses on your home network, not for websites. '
                'You can remove it whenever you want from Settings → General → VPN &amp; Device Management.">El certificado '
                'solo sirve para direcciones de tu red de casa, no para sitios de internet. Lo podés sacar cuando quieras '
                'desde Ajustes → General → VPN y gestión de dispositivos.</small>')
CAMBIOS_CONFIGURAR = [
    ('<title>Configurar Control Celular</title>', '<title>Configurar Control Celular (iPhone)</title>'),
    ('<h1>Control Celular</h1>', '<h1>Control Celular <small style="font-size:15px">· iPhone</small></h1>'),
    ('data-en="Once the certificate is installed, this page notices it and takes you to the controller. There, in the '
     '☰ menu, you\'ll be able to <b>install the app</b>.">Cuando el certificado esté instalado, esta página lo detecta '
     'sola y te lleva al control.\n      Ahí, en el menú ☰, vas a poder <b>instalar la app</b>.</div>',
     'data-en="Once the certificate is trusted, this page notices it and takes you to the controller. To install it '
     'as an app: in Safari tap <b>Share</b> → <b>Add to Home Screen</b>.">Cuando el certificado tenga la confianza '
     'activada, esta página lo detecta sola y te lleva al control.\n      Para instalarlo como app: en Safari tocá '
     '<b>Compartir</b> → <b>Agregar a inicio</b>.</div>'),
    ('<a id=&quot;sinApp&quot; href=&quot;/index.html&quot;>', '<a id=&quot;sinApp&quot; href=&quot;/iphone.html&quot;>'),
    ('<a id="sinApp" href="/index.html">', '<a id="sinApp" href="/iphone.html">'),
    ('document.getElementById("sinApp").href = "/index.html" +', 'document.getElementById("sinApp").href = "/iphone.html" +'),
    ('document.title = "Set up Control Celular";', 'document.title = "Set up Control Celular (iPhone)";'),
]


def _reemplazar(texto: str, cambios, archivo: str) -> str:
    for viejo, nuevo in cambios:
        if viejo not in texto:
            raise SystemExit(f"[hacer_iphone] En {archivo} no encontré este pedazo (¿cambió?):\n  {viejo[:120]!r}")
        texto = texto.replace(viejo, nuevo, 1)
    return texto


def _entre(texto: str, desde: str, hasta: str, nuevo: str, archivo: str, incluir_hasta=False) -> str:
    if desde not in texto:
        raise SystemExit(f"[hacer_iphone] En {archivo} no encontré: {desde[:80]!r}")
    i = texto.index(desde)
    j = texto.index(hasta, i) + (len(hasta) if incluir_hasta else 0)
    return texto[:i] + nuevo + texto[j:]


def generar_control(s: str) -> str:
    return _reemplazar(s, CAMBIOS_CONTROL, "web/index.html")


def generar_configurar(c: str) -> str:
    archivo = "web/configurar.html"
    c = _entre(c, '    <div class="marcas" id="marcas">', '    <small data-en="<b>Can', GUIA_IPHONE, archivo)
    c = _entre(c, '    <small data-en="<b>Can', "</small>", AVISO_IPHONE, archivo, incluir_hasta=True)
    c = _reemplazar(c, CAMBIOS_CONFIGURAR, archivo)
    # En iPhone no hay pestañas de marcas: se saca el código que las elige.
    c, n = re.subn(r"\n  // Guía según la marca.*?document\.getElementById\(\"marcas\"\)\.onclick = .*?\n", "\n", c,
                   flags=re.S)
    if n != 1:
        raise SystemExit(f"[hacer_iphone] En {archivo} no encontré el código que elige la marca.")
    return c


def archivos() -> dict[Path, str]:
    return {
        WEB / "iphone.html": generar_control((WEB / "index.html").read_text("utf-8")),
        WEB / "configurar-iphone.html": generar_configurar((WEB / "configurar.html").read_text("utf-8")),
    }


if __name__ == "__main__":
    generados = archivos()
    if "--comprobar" in sys.argv:
        viejos = [p.name for p, t in generados.items() if not p.exists() or p.read_text("utf-8") != t]
        if viejos:
            raise SystemExit("[hacer_iphone] Desactualizados: " + ", ".join(viejos) +
                             ". Corré: python herramientas/hacer_iphone.py")
        print("[hacer_iphone] La versión de iPhone está al día.")
    else:
        for p, t in generados.items():
            p.write_text(t, "utf-8")
            print("[hacer_iphone] Generado", p.relative_to(RAIZ))
