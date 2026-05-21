const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");
const splashScreen = document.getElementById("splash-screen");
const playScreen = document.getElementById("play-screen");
const overlay = document.getElementById("overlay");
const overlayEyebrow = document.getElementById("overlay-eyebrow");
const overlayTitle = document.getElementById("overlay-title");
const overlayCopy = document.getElementById("overlay-copy");
const startButton = document.getElementById("start-button");
const enterPlayButton = document.getElementById("enter-play-button");
const googleLoginButton = document.getElementById("google-login-button");
const loginStatus = document.getElementById("login-status");
const scoreNode = document.getElementById("score");

const config = {
  gravity: 0.24,
  flapVelocity: -6.4,
  pipeSpeed: 2.0,
  pipeWidth: 78,
  pipeGap: 214,
  pipeSpacing: 290,
  floorHeight: 92,
  scorePerSecond: 1,
  difficultyRampMs: 55000,
  maxDifficultyMultiplier: 1.4,
  minPipeGap: 170,
  minPipeSpacing: 248,
};

const owl = {
  x: 126,
  y: canvas.height / 2,
  radius: 20,
  velocity: 0,
  tilt: 0,
};

let state = "menu";
let score = 0;
let bestScore = 0;
let runStartedAt = 0;
let lastTime = 0;
let deathTimer = null;
let pipes = [];
let hasEnteredPlayScreen = false;
let signedInProvider = null;

function updateLoginStatus(copy) {
  loginStatus.textContent = copy;
}

function handleNativeGoogleLogin(provider = "Google") {
  signedInProvider = provider;
  updateLoginStatus(`${provider} sign-in connected for the Android MVP shell. You can open the play screen now.`);
}

window.handleNativeGoogleLogin = handleNativeGoogleLogin;

function showPlayScreen() {
  hasEnteredPlayScreen = true;
  splashScreen.classList.add("is-hidden");
  playScreen.classList.remove("is-hidden");
}

function resetRun() {
  owl.y = canvas.height / 2;
  owl.velocity = 0;
  owl.tilt = 0;
  score = 0;
  scoreNode.textContent = "0";
  runStartedAt = performance.now();
  pipes = [
    createPipe(canvas.width + 120),
    createPipe(canvas.width + 120 + config.pipeSpacing),
    createPipe(canvas.width + 120 + config.pipeSpacing * 2),
  ];
}

function createPipe(x) {
  const minTop = 90;
  const currentGap = getCurrentPipeGap();
  const maxTop = canvas.height - config.floorHeight - currentGap - 90;
  const topHeight = minTop + Math.random() * (maxTop - minTop);

  return {
    x,
    topHeight,
    gap: currentGap,
    passed: false,
  };
}

function getDifficultyProgress() {
  const elapsed = Math.max(0, performance.now() - runStartedAt);
  return Math.min(1, elapsed / config.difficultyRampMs);
}

function getDifficultyMultiplier() {
  return 1 + (config.maxDifficultyMultiplier - 1) * getDifficultyProgress();
}

function getCurrentPipeGap() {
  return config.pipeGap - (config.pipeGap - config.minPipeGap) * getDifficultyProgress();
}

function getCurrentPipeSpacing() {
  return config.pipeSpacing - (config.pipeSpacing - config.minPipeSpacing) * getDifficultyProgress();
}

function startRun() {
  clearTimeout(deathTimer);
  if (!hasEnteredPlayScreen) {
    showPlayScreen();
  }
  resetRun();
  state = "playing";
  overlay.classList.add("is-hidden");
}

function showMenu({ eyebrow, title, copy, buttonLabel }) {
  overlayEyebrow.textContent = eyebrow;
  overlayTitle.textContent = title;
  overlayCopy.textContent = copy;
  startButton.textContent = buttonLabel;
  overlay.classList.remove("is-hidden");
}

function endRun() {
  if (state !== "playing") {
    return;
  }

  state = "dead";
  const finalScore = score;
  bestScore = Math.max(bestScore, score);
  overlayEyebrow.textContent = "Ouch";
  overlayTitle.textContent = "The owl wiped out";
  overlayCopy.textContent = `Score ${finalScore}. Best ${bestScore}. Resetting to the play screen...`;
  startButton.textContent = "Play again";
  overlay.classList.remove("is-hidden");

  deathTimer = window.setTimeout(() => {
    state = "menu";
    resetRun();
    showMenu({
      eyebrow: "Ready",
      title: "Start a fresh run",
      copy: `Last score ${finalScore}. Best ${bestScore}. Space, click, or tap to flap again.`,
      buttonLabel: "Play",
    });
  }, 900);
}

function flap() {
  if (!hasEnteredPlayScreen) {
    return;
  }

  if (state === "menu") {
    startRun();
  }

  if (state !== "playing") {
    return;
  }

  owl.velocity = config.flapVelocity;
}

function update(delta) {
  if (state !== "playing") {
    return;
  }

  owl.velocity += config.gravity * delta;
  owl.y += owl.velocity * delta * 1.8;
  owl.tilt = Math.max(-0.45, Math.min(0.9, owl.velocity / 10));

  const nextScore = Math.floor((performance.now() - runStartedAt) / 1000) * config.scorePerSecond;
  if (nextScore !== score) {
    score = nextScore;
    scoreNode.textContent = String(score);
  }

  const difficultyMultiplier = getDifficultyMultiplier();
  const pipeVelocity = config.pipeSpeed * difficultyMultiplier * delta * 1.8;
  const pipeSpacing = getCurrentPipeSpacing();

  for (const pipe of pipes) {
    pipe.x -= pipeVelocity;
  }

  const lastPipe = pipes[pipes.length - 1];
  if (lastPipe && lastPipe.x < canvas.width - pipeSpacing) {
    pipes.push(createPipe(lastPipe.x + pipeSpacing));
  }

  pipes = pipes.filter((pipe) => pipe.x + config.pipeWidth > -20);

  if (owl.y + owl.radius >= canvas.height - config.floorHeight || owl.y - owl.radius <= 0) {
    endRun();
    return;
  }

  for (const pipe of pipes) {
    const hitsX = owl.x + owl.radius > pipe.x && owl.x - owl.radius < pipe.x + config.pipeWidth;
    const hitsTop = owl.y - owl.radius < pipe.topHeight;
    const hitsBottom = owl.y + owl.radius > pipe.topHeight + pipe.gap;

    if (hitsX && (hitsTop || hitsBottom)) {
      endRun();
      return;
    }
  }
}

function drawBackground() {
  ctx.fillStyle = "#97d6ff";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.fillStyle = "#d7f2ff";
  for (let i = 0; i < 4; i += 1) {
    const x = (i * 130 + lastTime * 0.012) % (canvas.width + 180) - 90;
    ctx.beginPath();
    ctx.ellipse(x, 120 + (i % 2) * 34, 54, 22, 0, 0, Math.PI * 2);
    ctx.fill();
  }

  ctx.fillStyle = "#5d975a";
  for (let i = 0; i < 7; i += 1) {
    const x = i * 68 - 24;
    ctx.beginPath();
    ctx.moveTo(x, canvas.height - config.floorHeight);
    ctx.lineTo(x + 22, canvas.height - config.floorHeight - 74);
    ctx.lineTo(x + 44, canvas.height - config.floorHeight);
    ctx.closePath();
    ctx.fill();
  }

  ctx.fillStyle = "#ab8f4c";
  ctx.fillRect(0, canvas.height - config.floorHeight, canvas.width, config.floorHeight);
}

function drawPipes() {
  for (const pipe of pipes) {
    ctx.fillStyle = "#487c42";
    ctx.fillRect(pipe.x, 0, config.pipeWidth, pipe.topHeight);
    ctx.fillRect(
      pipe.x,
      pipe.topHeight + pipe.gap,
      config.pipeWidth,
      canvas.height - pipe.topHeight - pipe.gap - config.floorHeight
    );

    ctx.fillStyle = "#2b5727";
    ctx.fillRect(pipe.x - 3, pipe.topHeight - 16, config.pipeWidth + 6, 16);
    ctx.fillRect(pipe.x - 3, pipe.topHeight + pipe.gap, config.pipeWidth + 6, 16);
  }
}

function drawOwl() {
  ctx.save();
  ctx.translate(owl.x, owl.y);
  ctx.rotate(owl.tilt);

  ctx.fillStyle = "#8a5a34";
  ctx.beginPath();
  ctx.ellipse(0, 0, 24, 20, 0, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "#b97845";
  ctx.beginPath();
  ctx.ellipse(-6, 2, 10, 13, 0, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "#f6ecd9";
  ctx.beginPath();
  ctx.ellipse(2, 6, 11, 9, 0, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "#fff";
  ctx.beginPath();
  ctx.arc(6, -4, 6, 0, Math.PI * 2);
  ctx.arc(-6, -4, 6, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "#23190f";
  ctx.beginPath();
  ctx.arc(6, -4, 2.4, 0, Math.PI * 2);
  ctx.arc(-6, -4, 2.4, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "#d5802c";
  ctx.beginPath();
  ctx.moveTo(1, 1);
  ctx.lineTo(14, 4);
  ctx.lineTo(1, 8);
  ctx.closePath();
  ctx.fill();

  ctx.strokeStyle = "#6a3919";
  ctx.lineWidth = 4;
  ctx.lineCap = "round";
  ctx.beginPath();
  ctx.moveTo(-16, 18);
  ctx.lineTo(-14, 25);
  ctx.moveTo(-2, 18);
  ctx.lineTo(-4, 25);
  ctx.stroke();

  ctx.restore();
}

function drawPrompt() {
  if (state === "playing" || !hasEnteredPlayScreen) {
    return;
  }

  ctx.fillStyle = "rgba(49, 35, 18, 0.08)";
  ctx.font = "700 18px Trebuchet MS";
  ctx.textAlign = "center";
  ctx.fillText("Tap or press space to flap", canvas.width / 2, canvas.height - 130);
}

function render() {
  drawBackground();
  drawPipes();
  drawOwl();
  drawPrompt();
}

function frame(timestamp) {
  if (!lastTime) {
    lastTime = timestamp;
  }

  const delta = Math.min(1.6, (timestamp - lastTime) / 16.6667);
  lastTime = timestamp;

  update(delta);
  render();
  window.requestAnimationFrame(frame);
}

startButton.addEventListener("click", startRun);
enterPlayButton.addEventListener("click", () => {
  showPlayScreen();
  state = "menu";
  showMenu({
    eyebrow: signedInProvider ? "Signed in" : "Ready",
    title: "Start a run",
    copy: signedInProvider
      ? `Signed in with ${signedInProvider}. Keep the owl airborne, pass the branches, and survive as long as you can.`
      : "Keep the owl airborne, pass the branches, and survive as long as you can.",
    buttonLabel: "Start run",
  });
});
googleLoginButton.addEventListener("click", () => {
  if (window.AndroidAuth && typeof window.AndroidAuth.beginGoogleLogin === "function") {
    updateLoginStatus("Opening the Android Google sign-in stub...");
    window.AndroidAuth.beginGoogleLogin();
    return;
  }

  handleNativeGoogleLogin("Google");
});

window.addEventListener("keydown", (event) => {
  if (event.code !== "Space") {
    return;
  }

  event.preventDefault();
  flap();
});

canvas.addEventListener("pointerdown", flap);

showMenu({
  eyebrow: "Ready",
  title: "Start a run",
  copy: "Keep the owl airborne, pass the branches, and survive as long as you can.",
  buttonLabel: "Start run",
});
resetRun();
window.requestAnimationFrame(frame);
