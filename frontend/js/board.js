// Draws the board with three.js: the grid, plant cells, and growing tips.
// World units are hex corner radii, and the camera zoom is the hex size in
// pixels, so "hex size" and zoom are the same value.

import * as THREE from "three";
import { DIRECTIONS, SQRT3, hexToWorld, worldToHex } from "./hex.js";

export const MIN_HEX_SIZE = 6;
export const MAX_HEX_SIZE = 80;

// Grid outlines fade out between these hex sizes and are skipped below the lower one.
const GRID_HIDDEN_AT = 8;
const GRID_SOLID_AT = 16;

const VINE_WIDTH = 0.3;
const STUMP_COLOR = new THREE.Color(0x8a6f52);
const BLOCKED_TIP_COLOR = new THREE.Color(0x77807a);
const WHITE = new THREE.Color(0xffffff);

const ORDER = { grid: 0, hover: 1, links: 2, cells: 3, tips: 4 };

const matrix = new THREE.Matrix4();
const scale = new THREE.Vector3();

// A pool of instances of one shape that grows as the board does.
class Instances {
  constructor(scene, geometry, renderOrder) {
    this.scene = scene;
    this.geometry = geometry;
    this.renderOrder = renderOrder;
    this.material = new THREE.MeshBasicMaterial({ depthTest: false });
    this.capacity = 0;
    this.mesh = null;
    this.count = 0;
    this.reserve(64);
  }

  reserve(capacity) {
    if (this.mesh) {
      this.scene.remove(this.mesh);
      this.mesh.dispose();
    }
    this.capacity = capacity;
    this.mesh = new THREE.InstancedMesh(this.geometry, this.material, capacity);
    this.mesh.setColorAt(0, STUMP_COLOR); // allocates the per-instance colour buffer
    this.mesh.frustumCulled = false;
    this.mesh.renderOrder = this.renderOrder;
    this.mesh.count = 0;
    this.scene.add(this.mesh);
  }

  begin(count) {
    if (count > this.capacity) this.reserve(Math.max(count, this.capacity * 2));
    this.count = 0;
  }

  put(x, y, angle, scaleX, scaleY, color) {
    matrix.makeRotationZ(angle).scale(scale.set(scaleX, scaleY, 1)).setPosition(x, y, 0);
    this.mesh.setMatrixAt(this.count, matrix);
    this.mesh.setColorAt(this.count, color);
    this.count += 1;
  }

  end() {
    this.mesh.count = this.count;
    this.mesh.instanceMatrix.needsUpdate = true;
    this.mesh.instanceColor.needsUpdate = true;
  }
}

function parseFraction(text) {
  const [numerator, denominator] = String(text).split("/");
  return denominator === undefined ? Number(numerator) : Number(numerator) / Number(denominator);
}

export class Board {
  constructor(canvas, hexSize) {
    this.canvas = canvas;
    this.hexSize = hexSize;
    this.center = { x: 0, y: 0 };

    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.renderer.setClearColor(0x101613);
    this.scene = new THREE.Scene();
    this.camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 100);
    this.camera.position.z = 10;

    this.grid = this.makeGrid();
    this.gridBounds = null;
    this.hover = this.makeHover();

    // A unit strip from x = 0 to x = 1, stretched along a vine.
    const strip = new THREE.PlaneGeometry(1, 1).translate(0.5, 0, 0);
    const disc = new THREE.CircleGeometry(1, 24);
    const hexagon = new THREE.CircleGeometry(1, 6).rotateZ(Math.PI / 6);
    this.links = new Instances(this.scene, strip, ORDER.links);
    this.segments = new Instances(this.scene, disc, ORDER.cells);
    this.roots = new Instances(this.scene, disc, ORDER.cells);
    this.stumps = new Instances(this.scene, hexagon, ORDER.cells);
    this.tipStrips = new Instances(this.scene, strip, ORDER.tips);
    this.tipHeads = new Instances(this.scene, disc, ORDER.tips);

    this.plantColors = new Map();
    this.tips = [];
    this.shownProgress = new Map(); // tip id -> { q, r, shown }
    this.lastFrame = performance.now();

    this.resize();
    window.addEventListener("resize", () => this.resize());
  }

  start() {
    const frame = (now) => {
      const dt = Math.min((now - this.lastFrame) / 1000, 0.1);
      this.lastFrame = now;
      this.updateGrid();
      this.drawTips(dt);
      this.renderer.render(this.scene, this.camera);
      requestAnimationFrame(frame);
    };
    requestAnimationFrame(frame);
  }

  // -- view ---------------------------------------------------------------

  resize() {
    this.width = window.innerWidth;
    this.height = window.innerHeight;
    this.renderer.setSize(this.width, this.height, false);
    this.camera.left = -this.width / 2;
    this.camera.right = this.width / 2;
    this.camera.top = this.height / 2;
    this.camera.bottom = -this.height / 2;
    this.applyCamera();
  }

  applyCamera() {
    this.camera.zoom = this.hexSize;
    this.camera.position.x = this.center.x;
    this.camera.position.y = this.center.y;
    this.camera.updateProjectionMatrix();
  }

  screenToWorld(px, py) {
    return [
      this.center.x + (px - this.width / 2) / this.hexSize,
      this.center.y - (py - this.height / 2) / this.hexSize,
    ];
  }

  hexAt(px, py) {
    return worldToHex(...this.screenToWorld(px, py));
  }

  panBy(dxPixels, dyPixels) {
    this.center.x -= dxPixels / this.hexSize;
    this.center.y += dyPixels / this.hexSize;
    this.applyCamera();
  }

  // Changes the hex size while keeping the world point under the anchor pixel still.
  setHexSize(size, anchorX = this.width / 2, anchorY = this.height / 2) {
    const [worldX, worldY] = this.screenToWorld(anchorX, anchorY);
    this.hexSize = Math.min(MAX_HEX_SIZE, Math.max(MIN_HEX_SIZE, size));
    this.center.x = worldX - (anchorX - this.width / 2) / this.hexSize;
    this.center.y = worldY + (anchorY - this.height / 2) / this.hexSize;
    this.applyCamera();
    return this.hexSize;
  }

  // -- grid ---------------------------------------------------------------

  makeGrid() {
    const geometry = new THREE.BufferGeometry();
    const material = new THREE.LineBasicMaterial({ color: 0x3b5145, transparent: true, depthTest: false });
    const grid = new THREE.LineSegments(geometry, material);
    grid.frustumCulled = false;
    grid.renderOrder = ORDER.grid;
    this.scene.add(grid);
    return grid;
  }

  // Outlines exist only for the hexes around the view and are rebuilt when the
  // view leaves that area.
  updateGrid() {
    if (this.hexSize < GRID_HIDDEN_AT) {
      this.grid.visible = false;
      return;
    }
    this.grid.visible = true;
    this.grid.material.opacity = Math.min(
      1,
      (this.hexSize - GRID_HIDDEN_AT) / (GRID_SOLID_AT - GRID_HIDDEN_AT) + 0.15,
    );

    const halfWidth = this.width / 2 / this.hexSize;
    const halfHeight = this.height / 2 / this.hexSize;
    const view = {
      left: this.center.x - halfWidth,
      right: this.center.x + halfWidth,
      bottom: this.center.y - halfHeight,
      top: this.center.y + halfHeight,
    };
    const built = this.gridBounds;
    const covered =
      built &&
      view.left >= built.left &&
      view.right <= built.right &&
      view.bottom >= built.bottom &&
      view.top <= built.top;
    // After zooming far in, the old outlines cover much more than is needed.
    const oversized = built && (built.right - built.left) > halfWidth * 12;
    if (covered && !oversized) return;

    const bounds = {
      left: view.left - halfWidth * 0.5,
      right: view.right + halfWidth * 0.5,
      bottom: view.bottom - halfHeight * 0.5,
      top: view.top + halfHeight * 0.5,
    };
    this.buildGrid(bounds);
    this.gridBounds = bounds;
  }

  buildGrid(bounds) {
    const rMin = Math.floor(-bounds.top / 1.5) - 1;
    const rMax = Math.ceil(-bounds.bottom / 1.5) + 1;
    const columns = Math.ceil((bounds.right - bounds.left) / SQRT3) + 3;
    const needed = (rMax - rMin + 1) * columns * 18;
    if (!this.gridVertices || this.gridVertices.length < needed) {
      this.gridVertices = new Float32Array(needed);
      this.grid.geometry.dispose();
      this.grid.geometry = new THREE.BufferGeometry();
      this.grid.geometry.setAttribute("position", new THREE.BufferAttribute(this.gridVertices, 3));
    }
    const vertices = this.gridVertices;
    const halfWidth = SQRT3 / 2;
    let i = 0;
    const line = (x1, y1, x2, y2) => {
      vertices[i] = x1;
      vertices[i + 1] = y1;
      vertices[i + 3] = x2;
      vertices[i + 4] = y2;
      i += 6;
    };
    for (let r = rMin; r <= rMax; r++) {
      const qMin = Math.floor(bounds.left / SQRT3 - r / 2) - 1;
      for (let q = qMin; q < qMin + columns; q++) {
        const [x, y] = hexToWorld(q, r);
        // Three of the six edges; the neighbours draw the other three.
        line(x + halfWidth, y - 0.5, x + halfWidth, y + 0.5);
        line(x + halfWidth, y + 0.5, x, y + 1);
        line(x, y + 1, x - halfWidth, y + 0.5);
      }
    }
    this.grid.geometry.getAttribute("position").needsUpdate = true;
    this.grid.geometry.setDrawRange(0, i / 3);
  }

  // -- hover --------------------------------------------------------------

  makeHover() {
    const geometry = new THREE.CircleGeometry(0.94, 6).rotateZ(Math.PI / 6);
    const material = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.28, depthTest: false });
    const hover = new THREE.Mesh(geometry, material);
    hover.renderOrder = ORDER.hover;
    hover.visible = false;
    this.scene.add(hover);
    return hover;
  }

  setHover(hex, color) {
    this.hover.visible = hex !== null;
    if (hex === null) return;
    const [x, y] = hexToWorld(hex[0], hex[1]);
    this.hover.position.set(x, y, 0);
    this.hover.material.color.set(color);
  }

  // -- plants -------------------------------------------------------------

  plantColor(plantId) {
    let color = this.plantColors.get(plantId);
    if (!color) {
      // Golden-ratio hue steps keep neighbouring plant ids easy to tell apart.
      color = new THREE.Color().setHSL((plantId * 0.618034) % 1, 0.55, 0.52);
      this.plantColors.set(plantId, color);
    }
    return color;
  }

  setCells(cells) {
    const counts = { link: 0, segment: 0, root: 0, stump: 0 };
    for (const cell of cells.values()) {
      counts[cell.kind] += 1;
      if (cell.parent) counts.link += 1;
    }
    this.links.begin(counts.link);
    this.segments.begin(counts.segment);
    this.roots.begin(counts.root);
    this.stumps.begin(counts.stump);

    const dark = new THREE.Color();
    for (const cell of cells.values()) {
      const color = this.plantColor(cell.plant);
      const [x, y] = hexToWorld(cell.q, cell.r);
      if (cell.parent) {
        const [px, py] = hexToWorld(cell.parent[0], cell.parent[1]);
        this.links.put(x, y, Math.atan2(py - y, px - x), SQRT3, VINE_WIDTH, color);
      }
      if (cell.kind === "root") {
        this.roots.put(x, y, 0, 0.5, 0.5, dark.copy(color).multiplyScalar(0.6));
      } else if (cell.kind === "stump") {
        this.stumps.put(x, y, 0, 0.42, 0.42, STUMP_COLOR);
      } else {
        this.segments.put(x, y, 0, VINE_WIDTH / 2, VINE_WIDTH / 2, color);
      }
    }
    this.links.end();
    this.segments.end();
    this.roots.end();
    this.stumps.end();
  }

  setTips(tips) {
    const shown = new Map();
    for (const tip of tips) {
      const previous = this.shownProgress.get(tip.id);
      const sameCell = previous && previous.q === tip.q && previous.r === tip.r;
      shown.set(tip.id, { q: tip.q, r: tip.r, shown: sameCell ? previous.shown : 0 });
    }
    this.shownProgress = shown;
    this.tips = tips.map((tip) => ({
      ...tip,
      target: tip.blocked ? 0 : Math.min(1, parseFraction(tip.progress)),
    }));
  }

  // Tips reach toward their next hex in proportion to their progress, easing
  // toward each newly reported value so slow plants creep instead of jumping.
  drawTips(dt) {
    const ease = 1 - Math.exp(-dt * 10);
    const light = new THREE.Color();
    this.tipStrips.begin(this.tips.length);
    this.tipHeads.begin(this.tips.length);
    for (const tip of this.tips) {
      const entry = this.shownProgress.get(tip.id);
      entry.shown += (tip.target - entry.shown) * ease;
      const [x, y] = hexToWorld(tip.q, tip.r);
      if (tip.blocked) {
        this.tipHeads.put(x, y, 0, 0.2, 0.2, BLOCKED_TIP_COLOR);
        continue;
      }
      const [dq, dr] = DIRECTIONS[tip.heading];
      const [nx, ny] = hexToWorld(tip.q + dq, tip.r + dr);
      const color = light.copy(this.plantColor(tip.plant)).lerp(WHITE, 0.45);
      const reach = entry.shown;
      if (reach > 0.001) {
        this.tipStrips.put(x, y, Math.atan2(ny - y, nx - x), SQRT3 * reach, VINE_WIDTH * 0.8, color);
      }
      this.tipHeads.put(x + (nx - x) * reach, y + (ny - y) * reach, 0, 0.22, 0.22, color);
    }
    this.tipStrips.end();
    this.tipHeads.end();
  }
}
