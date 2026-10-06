// Axial hex coordinates for a pointy-top grid. Mirrors backend/plantastic/sim/hex.py:
// directions are indexed 0 to 5 clockwise as seen on screen, starting at east.

export const DIRECTIONS = [
  [1, 0],   // 0 east
  [0, 1],   // 1 south-east
  [-1, 1],  // 2 south-west
  [-1, 0],  // 3 west
  [0, -1],  // 4 north-west
  [1, -1],  // 5 north-east
];

export const SQRT3 = Math.sqrt(3);

export function neighbor(q, r, direction) {
  const [dq, dr] = DIRECTIONS[((direction % 6) + 6) % 6];
  return [q + dq, r + dr];
}

export function hexKey(q, r) {
  return `${q},${r}`;
}

// World space has one unit equal to the hex's corner radius, with y pointing
// up, so a larger r is lower on screen.
export function hexToWorld(q, r) {
  return [SQRT3 * (q + r / 2), -1.5 * r];
}

export function worldToHex(x, y) {
  const fr = -y / 1.5;
  const fq = x / SQRT3 - fr / 2;
  return roundHex(fq, fr);
}

function roundHex(fq, fr) {
  const fs = -fq - fr;
  let q = Math.round(fq);
  let r = Math.round(fr);
  const s = Math.round(fs);
  const dq = Math.abs(q - fq);
  const dr = Math.abs(r - fr);
  const ds = Math.abs(s - fs);
  if (dq > dr && dq > ds) {
    q = -r - s;
  } else if (dr > ds) {
    r = -q - s;
  }
  // Adding 0 turns -0 into 0.
  return [q + 0, r + 0];
}

export function hexDistance(q1, r1, q2, r2) {
  const dq = q2 - q1;
  const dr = r2 - r1;
  return (Math.abs(dq) + Math.abs(dr) + Math.abs(dq + dr)) / 2;
}

// Every hex on the straight line from one hex to another, both included.
// Consecutive hexes are always neighbours, so a stroke drawn with it has no gaps.
export function hexLine([q1, r1], [q2, r2]) {
  const steps = hexDistance(q1, r1, q2, r2);
  const line = [];
  for (let i = 0; i <= steps; i++) {
    const t = steps === 0 ? 0 : i / steps;
    // The tiny offsets settle points that fall exactly on an edge.
    line.push(roundHex(q1 + (q2 - q1) * t + 1e-6, r1 + (r2 - r1) * t + 2e-6));
  }
  return line;
}

const LINE_SAMPLES = [
  [[0, 0], [0, 0]],
  [[0, 0], [5, 0]],
  [[-3, 2], [4, -6]],
  [[2, 2], [-7, 3]],
  [[1, -8], [1, 9]],
  [[0, 0], [6, -3]],
];

// Returns a list of problems; empty means the conversions agree.
export function selfCheck() {
  const problems = [];
  for (const [from, to] of LINE_SAMPLES) {
    const line = hexLine(from, to);
    const ends = String(line[0]) === String(from) && String(line.at(-1)) === String(to);
    const length = line.length === hexDistance(...from, ...to) + 1;
    const connected = line.every((hex, i) => i === 0 || hexDistance(...line[i - 1], ...hex) === 1);
    if (!ends || !length || !connected) problems.push(`hexLine ${from} -> ${to} gave ${line.join(" ")}`);
  }
  for (let q = -6; q <= 6; q++) {
    for (let r = -6; r <= 6; r++) {
      const [x, y] = hexToWorld(q, r);
      // The centre and points most of the way toward each neighbour stay in the hex.
      const samples = [[x, y]];
      for (let d = 0; d < 6; d++) {
        const [nq, nr] = neighbor(q, r, d);
        const [nx, ny] = hexToWorld(nq, nr);
        samples.push([x + (nx - x) * 0.45, y + (ny - y) * 0.45]);
      }
      for (const [sx, sy] of samples) {
        const [hq, hr] = worldToHex(sx, sy);
        if (hq !== q || hr !== r) {
          problems.push(`(${sx}, ${sy}) gave ${hq},${hr}, expected ${q},${r}`);
        }
      }
    }
  }
  const [ex] = hexToWorld(...neighbor(0, 0, 0));
  const [, sey] = hexToWorld(...neighbor(0, 0, 1));
  if (!(ex > 0)) problems.push("direction 0 is not east");
  if (!(sey < 0)) problems.push("direction 1 is not below the origin");
  return problems;
}
