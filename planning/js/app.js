/**
 * Bozdemir Makine — Üretim Planlama Uygulaması
 */

const DAY_MS = 86400000;
const DAY_W = 28;

const state = {
  data: loadState(),
  view: "dashboard",
  projectId: "all",
  stageId: "all",
  showPlanned: true,
  showActual: true,
  ganttMode: "project", // project | stage | cnc
  rangeStart: null,
  rangeEnd: null,
  editingTaskId: null,
  editingProjectId: null,
};

function person(id) {
  return MASTER.people.find((p) => p.id === id);
}

function machine(id) {
  return MASTER.machineTypes.find((m) => m.id === id);
}

function stage(id) {
  return MASTER.stages.find((s) => s.id === id);
}

function assemblyGroup(id) {
  return MASTER.assemblyGroups.find((g) => g.id === id);
}

function productGroup(id) {
  return MASTER.productGroups.find((g) => g.id === id);
}

function parseDate(s) {
  if (!s) return null;
  const [y, m, d] = s.split("-").map(Number);
  return new Date(y, m - 1, d);
}

function fmtDate(s) {
  if (!s) return "—";
  const d = parseDate(s);
  return d.toLocaleDateString("tr-TR", { day: "2-digit", month: "short", year: "numeric" });
}

function daysBetween(a, b) {
  if (!a || !b) return null;
  return Math.round((parseDate(b) - parseDate(a)) / DAY_MS);
}

function addDays(iso, n) {
  const d = parseDate(iso);
  d.setDate(d.getDate() + n);
  return toISO(d);
}

function toISO(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function todayISO() {
  return toISO(new Date());
}

/** Gecikme: gerçekleşen bitiş - planlanan bitiş (veya bugün - planlanan bitiş) */
function taskDelay(task) {
  const plannedEnd = parseDate(task.plannedEnd);
  if (!plannedEnd) return 0;

  if (task.actualEnd) {
    return daysBetween(task.plannedEnd, task.actualEnd);
  }
  if (task.status === "active" || (task.actualStart && !task.actualEnd)) {
    const today = todayISO();
    if (today > task.plannedEnd) return daysBetween(task.plannedEnd, today);
  }
  return 0;
}

function taskPlannedDays(task) {
  return daysBetween(task.plannedStart, task.plannedEnd) ?? 0;
}

function taskActualDays(task) {
  if (!task.actualStart) return null;
  const end = task.actualEnd || todayISO();
  return daysBetween(task.actualStart, end);
}

function allTasks(filterFn) {
  const out = [];
  for (const prj of state.data.projects) {
    if (state.projectId !== "all" && prj.id !== state.projectId) continue;
    for (const t of prj.tasks) {
      if (state.stageId !== "all") {
        if (t.stageId !== state.stageId && t.subStageId !== state.stageId) continue;
      }
      const item = { project: prj, task: t };
      if (!filterFn || filterFn(item)) out.push(item);
    }
  }
  return out;
}

function persist() {
  saveState(state.data);
}

/* ═══════════ Navigation ═══════════ */

function setView(name) {
  state.view = name;
  document.querySelectorAll(".tab").forEach((el) => {
    el.classList.toggle("active", el.dataset.view === name);
  });
  document.querySelectorAll(".view").forEach((el) => {
    el.classList.toggle("active", el.id === `view-${name}`);
  });
  render();
}

function render() {
  renderSidebar();
  if (state.view === "dashboard") renderDashboard();
  if (state.view === "gantt") renderGantt();
  if (state.view === "projects") renderProjects();
  if (state.view === "cnc") renderCnc();
}

function renderSidebar() {
  const projList = document.getElementById("filter-projects");
  const stageList = document.getElementById("filter-stages");

  projList.innerHTML = `
    <button class="filter-item ${state.projectId === "all" ? "active" : ""}" data-pid="all">Tüm Projeler</button>
    ${state.data.projects
      .map(
        (p) => `
      <button class="filter-item ${state.projectId === p.id ? "active" : ""}" data-pid="${p.id}">
        <span class="code" style="font-family:var(--mono);font-size:0.68rem;opacity:.7">${p.code}</span>
        ${p.name.split("—")[0].trim()}
      </button>`
      )
      .join("")}
  `;

  const stageOpts = [{ id: "all", name: "Tüm Süreçler", color: "#8494a7" }];
  for (const s of MASTER.stages) {
    stageOpts.push(s);
    if (s.subStages) {
      for (const sub of s.subStages) stageOpts.push({ ...sub, name: `↳ ${sub.name}` });
    }
  }

  stageList.innerHTML = stageOpts
    .map(
      (s) => `
    <button class="filter-item ${state.stageId === s.id ? "active" : ""}" data-sid="${s.id}">
      <span class="dot" style="background:${s.color || "#8494a7"}"></span>
      ${s.name}
    </button>`
    )
    .join("");

  projList.querySelectorAll("[data-pid]").forEach((btn) => {
    btn.onclick = () => {
      state.projectId = btn.dataset.pid;
      render();
    };
  });
  stageList.querySelectorAll("[data-sid]").forEach((btn) => {
    btn.onclick = () => {
      state.stageId = btn.dataset.sid;
      render();
    };
  });
}

/* ═══════════ Dashboard ═══════════ */

function renderDashboard() {
  const items = allTasks();
  const active = items.filter((i) => i.task.status === "active");
  const delayed = items.filter((i) => taskDelay(i.task) > 0);
  const done = items.filter((i) => i.task.status === "done");
  const planned = items.filter((i) => i.task.status === "planned");

  const totalDelayDays = delayed.reduce((sum, i) => sum + taskDelay(i.task), 0);
  const avgSlip = delayed.length
    ? Math.round(
        delayed.reduce((sum, i) => {
          const p = taskPlannedDays(i.task) || 1;
          const a = taskActualDays(i.task) ?? p;
          return sum + a / p;
        }, 0) / delayed.length
      * 10) / 10
    : 1;

  document.getElementById("kpi-active").textContent = active.length;
  document.getElementById("kpi-delayed").textContent = delayed.length;
  document.getElementById("kpi-delay-days").textContent = totalDelayDays;
  document.getElementById("kpi-slip").textContent = `${avgSlip}×`;

  document.getElementById("kpi-active-hint").textContent = `${planned.length} planlandı · ${done.length} tamam`;
  document.getElementById("kpi-delayed-hint").textContent = delayed.length
    ? "Planlanan bitiş aşıldı"
    : "Gecikme yok";
  document.getElementById("kpi-delay-days-hint").textContent = "Toplam gecikme günü";
  document.getElementById("kpi-slip-hint").textContent = "Ort. gerçekleşen / planlanan";

  // Aktif işler
  const activeBody = document.getElementById("table-active");
  if (!active.length) {
    activeBody.innerHTML = `<tr><td colspan="6" class="empty">Aktif iş yok</td></tr>`;
  } else {
    activeBody.innerHTML = active
      .map(({ project, task }) => {
        const delay = taskDelay(task);
        const who = person(task.assigneeId);
        return `<tr>
          <td><strong>${task.title}</strong><div style="font-size:0.7rem;color:var(--text-muted)">${project.code}</div></td>
          <td>${who ? who.name : "—"}<div style="font-size:0.68rem;color:var(--text-muted)">${who ? who.unit : ""}</div></td>
          <td>${fmtDate(task.actualStart)}</td>
          <td>${fmtDate(task.plannedEnd)}</td>
          <td class="delay-num ${delay > 0 ? "late" : ""}">${delay > 0 ? `+${delay}g` : "—"}</td>
          <td><span class="badge badge-info">Devam</span></td>
        </tr>`;
      })
      .join("");
  }

  // Gecikenler
  const delayBody = document.getElementById("table-delayed");
  const sortedDelay = [...delayed].sort((a, b) => taskDelay(b.task) - taskDelay(a.task));
  if (!sortedDelay.length) {
    delayBody.innerHTML = `<tr><td colspan="5" class="empty">Geciken iş yok</td></tr>`;
  } else {
    delayBody.innerHTML = sortedDelay
      .map(({ project, task }) => {
        const delay = taskDelay(task);
        const pDays = taskPlannedDays(task);
        const aDays = taskActualDays(task);
        const who = person(task.assigneeId);
        return `<tr>
          <td><strong>${task.title}</strong><div style="font-size:0.7rem;color:var(--text-muted)">${project.name}</div></td>
          <td>${who ? who.name : "—"}</td>
          <td><span class="badge badge-muted">${pDays}g plan</span></td>
          <td><span class="badge badge-warn">${aDays != null ? aDays + "g gerçek" : "—"}</span></td>
          <td class="delay-num late">+${delay} gün</td>
        </tr>`;
      })
      .join("");
  }

  // Birim özeti
  const unitMap = {};
  for (const { task } of items) {
    const who = person(task.assigneeId);
    if (!who) continue;
    if (!unitMap[who.unit]) unitMap[who.unit] = { active: 0, delayed: 0, done: 0 };
    if (task.status === "active") unitMap[who.unit].active++;
    if (task.status === "done") unitMap[who.unit].done++;
    if (taskDelay(task) > 0) unitMap[who.unit].delayed++;
  }

  document.getElementById("table-units").innerHTML = Object.entries(unitMap)
    .map(
      ([unit, u]) => `<tr>
      <td><strong>${unit}</strong></td>
      <td>${u.active}</td>
      <td>${u.done}</td>
      <td class="${u.delayed ? "delay-num late" : ""}">${u.delayed}</td>
    </tr>`
    )
    .join("") || `<tr><td colspan="4" class="empty">Veri yok</td></tr>`;
}

/* ═══════════ Gantt ═══════════ */

function computeRange(items) {
  let min = null;
  let max = null;
  for (const { task } of items) {
    for (const key of ["plannedStart", "plannedEnd", "actualStart", "actualEnd"]) {
      if (!task[key]) continue;
      const d = parseDate(task[key]);
      if (!min || d < min) min = d;
      if (!max || d > max) max = d;
    }
  }
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  if (!min) min = new Date(today);
  if (!max) max = new Date(today);
  if (today < min) min = new Date(today);
  if (today > max) max = new Date(today);

  min.setDate(min.getDate() - 3);
  max.setDate(max.getDate() + 14);
  return { start: min, end: max };
}

function buildDayColumns(start, end) {
  const days = [];
  const cur = new Date(start);
  while (cur <= end) {
    days.push(new Date(cur));
    cur.setDate(cur.getDate() + 1);
  }
  return days;
}

function groupDaysByMonth(days) {
  const months = [];
  let current = null;
  for (const d of days) {
    const key = `${d.getFullYear()}-${d.getMonth()}`;
    if (!current || current.key !== key) {
      current = {
        key,
        label: d.toLocaleDateString("tr-TR", { month: "long", year: "numeric" }),
        days: [],
      };
      months.push(current);
    }
    current.days.push(d);
  }
  return months;
}

function dayOffset(start, iso) {
  return daysBetween(toISO(start), iso);
}

function buildGanttRows() {
  const items = allTasks();
  const rows = [];

  if (state.ganttMode === "cnc") {
    const machining = items.filter((i) => i.task.subStageId === "machining");
    const byPg = {};
    for (const pg of MASTER.productGroups) byPg[pg.id] = [];
    byPg["_none"] = [];
    for (const item of machining) {
      const gid = item.task.groupId || "_none";
      if (!byPg[gid]) byPg[gid] = [];
      byPg[gid].push(item);
    }
    for (const pg of MASTER.productGroups) {
      const list = byPg[pg.id] || [];
      if (!list.length && state.projectId !== "all") continue;
      rows.push({ type: "header", label: `${pg.name}`, sub: pg.diameter });
      list
        .sort((a, b) => (a.task.plannedStart || "").localeCompare(b.task.plannedStart || ""))
        .forEach((item) => rows.push({ type: "task", ...item }));
    }
    return rows;
  }

  if (state.ganttMode === "stage") {
    for (const s of MASTER.stages) {
      const stageItems = items.filter((i) => i.task.stageId === s.id);
      if (!stageItems.length) continue;
      rows.push({ type: "header", label: s.name, color: s.color });

      if (s.mode === "assembly_groups") {
        for (const ag of MASTER.assemblyGroups) {
          const groupItems = stageItems.filter((i) => i.task.groupId === ag.id);
          if (!groupItems.length) continue;
          rows.push({ type: "header", label: `  ${ag.name}`, soft: true });
          groupItems.forEach((item) => rows.push({ type: "task", ...item }));
        }
        stageItems.filter((i) => !i.task.groupId).forEach((item) => rows.push({ type: "task", ...item }));
      } else if (s.subStages) {
        for (const sub of s.subStages) {
          const subItems = stageItems.filter((i) => i.task.subStageId === sub.id);
          if (!subItems.length) continue;
          rows.push({ type: "header", label: `  ${sub.name}`, soft: true, color: sub.color });
          if (sub.mode === "product_groups") {
            for (const pg of MASTER.productGroups) {
              const pgItems = subItems.filter((i) => i.task.groupId === pg.id);
              if (!pgItems.length) continue;
              rows.push({ type: "header", label: `    ${pg.name}`, soft: true });
              pgItems.forEach((item) => rows.push({ type: "task", ...item }));
            }
            subItems.filter((i) => !i.task.groupId).forEach((item) => rows.push({ type: "task", ...item }));
          } else {
            subItems.forEach((item) => rows.push({ type: "task", ...item }));
          }
        }
      } else {
        stageItems.forEach((item) => rows.push({ type: "task", ...item }));
      }
    }
    return rows;
  }

  // project mode
  const projects =
    state.projectId === "all"
      ? state.data.projects
      : state.data.projects.filter((p) => p.id === state.projectId);

  for (const prj of projects) {
    const prjItems = items.filter((i) => i.project.id === prj.id);
    if (!prjItems.length) continue;
    const mt = machine(prj.machineTypeId);
    rows.push({
      type: "header",
      label: `${prj.code} — ${prj.name}`,
      sub: mt ? mt.name : "",
    });

    const byStage = {};
    for (const item of prjItems) {
      const key = item.task.stageId;
      if (!byStage[key]) byStage[key] = [];
      byStage[key].push(item);
    }

    for (const s of MASTER.stages) {
      const list = byStage[s.id];
      if (!list) continue;
      rows.push({ type: "header", label: s.name, soft: true, color: s.color });

      if (s.mode === "assembly_groups") {
        list.sort((a, b) => {
          const oa = assemblyGroup(a.task.groupId)?.order ?? 99;
          const ob = assemblyGroup(b.task.groupId)?.order ?? 99;
          return oa - ob;
        });
      } else if (s.id === "production") {
        const order = { machining: 1, welding: 2, paint: 3 };
        list.sort((a, b) => (order[a.task.subStageId] || 9) - (order[b.task.subStageId] || 9));
      }

      list.forEach((item) => rows.push({ type: "task", ...item }));
    }
  }
  return rows;
}

function renderGantt() {
  const rows = buildGanttRows();
  const taskItems = rows.filter((r) => r.type === "task");
  const range = computeRange(taskItems);
  const days = buildDayColumns(range.start, range.end);
  const months = groupDaysByMonth(days);
  const today = todayISO();
  const todayIdx = days.findIndex((d) => toISO(d) === today);

  document.documentElement.style.setProperty("--day-w", `${DAY_W}px`);

  const headerEl = document.getElementById("gantt-header");
  headerEl.innerHTML = months
    .map(
      (m) => `
    <div class="gantt-month" style="width:${m.days.length * DAY_W}px">
      <div class="gantt-month-label">${m.label}</div>
      <div class="gantt-days">
        ${m.days
          .map((d) => {
            const iso = toISO(d);
            const wd = d.getDay();
            const weekend = wd === 0 || wd === 6;
            const isToday = iso === today;
            return `<div class="gantt-day ${weekend ? "weekend" : ""} ${isToday ? "today-col" : ""}">
              <span>${["Pz", "Pt", "Sa", "Ça", "Pe", "Cu", "Ct"][wd]}</span>
              <span>${d.getDate()}</span>
            </div>`;
          })
          .join("")}
      </div>
    </div>`
    )
    .join("");

  const labelsEl = document.getElementById("gantt-labels");
  const barsEl = document.getElementById("gantt-bars");

  labelsEl.innerHTML = rows
    .map((r) => {
      if (r.type === "header") {
        return `<div class="gantt-row-label group-header" style="${r.color ? `border-left:3px solid ${r.color}` : ""}">
          ${r.label}
          ${r.sub ? `<span class="code">${r.sub}</span>` : ""}
        </div>`;
      }
      const who = person(r.task.assigneeId);
      const delay = taskDelay(r.task);
      return `<div class="gantt-row-label" data-task="${r.task.id}" title="${r.task.title}">
        <span class="indent"></span>
        <span style="overflow:hidden;text-overflow:ellipsis">${r.task.title}</span>
        ${delay > 0 ? `<span class="badge badge-danger" style="margin-left:4px">+${delay}</span>` : ""}
        <span class="assignee">${who ? who.name.split(" ")[0] : ""}</span>
      </div>`;
    })
    .join("");

  const totalW = days.length * DAY_W;
  barsEl.style.width = `${totalW}px`;
  barsEl.innerHTML = rows
    .map((r) => {
      if (r.type === "header") {
        return `<div class="gantt-row-bars group-header" style="width:${totalW}px"></div>`;
      }
      return `<div class="gantt-row-bars" style="width:${totalW}px" data-task="${r.task.id}">
        ${renderBars(r.task, range.start, days.length)}
      </div>`;
    })
    .join("");

  if (todayIdx >= 0) {
    const line = document.createElement("div");
    line.className = "today-line";
    line.style.left = `${todayIdx * DAY_W + DAY_W / 2}px`;
    barsEl.appendChild(line);
  }

  // interactions
  barsEl.querySelectorAll(".bar").forEach((bar) => {
    bar.addEventListener("mouseenter", (e) => showTooltip(e, bar.dataset.taskId));
    bar.addEventListener("mousemove", moveTooltip);
    bar.addEventListener("mouseleave", hideTooltip);
    bar.addEventListener("click", () => openTaskModal(bar.dataset.taskId));
  });
  labelsEl.querySelectorAll("[data-task]").forEach((el) => {
    el.style.cursor = "pointer";
    el.addEventListener("click", () => openTaskModal(el.dataset.task));
  });

  document.getElementById("gantt-meta").textContent = `${taskItems.length} görev · ${fmtDate(toISO(range.start))} – ${fmtDate(toISO(range.end))}`;
}

function renderBars(task, rangeStart, dayCount) {
  let html = "";
  const st = stage(task.stageId);
  const color = st?.color || "#1d4ed8";

  if (state.showPlanned && task.plannedStart && task.plannedEnd) {
    const left = dayOffset(rangeStart, task.plannedStart) * DAY_W;
    const width = Math.max(DAY_W * 0.5, (daysBetween(task.plannedStart, task.plannedEnd) + 1) * DAY_W - 2);
    html += `<div class="bar planned" data-task-id="${task.id}" style="left:${left}px;width:${width}px" title="Planlanan"></div>`;
  }

  if (state.showActual && task.actualStart) {
    const end = task.actualEnd || todayISO();
    const left = dayOffset(rangeStart, task.actualStart) * DAY_W;
    const width = Math.max(DAY_W * 0.5, (daysBetween(task.actualStart, end) + 1) * DAY_W - 2);
    const delay = taskDelay(task);
    const cls = [
      "bar",
      "actual",
      task.status === "done" ? "done" : "",
      task.status === "active" ? "active" : "",
      delay > 0 ? "late" : "",
    ]
      .filter(Boolean)
      .join(" ");
    html += `<div class="${cls}" data-task-id="${task.id}" style="left:${left}px;width:${width}px;${task.status === "done" || delay > 0 ? "" : `background:${color}`}"></div>`;
  }

  return html;
}

/* ═══════════ Tooltip ═══════════ */

function findTask(taskId) {
  for (const prj of state.data.projects) {
    const t = prj.tasks.find((x) => x.id === taskId);
    if (t) return { project: prj, task: t };
  }
  return null;
}

function showTooltip(e, taskId) {
  const found = findTask(taskId);
  if (!found) return;
  const { project, task } = found;
  const who = person(task.assigneeId);
  const delay = taskDelay(task);
  const tip = document.getElementById("tooltip");
  tip.innerHTML = `
    <strong>${task.title}</strong>
    ${project.code} · ${project.name}<br>
    Sorumlu: ${who ? who.name : "—"} (${who ? who.unit : "—"})<br>
    Plan: ${fmtDate(task.plannedStart)} → ${fmtDate(task.plannedEnd)} (${taskPlannedDays(task)}g)<br>
    Gerçek: ${fmtDate(task.actualStart)} → ${fmtDate(task.actualEnd)} ${taskActualDays(task) != null ? `(${taskActualDays(task)}g)` : ""}
    ${delay > 0 ? `<br><span style="color:#fca5a5">Gecikme: +${delay} gün</span>` : ""}
  `;
  tip.classList.add("visible");
  moveTooltip(e);
}

function moveTooltip(e) {
  const tip = document.getElementById("tooltip");
  tip.style.left = `${e.clientX + 12}px`;
  tip.style.top = `${e.clientY + 12}px`;
}

function hideTooltip() {
  document.getElementById("tooltip").classList.remove("visible");
}

/* ═══════════ Projects ═══════════ */

function renderProjects() {
  const el = document.getElementById("project-list");
  el.innerHTML = state.data.projects
    .map((prj) => {
      const total = prj.tasks.length;
      const done = prj.tasks.filter((t) => t.status === "done").length;
      const delayed = prj.tasks.filter((t) => taskDelay(t) > 0).length;
      const pct = total ? Math.round((done / total) * 100) : 0;
      const mt = machine(prj.machineTypeId);
      return `<div class="project-card" data-id="${prj.id}">
        <div>
          <h3>${prj.name}</h3>
          <div class="meta">
            <span style="font-family:var(--mono)">${prj.code}</span>
            <span>${prj.customer}</span>
            <span>${mt ? mt.name : ""}</span>
            <span>${done}/${total} görev</span>
            ${delayed ? `<span class="badge badge-danger">${delayed} gecikme</span>` : `<span class="badge badge-ok">Zamanında</span>`}
          </div>
        </div>
        <div style="text-align:right">
          <div style="font-weight:700;font-size:1.1rem;margin-bottom:0.35rem">${pct}%</div>
          <div class="progress-bar"><span style="width:${pct}%"></span></div>
        </div>
      </div>`;
    })
    .join("");

  el.querySelectorAll(".project-card").forEach((card) => {
    card.onclick = () => {
      state.projectId = card.dataset.id;
      setView("gantt");
    };
  });
}

/* ═══════════ CNC Board ═══════════ */

function renderCnc() {
  const items = allTasks((i) => i.task.subStageId === "machining");
  const el = document.getElementById("cnc-board");

  el.innerHTML = MASTER.productGroups
    .map((pg) => {
      const list = items
        .filter((i) => i.task.groupId === pg.id)
        .sort((a, b) => (a.task.plannedStart || "").localeCompare(b.task.plannedStart || ""));
      return `<div class="cnc-col">
        <div class="cnc-col-head">
          <h3>${pg.name}</h3>
          <div class="sub">${pg.diameter !== "—" ? pg.diameter + " · " : ""}${pg.family} · ${list.length} iş</div>
        </div>
        ${
          list.length
            ? list
                .map(({ project, task }) => {
                  const who = person(task.assigneeId);
                  const delay = taskDelay(task);
                  return `<div class="cnc-card" data-task="${task.id}">
                    <div class="title">${task.title}</div>
                    <div class="meta">${project.code} · ${who ? who.name : "—"}</div>
                    <div class="meta" style="margin-top:4px">
                      Plan ${fmtDate(task.plannedStart)} → ${fmtDate(task.plannedEnd)}
                      ${delay > 0 ? ` · <span class="delay-num late">+${delay}g</span>` : ""}
                    </div>
                    <div style="margin-top:6px"><span class="badge badge-${task.status === "done" ? "ok" : task.status === "active" ? "info" : "muted"}">${
                      task.status === "done" ? "Bitti" : task.status === "active" ? "Tezgâhta" : "Sırada"
                    }</span></div>
                  </div>`;
                })
                .join("")
            : `<div class="empty" style="padding:1rem;font-size:0.78rem">İş yok</div>`
        }
      </div>`;
    })
    .join("");

  el.querySelectorAll("[data-task]").forEach((card) => {
    card.style.cursor = "pointer";
    card.onclick = () => openTaskModal(card.dataset.task);
  });
}

/* ═══════════ Task Modal ═══════════ */

function openTaskModal(taskId, projectId) {
  const found = taskId ? findTask(taskId) : null;
  state.editingTaskId = taskId || null;
  state.editingProjectId = found?.project.id || projectId || state.projectId;

  const modal = document.getElementById("modal-task");
  const title = document.getElementById("modal-task-title");
  title.textContent = found ? "Görevi Düzenle" : "Yeni Görev";

  const t = found?.task || {
    title: "",
    stageId: "design",
    subStageId: null,
    groupId: null,
    assigneeId: MASTER.people[0].id,
    plannedStart: todayISO(),
    plannedEnd: addDays(todayISO(), 3),
    actualStart: "",
    actualEnd: "",
    status: "planned",
  };

  fillSelect("f-project", state.data.projects.map((p) => ({ value: p.id, label: `${p.code} — ${p.name}` })), state.editingProjectId === "all" ? state.data.projects[0]?.id : state.editingProjectId);
  fillSelect(
    "f-stage",
    MASTER.stages.map((s) => ({ value: s.id, label: s.name })),
    t.stageId
  );
  fillSelect(
    "f-assignee",
    MASTER.people.map((p) => ({ value: p.id, label: `${p.name} (${p.unit})` })),
    t.assigneeId
  );
  fillSelect(
    "f-status",
    [
      { value: "planned", label: "Planlandı" },
      { value: "active", label: "Devam ediyor" },
      { value: "done", label: "Tamamlandı" },
    ],
    t.status
  );

  document.getElementById("f-title").value = t.title;
  document.getElementById("f-planned-start").value = t.plannedStart || "";
  document.getElementById("f-planned-end").value = t.plannedEnd || "";
  document.getElementById("f-actual-start").value = t.actualStart || "";
  document.getElementById("f-actual-end").value = t.actualEnd || "";

  updateGroupFields(t.stageId, t.subStageId, t.groupId);
  document.getElementById("modal-backdrop").classList.add("open");
}

function updateGroupFields(stageId, subStageId, groupId) {
  const s = stage(stageId);
  const subWrap = document.getElementById("wrap-substage");
  const groupWrap = document.getElementById("wrap-group");
  const groupLabel = document.getElementById("label-group");

  if (s?.subStages) {
    subWrap.style.display = "";
    fillSelect(
      "f-substage",
      s.subStages.map((x) => ({ value: x.id, label: x.name })),
      subStageId || s.subStages[0].id
    );
    subStageId = document.getElementById("f-substage").value;
  } else {
    subWrap.style.display = "none";
    subStageId = null;
  }

  const effective = subStageId ? s?.subStages?.find((x) => x.id === subStageId) : s;
  const mode = effective?.mode;

  if (mode === "assembly_groups") {
    groupWrap.style.display = "";
    groupLabel.textContent = "Montaj / Tasarım Grubu";
    fillSelect(
      "f-group",
      [{ value: "", label: "— Seçin —" }, ...MASTER.assemblyGroups.map((g) => ({ value: g.id, label: g.name }))],
      groupId || ""
    );
  } else if (mode === "product_groups") {
    groupWrap.style.display = "";
    groupLabel.textContent = "Ürün Grubu (CNC)";
    fillSelect(
      "f-group",
      [{ value: "", label: "— Seçin —" }, ...MASTER.productGroups.map((g) => ({ value: g.id, label: g.name }))],
      groupId || ""
    );
  } else {
    groupWrap.style.display = "none";
  }
}

function fillSelect(id, options, selected) {
  const el = document.getElementById(id);
  el.innerHTML = options.map((o) => `<option value="${o.value}" ${o.value === selected ? "selected" : ""}>${o.label}</option>`).join("");
}

function closeModal() {
  document.getElementById("modal-backdrop").classList.remove("open");
  state.editingTaskId = null;
}

function saveTask() {
  const projectId = document.getElementById("f-project").value;
  const prj = state.data.projects.find((p) => p.id === projectId);
  if (!prj) return;

  const stageId = document.getElementById("f-stage").value;
  const s = stage(stageId);
  const subStageId = s?.subStages ? document.getElementById("f-substage").value : null;
  const groupVal = document.getElementById("f-group").value || null;

  const payload = {
    title: document.getElementById("f-title").value.trim() || "Adsız görev",
    stageId,
    subStageId,
    groupId: groupVal,
    assigneeId: document.getElementById("f-assignee").value,
    plannedStart: document.getElementById("f-planned-start").value || null,
    plannedEnd: document.getElementById("f-planned-end").value || null,
    actualStart: document.getElementById("f-actual-start").value || null,
    actualEnd: document.getElementById("f-actual-end").value || null,
    status: document.getElementById("f-status").value,
  };

  if (state.editingTaskId) {
    // move between projects if needed
    let task = null;
    for (const p of state.data.projects) {
      const idx = p.tasks.findIndex((t) => t.id === state.editingTaskId);
      if (idx >= 0) {
        task = p.tasks[idx];
        if (p.id !== projectId) {
          p.tasks.splice(idx, 1);
          prj.tasks.push(task);
        }
        break;
      }
    }
    if (task) Object.assign(task, payload);
  } else {
    prj.tasks.push({
      id: "t" + Date.now(),
      ...payload,
    });
  }

  persist();
  closeModal();
  render();
}

function deleteTask() {
  if (!state.editingTaskId) return;
  if (!confirm("Bu görevi silmek istiyor musunuz?")) return;
  for (const p of state.data.projects) {
    const idx = p.tasks.findIndex((t) => t.id === state.editingTaskId);
    if (idx >= 0) {
      p.tasks.splice(idx, 1);
      break;
    }
  }
  persist();
  closeModal();
  render();
}

/* ═══════════ New Project ═══════════ */

function openProjectModal() {
  document.getElementById("f-prj-name").value = "";
  document.getElementById("f-prj-customer").value = "";
  document.getElementById("f-prj-code").value = `PRJ-2026-${String(state.data.projects.length + 20).padStart(3, "0")}`;
  fillSelect(
    "f-prj-machine",
    MASTER.machineTypes.map((m) => ({ value: m.id, label: `${m.code} — ${m.name}` })),
    MASTER.machineTypes[0].id
  );
  document.getElementById("f-prj-template").checked = true;
  document.getElementById("modal-project-backdrop").classList.add("open");
}

function closeProjectModal() {
  document.getElementById("modal-project-backdrop").classList.remove("open");
}

function createProjectWithTemplate(prj) {
  const start = todayISO();
  let cursor = start;
  const tasks = [];
  let n = 0;

  const push = (partial) => {
    const ps = cursor;
    const pe = addDays(ps, partial.days);
    tasks.push({
      id: `t${Date.now()}_${n++}`,
      stageId: partial.stageId,
      subStageId: partial.subStageId || null,
      groupId: partial.groupId || null,
      title: partial.title,
      assigneeId: partial.assigneeId,
      plannedStart: ps,
      plannedEnd: pe,
      actualStart: null,
      actualEnd: null,
      status: "planned",
    });
    cursor = addDays(pe, 1);
  };

  push({ stageId: "sales", title: "Teklif & Sipariş Onayı", days: 5, assigneeId: "p1" });

  for (const ag of MASTER.assemblyGroups.slice(0, 6)) {
    push({
      stageId: "design",
      groupId: ag.id,
      title: `${ag.name} Tasarım`,
      days: 4,
      assigneeId: ag.id === "ag6" || ag.id === "ag7" ? "p10" : "p2",
    });
  }

  push({ stageId: "purchasing", title: "Malzeme Siparişi", days: 10, assigneeId: "p4" });

  push({ stageId: "production", subStageId: "machining", groupId: "pg1", title: "Ø18 ürün grubu CNC", days: 4, assigneeId: "p5" });
  push({ stageId: "production", subStageId: "machining", groupId: "pg4", title: "Flanş / Kapak CNC", days: 3, assigneeId: "p5" });
  push({ stageId: "production", subStageId: "welding", title: "Kaynak", days: 5, assigneeId: "p6" });
  push({ stageId: "production", subStageId: "paint", title: "Boyahane", days: 3, assigneeId: "p7" });
  push({ stageId: "qc", title: "Kalite Kontrol", days: 3, assigneeId: "p8" });

  for (const ag of MASTER.assemblyGroups.slice(0, 6)) {
    push({
      stageId: "assembly",
      groupId: ag.id,
      title: `${ag.name} Montaj`,
      days: 3,
      assigneeId: ag.id === "ag7" ? "p10" : "p9",
    });
  }

  prj.tasks = tasks;
}

function saveProject() {
  const prj = {
    id: "prj" + Date.now(),
    code: document.getElementById("f-prj-code").value.trim(),
    name: document.getElementById("f-prj-name").value.trim() || "Yeni Proje",
    machineTypeId: document.getElementById("f-prj-machine").value,
    customer: document.getElementById("f-prj-customer").value.trim() || "—",
    status: "active",
    createdAt: todayISO(),
    tasks: [],
  };

  if (document.getElementById("f-prj-template").checked) {
    createProjectWithTemplate(prj);
  }

  state.data.projects.push(prj);
  persist();
  closeProjectModal();
  state.projectId = prj.id;
  setView("gantt");
}

function resetSampleData() {
  if (!confirm("Örnek verilere dönülsün mü? Kaydedilmiş değişiklikler silinir.")) return;
  localStorage.removeItem(STORAGE_KEY);
  state.data = loadState();
  state.projectId = "all";
  render();
}

function exportJson() {
  const blob = new Blob([JSON.stringify(state.data, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `planlama_${todayISO()}.json`;
  a.click();
}

/* ═══════════ Init ═══════════ */

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => setView(tab.dataset.view));
  });

  document.getElementById("btn-new-task").onclick = () => openTaskModal(null);
  document.getElementById("btn-new-project").onclick = openProjectModal;
  document.getElementById("btn-export").onclick = exportJson;
  document.getElementById("btn-reset").onclick = resetSampleData;

  document.getElementById("btn-save-task").onclick = saveTask;
  document.getElementById("btn-delete-task").onclick = deleteTask;
  document.getElementById("btn-close-task").onclick = closeModal;
  document.getElementById("btn-cancel-task").onclick = closeModal;

  document.getElementById("btn-save-project").onclick = saveProject;
  document.getElementById("btn-close-project").onclick = closeProjectModal;
  document.getElementById("btn-cancel-project").onclick = closeProjectModal;

  document.getElementById("f-stage").addEventListener("change", (e) => {
    updateGroupFields(e.target.value, null, null);
  });
  document.getElementById("f-substage").addEventListener("change", () => {
    updateGroupFields(document.getElementById("f-stage").value, document.getElementById("f-substage").value, null);
  });

  document.querySelectorAll("[data-toggle]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const key = btn.dataset.toggle;
      if (key === "planned") {
        state.showPlanned = !state.showPlanned;
        btn.classList.toggle("active", state.showPlanned);
      }
      if (key === "actual") {
        state.showActual = !state.showActual;
        btn.classList.toggle("active", state.showActual);
      }
      if (state.view === "gantt") renderGantt();
    });
  });

  document.querySelectorAll("[data-gantt-mode]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.ganttMode = btn.dataset.ganttMode;
      document.querySelectorAll("[data-gantt-mode]").forEach((b) => b.classList.toggle("active", b === btn));
      renderGantt();
    });
  });

  document.getElementById("modal-backdrop").addEventListener("click", (e) => {
    if (e.target.id === "modal-backdrop") closeModal();
  });
  document.getElementById("modal-project-backdrop").addEventListener("click", (e) => {
    if (e.target.id === "modal-project-backdrop") closeProjectModal();
  });

  render();
});
