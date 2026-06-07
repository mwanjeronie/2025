// Ripeness guide: show the tip for the selected stage.
const ripeTrack = document.getElementById("ripeness-track");
const ripeTip = document.getElementById("ripe-tip");

if (ripeTrack && ripeTip) {
  ripeTrack.addEventListener("click", (event) => {
    const stage = event.target.closest(".ripe-stage");
    if (!stage) return;

    ripeTrack
      .querySelectorAll(".ripe-stage")
      .forEach((el) => el.classList.remove("active"));
    stage.classList.add("active");
    ripeTip.textContent = stage.dataset.tip;
  });
}

// Random banana trivia.
const facts = [
  "Bananas float in water because they are less dense than it.",
  "The inside of a banana peel can help soothe a bug bite or sunburn.",
  "Humans share about 50% of their DNA with bananas.",
  "Rubbing a banana peel on shoes can give them a quick shine.",
  "Bananas grow pointing upward, toward the sun.",
  "A cluster of bananas is called a 'hand', and a single banana is a 'finger'.",
  "India is the world's largest producer of bananas.",
  "The word 'banana' is thought to come from the Arabic word 'banan', meaning finger.",
  "Bananas are naturally slightly radioactive due to their potassium content.",
  "Wild bananas are full of hard seeds and quite different from the ones we eat today.",
];

const triviaBtn = document.getElementById("trivia-btn");
const triviaBox = document.getElementById("trivia-box");
let lastIndex = -1;

if (triviaBtn && triviaBox) {
  triviaBtn.addEventListener("click", () => {
    let index;
    do {
      index = Math.floor(Math.random() * facts.length);
    } while (index === lastIndex && facts.length > 1);
    lastIndex = index;
    triviaBox.textContent = facts[index];
  });
}
