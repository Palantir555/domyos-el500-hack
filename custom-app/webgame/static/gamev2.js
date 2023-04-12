const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");
const dotSize = 4;
const gravity = 9.8;
const timeInterval = 100;

const balls = [];

function updatePastDotPositions(ballIndex, horizontalDisplacement, verticalDisplacement) {
  //const pastPositions = balls[ballIndex].pastPositions;
  //for (let i = 0; i < pastPositions.length; i++) {
  //  pastPositions[i].x -= horizontalDisplacement;
  //  pastPositions[i].y += verticalDisplacement;
  //}
  // Update the positions of all the balls
    balls.forEach((ball, index) => {
        //if (index === ballIndex) return;
        const pastPositions = ball.pastPositions;
        for (let i = 0; i < pastPositions.length; i++) {
            pastPositions[i].x -= horizontalDisplacement;
            pastPositions[i].y += verticalDisplacement;
        }
        
    });
}

function drawDot() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  balls.forEach((ball) => {
    const pastPositions = ball.pastPositions;

    // Draw the trail (smaller dots) for past positions
    ctx.fillStyle = ball.id === 0 ? "#dddcd8" : `rgba(${ball.id * 20}, ${ball.id * 20}, ${ball.id * 20}, 1)`;
    pastPositions.forEach((position) => {
      ctx.beginPath();
      ctx.arc(position.x, position.y, dotSize / 2, 0, 2 * Math.PI);
      ctx.fill();
      ctx.closePath();
    });

    // Draw the main dot
    ctx.beginPath();
    ctx.arc(ball.position.x, ball.position.y, dotSize, 0, 2 * Math.PI);
    ctx.fillStyle = ball.id === 0 ? "#dddcd8" : `rgba(${ball.id * 40}, ${ball.id * 40}, ${ball.id * 50}, 1)`;
    ctx.fill();
    ctx.closePath();
  });
}

async function getData() {
  const response = await fetch("/get_data");
  const data = await response.json();

  data.forEach((ballData) => {
    const ballIndex = balls.findIndex((ball) => ball.id === ballData.id);

    if (ballIndex >= 0) {
      // Update the existing ball's data
      balls[ballIndex] = { ...balls[ballIndex], ...ballData };
    } else {
      // Add the new ball to the balls array
      ballData.pastPositions = [{ x: 0, y: canvas.height - (3 * dotSize) }];
      balls.push(ballData);
    }
  });

  setTimeout(getData, timeInterval);
}

function updateDot() {
  balls.forEach((ball, index) => {
    const slopeInRadians = (ball.slope * Math.PI) / 180;
    const horizontalDisplacement = ball.speed * Math.cos(slopeInRadians);
    const verticalDisplacement = ball.speed * Math.sin(slopeInRadians);

    // ball's position is the last position in the pastPositions array
    ball.position = ball.pastPositions[ball.pastPositions.length - 1];
    let newBallX = ball.position.x + horizontalDisplacement;
    let newBallY = ball.position.y - verticalDisplacement;
    let canvasUpdated = false;

    if (ball.id === 0 && newBallX >= 3 * (canvas.width / 4)) {
      canvas.style.left = horizontalDisplacement + "px";
      newBallX = 3 * (canvas.width / 4);
      canvasUpdated = true;
    }
    if (ball.id === 0 && newBallY <= (canvas.height / 4)) {
      canvas.style.top = verticalDisplacement + "px";
      newBallY = (canvas.height / 4);
      canvasUpdated = true;
    }

    if (canvasUpdated) {
      updatePastDotPositions(index, horizontalDisplacement, verticalDisplacement);
    }

    balls[index].pastPositions.push({ x: newBallX, y: newBallY });
    balls[index].position.x = newBallX;
    balls[index].position.y = newBallY;
  });

  drawDot();
  setTimeout(updateDot, timeInterval);
}

getData();
updateDot(); 

