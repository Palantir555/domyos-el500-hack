const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");
const doneButton = document.getElementById("doneButton");

let dotX = 0;
let dotY = canvas.height / 2;
const dotSize = 5;
let speed = 1;
let resistance = 0;

let timeInterval = 100; // Time interval between data updates in milliseconds

function drawDot() {
  ctx.beginPath();
  ctx.arc(dotX, dotY, dotSize, 0, 2 * Math.PI);
  ctx.fillStyle = "#dddcd8";
  ctx.fill();
  ctx.closePath();
}

function updateDotPosition() {
  const angle = Math.atan(resistance * 3);
  dotX += speed * Math.cos(angle);
  dotY -= speed * Math.sin(angle);

  // Update canvas position to follow the dot
  canvas.style.transform = `translateX(-${dotX - canvas.width / 2}px)`;
}

function gameLoop() {
  updateDotPosition();
  drawDot();

  if (dotX < canvas.width * 2) {
    requestAnimationFrame(gameLoop);
  } else {
    doneButton.style.display = "block"; // Show the "Done" button when the dot reaches the end
  }
}

async function getData() {
  const response = await fetch("/get_data");
  const data = await response.json();
  speed = data.speed;
  resistance = data.resistance;

  console.log("Speed:", speed, "Resistance:", resistance);

  setTimeout(getData, timeInterval);
}

// Zoom out and show the entire trail when the "Done" button is pressed
doneButton.addEventListener("click", () => {
  canvas.style.transform = "translateX(0)";
  canvas.width *= 0.5;
  canvas.height *= 0.5;
  ctx.scale(0.5, 0.5);
  dotX = 0;
  dotY = canvas.height / 2;
  gameLoop();
});

getData();
gameLoop();
