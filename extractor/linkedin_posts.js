/*
 * Extractor de publicaciones de LinkedIn con vacantes (v2).
 *
 * Dónde se ejecuta:
 *   - En una búsqueda de publicaciones: https://www.linkedin.com/search/results/content/?keywords=...
 *   - En el feed de inicio:             https://www.linkedin.com/feed/
 *   - Por hashtag: es una búsqueda con keywords=%23trabajosihay
 *
 * Quién lo usa:
 *   - Claude en el chat (herramienta javascript del navegador integrado), y
 *   - el modo local con Playwright (src/buscador_empleo/fuentes/linkedin.py).
 *
 * Qué devuelve: un JSON PEQUEÑO, nunca la página completa (ahorro de tokens).
 *   [{ correos, autor, autorUrl, hace, url, fuente, texto, hashtags, imagenes, sinCorreo }]
 *   - Posts con correo nuevo (siempre).
 *   - Posts SIN correo en el texto pero con imagen y "cara de vacante" (solo si
 *     incluirImagenes = true). El correo suele estar dentro del afiche: Python lo
 *     lee después con OCR (ver src/buscador_empleo/imagenes.py).
 *
 * Configuración opcional (la arma `python -m buscador_empleo js`):
 *   window.__CTI_CONFIG = {
 *     conocidos: ["correo@ya-visto.com"],   // se omiten (ya postulados o ya vistos)
 *     excluirPaises: ["ecuador", ...],      // se omiten si no mencionan Bogotá/Colombia
 *     claves: ["power bi", "seleccion"],   // si se da, el post debe tener al menos una
 *     scrolls: 12,                          // cuántas veces bajar la página
 *     maxTexto: 900,                        // caracteres por post (menos = menos tokens)
 *     incluirImagenes: false,               // true en Windows (OCR gratis); false en el chat
 *     maxImagenes: 3                        // imágenes por post como máximo
 *   };
 *
 * Detalles aprendidos (nov-2026):
 *   - El LinkedIn nuevo ya no pone data-urn en los posts y desplaza la página dentro de
 *     <main id="workspace">, no en window. Por eso se desplaza todo lo desplazable y cada
 *     post se ubica por su encabezado oculto "Publicación en el feed" / "Feed post".
 *   - El feed puede desmontar posts al bajar: se recogen en cada paso de scroll, no al final.
 *   - Fotos de perfil (profile-displayphoto), logos (company-logo) y portadas de video
 *     (videocover) no sirven: se ignoran. Los afiches suelen ser "feedshare-shrink_*".
 */
(async () => {
  const cfg = Object.assign(
    { conocidos: [], excluirPaises: [], claves: [], scrolls: 12, maxTexto: 900,
      incluirImagenes: false, maxImagenes: 3 },
    window.__CTI_CONFIG || {}
  );
  const dormir = (ms) => new Promise((r) => setTimeout(r, ms));
  const RE = /(?<![\wÀ-ÿ.%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}/g;
  const RE_ENCABEZADO = /^(Publicación en el feed|Feed post)/;
  // Señales fuertes de vacante (para posts sin correo en el texto). Palabras sueltas como
  // "empleo" o "trabajo" no bastan: los consejos de hoja de vida también las usan.
  const RE_VACANTE = /vacantes?\b|estamos buscando|buscamos (?:talento|personal|un|una|profesional|analista|auxiliar)|estamos contratando|#hiring|#vacante|oferta laboral|ofertas? de empleo|env[ií](?:a|e|anos|en) (?:tu|su) (?:hv|hoja de vida|cv)|post[uú]late|se requiere|requiere contratar|[uú]nete a nuestro equipo|cargo\s*:|#trabajosihay/;
  const RE_IMG_INUTIL = /profile-displayphoto|company-logo|videocover|profile-framedphoto|background|ghost|emoji|reactions?/i;
  const norm = (s) => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();

  const expandir = () =>
    document.querySelectorAll("button").forEach((b) => {
      const t = (b.innerText || "").trim().toLowerCase();
      if ((t.length < 12 && (t.endsWith("más") || t.endsWith("more"))) || t === "cargar más" || t === "show more results") {
        try { b.click(); } catch (e) {}
      }
    });

  const bajar = () => {
    window.scrollTo(0, document.body.scrollHeight);
    // LinkedIn nuevo: el contenido se desplaza dentro de <main> u otro contenedor.
    document.querySelectorAll("main, [id='workspace'], .scaffold-finite-scroll").forEach((e) => {
      try { e.scrollTop = e.scrollHeight; } catch (x) {}
    });
  };

  // Un post = el ancestro más grande de su encabezado oculto que no contiene otro encabezado.
  const contenedores = () => {
    const H = [...document.querySelectorAll("h2, span, div")].filter(
      (e) => e.children.length === 0 && RE_ENCABEZADO.test((e.textContent || "").trim())
    );
    const viejos = [...document.querySelectorAll('[data-urn^="urn:li:activity"], [data-id^="urn:li:activity"]')];
    const salida = [...viejos];
    for (const h of H) {
      let c = h;
      while (c.parentElement && H.filter((x) => c.parentElement.contains(x)).length === 1 &&
             c.parentElement !== document.body) c = c.parentElement;
      if (!salida.some((s) => s.contains(c) || c.contains(s))) salida.push(c);
    }
    return salida;
  };

  const datosDe = (c) => {
    const texto = (c.innerText || "").replace(RE_ENCABEZADO, "");
    const plano = texto.replace(/\s+/g, " ").trim();
    const cabeza = plano.slice(0, 200);
    // Autor: el post puede empezar con contexto social ("Seguido por X", "A X le gusta esto",
    // "Te recomendamos"). El autor real es el último nombre enlazado ANTES de la marca de
    // grado/seguidores/tiempo ("• 2º", "1.234 seguidores", "6 días").
    const marca = cabeza.search(/ • |\d[\d.]* seguidores|\b\d+\s*(?:h|d|sem|min|días?|mes(?:es)?)\b/);
    let autorUrl = "", autorNombre = "", mejor = -1, primero = "";
    for (const a of c.querySelectorAll("a[href]")) {
      const u = (a.href || "").split("?")[0];
      if (!/linkedin\.com\/(in|company|school)\//.test(u)) continue;
      if (!primero) primero = u;
      const t = (a.innerText || "").trim().split("\n")[0].slice(0, 60);
      const pos = t ? cabeza.indexOf(t) : -1;
      if (pos < 0 || (marca > 0 && pos >= marca)) continue;
      if (pos > mejor) { mejor = pos; autorUrl = u; autorNombre = t; }
    }
    if (!autorUrl) autorUrl = primero;
    let url = "";
    const urn = c.getAttribute("data-urn") || c.getAttribute("data-id") || "";
    if (urn) url = `https://www.linkedin.com/feed/update/${urn}/`;
    if (!url) {
      const a = [...c.querySelectorAll("a[href*='/feed/update/']")][0];
      if (a) url = a.href.split("?")[0];
    }
    const imagenes = [];
    for (const im of c.querySelectorAll("img")) {
      const src = im.currentSrc || im.src || "";
      if (!/media\.licdn\.com/.test(src) || RE_IMG_INUTIL.test(src)) continue;
      const ancho = im.naturalWidth || parseInt(im.getAttribute("width") || "0", 10);
      if (ancho && ancho < 250) continue;
      if (!imagenes.some((x) => x.src === src)) imagenes.push({ src, alt: (im.alt || "").slice(0, 300) });
    }
    const promocionado = /\bPromocionado\b|\bPromoted\b/.test(cabeza);
    return { plano, cabeza, autorUrl, autorNombre, url, imagenes, promocionado };
  };

  // Recolección incremental (el feed desmonta posts al bajar).
  const posts = new Map();
  const recoger = () => {
    for (const c of contenedores()) {
      const d = datosDe(c);
      if (d.plano.length < 40) continue;
      const clave = norm(d.plano.slice(0, 160));
      const previo = posts.get(clave);
      if (!previo || d.plano.length > previo.plano.length) {
        if (previo) d.imagenes = [...previo.imagenes, ...d.imagenes.filter((i) => !previo.imagenes.some((p) => p.src === i.src))];
        posts.set(clave, d);
      }
    }
  };

  await dormir(2500);
  expandir();
  recoger();
  for (let i = 0; i < cfg.scrolls; i++) {
    bajar();
    await dormir(1200 + Math.random() * 600);
    expandir();
    recoger();
  }
  await dormir(800);
  expandir();
  recoger();

  // Respaldo: si no se encontró ningún contenedor, partir el texto visible.
  if (!posts.size) {
    const main = (document.querySelector("main") || document.body).innerText || "";
    main.split(/Publicación en el feed|Feed post/).forEach((t) => {
      const plano = t.replace(/\s+/g, " ").trim();
      if (plano.length >= 40) posts.set(norm(plano.slice(0, 160)), { plano, cabeza: plano.slice(0, 200), autorUrl: "", autorNombre: "", url: "", imagenes: [], promocionado: false });
    });
  }

  const conocidos = new Set(cfg.conocidos.map((c) => c.toLowerCase()));
  const paises = cfg.excluirPaises.map(norm);
  const claves = cfg.claves.map(norm);
  const salida = [];
  const vistos = new Set();
  for (const d of posts.values()) {
    const { plano, cabeza } = d;
    if (d.promocionado) continue; // anuncios pagados del feed
    const correos = [...new Set((plano.match(RE) || []).map((c) => c.replace(/\.$/, "").toLowerCase()))];
    const nuevos = correos.filter((c) => !conocidos.has(c));
    const n = norm(plano);
    const altTexto = norm(d.imagenes.map((i) => i.alt).join(" "));
    let sinCorreo = false;
    if (!nuevos.length) {
      // Sin correo en el texto: solo sirve si hay afiche y el post parece una vacante.
      if (correos.length || !cfg.incluirImagenes || !d.imagenes.length || !RE_VACANTE.test(n + " " + altTexto)) continue;
      sinCorreo = true;
    }
    if (paises.some((p) => new RegExp(`\\b${p}\\b`).test(n)) && !/\bbogota\b|\bcolombia\b/.test(n)) continue;
    // Con afiche, las palabras clave pueden estar solo en la imagen: no se exige.
    if (!sinCorreo && claves.length && !claves.some((c) => n.includes(c))) continue;
    const clave = sinCorreo ? "img:" + d.imagenes[0].src : nuevos.join(",");
    if (vistos.has(clave)) continue;
    vistos.add(clave);
    // Recorte: inicio del post + zona alrededor del primer correo.
    const k = plano.search(RE);
    let texto = plano.slice(0, Math.floor(cfg.maxTexto * 0.55));
    if (k > texto.length) texto += " … " + plano.slice(Math.max(texto.length, k - Math.floor(cfg.maxTexto * 0.4)), k + 120);
    if (sinCorreo) texto = plano.slice(0, cfg.maxTexto);
    const hace = (cabeza.match(/\b(\d+\s*(?:h|d|sem|mes|meses|días?|min))\b/) || [""])[0];
    const hashtags = [...new Set((plano.match(/#[\wÀ-ÿ]+/g) || []).map((h) => h.toLowerCase()))].slice(0, 25);
    const item = {
      correos: nuevos, autor: (d.autorNombre || cabeza.split(" • ")[0]).slice(0, 80), autorUrl: d.autorUrl, hace,
      url: d.url, fuente: "linkedin", texto, hashtags,
    };
    if (cfg.incluirImagenes && d.imagenes.length) item.imagenes = d.imagenes.slice(0, cfg.maxImagenes);
    if (sinCorreo) item.sinCorreo = true;
    salida.push(item);
  }
  return JSON.stringify(salida);
})();
