const tabs = document.querySelectorAll(".tab");
const views = document.querySelectorAll(".view");

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    const target = tab.dataset.tab;

    tabs.forEach((item) => item.classList.remove("active"));
    tab.classList.add("active");

    views.forEach((view) => {
      view.classList.toggle("active", view.dataset.view === target);
    });
  });
});

const phraseInput = document.getElementById("phraseInput");
const addPhraseBtn = document.getElementById("addPhraseBtn");
const phraseList = document.getElementById("phraseList");

function addPhrase() {
  const value = phraseInput.value.trim();
  if (!value) return;

  const tag = document.createElement("span");
  tag.textContent = value;
  phraseList.prepend(tag);
  phraseInput.value = "";
}

addPhraseBtn.addEventListener("click", addPhrase);
phraseInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    addPhrase();
  }
});
