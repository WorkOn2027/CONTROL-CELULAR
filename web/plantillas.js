// Controles armados según el tipo de juego.
// Cada elemento: k = "btn" | "stick" | "dpad"; x, y = centro en % del control; d = diámetro en vh (redondo)
// o w, h en vh (píldora). btn: b = botón de Xbox, t = gatillo (L/R); se pueden combinar (Derrape = RT + A).
// txt = lo que hace, sub = qué botón manda, c = color (A/B/X/Y), g = grupo para deslizar el dedo entre botones.
// El menú (☰) y el puntito de conexión se agregan solos arriba al centro.
(() => {
  const sel = [
    { k: "btn", x: 34, y: 9, w: 11, h: 7, b: "BACK", txt: "Select" },
    { k: "btn", x: 66, y: 9, w: 11, h: 7, b: "START", txt: "Start" },
  ];
  const hombros = (lt, rt) => [
    { k: "btn", x: 9, y: 9, w: 30, h: 12, t: "L", txt: lt || "LT", sub: lt ? "LT" : "" },
    { k: "btn", x: 24.5, y: 9, w: 30, h: 12, b: "LB", txt: "LB" },
    { k: "btn", x: 75.5, y: 9, w: 30, h: 12, b: "RB", txt: "RB" },
    { k: "btn", x: 91, y: 9, w: 30, h: 12, t: "R", txt: rt || "RT", sub: rt ? "RT" : "" },
  ];
  const abxy = (cx, cy, d, dx, dy, nombres = {}) => [
    { k: "btn", x: cx, y: cy - dy, d, b: "Y", c: "Y", g: "f", txt: nombres.Y || "Y", sub: nombres.Y ? "Y" : "" },
    { k: "btn", x: cx - dx, y: cy, d, b: "X", c: "X", g: "f", txt: nombres.X || "X", sub: nombres.X ? "X" : "" },
    { k: "btn", x: cx + dx, y: cy, d, b: "B", c: "B", g: "f", txt: nombres.B || "B", sub: nombres.B ? "B" : "" },
    { k: "btn", x: cx, y: cy + dy, d, b: "A", c: "A", g: "f", txt: nombres.A || "A", sub: nombres.A ? "A" : "" },
  ];

  // Igual que el control completo de Xbox (para acción, aventura, estrategia y lo que no se sabe).
  const completo = [
    ...hombros(),
    { k: "stick", s: "L", x: 18, y: 47, d: 34 },
    { k: "stick", s: "R", x: 62, y: 75, d: 34 },
    { k: "dpad", x: 38, y: 75, d: 32 },
    ...abxy(81, 47, 13.5, 5.6, 12.6),
    { k: "btn", x: 42, y: 34, w: 10, h: 7, b: "BACK", txt: "Select" },
    { k: "btn", x: 50, y: 34, d: 10, b: "GUIDE", txt: "●" },
    { k: "btn", x: 58, y: 34, w: 10, h: 7, b: "START", txt: "Start" },
    { k: "btn", x: 18, y: 84, d: 8, b: "LS", txt: "L3" },
    { k: "btn", x: 81, y: 84, d: 8, b: "RS", txt: "R3" },
  ];

  // Los dos controles de siempre (también se pueden editar con el editor de control).
  // c = "W" es botón blanco; f = tamaño de letra en vh (opcional).
  window.BASES = {
    completo: { nombre: "Completo (Xbox)", el: completo },
    // Con la forma de un control de PS4: touchpad grande arriba, sticks juntos abajo. Manda como DualShock 4.
    ps4: {
      nombre: "PS4 (DualShock 4)", mando: "ds4",
      el: [
        { k: "btn", x: 9, y: 9, w: 30, h: 12, t: "L", txt: "L2" },
        { k: "btn", x: 24.5, y: 9, w: 30, h: 12, b: "LB", txt: "L1" },
        { k: "btn", x: 75.5, y: 9, w: 30, h: 12, b: "RB", txt: "R1" },
        { k: "btn", x: 91, y: 9, w: 30, h: 12, t: "R", txt: "R2" },
        { k: "btn", x: 50, y: 28, w: 62, h: 20, b: "TOUCH", txt: "Touchpad" },
        { k: "btn", x: 27, y: 28, w: 13, h: 7, b: "BACK", txt: "Share" },
        { k: "btn", x: 73, y: 28, w: 13, h: 7, b: "START", txt: "Options" },
        { k: "dpad", x: 17, y: 50, d: 32 },
        { k: "btn", x: 50, y: 52, d: 10, b: "GUIDE", txt: "PS" },
        { k: "btn", x: 83, y: 36, d: 13.5, b: "Y", c: "A", g: "f", f: 7, txt: "△" },
        { k: "btn", x: 77.4, y: 50, d: 13.5, b: "X", c: "V", g: "f", f: 7, txt: "□" },
        { k: "btn", x: 88.6, y: 50, d: 13.5, b: "B", c: "B", g: "f", f: 7, txt: "○" },
        { k: "btn", x: 83, y: 64, d: 13.5, b: "A", c: "X", g: "f", f: 7, txt: "✕" },
        { k: "stick", s: "L", x: 35, y: 78, d: 30 },
        { k: "stick", s: "R", x: 65, y: 78, d: 30 },
        { k: "btn", x: 10, y: 86, d: 8, b: "LS", txt: "L3" },
        { k: "btn", x: 90, y: 86, d: 8, b: "RS", txt: "R3" },
      ],
    },
    alargado: {
      nombre: "Alargado", forma: "alargado", barra: { x: 95.9, y: 50, v: true },
      el: [
        { k: "dpad", x: 14.4, y: 50, d: 46 },
        { k: "btn", x: 33, y: 31, d: 27, f: 10, t: "L", txt: "1", sub: "poder", c: "W", g: "izq" },
        { k: "btn", x: 33, y: 69, d: 19, f: 7, b: "Y", txt: "2", g: "izq" },
        { k: "btn", x: 46.4, y: 26, d: 11, f: 5, b: "START", txt: "+" },
        { k: "btn", x: 46.4, y: 50, d: 11, f: 4, b: "GUIDE", txt: "⌂" },
        { k: "btn", x: 46.4, y: 74, d: 11, f: 5, b: "BACK", txt: "−" },
        { k: "btn", x: 65, y: 64, d: 15, f: 6, b: "B", txt: "B", c: "W", g: "der" },
        { k: "btn", x: 82.5, y: 60, d: 25, f: 9, b: "A", txt: "A", c: "W", g: "der" },
        { k: "btn", x: 78.4, y: 19, w: 58, h: 17, f: 5, t: "R", b: "A", txt: "Derrape", sub: "+ acelera", g: "der" },
      ],
    },
  };

  window.PLANTILLAS = {
    carreras: {
      nombre: "Carreras",
      el: [
        ...sel,
        { k: "btn", x: 10, y: 9, w: 26, h: 12, b: "LB", txt: "LB" },
        { k: "btn", x: 90, y: 9, w: 26, h: 12, b: "RB", txt: "RB" },
        { k: "stick", s: "L", x: 17, y: 56, d: 42 },
        { k: "dpad", x: 37, y: 80, d: 24 },
        { k: "btn", x: 84, y: 62, d: 30, t: "R", txt: "Acelerar", sub: "RT", c: "A", g: "r" },
        { k: "btn", x: 66, y: 77, d: 20, t: "L", txt: "Frenar", sub: "LT", c: "B", g: "r" },
        ...abxy(66, 38, 12, 7, 12),
      ],
    },
    disparos: {
      nombre: "Disparos",
      el: [
        ...sel,
        { k: "btn", x: 10, y: 9, w: 26, h: 11, b: "LB", txt: "LB" },
        { k: "btn", x: 90, y: 9, w: 26, h: 11, b: "RB", txt: "RB" },
        { k: "btn", x: 12, y: 31, w: 30, h: 14, t: "L", txt: "Apuntar", sub: "LT" },
        { k: "stick", s: "L", x: 17, y: 64, d: 38 },
        { k: "dpad", x: 38, y: 42, d: 22 },
        { k: "stick", s: "R", x: 70, y: 68, d: 38 },
        { k: "btn", x: 88, y: 40, d: 22, t: "R", txt: "Disparar", sub: "RT", c: "B" },
        { k: "btn", x: 86, y: 80, d: 15, b: "A", txt: "Saltar", sub: "A", c: "A" },
        { k: "btn", x: 95, y: 62, d: 13, b: "B", txt: "Agachar", sub: "B", c: "B" },
        { k: "btn", x: 77, y: 30, d: 14, b: "X", txt: "Recargar", sub: "X", c: "X" },
        { k: "btn", x: 64, y: 22, d: 13, b: "Y", txt: "Arma", sub: "Y", c: "Y" },
        { k: "btn", x: 31, y: 88, d: 11, b: "LS", txt: "Correr", sub: "L3" },
        { k: "btn", x: 52, y: 88, d: 11, b: "RS", txt: "Golpe", sub: "R3" },
      ],
    },
    plataformas: {
      nombre: "Plataformas",
      el: [
        ...sel, ...hombros(),
        { k: "stick", s: "L", x: 17, y: 58, d: 40 },
        { k: "dpad", x: 37, y: 80, d: 22 },
        { k: "btn", x: 84, y: 66, d: 28, b: "A", txt: "Saltar", sub: "A", c: "A", g: "f" },
        { k: "btn", x: 68, y: 80, d: 18, b: "B", txt: "B", c: "B", g: "f" },
        { k: "btn", x: 68, y: 46, d: 18, b: "X", txt: "X", c: "X", g: "f" },
        { k: "btn", x: 84, y: 32, d: 18, b: "Y", txt: "Y", c: "Y", g: "f" },
      ],
    },
    deportes: {
      nombre: "Deportes",
      el: [
        ...sel,
        { k: "btn", x: 10, y: 9, w: 26, h: 11, b: "LB", txt: "LB" },
        { k: "btn", x: 26, y: 9, w: 26, h: 11, t: "L", txt: "LT" },
        { k: "btn", x: 74, y: 9, w: 26, h: 11, b: "RB", txt: "RB" },
        { k: "btn", x: 90, y: 9, w: 26, h: 11, t: "R", txt: "Correr", sub: "RT" },
        { k: "stick", s: "L", x: 17, y: 60, d: 40 },
        { k: "dpad", x: 36, y: 79, d: 22 },
        { k: "stick", s: "R", x: 55, y: 79, d: 24 },
        ...abxy(80, 56, 17, 7.6, 17),
      ],
    },
    pelea: {
      nombre: "Pelea",
      el: [
        ...sel,
        { k: "btn", x: 79, y: 14, w: 18, h: 9, b: "LB", txt: "LB" },
        { k: "btn", x: 92, y: 14, w: 18, h: 9, t: "L", txt: "LT" },
        { k: "dpad", x: 18, y: 58, d: 48 },
        { k: "btn", x: 58, y: 42, d: 20, b: "X", txt: "X", c: "X", g: "p" },
        { k: "btn", x: 72, y: 42, d: 20, b: "Y", txt: "Y", c: "Y", g: "p" },
        { k: "btn", x: 86, y: 42, d: 20, b: "RB", txt: "RB", g: "p" },
        { k: "btn", x: 58, y: 74, d: 20, b: "A", txt: "A", c: "A", g: "p" },
        { k: "btn", x: 72, y: 74, d: 20, b: "B", txt: "B", c: "B", g: "p" },
        { k: "btn", x: 86, y: 74, d: 20, t: "R", txt: "RT", g: "p" },
      ],
    },
    accion: { nombre: "Completo (acción, aventura, estrategia)", el: completo },
  };

  // Juegos con controles conocidos (appid de Steam -> control propio).
  window.PERFILES = {
    // Sonic Racing: CrossWorlds: A acelera, B frena, RT derrapa, LT ítem, X mira atrás.
    2486820: {
      nombre: "Propio de Sonic Racing",
      el: [
        ...sel,
        { k: "btn", x: 16, y: 12, w: 30, h: 13, t: "L", txt: "Ítem", sub: "LT" },
        { k: "stick", s: "L", x: 17, y: 58, d: 42 },
        { k: "dpad", x: 37, y: 80, d: 22 },
        { k: "btn", x: 84, y: 62, d: 30, b: "A", txt: "Acelerar", sub: "A", c: "A", g: "r" },
        { k: "btn", x: 66, y: 76, d: 20, b: "B", txt: "Frenar", sub: "B", c: "B", g: "r" },
        { k: "btn", x: 80, y: 22, w: 34, h: 14, t: "R", b: "A", txt: "Derrape", sub: "RT + acelera", g: "r" },
        { k: "btn", x: 63, y: 46, d: 15, b: "X", txt: "Atrás", sub: "X", c: "X" },
      ],
    },
  };
})();
