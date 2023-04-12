const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");
const dotSize = 4;
const gravity = 9.8;
const timeInterval = 100;

let dotX = 0;
let dotY = canvas.height - (3*dotSize);
let speed = 0;
let slope = 0;
pastPositionsUpdated = false;

const pastDotPositions = []; // Add this line to store past dot positions

function updatePastDotPositions(horizontalDisplacement, verticalDisplacement) {
  for (let i = 0; i < pastDotPositions.length; i++) {
    pastDotPositions[i].x -= horizontalDisplacement;
    pastDotPositions[i].y += verticalDisplacement;
  }
  pastPositionsUpdated = true;
}

function drawDot() {
  // Clear the canvas only when necessary, e.g., when resizing
  if (pastPositionsUpdated) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    pastPositionsUpdated = false;
  }

  // Store the current dot position
  pastDotPositions.push({ x: dotX, y: dotY });

  // Draw the trail (smaller dots) for past positions
  ctx.fillStyle = "#dddcd8";
  pastDotPositions.forEach((position) => {
    ctx.beginPath();
    ctx.arc(position.x, position.y, dotSize / 2, 0, 2 * Math.PI);
    ctx.fill();
    ctx.closePath();
  });

  // Draw the main dot
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
  canvasupdated = false;

  if (dotX >= 3 * (canvas.width / 4)) {
    // Move the canvas to the left by -horizontalDisplacement
    canvas.style.left = horizontalDisplacement + "px";
    // Keep the dot next to the right edge of the canvas
    dotX = 3 * (canvas.width / 4);
    canvasupdated = true;
  }
  if (dotY <= (canvas.height / 4)) {
    // Move the canvas by verticalDisplacement
    canvas.style.top = verticalDisplacement + "px";
    // Keep the dot next to the top edge of the canvas
    dotY = (canvas.height / 4);
    canvasupdated = true;
  }
  if (canvasupdated) {
    // Move the dot trail
    // TODO: This will move both axes even if only 1 is updated. It's just less
    //       wasteful this way, but maybe unnecessarily so(?)
    updatePastDotPositions(horizontalDisplacement, verticalDisplacement);
  }

  drawDot();
  setTimeout(updateDot, timeInterval);
}

getData();
updateDot();

