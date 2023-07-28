let particles = [];
let rand_col = 0; 

function setup() {
  let canvas = createCanvas(windowWidth, windowHeight);
  canvas.parent('canvasContainer');
  frameRate(30);
  colorMode(HSB, 100);  // Use HSB color mode for easy color variations
  background(0);  // Black background
  rand_col = random(100);
  rand_sal = random(100);
}

function draw() {
  background(0, 0, 0, 10);  // Apply a semi-transparent black background to create a trailing effect

  if (particles.length < 100) {  // Limit the number of particles
    let p = new Particle();  // Create a new particle
    particles.push(p);  // Add it to the array
  }

  for (let i = particles.length - 1; i >= 0; i--) {
    particles[i].update();  // Update the particle's position
    particles[i].display();  // Draw the particle
    if (particles[i].isDead()) {  // If the particle is dead
      particles.splice(i, 1);  // Remove it from the array
    }
  }
}

class Particle {
  constructor() {
    this.position = createVector(random(width), random(height));  // Random starting position
    this.velocity = createVector(random(-1, 1), random(-1, 1));  // Random initial velocity
    this.lifespan = 255;  // Initial lifespan
    this.hue = (rand_col, rand_sal); //random(100);  // Random initial color
  }

  update() {
    this.position.add(this.velocity);  // Update position
    this.lifespan -= 2;  // Decrease lifespan
    this.hue += 0.1;  // Gradually change color
  }

  display() {
    noStroke();
    fill(this.hue, 100, 100, this.lifespan);  // Use color and lifespan to set fill
    ellipse(this.position.x, this.position.y, 12);  // Draw a circle at the particle's position
  }

  isDead() {
    return this.lifespan < 0;  // If the lifespan is less than 0, the particle is dead
  }
}