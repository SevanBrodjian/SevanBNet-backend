let particles = [];

function setup() {
  let canvas = createCanvas(windowWidth, windowHeight);
  canvas.parent('canvasContainer');
  frameRate(30);
  colorMode(HSB, 255);
  background(0);
}

function mulVecs(vectorA, vectorB){
  return createVector(vectorA.x * vectorB.x, vectorA.y * vectorB.y);
}

function draw() {
  // Clear the background more aggressively to avoid buildup, adjust alpha as needed
  background(30, 0, 0, 30);

  let forceDirection = createVector(mouseX - width / 2, mouseY - height / 2);
  forceDirection.normalize().mult(0.1); // Reduced force to cursor
  drivingVector = createVector(0, 0.2)
  forceDirection.add(drivingVector)

  // Reduce particle count
  if (particles.length < 2000) { 
    particles.push(new Particle(forceDirection));
    if(random(1) > 0.7){
      particles.push(new Particle(forceDirection));
    }
  }

  for (let i = particles.length - 1; i >= 0; i--) {
    particles[i].attract(forceDirection);
    particles[i].update();
    particles[i].display();
    if (particles[i].isDead()) {
      particles.splice(i, 1);
    }
  }
}

// function draw() {
//   background(0, 0, 0, 20);
//   let mousePosition = createVector(mouseX, mouseY); // Create a vector for the mouse position

//   // Reduce particle count
//   if (particles.length < 90) { 
//     particles.push(new Particle());
//   }

//   for (let i = particles.length - 1; i >= 0; i--) {
//       particles[i].attract(mousePosition); // Pass the mouse position to the attract method
//       particles[i].update();
//       particles[i].display();
//       if (particles[i].isDead()) {
//           particles.splice(i, 1);
//       }
//   }
// }

class Particle {
  constructor(forceDirection) {
    this.position = createVector(random(width), random(height));
    this.prevPos = this.position.copy(); // New property to store the previous position
    this.velocity = forceDirection.mult(0.4); //createVector(random(-1, 1), random(-1, 1));
    this.acceleration = createVector();
    this.lifespan = 255;
    this.hue = random(255);
    this.size = random(1.5, 3.5)
  }

  attract(force) {
    this.acceleration.add(force);
  }
  // attract(mousePosition) {
  //   // Calculate direction of force: from this particle's position towards the mouse position
  //   let forceDirection = p5.Vector.sub(mousePosition, this.position); 
  //   // Limiting the magnitude of the force to avoid very rapid movement
  //   forceDirection.setMag(0.5);
  //   // Apply this force to the particle's acceleration
  //   this.acceleration.add(forceDirection);
  // }


  update() {
    this.velocity.add(this.acceleration);
    this.prevPos = this.position.copy(); // Store the current position before updating it
    this.position.add(this.velocity);
    this.acceleration.mult(0.55);
    this.lifespan -= random(18); // They fade faster
    this.hue = (this.hue + 2) % 255; // Cycle hue values
  }

  display() {
    strokeWeight(this.size); // Make the line thicker
    stroke(this.hue, 255, 255, this.lifespan);
    line(this.position.x, this.position.y, this.prevPos.x, this.prevPos.y); // Draw a line from previous position to current position
    noStroke();
  }

  isDead() {
    return this.lifespan < 0;
  }
}
