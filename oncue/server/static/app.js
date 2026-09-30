"use strict";
(() => {
  const $ = (selector) => document.querySelector(selector);
  const state = {scenes: [], scene: null, result: null, selected: 0, revision: 0,
    current: null, busy: false, controller: null, status: null, archives: [], draft: ""};
  const ARCHIVES_KEY = "oncue.takes.v02", DRAFT_KEY = "oncue.draft.v02";
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const playback = {timer: null, revision: 0, items: [], index: 0, running: false};
  let storageNotice = "";

  function node(tag, className, text) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined) el.textContent = text;
    return el;
  }
  function say(selector, text, error = false) {
    $(selector).textContent = text;
    $(selector).classList.toggle("error", error);
  }
  async function api(path, data, signal) {
    const response = await fetch(path, data === undefined ? {signal} :
      {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(data), signal});
    const value = await response.json();
    if (!response.ok) {
      if (response.status === 401 && path !== "/api/login") showLogin();
      throw new Error(value.error?.message || "服务暂时不可用，请重试。");
    }
    return value;
  }
  function readLocal(key, fallback) {
    try {return JSON.parse(localStorage.getItem(key) || "null") ?? fallback;}
    catch {storageNotice = "浏览器存储不可用；仍可试映和导出台词。"; return fallback;}
  }
  function writeLocal(key, value) {
    try {localStorage.setItem(key, JSON.stringify(value)); return true;}
    catch {say("#archive-status", "浏览器未能保存，请使用导出保留内容。", true); return false;}
  }
  function validArchive(x) {
    return x && typeof x.id === "string" && typeof x.trial === "string" && typeof x.created === "string" &&
      Array.isArray(x.messages) && x.messages.length > 0 && typeof x.scene_name === "string" &&
      x.result && typeof x.result.summary === "string" && Array.isArray(x.result.routes) &&
      x.result.routes.length === 3 && x.result.routes.every(r => r && typeof r.title === "string" &&
        typeof r.subtitle === "string" && typeof r.draft === "string" && Array.isArray(r.replies) &&
        r.replies.every(t => typeof t === "string") && Array.isArray(r.evidence));
  }
  function invalidate() {
    cancelPlayback();
    state.revision += 1;
    if (state.controller) state.controller.abort();
    state.controller = null;
    setBusy(false);
    state.result = null; state.current = null;
    $("#result-panel").hidden = true;
    $("#take-counter").textContent = "待试映";
    say("#stage-status", "现场或台词已改变，重新试映看看。");
  }
  function setBusy(busy) {
    state.busy = busy;
    $("#rehearse").disabled = busy;
    $("#stop").hidden = !busy;
    $("#rehearse-form").setAttribute("aria-busy", String(busy));
    $("#rehearse").textContent = busy ? "正在试映…" : "▶ 试映下一幕";
  }
  function renderSource() {
    const box = $("#messages"); box.replaceChildren();
    state.scene.messages.forEach((m, i) => {
      const message = node("div", "message"); message.id = "source-" + (i + 1);
      const meta = node("div", "message-meta");
      meta.append(node("span", "message-id", "#" + (i + 1)), node("span", "", m.sender));
      message.append(meta, node("div", "message-text", m.text)); box.append(message);
    });
    $("#scene-caption").textContent = state.scene.caption || "你提供的现场片段。";
    $("#source-label").textContent = state.scene.custom ? "自定义片段" : "虚构样例";
    $("#source-name").value = state.scene.name;
    $("#source-text").value = state.scene.messages.map(m => m.sender + "：" + m.text).join("\n");
    const presets = $("#presets"); presets.replaceChildren();
    (state.scene.trials || []).forEach((trial, i) => {
      const button = node("button", "", ["直接接一句", "先对齐条件", "换个玩法"][i] || "换一句");
      button.type = "button"; button.addEventListener("click", () => {$("#trial").value = trial; $("#model-consent").checked = false; invalidate();});
      presets.append(button);
    });
  }
  function changeScene(id) {
    const scene = state.scenes.find(s => s.id === id);
    if (!scene) return;
    invalidate(); $("#model-consent").checked = false; state.scene = structuredClone(scene); renderSource();
    $("#trial").value = scene.trials[0];
    say("#source-status", ""); say("#stage-status", "虚构现场已就位，试一句台词。");
  }
  function importSource() {
    const raw = $("#source-text").value.trim(), name = $("#source-name").value.trim();
    if (!raw || !name) {say("#source-status", "先填写现场名称和消息片段。", true); return;}
    const lines = raw.split(/\r?\n/).map(x => x.trim()).filter(Boolean);
    if (lines.length > 20) {say("#source-status", "最多使用20条消息，请精简后重试。", true); return;}
    const messages = [];
    for (let i = 0; i < lines.length; i += 1) {
      const match = lines[i].match(/^([^：:]{1,40})[：:]\s*(.+)$/);
      if (!match || !match[1].trim() || !match[2].trim() || match[2].length > 500) {
        say("#source-status", "第" + (i + 1) + "行请写成「名字：消息」，消息最多500字。", true); return;
      }
      messages.push({id: i + 1, sender: match[1].trim(), text: match[2].trim()});
    }
    invalidate(); $("#model-consent").checked = false; state.scene = {id: "custom", name, messages, custom: true, trials: []};
    let option = $("#scene-select option[value=custom]");
    if (!option) {option = node("option", "", name); option.value = "custom"; $("#scene-select").append(option);}
    option.textContent = name; $("#scene-select").value = "custom";
    renderSource(); $("#source-editor").open = false; $("#trial").value = "";
    say("#stage-status", "自定义现场已就位。本地模式示范通用接法，模型模式会根据片段创作。");
    $("#trial").focus();
  }
  function highlightSource(id) {
    const source = $("#source-" + id);
    if (!source) return;
    document.querySelectorAll(".message.highlight").forEach(el => el.classList.remove("highlight"));
    source.classList.add("highlight");
    source.scrollIntoView({behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "nearest"});
  }
  function cancelPlayback() {
    window.clearTimeout(playback.timer);
    playback.timer = null; playback.revision += 1; playback.running = false;
    if ($("#playback-status")) updatePlaybackControls();
  }
  function updatePlaybackControls() {
    const complete = playback.index === playback.items.length;
    $("#play-scene").textContent = complete ? "重新播放" : playback.running ? "暂停" :
      playback.index ? "继续播放" : "播放下一幕";
    $("#next-cue").disabled = complete;
    $("#show-scene").disabled = complete;
    $("#playback-status").textContent = complete ? "本幕结束 · 已展开 " + playback.index + " 句假设接话" :
      (playback.running ? "播放中" : "已暂停") + " · 假设接话 " + playback.index + "/" + playback.items.length;
  }
  function revealCue(animate = true) {
    const reply = playback.items[playback.index];
    if (!reply) return;
    reply.hidden = false;
    reply.classList.toggle("scene-enter", animate && !reducedMotion.matches);
    playback.index += 1;
  }
  function showScene() {
    if (!state.result) return;
    cancelPlayback();
    while (playback.index < playback.items.length) revealCue(false);
    updatePlaybackControls();
  }
  function startPlayback() {
    if (reducedMotion.matches) {showScene(); return;}
    if (document.hidden) {updatePlaybackControls(); return;}
    const revision = playback.revision;
    playback.running = true;
    updatePlaybackControls();
    const step = () => {
      if (!state.result || revision !== playback.revision || !playback.running) return;
      revealCue();
      if (playback.index === playback.items.length) cancelPlayback();
      else playback.timer = window.setTimeout(step, 900);
      updatePlaybackControls();
    };
    playback.timer = window.setTimeout(step, 650);
  }
  function playScene() {
    if (!state.result) return;
    if (playback.running) {cancelPlayback(); updatePlaybackControls(); return;}
    if (playback.index === playback.items.length) {
      playback.items.forEach(reply => {reply.hidden = true; reply.classList.remove("scene-enter");});
      playback.index = 0;
    }
    startPlayback();
  }
  function nextCue() {
    if (!state.result) return;
    cancelPlayback(); revealCue(); updatePlaybackControls();
  }
  function renderPlayback(route) {
    cancelPlayback(); playback.index = 0;
    $("#scene-line").textContent = state.current.trial;
    const replies = $("#replies"); replies.replaceChildren();
    playback.items = route.replies.map((text, i) => {
      const reply = node("div", "reply"); reply.hidden = true;
      reply.append(node("span", "", "假设接话 " + (i + 1)), node("p", "", text));
      replies.append(reply); return reply;
    });
    if (reducedMotion.matches || document.hidden || !playback.items.length) showScene();
    else startPlayback();
  }
  function selectRoute(index) {
    state.selected = index;
    const route = state.result.routes[index];
    document.querySelectorAll(".route").forEach((el, i) => el.setAttribute("aria-pressed", String(i === index)));
    $("#route-subtitle").textContent = route.subtitle;
    renderPlayback(route);
    const refs = $("#evidence-links"); refs.replaceChildren();
    route.evidence.forEach(ref => {
      const button = node("button", "", "#" + ref.message_id);
      button.title = ref.quote; button.setAttribute("aria-label", "回看消息" + ref.message_id + "：" + ref.quote);
      button.addEventListener("click", () => highlightSource(ref.message_id)); refs.append(button);
    });
    const notes = $("#route-warnings"); notes.replaceChildren();
    const warnings = Array.isArray(route.warnings) ? route.warnings : [];
    notes.hidden = !warnings.length;
    if (warnings.length) notes.append(node("span", "", "这一幕还有待确认"));
    warnings.forEach(text => notes.append(node("p", "", text)));
    $("#suggested-text").textContent = route.draft;
  }
  function renderResult() {
    $("#result-panel").hidden = false;
    $("#scene-summary").textContent = state.result.summary;
    $("#result-label").textContent = state.result.label;
    $("#take-counter").textContent = "TAKE / " + (state.archives.length + 1);
    const routes = $("#routes"); routes.replaceChildren();
    state.result.routes.forEach((route, i) => {
      const button = node("button", "route");
      button.setAttribute("aria-pressed", String(i === state.selected));
      button.append(node("span", "route-title", route.title), node("span", "route-subtitle", route.subtitle));
      button.addEventListener("click", () => selectRoute(i)); routes.append(button);
    });
    selectRoute(state.selected);
  }
  function updateMode() {
    const real = $("#generation-mode").value === "minimax";
    $("#consent-row").hidden = !real;
    $("#model-note").textContent = real ? (state.status.model_ready ? "使用你配置的模型；点击后开始一次调用。" :
      "模型尚未配置，可在服务器设置API Key后使用。") : "规则演示；下一幕由本地预设生成。";
    $("#mode-badge").textContent = real ? "MiniMax 试映" : "本地演示";
  }
  async function rehearse(event) {
    event.preventDefault();
    const trial = $("#trial").value.trim();
    if (!trial) {say("#stage-status", "先写一句想接的话。", true); $("#trial").focus(); return;}
    const mode = $("#generation-mode").value;
    if (mode === "minimax" && !$("#model-consent").checked) {
      say("#stage-status", "先确认本次使用这些消息与台词进行模型试映。", true); return;
    }
    invalidate(); const revision = state.revision;
    const payload = {scene_name: state.scene.name, messages: structuredClone(state.scene.messages),
      trial, mode, consent: $("#model-consent").checked};
    const controller = new AbortController(); state.controller = controller; setBusy(true);
    const timer = window.setTimeout(() => controller.abort(), 100_000);
    say("#stage-status", mode === "demo" ? "正在展开本地样例…" : "模型正在写三条路线，可继续改台词。");
    try {
      const {result} = await api("/api/rehearse", payload, controller.signal);
      if (revision !== state.revision) return;
      state.result = result; state.selected = 0; state.current = payload; renderResult();
      say("#stage-status", "下一幕已展开。换条路线，或者重写台词再试一次。");
    } catch (error) {
      if (revision !== state.revision) return;
      say("#stage-status", error.name === "AbortError" ? "等待已结束。模型调用若已开始，仍可能完成并计费。" : error.message, true);
    } finally {
      window.clearTimeout(timer);
      if (revision === state.revision) {state.controller = null; setBusy(false);}
    }
  }
  function saveTake() {
    if (!state.result || !state.current) return;
    const take = {...structuredClone(state.current), result: structuredClone(state.result),
      id: typeof crypto.randomUUID === "function" ? crypto.randomUUID() : Date.now() + "-" + Math.random().toString(36).slice(2),
      created: new Date().toISOString(), selected: state.selected, draft: $("#draft").value};
    const next = [take, ...state.archives].slice(0, 12);
    if (!writeLocal(ARCHIVES_KEY, next)) return;
    state.archives = next; renderArchives();
    say("#archive-status", "存档点已保存到当前浏览器，最多保留12个。");
  }
  function restoreTake(take) {
    invalidate(); state.scene = {id: "custom", name: take.scene_name, messages: structuredClone(take.messages),
      custom: true, trials: [], caption: "从剧情存档恢复的现场。"};
    let option = $("#scene-select option[value=custom]");
    if (!option) {option = node("option"); option.value = "custom"; $("#scene-select").append(option);}
    option.textContent = take.scene_name; $("#scene-select").value = "custom"; renderSource();
    $("#trial").value = take.trial; $("#generation-mode").value = take.mode; $("#model-consent").checked = false;
    state.result = structuredClone(take.result); state.selected = Number.isInteger(take.selected) ? take.selected : 0;
    if (state.selected < 0 || state.selected > 2) state.selected = 0;
    state.current = {scene_name: take.scene_name, messages: structuredClone(take.messages), trial: take.trial,
      mode: take.mode, consent: false};
    updateMode(); renderResult();
    if (take.draft) {$("#draft").value = take.draft; $("#draft-panel").hidden = false;}
    say("#stage-status", "已恢复存档。可以换一句台词，继续试映。");
    $("#stage-heading").scrollIntoView({block: "start"});
  }
  function download(text, name, type = "text/plain;charset=utf-8") {
    const url = URL.createObjectURL(new Blob([text], {type}));
    const link = node("a"); link.href = url; link.download = name;
    document.body.append(link); link.click(); link.remove(); window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function takeMarkdown(take) {
    const lines = ["# OnCue · 群聊试映室", "", "现场：" + take.scene_name, "", take.result.label,
      "", "所有下一幕均为假设；没有发送群消息。", "", "## 原始消息", ""];
    take.messages.forEach(m => lines.push("> #" + m.id + " " + m.sender + "：" + m.text.replace(/\n/g, "\n> ")));
    lines.push("", "## 试写台词", "", take.trial, "", "## 三条假设路线");
    take.result.routes.forEach(r => {
      lines.push("", "### " + r.title + " · " + r.subtitle, "");
      r.replies.forEach(t => lines.push("- 假设回应：" + t));
      lines.push("", "建议台词：" + r.draft, "", "来源：" + r.evidence.map(e => "#" + e.message_id + "「" + e.quote + "」").join("；"));
    });
    if (take.draft) lines.push("", "## 我的草稿", "", take.draft);
    return lines.join("\n") + "\n";
  }
  function renderArchives() {
    const box = $("#archive-list"); box.replaceChildren(); $("#compare-panel").hidden = true;
    $("#compare").disabled = state.archives.length < 2;
    if (!state.archives.length) {box.append(node("p", "empty-archive", "还没有存档。试映之后，保存一个你想继续玩的现场。")); return;}
    state.archives.forEach(take => {
      const card = node("article", "archive-card");
      const meta = node("div", "archive-meta");
      meta.append(node("span", "", new Date(take.created).toLocaleString("zh-CN", {month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"})),
        node("span", "", take.mode === "demo" ? "本地演示" : "模型试映"));
      card.append(meta, node("h3", "", take.scene_name), node("p", "", take.trial));
      const actions = node("div", "archive-actions");
      [["继续这一幕", () => restoreTake(take)], ["导出剧本", () => download(takeMarkdown(take), "OnCue-剧本.md")],
        ["删除", () => {const next = state.archives.filter(x => x.id !== take.id); if (writeLocal(ARCHIVES_KEY, next)) {
          state.archives = next; renderArchives(); say("#archive-status", "这个存档已从当前浏览器删除。");}}]].forEach(([label, action]) => {
        const button = node("button", "", label); button.addEventListener("click", action); actions.append(button);
      });
      card.append(actions); box.append(card);
    });
  }
  function compareTakes() {
    if (state.archives.length < 2) return;
    const box = $("#compare-panel"); box.replaceChildren(); box.hidden = false;
    [state.archives[1], state.archives[0]].forEach((take, i) => {
      const pane = node("article", "compare-take");
      pane.append(node("h3", "", i === 0 ? "上一版台词" : "最新一版台词"), node("p", "hint", take.scene_name), node("p", "", take.trial));
      take.result.routes.forEach(r => {
        const route = node("div", "compare-route"); route.append(node("h3", "", r.title), node("p", "", r.draft)); pane.append(route);
      });
      box.append(pane);
    });
  }
  function showLogin() {
    cancelPlayback();
    $("#studio").hidden = true; $("#login-panel").hidden = false;
    $("#logout").hidden = true; $("#mode-badge").textContent = "私人试映室";
  }
  async function boot() {
    try {
      state.status = await api("/api/status");
      if (!state.status.authenticated) {showLogin(); return;}
      const {scenes} = await api("/api/scenes"); state.scenes = scenes;
      const select = $("#scene-select"); select.replaceChildren();
      scenes.forEach(s => {const option = node("option", "", s.name); option.value = s.id; select.append(option);});
      $("#login-panel").hidden = true; $("#studio").hidden = false;
      $("#logout").hidden = !state.status.requires_login;
      changeScene(scenes[0].id); updateMode();
      const stored = readLocal(ARCHIVES_KEY, []);
      state.archives = Array.isArray(stored) ? stored.filter(validArchive).slice(0, 12) : [];
      const draft = readLocal(DRAFT_KEY, "");
      if (typeof draft === "string" && draft) {state.draft = draft; $("#draft").value = draft; $("#draft-panel").hidden = false;
        say("#draft-status", "已恢复你保留的草稿；尚未发送。");}
      renderArchives(); if (storageNotice) say("#archive-status", storageNotice, true);
    } catch (error) {$("#studio").hidden = false; say("#stage-status", "连接失败：" + error.message, true);}
  }
  $("#login-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {await api("/api/login", {token: $("#access-token").value}); $("#access-token").value = ""; await boot();}
    catch (error) {say("#login-status", error.message, true);}
  });
  $("#logout").addEventListener("click", async () => {try {await api("/api/logout", {}); invalidate(); showLogin();} catch (e) {say("#stage-status", e.message, true);}});
  $("#scene-select").addEventListener("change", event => changeScene(event.target.value));
  $("#import-source").addEventListener("click", importSource);
  $("#trial").addEventListener("input", () => {$("#model-consent").checked = false; invalidate();});
  $("#generation-mode").addEventListener("change", () => {invalidate(); $("#model-consent").checked = false; updateMode();});
  $("#rehearse-form").addEventListener("submit", rehearse);
  $("#play-scene").addEventListener("click", playScene);
  $("#next-cue").addEventListener("click", nextCue);
  $("#show-scene").addEventListener("click", showScene);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden && playback.running) {cancelPlayback(); updatePlaybackControls();}
  });
  reducedMotion.addEventListener("change", () => {if (reducedMotion.matches && state.result) showScene();});
  $("#stop").addEventListener("click", () => {invalidate(); say("#stage-status", "已停止等待。已经发起的模型调用仍可能完成并计费。");});
  $("#use-draft").addEventListener("click", () => {
    if (!state.result) return;
    $("#draft-panel").hidden = false; $("#draft").value = state.result.routes[state.selected].draft;
    say("#draft-status", "可以继续修改；尚未发送。"); $("#draft").focus();
  });
  $("#draft").addEventListener("input", () => say("#draft-status", "草稿已修改；尚未发送。"));
  $("#keep-draft").addEventListener("click", () => {
    const text = $("#draft").value.trim();
    if (!text) {say("#draft-status", "先写一句想保留的话。", true); return;}
    if (writeLocal(DRAFT_KEY, text)) say("#draft-status", "已保留到当前浏览器；尚未发送。");
  });
  $("#export-draft").addEventListener("click", () => {
    const text = $("#draft").value.trim();
    if (!text) {say("#draft-status", "先写一句要导出的台词。", true); return;}
    download(text + "\n", "OnCue-我的台词.txt"); say("#draft-status", "台词已导出；尚未发送。");
  });
  $("#clear-draft").addEventListener("click", () => {
    if (writeLocal(DRAFT_KEY, "")) {$("#draft").value = ""; state.draft = "";
      say("#draft-status", "当前草稿已清空；历史存档中的草稿仍可单独删除。");}
  });
  $("#save-take").addEventListener("click", saveTake);
  $("#compare").addEventListener("click", compareTakes);
  boot();
})();
