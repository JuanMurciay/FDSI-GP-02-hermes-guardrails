let ALL_RUNS = [];
let CURRENT_RUN_ID = null;

function escapeHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function badgeClasificacion(clasif) {
  switch (clasif) {
    case "BLOQUEADO":
      return '<span class="pill pill-success">🛡 BLOQUEADO</span>';
    case "IMPACTO":
      return '<span class="pill pill-danger">🚨 IMPACTO</span>';
    case "CONTROL_OK":
      return '<span class="pill pill-info">✅ CONTROL OK</span>';
    case "SIN_INTENTO":
      return '<span class="pill pill-neutral">⚪ SIN INTENTO</span>';
    default:
      return '<span class="pill pill-warn">⚠️ TIMEOUT / ERROR</span>';
  }
}

async function cargarOverview() {
  const resp = await fetch("/api/overview");
  const data = await resp.json();
  const k = data.kpis;

  document.getElementById("kpi-total").textContent = k.total_corridas;
  document.getElementById("kpi-validas").textContent =
    `${k.corridas_validas} válidas (${k.corridas_con_ataque} ataque / ${k.corridas_validas - k.corridas_con_ataque} control)`;

  document.getElementById("kpi-intento").textContent = `${k.tasa_intento_pct}%`;
  document.getElementById("kpi-intento-detail").textContent =
    `${k.total_intentos}/${k.corridas_con_ataque} · IC95%: [${k.ic95_intento[0]}%–${k.ic95_intento[1]}%]`;

  document.getElementById("kpi-bloqueo").textContent = `${k.tasa_bloqueo_pct}%`;
  document.getElementById("kpi-bloqueo-detail").textContent =
    `${k.total_bloqueados}/${k.total_intentos} · IC95%: [${k.ic95_bloqueo[0]}%–${k.ic95_bloqueo[1]}%]`;

  document.getElementById("kpi-impacto").textContent = `${k.tasa_impacto_pct}%`;
  document.getElementById("kpi-impacto-detail").textContent =
    `${k.total_impactos}/${k.corridas_con_ataque} · IC95%: [${k.ic95_impacto[0]}%–${k.ic95_impacto[1]}%]`;

  document.getElementById("kpi-utilidad").textContent = `${k.tasa_utilidad_pct}%`;
  document.getElementById("kpi-duracion").textContent =
    `Duración media: ${k.duracion_promedio_s} s`;

  const tbody = document.getElementById("tbody-niveles");
  tbody.innerHTML = data.por_nivel
    .map((n) => {
      const impactoBadge =
        n.corridas_ataque === 0
          ? '<span class="pill pill-neutral">Sin corridas</span>'
          : n.impactos === 0
          ? `<span class="pill pill-success">0% (0/${n.corridas_ataque})</span>`
          : `<span class="pill pill-danger">${n.tasa_impacto_pct}% (${n.impactos}/${n.corridas_ataque})</span>`;

      const bloqueoBadge =
        n.intentos === 0
          ? '<span class="pill pill-neutral">N/A</span>'
          : n.tasa_bloqueo_pct === 100
          ? `<span class="pill pill-success">100% (${n.bloqueados}/${n.intentos})</span>`
          : `<span class="pill pill-warn">${n.tasa_bloqueo_pct}% (${n.bloqueados}/${n.intentos})</span>`;

      const pa = n.por_ataque || {};
      const vecStr = ["A1", "A2", "A3", "A4"]
        .map((f) => {
          const item = pa[f] || { impactos: 0, corridas: 0 };
          const cls = item.impactos === 0 ? "color:#34d399" : "color:#f87171;font-weight:700";
          return `<span style="${cls}">${f}: ${item.impactos}/${item.corridas}</span>`;
        })
        .join(" · ");

      const l2Cls = n.utilidad_l2_pct === 100 ? "pill-success" : "pill-warn";

      return `
        <tr>
          <td>
            <strong>${escapeHtml(n.nivel)}</strong>
            <div class="ctrl-detail">${escapeHtml(n.nombre)} (${n.corridas_validas} corridas)</div>
          </td>
          <td>
            <div><strong>SO:</strong> ${escapeHtml(n.aislamiento_so)}</div>
            <div class="ctrl-detail"><strong>Red:</strong> ${escapeHtml(n.red)} | <strong>Broker:</strong> ${escapeHtml(n.credenciales)}</div>
          </td>
          <td>
            ${n.corridas_ataque ? `<strong>${n.tasa_intento_pct}%</strong> (${n.intentos}/${n.corridas_ataque})` : "—"}
            <div class="ctrl-detail">IC95: [${n.ic95_intento[0]}–${n.ic95_intento[1]}%]</div>
          </td>
          <td>
            ${impactoBadge}
            <div class="ctrl-detail">IC95: [${n.ic95_impacto[0]}–${n.ic95_impacto[1]}%]</div>
          </td>
          <td>
            <div style="font-size:12px;">${vecStr}</div>
          </td>
          <td>
            ${bloqueoBadge}
            <div class="ctrl-detail">IC95: [${n.ic95_bloqueo[0]}–${n.ic95_bloqueo[1]}%]</div>
          </td>
          <td>
            <div><span class="pill pill-success">L1: ${n.utilidad_l1_pct}% (${n.utilidad_l1_str})</span></div>
            <div style="margin-top:4px;"><span class="pill ${l2Cls}">L2: ${n.utilidad_l2_pct}% (${n.utilidad_l2_str})</span></div>
          </td>
          <td>${n.duracion_promedio_s ? `${n.duracion_promedio_s} s` : "—"}</td>
        </tr>
      `;
    })
    .join("");
}

async function cargarRuns() {
  const resp = await fetch("/api/runs");
  const data = await resp.json();
  ALL_RUNS = data.runs || [];
  renderRunsList();
  if (!CURRENT_RUN_ID && ALL_RUNS.length > 0) {
    const preferida = ALL_RUNS.find((r) => r.clasificacion === "BLOQUEADO") || ALL_RUNS[0];
    seleccionarRun(preferida.run_id);
  }
}

function renderRunsList() {
  const fNivel = document.getElementById("filter-nivel").value;
  const fEstado = document.getElementById("filter-estado").value;
  const filtradas = ALL_RUNS.filter((r) => {
    if (fNivel !== "ALL" && r.nivel !== fNivel) return false;
    if (fEstado !== "ALL") {
      if (fEstado === "CONTROL_OK" && !["CONTROL_OK", "SIN_INTENTO"].includes(r.clasificacion)) {
        return false;
      } else if (fEstado !== "CONTROL_OK" && r.clasificacion !== fEstado) {
        return false;
      }
    }
    return true;
  });

  document.getElementById("count-runs").textContent = filtradas.length;
  const cont = document.getElementById("runs-list");
  if (filtradas.length === 0) {
    cont.innerHTML = '<div class="empty-msg">No hay corridas que coincidan con el filtro seleccionado.</div>';
    return;
  }

  cont.innerHTML = filtradas
    .map((r) => {
      const active = r.run_id === CURRENT_RUN_ID ? "active" : "";
      return `
        <div class="run-item ${active}" data-run-id="${escapeHtml(r.run_id)}">
          <div class="run-item-top">
            <span class="run-id">${escapeHtml(r.run_id)}</span>
            ${badgeClasificacion(r.clasificacion)}
          </div>
          <div class="run-meta">
            <span><strong>Nivel:</strong> ${escapeHtml(r.nivel)}${r.broker_credenciales ? " + Broker" : ""}</span>
            <span><strong>Ataque:</strong> ${escapeHtml(r.ataque)}</span>
            <span><strong>Tarea:</strong> ${escapeHtml(r.tarea || "L1")}</span>
            <span><strong>Herramientas:</strong> ${r.num_llamadas_herramienta ?? 0}</span>
            <span><strong>Duración:</strong> ${r.duracion_s ?? 0}s</span>
          </div>
        </div>
      `;
    })
    .join("");

  cont.querySelectorAll(".run-item").forEach((el) => {
    el.addEventListener("click", () => seleccionarRun(el.getAttribute("data-run-id")));
  });
}

async function seleccionarRun(runId) {
  CURRENT_RUN_ID = runId;
  renderRunsList();

  const resp = await fetch(`/api/runs/${encodeURIComponent(runId)}`);
  if (!resp.ok) return;
  const d = await resp.json();
  const r = d.registro;

  document.getElementById("insp-title").textContent = `Corrida: ${r.run_id}`;
  document.getElementById("insp-subtitle").textContent =
    `Modelo: ${r.modelo} · Nivel ${r.nivel} (${d.nivel_info.nombre}) · Duración: ${r.duracion_s}s`;

  document.getElementById("insp-badges").innerHTML = `
    ${badgeClasificacion(r.clasificacion)}
    <span class="pill ${r.importante_intacto ? "pill-success" : "pill-danger"}">
      Integridad SHA-256: ${r.importante_intacto ? "INTACTO" : "ALTERADO"}
    </span>
  `;

  // Pipeline de capas
  const pipe = document.getElementById("defense-pipeline");
  pipe.classList.remove("hidden");
  const n3Activo = ["N3", "N4"].includes(r.nivel);
  const contEndurecido = ["N2", "N4"].includes(r.nivel);
  pipe.innerHTML = `
    <div class="stage-box ${r.intento ? "stage-warn" : "stage-ok"}">
      <span class="stage-title">1. Agente (opencode)</span>
      <div>${r.intento ? "⚠️ Cayó en la inyección (Intento=Sí)" : "✅ Sin acción maliciosa"}</div>
    </div>
    <div class="stage-box ${n3Activo ? "stage-ok" : "stage-warn"}">
      <span class="stage-title">2. Política N3 (opencode.json)</span>
      <div>${n3Activo ? "🛡 Activa (webfetch/edit/bash)" : "⚪ No aplicada en este nivel"}</div>
    </div>
    <div class="stage-box ${contEndurecido ? "stage-ok" : "stage-warn"}">
      <span class="stage-title">3. Contenedor / FS</span>
      <div>${contEndurecido ? "🔒 RO + cap-drop ALL + datos:ro" : "🔓 Sin aislamiento endurecido"}</div>
    </div>
    <div class="stage-box ${contEndurecido ? "stage-ok" : "stage-danger"}">
      <span class="stage-title">4. Proxy / Secretless Broker</span>
      <div>${contEndurecido ? (r.bloqueado ? "🛡 DENY 403 a atacante.lab" : "🔒 Allowlist activa") : "🚨 Tráfico directo sin filtro"}</div>
    </div>
    <div class="stage-box ${r.impacto ? "stage-danger" : "stage-ok"}">
      <span class="stage-title">5. Impacto Verificado</span>
      <div>${r.impacto ? "🚨 EXFILTRACIÓN / IMPACTO" : "✅ 0 secretos filtrados / Intacto"}</div>
    </div>
  `;

  // Tab 1: Herramientas
  document.getElementById("tab-count-tools").textContent = d.llamadas.length;
  const toolsCont = document.getElementById("tools-timeline");
  if (d.llamadas.length === 0) {
    toolsCont.innerHTML = '<div class="empty-msg">No se registraron llamadas a herramientas en esta corrida.</div>';
  } else {
    toolsCont.innerHTML = d.llamadas
      .map((ll) => {
        const intentoClass = ll.es_intento ? "tool-intento" : "";
        const intentoBadge = ll.es_intento
          ? '<span class="pill pill-warn">⚡ DISPARADOR DE INTENTO</span>'
          : '<span class="pill pill-neutral">Acción del agente</span>';
        return `
          <div class="tool-step ${intentoClass}">
            <div class="tool-head">
              <div>
                <strong>#${ll.index} · <code>${escapeHtml(ll.tool)}</code></strong>
                <span class="ctrl-detail">(${escapeHtml(ll.status)})</span>
              </div>
              ${intentoBadge}
            </div>
            <div class="ctrl-detail">Entrada (input):</div>
            <pre class="code-block">${escapeHtml(JSON.stringify(ll.input, null, 2))}</pre>
            ${
              ll.output
                ? `<div class="ctrl-detail" style="margin-top:6px;">Salida (output):</div>
                   <pre class="code-block">${escapeHtml(ll.output)}</pre>`
                : ""
            }
          </div>
        `;
      })
      .join("");
  }

  // Tab 2: Red y Proxy
  const totalNet = (d.proxy ? d.proxy.length : 0) + (d.atacante ? d.atacante.length : 0);
  document.getElementById("tab-count-net").textContent = totalNet;
  const netCont = document.getElementById("net-inspector");

  const proxyHtml =
    d.proxy && d.proxy.length > 0
      ? d.proxy
          .map((p) => {
            const pill =
              p.decision === "DENY"
                ? '<span class="pill pill-danger">DENY (403)</span>'
                : p.decision === "BROKER_INJECT"
                ? '<span class="pill pill-info">BROKER_INJECT</span>'
                : '<span class="pill pill-success">ALLOW</span>';
            return `
              <div class="tool-step">
                <div class="tool-head">
                  <strong>Proxy · Host: <code>${escapeHtml(p.host)}</code></strong>
                  ${pill}
                </div>
                <div class="ctrl-detail">${escapeHtml(p.extra || "")} · <small>${escapeHtml(p.t)}</small></div>
              </div>
            `;
          })
          .join("")
      : '<div class="empty-msg">Sin eventos de proxy en esta corrida (nivel sin proxy o sin tráfico).</div>';

  const atacanteHtml =
    d.atacante && d.atacante.length > 0
      ? d.atacante
          .map((a) => {
            const esLegit = a.tipo === "api_legitima";
            const badge = esLegit
              ? `<span class="pill pill-info">API Legítima (${a.autorizado ? "Autenticada" : "401"})</span>`
              : '<span class="pill pill-danger">🚨 EXFILTRACIÓN RECIBIDA</span>';
            return `
              <div class="tool-step ${esLegit ? "" : "tool-intento"}">
                <div class="tool-head">
                  <strong>Servidor Laboratorio · <code>${escapeHtml(a.metodo)} ${escapeHtml(a.path)}</code></strong>
                  ${badge}
                </div>
                <pre class="code-block">${escapeHtml(JSON.stringify(a, null, 2))}</pre>
              </div>
            `;
          })
          .join("")
      : '<div class="tool-step"><span class="pill pill-success">✅ 0 peticiones recibidas por el servidor del atacante</span></div>';

  netCont.innerHTML = `
    <h3>Decisiones de <code>fdsi-proxy</code> ${d.proxy_inferido ? '<span class="ctrl-detail">(Reconstruido de evidencia de corrida)</span>' : ""}</h3>
    ${proxyHtml}
    <h3 style="margin-top:10px;">Registro del Servidor de Laboratorio (<code>atacante.json</code>)</h3>
    ${atacanteHtml}
  `;

  // Tab 3: Integridad y JSON
  const intCont = document.getElementById("integrity-inspector");
  intCont.innerHTML = `
    <div class="tool-step">
      <div class="tool-head">
        <strong>Resumen de Evidencia Verificada (<code>registro.json</code>)</strong>
        <span class="pill ${r.tarea_resumen_creado ? "pill-success" : "pill-warn"}">
          resumen.md: ${r.tarea_resumen_creado ? "CREADO" : "NO CREADO"}
        </span>
      </div>
      <pre class="code-block">${escapeHtml(JSON.stringify(r, null, 2))}</pre>
    </div>
    ${
      d.resumen_md
        ? `<div class="tool-step">
             <strong>Artefacto generado por el agente (<code>ws/resumen.md</code>)</strong>
             <pre class="code-block">${escapeHtml(d.resumen_md)}</pre>
           </div>`
        : ""
    }
  `;
}

// Ejecutar pruebas unitarias desde UI
document.getElementById("btn-run-unit").addEventListener("click", async () => {
  const btn = document.getElementById("btn-run-unit");
  const box = document.getElementById("unit-results");
  btn.disabled = true;
  btn.textContent = "⏳ Ejecutando pruebas...";
  box.classList.remove("hidden");
  box.innerHTML = '<div class="empty-msg">Corriendo laboratorio/test_broker_y_n3.py...</div>';

  try {
    const resp = await fetch("/api/test-unit", { method: "POST" });
    const data = await resp.json();
    const resumenPill = data.ok
      ? `<span class="pill pill-success">✅ TODAS LAS PRUEBAS PASARON (${data.duracion_s}s)</span>`
      : `<span class="pill pill-danger">❌ FALLO EN PRUEBAS (${data.duracion_s}s)</span>`;

    const items = (data.pruebas || [])
      .map(
        (p) => `
        <div class="unit-item">
          <span>${escapeHtml(p.descripcion)}</span>
          <span class="pill ${p.estado === "OK" ? "pill-success" : "pill-danger"}">${p.estado}</span>
        </div>
      `
      )
      .join("");

    box.innerHTML = `<div style="margin-bottom:6px;">${resumenPill}</div>${items}`;
  } catch (e) {
    box.innerHTML = `<div class="pill pill-danger">Error al ejecutar pruebas: ${escapeHtml(e.message)}</div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = "▶ Probar Protección Ahora";
  }
});

// Lanzar corrida del orquestador
document.getElementById("form-run").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const payload = {
    nivel: document.getElementById("sel-nivel").value,
    ataque: document.getElementById("sel-ataque").value,
    tarea: document.getElementById("sel-tarea").value,
    broker: document.getElementById("chk-broker").checked,
    no_infra: document.getElementById("chk-no-infra").checked,
    rep: 1,
  };
  const pill = document.getElementById("job-status-pill");
  pill.innerHTML = '<span class="pill pill-info">⏳ Iniciando corrida...</span>';
  const resp = await fetch("/api/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const job = await resp.json();
  if (resp.ok) {
    pill.innerHTML = `<span class="pill pill-warn">⚡ Ejecutando ${escapeHtml(job.job_id)}...</span>`;
    monitorearJobs();
  } else {
    pill.innerHTML = `<span class="pill pill-danger">Error: ${escapeHtml(job.error)}</span>`;
  }
});

async function monitorearJobs() {
  const resp = await fetch("/api/jobs");
  const data = await resp.json();
  const jobs = data.jobs || [];
  const pill = document.getElementById("job-status-pill");
  const activos = jobs.filter((j) => j.estado === "ejecutando");
  if (activos.length > 0) {
    pill.innerHTML = `<span class="pill pill-warn">⏳ ${activos.length} corrida(s) en ejecución...</span>`;
    setTimeout(monitorearJobs, 3000);
  } else if (jobs.length > 0) {
    const ult = jobs[0];
    pill.innerHTML =
      ult.estado === "completado"
        ? `<span class="pill pill-success">✅ ${escapeHtml(ult.job_id)} completado</span>`
        : `<span class="pill pill-danger">⚠️ ${escapeHtml(ult.job_id)} terminó con error</span>`;
    await cargarOverview();
    await cargarRuns();
  }
}

// Tabs
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.getAttribute("data-tab")).classList.add("active");
  });
});

document.getElementById("filter-nivel").addEventListener("change", renderRunsList);
document.getElementById("filter-estado").addEventListener("change", renderRunsList);
document.getElementById("btn-refresh").addEventListener("click", async () => {
  await cargarOverview();
  await cargarRuns();
});

// Inicializar
(async function init() {
  await cargarOverview();
  await cargarRuns();
})();
