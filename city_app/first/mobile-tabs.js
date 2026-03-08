function two(n) {
  return String(n).padStart(2, "0");
}

function renderTime() {
  const now = new Date();
  const t = `${two(now.getHours())}:${two(now.getMinutes())}`;
  const node = document.getElementById("mTime");
  if (node) node.textContent = t;
}

function bindTabs() {
  const buttons = document.querySelectorAll(".tab-btn");
  const pages = document.querySelectorAll(".tab-page");

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const key = btn.dataset.tab;
      buttons.forEach((x) => x.classList.remove("active"));
      pages.forEach((x) => x.classList.remove("active"));
      btn.classList.add("active");
      const page = document.getElementById(`tab-${key}`);
      if (page) page.classList.add("active");
    });
  });
}

function bindWordForm() {
  const form = document.getElementById("mWordForm");
  const word = document.getElementById("mWord");
  const risk = document.getElementById("mRisk");
  const scene = document.getElementById("mScene");
  const list = document.getElementById("mWordList");

  if (!form || !word || !risk || !scene || !list) return;

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const w = word.value.trim();
    const s = scene.value.trim();
    if (!w || !s) return;

    const li = document.createElement("li");
    li.innerHTML = `<b>${w}</b><em>${risk.value} · ${s}</em>`;
    list.prepend(li);

    word.value = "";
    scene.value = "";
  });
}

function bindAlertSimulate() {
  const btn = document.getElementById("simulateBtn");
  const list = document.getElementById("mAlertList");
  const active = document.getElementById("mActive");
  if (!btn || !list || !active) return;

  btn.addEventListener("click", () => {
    const first = list.querySelector("li");
    if (first) first.remove();
    const value = Number(active.textContent) || 0;
    active.textContent = String(Math.max(0, value - 1));
  });
}

renderTime();
setInterval(renderTime, 1000 * 30);
bindTabs();
bindWordForm();
bindAlertSimulate();
