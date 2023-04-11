const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");
const dotSize = 4;
const gravity = 9.8;
const timeInterval = 100;

let dotX = 0;
let dotY = canvas.height - (3*dotSize); //canvas.height / 2;
let speed = 0;
let slope = 0;

function drawDot() {
  // Leave a trail behind the dot
    ctx.fillStyle = "rgba(255, 255, 255, 0.3)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.beginPath();
  ctx.arc(dotX, dotY, dotSize, 0, 2 * Math.PI);
  ctx.fillStyle = "#dddcd8";
  ctx.fill();
  ctx.closePath();
}

function calculateDisplacement(speed, slope) {

  return {
    horizontal: horizontalDisplacement,
    vertical: verticalDisplacement,
  };
}

async function getData() {
  const response = await fetch("/get_data");
  const data = await response.json();
  speed = data.speed;
  slope = data.slope;

  console.log("Speed:", speed, "slope:", slope);

  setTimeout(getData, timeInterval);
}


function updateDot() {
  // Convert the slope from degrees to radians
  const slopeInRadians = (slope * Math.PI) / 180;
  // Calculate the horizontal and vertical displacements using trigonometry
  const horizontalDisplacement = speed * Math.cos(slopeInRadians);
  const verticalDisplacement = speed * Math.sin(slopeInRadians);
  // Move the dot
  dotX += horizontalDisplacement;
  dotY -= verticalDisplacement;

  if (dotX >= (canvas.width - 3*dotSize)) {
    // Move the canvas to the left by -horizontalDisplacement
    canvas.style.left = -horizontalDisplacement + "px";
    // Keep the dot next to the right edge of the canvas
    dotX = canvas.width - (3*dotSize);
  }
  if (dotY <= (canvas.height / 4)) {
    // Move the canvas by verticalDisplacement
    canvas.style.top = -verticalDisplacement + "px";
    // Keep the dot next to the top edge of the canvas
    dotY = (canvas.height / 4);
  }

  drawDot();
  setTimeout(updateDot, timeInterval);
}

getData();
updateDot();

