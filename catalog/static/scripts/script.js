let particles = [];

function setup() {
  let canvas = createCanvas(windowWidth, windowHeight);
  canvas.parent('canvasContainer');
  frameRate(30);
  colorMode(HSB, 255);
  background(0);
}

function draw() {
  // Clear the background more aggressively to avoid buildup, adjust alpha as needed
  background(0, 0, 0, 20);

  let forceDirection = createVector(mouseX - width / 2, mouseY - height / 2);
  forceDirection.normalize().mult(0.1); // Reduced force to cursor

  // Reduce particle count
  if (particles.length < 90) { 
    particles.push(new Particle());
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
  constructor() {
    this.position = createVector(random(width), random(height));
    this.prevPos = this.position.copy(); // New property to store the previous position
    this.velocity = createVector(random(-2, 2), random(-2, 2));
    this.acceleration = createVector();
    this.lifespan = 255;
    this.hue = random(255);
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
    this.acceleration.mult(0.7);
    this.lifespan -= 4; // They fade faster
    this.hue = (this.hue + 1) % 255; // Cycle hue values
  }

  display() {
    strokeWeight(4); // Make the line thicker
    stroke(this.hue, 255, 255, this.lifespan);
    line(this.position.x, this.position.y, this.prevPos.x, this.prevPos.y); // Draw a line from previous position to current position
    noStroke();
  }

  isDead() {
    return this.lifespan < 0;
  }
}
