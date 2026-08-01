/**
 * W4-UI-A/B/C/D/E command-center shell helpers.
 * Secrets: mask-only — never render plaintext keys.
 */
(function (global) {
  "use strict";

  var SECRET_PATTERNS = [
    /sk-[A-Za-z0-9]{10,}/g,
    /api[_-]?key\s*[:=]\s*["']?[^"'\s]+/gi,
    /Bearer\s+[A-Za-z0-9\-._~+/]+=*/g,
  ];

  var NAV_ICONS = {
    p1: "⌂",
    p5: "▦",
    p4: "▣",
    p3: "◈",
    p2: "◇",
    settings: "⚙",
  };

  var KPI_ICONS = {
    pulse: "◎",
    clock: "◷",
    user: "☺",
    check: "✓",
    timer: "◔",
    alert: "!",
    coin: "¤",
    default: "•",
  };

  var FLOW_ICONS = {
    chat: "💬",
    crown: "♛",
    scroll: "📜",
    stamp: "✱",
    board: "▦",
    people: "☰",
    shield: "⛨",
    box: "▣",
    flow: "⇄",
    graph: "⬡",
    cube: "▦",
    brain: "◎",
    target: "◎",
    globe: "○",
  };

  var MODULE_ICONS = {
    flow: "⇄",
    graph: "⬡",
    cube: "▣",
    brain: "◎",
    target: "⌖",
    globe: "◌",
    box: "▦",
    default: "•",
  };

  function maskSecrets(text) {
    var s = String(text == null ? "" : text);
    for (var i = 0; i < SECRET_PATTERNS.length; i++) {
      s = s.replace(SECRET_PATTERNS[i], "••••••••");
    }
    return s;
  }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = maskSecrets(text);
    return node;
  }

  function statusColor(status) {
    if (status === "yellow") return "var(--yellow)";
    if (status === "red") return "var(--red)";
    if (status === "blue") return "var(--accent-blue)";
    if (status === "gold") return "var(--gold)";
    if (status === "gray") return "var(--text-dim)";
    return "var(--green)";
  }

  function loadJson(url) {
    return fetch(url, { cache: "no-store" }).then(function (res) {
      if (!res.ok) throw new Error("data load failed: " + res.status + " · " + url);
      return res.json();
    });
  }

  /**
   * Data source switch for W4-UI-F.
   * Default: mock (preserves A–E regression).
   * Enable live: ?source=live or ?data=live
   */
  function resolveDataSource() {
    try {
      var params = new URLSearchParams(window.location.search || "");
      var q = String(params.get("source") || params.get("data") || "").toLowerCase();
      if (q === "live" || q === "mock") return q;
    } catch (e) {
      /* ignore */
    }
    return "mock";
  }

  /**
   * Load page JSON: live primary when source=live, else mock.
   * Live failure falls back to mock and tags _resolved_source=mock_fallback.
   * opts: { mockUrl, liveUrl }
   */
  function loadPageData(opts) {
    var mockUrl = (opts && opts.mockUrl) || "";
    var liveUrl = (opts && opts.liveUrl) || mockUrl;
    var source = resolveDataSource();
    var primary = source === "live" ? liveUrl : mockUrl;

    function tag(data, resolved, url, liveErr) {
      if (!data || typeof data !== "object") throw new Error("invalid page data");
      data._resolved_source = resolved;
      data._loaded_url = url;
      if (liveErr) data._live_error = liveErr;
      return data;
    }

    return loadJson(primary)
      .then(function (data) {
        if (!data || data.ok !== true) throw new Error("primary ok!=true");
        return tag(data, source, primary, null);
      })
      .catch(function (err) {
        var msg = String(err && err.message ? err.message : err);
        if (source === "live" && mockUrl && primary !== mockUrl) {
          return loadJson(mockUrl).then(function (data) {
            if (!data || data.ok !== true) throw err;
            return tag(data, "mock_fallback", mockUrl, msg);
          });
        }
        throw err;
      });
  }

  function applyBrand(data) {
    var brand = data.brand || {};
    var brandEl = document.getElementById("brand-title");
    if (brandEl) brandEl.textContent = brand.title || "三省六部指揮中心";
    var titleEl = document.getElementById("page-title");
    if (titleEl) titleEl.textContent = brand.page_title || "";
    var subEl = document.getElementById("page-sub");
    if (subEl) subEl.textContent = brand.subtitle || "";
    var tzEl = document.getElementById("tz-label");
    if (tzEl) tzEl.textContent = brand.timezone_label || "";
    var clockEl = document.getElementById("clock-label");
    if (clockEl) clockEl.textContent = brand.clock_demo || "";
    var opEl = document.getElementById("operator-label");
    if (opEl) opEl.textContent = brand.operator || "";
    var secretEl = document.getElementById("secret-mask");
    if (secretEl && data.secrets) {
      secretEl.textContent = data.secrets.api_key_display || "••••••••";
    }
  }

  function setDemoBanner(data, pageTag) {
    var banner = document.getElementById("demo-banner");
    if (!banner) return;
    var resolved = data._resolved_source || (data.data_source === "live_projection" ? "live" : "mock");
    var modeLabel =
      resolved === "live"
        ? "live projection"
        : resolved === "mock_fallback"
          ? "mock fallback (live failed)"
          : data.demo
            ? "demo mock"
            : "mock";
    banner.textContent =
      modeLabel +
      " · read_only · " +
      (pageTag || "shell") +
      " · source=" +
      resolved +
      " · host=" +
      (data.host || "ui/command_center") +
      " · ≠ Grafana / PG soak / DarkOps / Operator prod · 金鑰僅遮罩";
  }

  function renderNav(navRoot, items) {
    if (!navRoot) return;
    navRoot.innerHTML = "";
    (items || []).forEach(function (item) {
      var a = el(
        "a",
        "nav-item" + (item.active ? " active" : "") + (item.deferred ? " deferred" : "")
      );
      a.href = item.href || "#";
      if (item.deferred) a.title = "Deferred: " + item.deferred;
      a.appendChild(el("span", "nav-icon", NAV_ICONS[item.id] || "•"));
      a.appendChild(el("span", null, item.label));
      navRoot.appendChild(a);
    });
  }

  function renderKpis(root, kpis) {
    if (!root) return;
    root.innerHTML = "";
    (kpis || []).forEach(function (kpi) {
      var card = el("div", "kpi-card");
      var top = el("div", "kpi-top");
      var icon = el("span", "kpi-icon", KPI_ICONS[kpi.icon] || KPI_ICONS.default);
      top.appendChild(icon);
      top.appendChild(el("div", "kpi-label", kpi.label));
      card.appendChild(top);
      var value = el("div", "kpi-value", kpi.value);
      if (kpi.key_related) value.classList.add("mask");
      card.appendChild(value);
      card.appendChild(el("div", "kpi-delta " + (kpi.tone === "up" ? "kpi-up" : "kpi-down"), kpi.delta));
      root.appendChild(card);
    });
  }

  function renderFlow(root, flow) {
    if (!root) return;
    root.innerHTML = "";
    (flow || []).forEach(function (step, idx) {
      if (idx > 0) root.appendChild(el("div", "flow-arrow", "→"));
      var node = el("div", "flow-node" + (step.highlight ? " highlight" : ""));
      var glyph = FLOW_ICONS[step.icon] || (step.label || "?").slice(0, 1);
      node.appendChild(el("div", "flow-node-icon", glyph));
      if (step.highlight) node.appendChild(el("span", "flow-status-dot yellow", ""));
      else node.appendChild(el("span", "flow-status-dot green", ""));
      node.appendChild(el("div", "flow-node-label", step.label));
      root.appendChild(node);
    });
  }

  function renderStatusList(root, rows) {
    if (!root) return;
    root.innerHTML = "";
    var wrap = el("div", "status-chip-grid");
    (rows || []).forEach(function (row) {
      var chip = el("div", "status-chip");
      chip.appendChild(el("span", "dot dot-" + (row.status || "green")));
      chip.appendChild(el("span", "status-name", row.name));
      var lab = el("span", "status-label", row.label);
      lab.style.color = statusColor(row.status);
      chip.appendChild(lab);
      wrap.appendChild(chip);
    });
    root.appendChild(wrap);
  }

  function renderActivity(root, rows) {
    if (!root) return;
    root.innerHTML = "";
    (rows || []).forEach(function (row) {
      var line = el("div", "log-entry");
      line.appendChild(el("span", "log-time", row.time));
      line.appendChild(el("span", "log-tag tag-" + (row.tag || "info"), row.tag_label || row.tag));
      line.appendChild(el("span", "log-msg", row.msg));
      root.appendChild(line);
    });
  }

  function boolCell(v) {
    return el("span", v ? "badge-true" : "badge-false", v ? "true" : "false");
  }

  function renderOperatorFields(root, op) {
    if (!root) return;
    root.innerHTML = "";
    if (!op || op.ok !== true) {
      root.appendChild(el("div", "skeleton-note", "operator_fields unavailable / skeleton"));
      return;
    }
    var table = el("table", "op-table");
    var thead = document.createElement("thead");
    var hr = document.createElement("tr");
    (op.fields || []).forEach(function (f) {
      hr.appendChild(el("th", null, f));
    });
    thead.appendChild(hr);
    table.appendChild(thead);
    var tbody = document.createElement("tbody");
    (op.rows || []).forEach(function (row) {
      var tr = document.createElement("tr");
      (op.fields || []).forEach(function (f) {
        var td = document.createElement("td");
        var val = row[f];
        if (typeof val === "boolean") {
          td.appendChild(boolCell(val));
        } else {
          td.textContent = maskSecrets(val == null ? "—" : String(val));
        }
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    root.appendChild(table);
    root.appendChild(
      el(
        "div",
        "skeleton-note",
        "schema=" + (op.schema_version || "?") + " · demo=" + String(!!op.demo) + " · read_only=" + String(!!op.read_only)
      )
    );
  }

  function renderSummaryList(root, rows, kind) {
    if (!root) return;
    root.innerHTML = "";
    (rows || []).forEach(function (row) {
      var line = el("div", "side-row");
      line.appendChild(el("span", "side-label", row.label));
      var right = el("span", "side-right");
      right.appendChild(el("span", "side-value", String(row.value)));
      if (kind === "business" && row.delta) {
        right.appendChild(
          el("span", "side-delta " + (row.tone === "up" ? "kpi-up" : "kpi-down"), row.delta)
        );
      }
      if (kind === "ops" && row.link) {
        right.appendChild(el("span", "linkish", row.link));
      }
      line.appendChild(right);
      root.appendChild(line);
    });
  }

  function renderSkills(root, rows) {
    if (!root) return;
    root.innerHTML = "";
    var max = 1;
    (rows || []).forEach(function (r) {
      if (r.count > max) max = r.count;
    });
    (rows || []).forEach(function (row) {
      var line = el("div", "bar-row");
      line.appendChild(el("span", "bar-label", row.name));
      var track = el("div", "bar-track");
      var fill = el("div", "bar-fill");
      fill.style.width = Math.max(8, Math.round((row.count / max) * 100)) + "%";
      track.appendChild(fill);
      line.appendChild(track);
      line.appendChild(el("span", "bar-count", String(row.count)));
      root.appendChild(line);
    });
  }

  function renderNamedStatus(root, rows, withExtra) {
    if (!root) return;
    root.innerHTML = "";
    (rows || []).forEach(function (row) {
      var line = el("div", "status-row");
      line.appendChild(el("span", "dot dot-" + (row.status || "green")));
      line.appendChild(el("span", "status-name", row.name));
      var lab = el("span", "status-label", row.label || row.latency || row.success_rate || "");
      lab.style.color = statusColor(row.status);
      line.appendChild(lab);
      if (withExtra === "latency" && row.latency) {
        line.appendChild(el("span", "meta-right", row.latency));
      }
      if (withExtra === "rate" && row.success_rate) {
        line.appendChild(el("span", "meta-right", row.success_rate));
      }
      root.appendChild(line);
    });
  }

  function cellClass(state) {
    return "swim-cell state-" + (state || "idle");
  }

  function renderSwimlane(root, swim) {
    if (!root) return;
    root.innerHTML = "";
    if (!swim) {
      root.appendChild(el("div", "skeleton-note", "swimlane skeleton"));
      return;
    }
    var board = el("div", "swim-board");
    var head = el("div", "swim-head");
    head.appendChild(el("div", "swim-task-col head-label", "任務"));
    (swim.stages || []).forEach(function (st) {
      var col = el("div", "swim-stage-head");
      col.appendChild(el("div", "stage-title", st.label));
      col.appendChild(el("div", "stage-sub", st.sub || ""));
      head.appendChild(col);
    });
    head.appendChild(el("div", "swim-term-col head-label", "終態"));
    board.appendChild(head);

    (swim.tasks || []).forEach(function (task) {
      var row = el("div", "swim-row");
      var meta = el("div", "swim-task-col");
      meta.appendChild(el("div", "task-name", task.name));
      meta.appendChild(el("div", "task-id", "#" + task.id));
      var badges = el("div", "task-badges");
      badges.appendChild(el("span", "prio prio-" + (task.priority_tone || "mid"), task.priority));
      badges.appendChild(el("span", "task-status", task.status_label));
      meta.appendChild(badges);
      row.appendChild(meta);

      (task.cells || []).forEach(function (cell) {
        var c = el("div", cellClass(cell.state));
        if (cell.state === "running" && cell.progress != null) {
          var bar = el("div", "mini-progress");
          var fill = el("div", "mini-progress-fill");
          fill.style.width = String(cell.progress) + "%";
          bar.appendChild(fill);
          c.appendChild(bar);
          c.appendChild(el("div", "cell-label", cell.label || cell.progress + "%"));
        } else if (cell.label) {
          c.appendChild(el("div", "cell-label", cell.label));
        } else {
          c.appendChild(el("span", "cell-dot", ""));
        }
        row.appendChild(c);
      });

      var term = el("div", "swim-term-col terminal-" + ((task.terminal && task.terminal.tone) || "gray"));
      if (task.terminal) {
        term.appendChild(el("div", "term-label", task.terminal.label));
        term.appendChild(el("div", "term-count", String(task.terminal.count)));
      }
      row.appendChild(term);
      board.appendChild(row);
    });
    root.appendChild(board);
  }

  function renderLegend(root, legend) {
    if (!root) return;
    root.innerHTML = "";
    (legend || []).forEach(function (item) {
      var chip = el("span", "legend-item");
      chip.appendChild(el("span", "dot dot-" + (item.color === "blue" ? "blue" : item.color === "gray" ? "gray" : item.color), ""));
      chip.appendChild(el("span", null, item.label));
      root.appendChild(chip);
    });
  }

  function renderP1(data) {
    applyBrand(data);
    renderNav(document.getElementById("sidebar-nav"), data.nav);
    renderKpis(document.getElementById("kpi-grid"), data.kpis);
    renderFlow(document.getElementById("flow-row"), data.flow);
    renderStatusList(document.getElementById("dept-status"), data.departments);
    renderStatusList(document.getElementById("dark-status"), data.dark_modules);
    renderActivity(document.getElementById("activity-log"), data.activity);
    renderOperatorFields(document.getElementById("operator-fields"), data.operator_fields);
    setDemoBanner(data, "P1");
  }

  function renderP5(data) {
    applyBrand(data);
    renderNav(document.getElementById("sidebar-nav"), data.nav);
    renderKpis(document.getElementById("kpi-grid"), data.kpis);
    var swim = data.swimlane || {};
    renderLegend(document.getElementById("swim-legend"), swim.legend);
    renderSwimlane(document.getElementById("swimlane-board"), swim);
    renderSummaryList(document.getElementById("business-summary"), data.business_summary, "business");
    renderSummaryList(document.getElementById("ops-monitor"), data.ops_monitor, "ops");
    renderSkills(document.getElementById("skills-top"), data.skills_top);
    renderNamedStatus(document.getElementById("tools-status"), data.tools);
    renderNamedStatus(document.getElementById("models-status"), data.models, "latency");
    renderNamedStatus(document.getElementById("apis-status"), data.apis, "rate");
    setDemoBanner(data, "P5");
  }

  function renderMetricGrid(root, metrics) {
    if (!root) return;
    var grid = el("div", "p4-metric-grid");
    (metrics || []).forEach(function (m) {
      var cell = el("div", "p4-metric");
      cell.appendChild(el("div", "p4-metric-label", m.label));
      var val = el("div", "p4-metric-value" + (m.tone ? " tone-" + m.tone : ""), String(m.value));
      cell.appendChild(val);
      grid.appendChild(cell);
    });
    root.appendChild(grid);
  }

  function renderProvinceCard(root, card, kind) {
    if (!root || !card) return;
    root.innerHTML = "";
    root.className = "p4-province-card" + (kind ? " kind-" + kind : "");
    var head = el("div", "p4-card-head");
    head.appendChild(el("div", "p4-card-name", card.name));
    if (card.tag) head.appendChild(el("span", "p4-card-tag", card.tag));
    root.appendChild(head);
    root.appendChild(el("div", "p4-card-role", card.role || ""));
    if (card.metrics) renderMetricGrid(root, card.metrics);
    if (card.kpis) {
      var kpiRow = el("div", "p4-shangshu-kpis");
      (card.kpis || []).forEach(function (k) {
        var box = el("div", "p4-shangshu-kpi");
        box.appendChild(el("div", "p4-metric-label", k.label));
        box.appendChild(el("div", "p4-metric-value", String(k.value)));
        if (k.delta) box.appendChild(el("div", "kpi-up", k.delta));
        if (k.progress != null) {
          var bar = el("div", "mini-progress");
          var fill = el("div", "mini-progress-fill");
          fill.style.width = String(k.progress) + "%";
          bar.appendChild(fill);
          box.appendChild(bar);
        }
        kpiRow.appendChild(box);
      });
      root.appendChild(kpiRow);
    }
  }

  function renderEntryNodes(root, nodes) {
    if (!root) return;
    root.innerHTML = "";
    (nodes || []).forEach(function (n) {
      var card = el("div", "p4-entry-node");
      var glyph = FLOW_ICONS[n.icon] || (n.label || "?").slice(0, 1);
      card.appendChild(el("div", "flow-node-icon", glyph));
      card.appendChild(el("div", "p4-entry-label", n.label));
      if (n.hint) card.appendChild(el("div", "p4-entry-hint", n.hint));
      root.appendChild(card);
    });
  }

  function renderMinistries(root, rows) {
    if (!root) return;
    root.innerHTML = "";
    (rows || []).forEach(function (m) {
      var card = el("div", "p4-ministry-card");
      var head = el("div", "p4-ministry-head");
      head.appendChild(el("span", "p4-ministry-name", m.name));
      head.appendChild(el("span", "dot dot-" + (m.status || "green"), ""));
      card.appendChild(head);
      card.appendChild(el("div", "p4-ministry-tasks", String(m.tasks) + " 任務"));
      card.appendChild(el("div", "p4-ministry-status", m.status_label || ""));
      var skills = el("div", "p4-ministry-skills");
      (m.skills || []).forEach(function (s) {
        skills.appendChild(el("span", "p4-skill-chip", s));
      });
      card.appendChild(skills);
      card.appendChild(el("div", "p4-ministry-agent", m.agent || ""));
      root.appendChild(card);
    });
  }

  function renderTaskQueues(root, monitor) {
    if (!root) return;
    root.innerHTML = "";
    if (!monitor) {
      root.appendChild(el("div", "skeleton-note", "task_monitor skeleton"));
      return;
    }
    (monitor.queues || []).forEach(function (q) {
      var box = el("div", "p4-queue" + (q.tone === "red" ? " alert" : ""));
      var head = el("div", "p4-queue-head");
      head.appendChild(el("span", "p4-queue-label", q.label));
      head.appendChild(el("span", "p4-queue-count tone-" + (q.tone || "cyan"), String(q.count)));
      box.appendChild(head);
      (q.items || []).forEach(function (item) {
        var line = el("div", "p4-queue-item" + (item.severity ? " critical" : ""));
        line.appendChild(el("span", "p4-queue-id", "#" + item.id));
        line.appendChild(el("span", "p4-queue-title", item.title));
        box.appendChild(line);
      });
      var more = el("div", "linkish p4-queue-more", "查看全部 →");
      box.appendChild(more);
      root.appendChild(box);
    });
  }

  function renderP4(data) {
    applyBrand(data);
    renderNav(document.getElementById("sidebar-nav"), data.nav);
    var prov = data.provinces || {};
    renderEntryNodes(document.getElementById("p4-entry-nodes"), prov.entry_nodes);
    renderProvinceCard(document.getElementById("p4-zhongshu"), prov.zhongshu, "zhongshu");
    renderProvinceCard(document.getElementById("p4-menxia"), prov.menxia, "menxia");
    renderProvinceCard(document.getElementById("p4-shangshu"), prov.shangshu, "shangshu");
    renderMinistries(document.getElementById("p4-ministries"), data.ministries);
    var mon = data.task_monitor || {};
    var monTitle = document.getElementById("p4-monitor-title");
    if (monTitle) monTitle.textContent = mon.title || "任務監控";
    renderTaskQueues(document.getElementById("p4-task-queues"), mon);
    renderOperatorFields(document.getElementById("operator-fields"), data.operator_fields);
    setDemoBanner(data, "P4");
  }

  function toneClass(tone) {
    if (!tone) return "";
    if (tone === "accent") return " tone-accent";
    return " tone-" + tone;
  }

  function renderP3Modules(root, modules) {
    if (!root) return;
    root.innerHTML = "";
    (modules || []).forEach(function (m) {
      var card = el("div", "p3-module-card");
      var head = el("div", "p3-module-head");
      head.appendChild(
        el("span", "p3-module-icon", MODULE_ICONS[m.icon] || MODULE_ICONS.default)
      );
      head.appendChild(el("span", "dot dot-" + (m.status || "green"), ""));
      head.appendChild(el("span", "p3-module-name", m.name));
      card.appendChild(head);
      card.appendChild(
        el(
          "div",
          "p3-module-stat",
          "健康：" + (m.health || "—") + " · " + (m.metric_label || "") + "：" + (m.metric_value || "—")
        )
      );
      root.appendChild(card);
    });
  }

  function renderP3Loop(root, loop) {
    if (!root) return;
    root.innerHTML = "";
    if (!loop) {
      root.appendChild(el("div", "skeleton-note", "loop_flow skeleton"));
      return;
    }
    (loop.stages || []).forEach(function (stage, idx) {
      if (idx > 0) root.appendChild(el("div", "p3-loop-arrow", "→"));
      var box = el("div", "p3-loop-box" + (stage.highlight ? " highlight" : ""));
      var head = el("div", "p3-loop-box-title");
      var glyph = FLOW_ICONS[stage.icon] || MODULE_ICONS[stage.icon] || "•";
      head.appendChild(el("span", "p3-loop-icon", glyph));
      head.appendChild(el("span", null, stage.label));
      box.appendChild(head);
      (stage.items || []).forEach(function (item) {
        var line = el("div", "p3-loop-item");
        line.appendChild(el("span", null, item.label));
        line.appendChild(
          el("span", "p3-loop-val" + toneClass(item.tone), String(item.value))
        );
        box.appendChild(line);
      });
      if (stage.footer) {
        var foot = el("div", "p3-loop-footer");
        foot.appendChild(el("span", null, stage.footer.label));
        foot.appendChild(
          el(
            "span",
            "p3-loop-val" + toneClass(stage.footer.tone),
            String(stage.footer.value)
          )
        );
        box.appendChild(foot);
      }
      root.appendChild(box);
    });
  }

  function renderP3Side(root, monitor) {
    if (!root) return;
    root.innerHTML = "";
    if (!monitor) {
      root.appendChild(el("div", "skeleton-note", "side_monitor skeleton"));
      return;
    }
    (monitor.cards || []).forEach(function (c) {
      var card = el("div", "p3-monitor-card");
      var head = el("div", "p3-monitor-head");
      head.appendChild(el("span", "p3-monitor-label", c.label));
      if (c.status_label) {
        head.appendChild(
          el("span", "p3-monitor-status tone-" + (c.status || "green"), c.status_label)
        );
      }
      card.appendChild(head);
      card.appendChild(
        el(
          "div",
          "p3-monitor-value" + (c.status === "yellow" ? " tone-yellow" : ""),
          String(c.value)
        )
      );
      if (c.delta) {
        card.appendChild(
          el(
            "div",
            "p3-monitor-delta " +
              (c.delta_tone === "up"
                ? "kpi-up"
                : c.delta_tone === "down"
                  ? "kpi-down"
                  : ""),
            c.delta
          )
        );
      }
      if (c.breakdown) {
        card.appendChild(el("div", "p3-monitor-break", c.breakdown));
      }
      if (c.instances) {
        card.appendChild(el("div", "p3-monitor-meta", "可用實例 " + c.instances));
      }
      if (c.resource_pct != null) {
        card.appendChild(el("div", "p3-monitor-meta", c.resource_label || "資源使用率"));
        var bar = el("div", "mini-progress");
        var fill = el("div", "mini-progress-fill");
        fill.style.width = String(c.resource_pct) + "%";
        bar.appendChild(fill);
        card.appendChild(bar);
      }
      root.appendChild(card);
    });
  }

  function renderP3Footer(root, strip) {
    if (!root) return;
    root.innerHTML = "";
    if (!strip) return;
    ["uptime", "global_success", "today_exec", "updated_at", "source"].forEach(function (k) {
      if (strip[k]) root.appendChild(el("span", "p3-footer-item", strip[k]));
    });
  }

  function renderP3(data) {
    applyBrand(data);
    renderNav(document.getElementById("sidebar-nav"), data.nav);
    var brand = data.brand || {};
    var badge = document.getElementById("p3-sys-badge");
    if (badge && brand.system_status) {
      badge.textContent = "● " + brand.system_status;
      badge.className = "p3-sys-badge tone-" + (brand.system_status_tone || "green");
    }
    renderP3Modules(document.getElementById("p3-modules"), data.modules);
    var loop = data.loop_flow || {};
    var loopTitle = document.getElementById("p3-loop-title");
    if (loopTitle) loopTitle.textContent = loop.title || "流程閉環視圖";
    renderP3Loop(document.getElementById("p3-loop-stages"), loop);
    var back = document.getElementById("p3-backflow");
    if (back) {
      back.textContent = loop.backflow_label
        ? "↺ " + loop.backflow_label
        : "";
    }
    var mon = data.side_monitor || {};
    var monTitle = document.getElementById("p3-monitor-title");
    if (monTitle) monTitle.textContent = mon.title || "即時監控";
    renderP3Side(document.getElementById("p3-side-cards"), mon);
    renderP3Footer(document.getElementById("p3-footer-strip"), data.footer_strip);
    renderOperatorFields(document.getElementById("operator-fields"), data.operator_fields);
    setDemoBanner(data, "P3");
  }

  function renderSparkline(root, values) {
    if (!root) return;
    root.innerHTML = "";
    var vals = values || [];
    var max = 1;
    vals.forEach(function (v) {
      if (v > max) max = v;
    });
    var row = el("div", "p2-sparkline");
    vals.forEach(function (v) {
      var bar = el("span", "p2-spark-bar");
      bar.style.height = Math.max(12, Math.round((v / max) * 36)) + "px";
      row.appendChild(bar);
    });
    root.appendChild(row);
  }

  function renderDonut(root, mix) {
    if (!root || !mix) return;
    root.innerHTML = "";
    var local = Number(mix.local_pct) || 0;
    var cloud = Number(mix.cloud_pct) || 0;
    var wrap = el("div", "p2-donut-wrap");
    var donut = el("div", "p2-donut");
    donut.style.background =
      "conic-gradient(var(--accent-deep) 0 " +
      local +
      "%, var(--accent-blue) " +
      local +
      "% 100%)";
    var hole = el("div", "p2-donut-hole");
    hole.appendChild(el("div", "p2-donut-pct", local + "% / " + cloud + "%"));
    donut.appendChild(hole);
    wrap.appendChild(donut);
    var legend = el("div", "p2-donut-legend");
    legend.appendChild(
      el("div", null, (mix.local_label || "本地") + " " + local + "%")
    );
    legend.appendChild(
      el("div", null, (mix.cloud_label || "雲端") + " " + cloud + "%")
    );
    wrap.appendChild(legend);
    root.appendChild(wrap);
  }

  function renderP2SkillCards(root, rows) {
    if (!root) return;
    root.innerHTML = "";
    (rows || []).forEach(function (m) {
      var card = el("div", "p2-skill-card");
      var head = el("div", "p2-skill-head");
      var glyph = FLOW_ICONS[m.icon] || MODULE_ICONS[m.icon] || KPI_ICONS[m.icon] || "•";
      head.appendChild(el("span", "p2-skill-icon", glyph));
      head.appendChild(el("span", "p2-skill-name", m.name));
      card.appendChild(head);
      card.appendChild(
        el("div", "p2-skill-mounted", "已掛載技能數 " + String(m.mounted_skills))
      );
      var mods = el("div", "p2-skill-modules");
      mods.appendChild(el("div", "p2-skill-mod-label", "技能模組"));
      (m.modules || []).forEach(function (name) {
        mods.appendChild(el("span", "p2-skill-chip", name));
      });
      card.appendChild(mods);
      var foot = el("div", "p2-skill-foot");
      var health = el(
        "span",
        "p2-skill-health tone-" + (m.health_status || "green"),
        m.health || "—"
      );
      foot.appendChild(health);
      foot.appendChild(
        el(
          "span",
          "p2-skill-anomaly" + (m.anomaly_count > 0 ? " has-anomaly" : ""),
          "異常數 " + String(m.anomaly_count == null ? 0 : m.anomaly_count)
        )
      );
      card.appendChild(foot);
      root.appendChild(card);
    });
  }

  function renderP2SkillMap(root, map) {
    if (!root) return;
    root.innerHTML = "";
    if (!map) {
      root.appendChild(el("div", "skeleton-note", "skill_module_map skeleton"));
      return;
    }
    var table = el("table", "p2-table");
    var thead = document.createElement("thead");
    var hr = document.createElement("tr");
    (map.columns || []).forEach(function (c) {
      hr.appendChild(el("th", null, c));
    });
    thead.appendChild(hr);
    table.appendChild(thead);
    var tbody = document.createElement("tbody");
    (map.rows || []).forEach(function (row) {
      var tr = document.createElement("tr");
      [
        row.skill,
        row.dept,
        row.type,
        row.module,
        row.status,
        row.updated_at,
      ].forEach(function (val, idx) {
        var td = document.createElement("td");
        if (idx === 4) {
          td.appendChild(
            el(
              "span",
              "p2-status-pill tone-" + (row.status_tone || "cyan"),
              String(val || "—")
            )
          );
        } else {
          td.textContent = maskSecrets(val == null ? "—" : String(val));
        }
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    root.appendChild(table);
  }

  function renderP2ResourceTop(root, gov) {
    if (!root) return;
    root.innerHTML = "";
    if (!gov) return;
    var mixCard = el("div", "p2-metric-card");
    mixCard.appendChild(el("div", "p2-metric-title", (gov.deploy_mix || {}).title || "部署環境占比"));
    var donutHost = el("div", null);
    mixCard.appendChild(donutHost);
    root.appendChild(mixCard);
    renderDonut(donutHost, gov.deploy_mix);

    function metricCard(cfg) {
      var card = el("div", "p2-metric-card");
      card.appendChild(el("div", "p2-metric-title", cfg.title || ""));
      card.appendChild(el("div", "p2-metric-value", cfg.value || "—"));
      card.appendChild(
        el(
          "div",
          "p2-metric-delta " + (cfg.delta_tone === "up" ? "kpi-up" : "kpi-down"),
          cfg.delta || ""
        )
      );
      var spark = el("div", null);
      card.appendChild(spark);
      renderSparkline(spark, cfg.sparkline);
      return card;
    }
    root.appendChild(metricCard(gov.api_today || {}));
    root.appendChild(metricCard(gov.token_today || {}));
  }

  function renderP2CloudBars(root, breakdown) {
    if (!root) return;
    root.innerHTML = "";
    if (!breakdown) return;
    (breakdown.items || []).forEach(function (item) {
      var row = el("div", "p2-cloud-row");
      var head = el("div", "p2-cloud-head");
      head.appendChild(el("span", null, item.name));
      head.appendChild(
        el("span", "p2-cloud-meta", String(item.count) + " · " + String(item.pct) + "%")
      );
      row.appendChild(head);
      var track = el("div", "bar-track");
      var fill = el("div", "bar-fill");
      fill.style.width = Math.max(4, Math.min(100, Number(item.pct) || 0)) + "%";
      track.appendChild(fill);
      row.appendChild(track);
      root.appendChild(row);
    });
  }

  function renderP2KeyVault(root, vault) {
    if (!root) return;
    root.innerHTML = "";
    if (!vault) {
      root.appendChild(el("div", "skeleton-note", "key_vault skeleton"));
      return;
    }
    var table = el("table", "p2-table p2-vault-table");
    var thead = document.createElement("thead");
    var hr = document.createElement("tr");
    (vault.columns || []).forEach(function (c) {
      hr.appendChild(el("th", null, c));
    });
    thead.appendChild(hr);
    table.appendChild(thead);
    var tbody = document.createElement("tbody");
    (vault.rows || []).forEach(function (row) {
      var tr = document.createElement("tr");
      var nameTd = document.createElement("td");
      nameTd.appendChild(el("span", "mask", row.name_masked || "*********"));
      tr.appendChild(nameTd);
      tr.appendChild(el("td", null, row.service || "—"));
      tr.appendChild(el("td", null, row.quota_left || "—"));
      tr.appendChild(el("td", null, row.daily_limit || "—"));
      var stTd = document.createElement("td");
      var st = el("span", "p2-vault-status");
      st.appendChild(el("span", "dot dot-" + (row.status_tone || "green"), ""));
      st.appendChild(el("span", null, row.status || "—"));
      stTd.appendChild(st);
      tr.appendChild(stTd);
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    root.appendChild(table);
  }

  function renderP2(data) {
    applyBrand(data);
    renderNav(document.getElementById("sidebar-nav"), data.nav);
    renderP2SkillCards(document.getElementById("p2-skill-cards"), data.skill_ministries);
    var map = data.skill_module_map || {};
    var mapTitle = document.getElementById("p2-map-title");
    if (mapTitle) mapTitle.textContent = map.title || "技能 ↔ 執行模組 對應映射表";
    renderP2SkillMap(document.getElementById("p2-skill-map"), map);
    var mapFoot = document.getElementById("p2-map-footer");
    if (mapFoot) mapFoot.textContent = map.footer_link || "";
    var gov = data.resource_governance || {};
    renderP2ResourceTop(document.getElementById("p2-resource-top"), gov);
    var cloud = gov.cloud_breakdown || {};
    var cloudTitle = document.getElementById("p2-cloud-title");
    if (cloudTitle) cloudTitle.textContent = cloud.title || "雲端服務分項消耗";
    renderP2CloudBars(document.getElementById("p2-cloud-bars"), cloud);
    var vault = gov.key_vault || {};
    var vaultTitle = document.getElementById("p2-vault-title");
    if (vaultTitle) vaultTitle.textContent = vault.title || "金鑰庫";
    renderP2KeyVault(document.getElementById("p2-key-vault"), vault);
    var vaultFoot = document.getElementById("p2-vault-footer");
    if (vaultFoot) vaultFoot.textContent = vault.footer_link || "";
    var vaultNote = document.getElementById("p2-vault-note");
    if (vaultNote) vaultNote.textContent = vault.policy_note || "僅遮罩展示";
    renderOperatorFields(document.getElementById("operator-fields"), data.operator_fields);
    setDemoBanner(data, "P2");
  }

  function renderNavOnly(data) {
    applyBrand(data);
    renderNav(document.getElementById("sidebar-nav"), data.nav);
    setDemoBanner(data, "settings-stub");
  }

  global.CommandCenterShell = {
    loadJson: loadJson,
    loadPageData: loadPageData,
    resolveDataSource: resolveDataSource,
    maskSecrets: maskSecrets,
    renderNavOnly: renderNavOnly,
    renderP1: renderP1,
    renderP5: renderP5,
    renderP4: renderP4,
    renderP3: renderP3,
    renderP2: renderP2,
  };
})(window);
