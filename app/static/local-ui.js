(function () {
  "use strict";

  const $ = (sel) => document.querySelector(sel);

  function gateBadgeClass(status) {
    if (!status) return "badge-neutral";
    const s = String(status).toLowerCase();
    if (s === "accepted" || s === "ok" || s === "true") return "badge-ok";
    if (s === "warning") return "badge-warning";
    if (s === "review_needed") return "badge-review";
    if (s === "rejected" || s === "false" || s === "fail") return "badge-fail";
    return "badge-neutral";
  }

  function setBadge(el, text, statusKey) {
    el.textContent = text || "—";
    el.className = "value badge " + gateBadgeClass(statusKey || text);
  }

  function clearResults() {
    ["status-bar", "highlights", "artifacts", "matches-block", "raw-json-wrap", "stderr-block"].forEach((id) => {
      $( "#" + id).classList.add("hidden");
    });
    $("#empty-state").classList.add("hidden");
  }

  function showResponse(payload) {
    clearResults();
    const data = payload.data || {};
    const action = payload.action || "unknown";

    $("#status-bar").classList.remove("hidden");
    $("#status-action").textContent = "操作：" + action;
    const okEl = $("#status-ok");
    okEl.textContent = "成功：" + String(payload.ok);
    okEl.className = "status-pill " + (payload.ok ? "status-ok-true" : "status-ok-false");

    if (action === "lookup") {
      renderLookup(data);
    } else {
      renderHighlights(data, action);
      renderArtifacts(data, action);
    }

    $("#raw-json-wrap").classList.remove("hidden");
    $("#raw-json").textContent = JSON.stringify(payload, null, 2);

    if (payload.stderr) {
      $("#stderr-block").classList.remove("hidden");
      $("#stderr-text").textContent = payload.stderr;
    }
  }

  function renderLookup(data) {
    $("#matches-block").classList.remove("hidden");
    const matches = data.matches || [];
    const rows = matches.map((m) => `
      <tr>
        <td class="mono">${esc(m.case_dir || "")}</td>
        <td>${esc(m.client_ref || "")}</td>
        <td>${esc(m.case_id || "")}</td>
        <td>${esc(m.product_sku || "")}</td>
        <td><span class="badge ${gateBadgeClass(m.gate_status)}">${esc(m.gate_status || "")}</span></td>
        <td>${esc((m.known_limits || []).join(", "))}</td>
      </tr>
    `).join("");

    $("#matches-table").innerHTML = `
      <table>
        <thead><tr>
          <th>案例目錄</th><th>客戶代號</th><th>case_id</th><th>產品 SKU</th><th>Gate 狀態</th><th>known_limits</th>
        </tr></thead>
        <tbody>${rows || "<tr><td colspan='6'>無符合案例</td></tr>"}</tbody>
      </table>
    `;

    const indexNotes = data.notes || [];
    const notesEl = $("#lookup-notes");
    if (indexNotes.length) {
      notesEl.textContent = "備註：" + indexNotes.join(", ");
      notesEl.classList.remove("hidden");
    } else {
      notesEl.textContent = "";
      notesEl.classList.add("hidden");
    }

    const limits = data.known_limits || data.disclaimer || "";
    const matchCount = data.match_count ?? matches.length;
    $("#known-limits").textContent = limits
      ? "known_limits：" + (typeof limits === "string" ? limits : JSON.stringify(limits))
      : "符合筆數：" + matchCount;
  }

  function renderHighlights(data, action) {
    $("#highlights").classList.remove("hidden");

    const caseDir = data.case_dir || data.case_dir_rel || "";
    $("#hl-case-dir").textContent = caseDir || "—";

    const gateStatus = data.gate_status || data.eligibility || (data.gate && data.gate.eligibility) || "";
    setBadge($("#hl-gate-status"), gateStatus, gateStatus);

    let schemaNotes = [];
    if (data.schema && data.schema.notes) {
      schemaNotes = data.schema.notes;
    } else if (data.schema_notes) {
      schemaNotes = data.schema_notes;
    } else if (data.gate && data.gate.dimensions && data.gate.dimensions.schema) {
      schemaNotes = data.gate.dimensions.schema.notes || [];
    }
    $("#hl-schema-notes").textContent = schemaNotes.length ? schemaNotes.join(", ") : "—";

    let schemaWarnings = [];
    if (data.schema && data.schema.warnings) {
      schemaWarnings = data.schema.warnings;
    } else if (data.schema_warnings) {
      schemaWarnings = data.schema_warnings;
    } else if (data.gate && data.gate.dimensions && data.gate.dimensions.schema) {
      schemaWarnings = data.gate.dimensions.schema.warnings || [];
    }
    $("#hl-schema-warnings").textContent = schemaWarnings.length ? schemaWarnings.join(", ") : "—";

    const og = data.output_guard || {};
    const ogStatus = og.status || "";
    setBadge($("#hl-og-status"), ogStatus || "—", ogStatus);
    $("#hl-og-ratio").textContent = og.ratio != null ? String(og.ratio) : "—";

    if (action === "e2e" && data.overall_ok != null) {
      const okEl = $("#status-ok");
      okEl.textContent = "整體結果：" + String(data.overall_ok);
      okEl.className = "status-pill " + (data.overall_ok ? "status-ok-true" : "status-ok-false");
    }
  }

  function renderArtifacts(data, action) {
    const arts = data.artifacts || {};
    const caseDir = data.case_dir || "";
    const paths = [];

    const keys = [
      ["report_json", "reports/report.json"],
      ["report_md", "reports/report.md"],
      ["eligibility_result_json", "reports/eligibility_result.json"],
      ["delivery_signoff_md", "delivery_signoff.md"],
      ["cleaned_csv", "cleaned/*.csv"],
    ];

    keys.forEach(([key, fallback]) => {
      const val = arts[key];
      if (val) paths.push({ path: val, exists: true });
      else if (caseDir) paths.push({ path: caseDir + "/" + fallback, exists: false });
    });

    if (!paths.length) return;

    $("#artifacts").classList.remove("hidden");
    $("#artifact-list").innerHTML = paths.map((p) =>
      `<li class="${p.exists ? "" : "missing"}">${esc(p.path)}${p.exists ? "" : "（回應中未含）"}</li>`
    ).join("");
  }

  function esc(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  async function postJson(url, body) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return res.json();
  }

  function formToObject(form) {
    const fd = new FormData(form);
    const obj = {};
    fd.forEach((v, k) => { obj[k] = v; });
    if (form.querySelector("[name=run_gate]")) {
      obj.run_gate = form.querySelector("[name=run_gate]").checked;
    }
    if (form.querySelector("[name=list_all]")) {
      obj.list_all = form.querySelector("[name=list_all]").checked;
    }
    return obj;
  }

  async function handleSubmit(form, url, panel) {
    panel.classList.add("loading");
    try {
      const payload = await postJson(url, formToObject(form));
      showResponse(payload);
    } catch (err) {
      showResponse({ ok: false, action: "error", message: String(err), data: {} });
    } finally {
      panel.classList.remove("loading");
    }
  }

  $("#lookup-form").addEventListener("submit", (e) => {
    e.preventDefault();
    handleSubmit(e.target, "/api/lookup", $("#lookup-panel"));
  });

  $("#newcase-form").addEventListener("submit", (e) => {
    e.preventDefault();
    handleSubmit(e.target, "/api/new-case", $("#newcase-panel"));
  });

  $("#e2e-form").addEventListener("submit", (e) => {
    e.preventDefault();
    handleSubmit(e.target, "/api/e2e", $("#e2e-panel"));
  });

  document.querySelectorAll(".preset").forEach((btn) => {
    btn.addEventListener("click", () => {
      $("#case-dir-input").value = btn.dataset.case;
    });
  });

  $("#btn-reindex").addEventListener("click", async () => {
    $("#lookup-panel").classList.add("loading");
    try {
      const payload = await postJson("/api/reindex", {});
      showResponse(payload);
    } catch (err) {
      showResponse({ ok: false, action: "reindex", message: String(err), data: {} });
    } finally {
      $("#lookup-panel").classList.remove("loading");
    }
  });
})();
