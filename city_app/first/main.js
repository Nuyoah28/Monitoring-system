function pad(value) {
  return value.toString().padStart(2, "0");
}

function updateClock() {
  const now = new Date();
  const text = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
  const node = document.getElementById("currentTime");
  if (node) node.textContent = text;
}

function bindAlertMock() {
  const btn = document.getElementById("toggleAlertState");
  const list = document.getElementById("alertList");
  const count = document.getElementById("activeAlertCount");

  if (!btn || !list || !count) return;

  btn.addEventListener("click", () => {
    const first = list.querySelector("li");
    if (!first) return;
    first.remove();

    const current = Number(count.textContent) || 0;
    count.textContent = String(Math.max(0, current - 1));
  });
}

function bindVocabForm() {
  const form = document.getElementById("vocabForm");
  const word = document.getElementById("wordInput");
  const risk = document.getElementById("riskInput");
  const scene = document.getElementById("sceneInput");
  const list = document.getElementById("vocabList");

  if (!form || !word || !risk || !scene || !list) return;

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const w = word.value.trim();
    const s = scene.value.trim();
    if (!w || !s) return;

    const item = document.createElement("li");
    const left = document.createElement("span");
    const right = document.createElement("em");

    left.textContent = w;
    right.textContent = `${risk.value} · ${s}`;

    item.appendChild(left);
    item.appendChild(right);
    list.prepend(item);

    word.value = "";
    scene.value = "";
  });
}

updateClock();
setInterval(updateClock, 1000);
bindAlertMock();
bindVocabForm();
