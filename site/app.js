"use strict";

const themeToggle = document.getElementById("theme-toggle");
const colorPreference = window.matchMedia("(prefers-color-scheme: dark)");
let themeChosen = false;
try {
  themeChosen = ["day", "night"].includes(localStorage.getItem("oncue-theme"));
} catch {}

function applyTheme(theme) {
  const night = theme === "night";
  document.documentElement.dataset.theme = night ? "night" : "day";
  document.documentElement.style.colorScheme = night ? "dark" : "light";
  document.querySelector('meta[name="theme-color"]').content = night ? "#18242f" : "#f3ede2";
  const label = night ? "切换到亮色主题" : "切换到暗色主题";
  themeToggle.setAttribute("aria-label", label);
  themeToggle.setAttribute("title", label);
  themeToggle.setAttribute("aria-pressed", String(night));
}

applyTheme(document.documentElement.dataset.theme);
themeToggle.hidden = false;
themeToggle.addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "night" ? "day" : "night";
  themeChosen = true;
  applyTheme(next);
  try { localStorage.setItem("oncue-theme", next); } catch {}
});
colorPreference.addEventListener("change", (event) => {
  if (!themeChosen) applyTheme(event.matches ? "night" : "day");
});
window.addEventListener("storage", (event) => {
  if (event.key !== "oncue-theme") return;
  themeChosen = ["day", "night"].includes(event.newValue);
  applyTheme(themeChosen ? event.newValue : colorPreference.matches ? "night" : "day");
});

const video = document.getElementById("demo-video");
const playVideo = document.getElementById("play-video");
const videoError = document.getElementById("video-error");
playVideo.hidden = false;
playVideo.addEventListener("click", () => {
  videoError.hidden = true;
  video.play().catch(() => { videoError.hidden = false; });
});
video.addEventListener("play", () => { playVideo.hidden = true; });
video.addEventListener("pause", () => { playVideo.hidden = false; });
video.addEventListener("ended", () => { playVideo.hidden = false; });
video.addEventListener("error", () => { videoError.hidden = false; });

const tabs = [...document.querySelectorAll('[role="tab"]')];

function selectStage(tab, focus = false) {
  for (const candidate of tabs) {
    const selected = candidate === tab;
    candidate.setAttribute("aria-selected", String(selected));
    candidate.tabIndex = selected ? 0 : -1;
    document.getElementById(candidate.getAttribute("aria-controls")).hidden = !selected;
  }
  if (focus) tab.focus();
}

for (const [index, tab] of tabs.entries()) {
  tab.addEventListener("click", () => selectStage(tab));
  tab.addEventListener("keydown", (event) => {
    let next;
    if (event.key === "ArrowRight" || event.key === "ArrowDown") next = (index + 1) % tabs.length;
    if (event.key === "ArrowLeft" || event.key === "ArrowUp") next = (index - 1 + tabs.length) % tabs.length;
    if (event.key === "Home") next = 0;
    if (event.key === "End") next = tabs.length - 1;
    if (next === undefined) return;
    event.preventDefault();
    selectStage(tabs[next], true);
  });
}

const dialog = document.getElementById("screenshot-dialog");
const screenshot = document.getElementById("full-screenshot");
const caption = document.getElementById("screenshot-caption");

for (const button of document.querySelectorAll("[data-zoom]")) {
  button.addEventListener("click", () => {
    if (typeof dialog.showModal !== "function") {
      window.location.assign(button.dataset.zoom);
      return;
    }
    screenshot.src = button.dataset.zoom;
    screenshot.alt = button.dataset.caption;
    caption.textContent = button.dataset.caption;
    dialog.showModal();
    document.body.classList.add("dialog-open");
  });
}

document.getElementById("close-dialog").addEventListener("click", () => dialog.close());
dialog.addEventListener("close", () => document.body.classList.remove("dialog-open"));
dialog.addEventListener("click", (event) => {
  if (event.target !== dialog) return;
  const bounds = dialog.getBoundingClientRect();
  if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
});
