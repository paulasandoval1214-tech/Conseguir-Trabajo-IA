/*
 * Extractor de posts de LinkedIn con correo de postulación.
 *
 * Se ejecuta DENTRO de una página de resultados de búsqueda de publicaciones
 * de LinkedIn (https://www.linkedin.com/search/results/content/?keywords=...).
 * Lo usan:
 *   - Claude en el chat (herramienta javascript del navegador integrado), y
 *   - el modo local con Playwright (fuentes/linkedin.py).
 *
 * Devuelve un JSON pequeño: solo posts que traen correo, con el texto
 * recortado. Así el asistente no tiene que leer la página completa
 * (ahorro grande de tokens).
 *
 * Configuración opcional antes de ejecutar:
 *   window.__CTI_CONFIG = {
 *     conocidos: ["correo@ya-postulado.com"],   // se omiten
 *     excluirPaises: ["ecuador", "peru", ...],  // se omiten
 *     claves: ["power bi", "seleccion", ...],   // si se da, el post debe tener al menos una
 *     scrolls: 12,                              // cuántas veces bajar la página
 *     maxTexto: 900                             // caracteres por post (menos = menos tokens)
 *   };
 */
(async () => {
  const cfg = Object.assign(
    { conocidos: [], excluirPaises: [], claves: [], scrolls: 12, maxTexto: 900 },
    window.__CTI_CONFIG || {}
  );
  const dormir = (ms) => new Promise((r) => setTimeout(r, ms));
  const RE = /(?<![\wÀ-ÿ.%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}/g;
  const norm = (s) => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();

  const expandir = () =>
    document.querySelectorAll("button").forEach((b) => {
      const t = (b.innerText || "").trim().toLowerCase();
      if ((t.length < 12 && (t.endsWith("más") || t.endsWith("more"))) || t === "cargar más" || t === "show more results") {
        try { b.click(); } catch (e) {}
      }
    });

  await dormir(2500);
  for (let i = 0; i < cfg.scrolls; i++) {
    window.scrollTo(0, document.body.scrollHeight);
    await dormir(1200 + Math.random() * 600);
    expandir();
  }
  await dormir(1000);

  // 1) Intento por DOM (permite sacar la URL del post).
  let bloques = [];
  const nodos = document.querySelectorAll('[data-urn^="urn:li:activity"], [data-id^="urn:li:activity"]');
  nodos.forEach((n) => {
    const urn = n.getAttribute("data-urn") || n.getAttribute("data-id");
    bloques.push({ texto: n.innerText || "", url: urn ? `https://www.linkedin.com/feed/update/${urn}/` : "" });
  });
  // 2) Respaldo: partir el texto visible por el separador de cada post.
  if (!bloques.length) {
    const main = (document.querySelector("main") || document.body).innerText || "";
    bloques = main.split(/Publicación en el feed|Feed post/).map((t) => ({ texto: t, url: "" }));
  }

  const conocidos = new Set(cfg.conocidos.map((c) => c.toLowerCase()));
  const paises = cfg.excluirPaises.map(norm);
  const claves = cfg.claves.map(norm);
  const salida = [];
  const vistos = new Set();
  for (const b of bloques) {
    const plano = b.texto.replace(/\s+/g, " ").trim();
    const correos = [...new Set((plano.match(RE) || []).map((c) => c.replace(/\.$/, "").toLowerCase()))];
    if (!correos.length) continue;
    const nuevos = correos.filter((c) => !conocidos.has(c));
    if (!nuevos.length) continue;
    const n = norm(plano);
    if (paises.some((p) => new RegExp(`\\b${p}\\b`).test(n)) && !/\bbogota\b|\bcolombia\b/.test(n)) continue;
    if (claves.length && !claves.some((c) => n.includes(c))) continue;
    const clave = nuevos.join(",");
    if (vistos.has(clave)) continue;
    vistos.add(clave);
    // Recorte: inicio del post + zona alrededor del primer correo.
    const k = plano.search(RE);
    let texto = plano.slice(0, Math.floor(cfg.maxTexto * 0.55));
    if (k > texto.length) texto += " … " + plano.slice(Math.max(texto.length, k - Math.floor(cfg.maxTexto * 0.4)), k + 120);
    const cabeza = plano.slice(0, 160);
    const hace = (cabeza.match(/\b(\d+\s*(?:h|d|sem|mes|meses|días?|min))\b/) || [""])[0];
    salida.push({ correos: nuevos, autor: cabeza.split(" • ")[0].slice(0, 80), hace, url: b.url, fuente: "linkedin", texto });
  }
  return JSON.stringify(salida);
})();
