let timerInterval = null;
let secondsLeft = 0;
let breakMode = false;

function formatTime(s) {
  const m = Math.floor(s/60);
  const sec = s % 60;
  return `${m.toString().padStart(2,'0')}:${sec.toString().padStart(2,'0')}`;
}

document.addEventListener("DOMContentLoaded", () => {
  const display = document.getElementById("timer-display");
  const mode = document.getElementById("timer-mode");
  const startBtn = document.getElementById("start-btn");
  const stopBtn = document.getElementById("stop-btn");
  const studyInput = document.getElementById("study-min");
  const breakInput = document.getElementById("break-min");
  const logStudyEl = document.getElementById("log-study");
  const logBreakEl = document.getElementById("log-break");

  function updateHidden() {
    logStudyEl.value = studyInput.value;
    logBreakEl.value = breakInput.value;
  }
  studyInput.addEventListener("change", updateHidden);
  breakInput.addEventListener("change", updateHidden);
  updateHidden();

  startBtn.addEventListener("click", () => {
    clearInterval(timerInterval);
    breakMode = false;
    secondsLeft = parseInt(studyInput.value) * 60;
    mode.textContent = "Study";
    display.textContent = formatTime(secondsLeft);
    timerInterval = setInterval(() => {
      secondsLeft -= 1;
      display.textContent = formatTime(secondsLeft);
      if (secondsLeft <= 0) {
        clearInterval(timerInterval);
        alert("Study session finished! Starting break.");
        // auto-start break
        breakMode = true;
        secondsLeft = parseInt(breakInput.value) * 60;
        mode.textContent = "Break";
        timerInterval = setInterval(() => {
          secondsLeft -= 1;
          display.textContent = formatTime(secondsLeft);
          if (secondsLeft <= 0) {
            clearInterval(timerInterval);
            mode.textContent = "Idle";
            display.textContent = "00:00";
            alert("Break finished! Time to study again.");
          }
        }, 1000);
      }
    }, 1000);
  });

  stopBtn.addEventListener("click", () => {
    clearInterval(timerInterval);
    mode.textContent = "Idle";
    display.textContent = "00:00";
  });
});
