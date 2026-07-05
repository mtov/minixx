const display = document.getElementById("display");
const startButton = document.getElementById("start");
const pauseButton = document.getElementById("pause");
const resetButton = document.getElementById("reset");

let elapsedMs = 0;
let startTime = 0;
let timerId = null;

function formatTime(totalMs) {
  const totalSeconds = Math.floor(totalMs / 1000);
  const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
  const seconds = String(totalSeconds % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

function render() {
  display.textContent = formatTime(elapsedMs);
}

function tick() {
  elapsedMs = Date.now() - startTime;
  render();
}

startButton.addEventListener("click", () => {
  if (timerId !== null) {
    return;
  }

  startTime = Date.now() - elapsedMs;
  timerId = window.setInterval(tick, 100);
});

pauseButton.addEventListener("click", () => {
  if (timerId === null) {
    return;
  }

  window.clearInterval(timerId);
  timerId = null;
  elapsedMs = Date.now() - startTime;
  render();
});

resetButton.addEventListener("click", () => {
  if (timerId !== null) {
    window.clearInterval(timerId);
    timerId = null;
  }

