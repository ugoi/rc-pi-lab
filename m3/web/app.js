const $ = (s) => document.querySelector(s),
  canvas = $("#view"),
  ctx = canvas.getContext("2d");
let state = {},
  epoch = null,
  seq = 0,
  client = crypto.randomUUID(),
  az = -0.8,
  el = 0.65,
  zoom = 320,
  drag = null,
  busy = false;
async function command(op) {
  if (!epoch) return;
  const ticket =
    op === "drive"
      ? state.ticket
      : (await (await fetch("/state")).json()).ticket;
  let c = {
    epoch,
    client,
    ticket,
    sent_unix_ms: Date.now(),
    seq: ++seq,
    op,
    steer: +$("#steer").value / 100,
    throttle: +$("#throttle").value / 100,
  };
  let r = await fetch("/command", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(c),
  });
  if (!r.ok) {
    $("#reason").textContent = (await r.json()).error;
  }
}
function neutral() {
  $("#throttle").value = 0;
  $("#steer").value = 0;
  labels();
}
function labels() {
  $("#tv").textContent = $("#throttle").value + " %";
  $("#sv").textContent = $("#steer").value + " %";
}
$("#arm").onclick = () => {
  neutral();
  command("arm");
};
$("#stop").onclick = () => {
  neutral();
  command("stop");
};
$("#center").onclick = () => {
  $("#steer").value = 0;
  labels();
};
for (let id of ["throttle", "steer"]) $("#" + id).oninput = labels;
window.onkeydown = (e) => {
  if (e.code === "Space") {
    e.preventDefault();
    neutral();
    command("stop");
  }
};
document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    neutral();
    command("stop");
  }
});
setInterval(async () => {
  if (busy) return;
  busy = true;
  try {
    let r = await fetch("/state");
    state = await r.json();
    if (epoch !== state.epoch) {
      epoch = state.epoch;
      seq = 0;
      neutral();
    }
    $("#status").textContent =
      state.telemetry_age_s > 0.5 ? "PHYSIK NICHT AKTUELL" : state.mode;
    $("#reason").textContent = state.reason;
    const t = state.telemetry || {};
    $("#metrics").textContent =
      `Geschwindigkeit: ${(t.speed_m_s || 0).toFixed(3)} m/s\nSimulationsfaktor: ${(t.factor || 0).toFixed(2)} ×\nSimzeit: ${(t.sim_s || 0).toFixed(2)} s\nPWM seq: ${state.pwm?.seq || 0}\nGast ACK: ${state.ack?.seq || 0}\nKontakte: ${t.contact_count || 0}`;
    if (!document.hidden) await command("drive");
  } catch (e) {
    $("#status").textContent = "VERBINDUNG UNTERBROCHEN";
    neutral();
  } finally {
    busy = false;
  }
}, 150);
canvas.onpointerdown = (e) => {
  drag = [e.clientX, e.clientY];
  canvas.setPointerCapture(e.pointerId);
};
canvas.onpointerup = () => (drag = null);
canvas.onpointermove = (e) => {
  if (drag) {
    az += (e.clientX - drag[0]) * 0.007;
    el = Math.max(0.15, Math.min(1.4, el + (e.clientY - drag[1]) * 0.007));
    drag = [e.clientX, e.clientY];
  }
};
canvas.onwheel = (e) => {
  e.preventDefault();
  zoom = Math.max(60, Math.min(600, zoom * Math.exp(-e.deltaY * 0.001)));
};
function render() {
  canvas.width = canvas.clientWidth * devicePixelRatio;
  canvas.height = canvas.clientHeight * devicePixelRatio;
  ctx.scale(devicePixelRatio, devicePixelRatio);
  let w = canvas.clientWidth,
    h = canvas.clientHeight,
    t = state.telemetry || {},
    car = t.position || [0, 0, 0.15];
  function proj(v) {
    let x = v[0] - car[0],
      y = v[1] - car[1],
      z = v[2];
    let a = Math.cos(az) * x - Math.sin(az) * y,
      b = Math.sin(az) * x + Math.cos(az) * y;
    return [
      w / 2 + a * zoom,
      h * 0.57 + (b * Math.sin(el) - z * Math.cos(el)) * zoom,
      b * Math.cos(el) + z * Math.sin(el),
    ];
  }
  ctx.strokeStyle = "#344957";
  ctx.lineWidth = 1;
  for (let i = -10; i <= 10; i++) {
    for (let pair of [
      [
        [i, -10, 0],
        [i, 10, 0],
      ],
      [
        [-10, i, 0],
        [10, i, 0],
      ],
    ]) {
      let a = proj(pair[0]),
        b = proj(pair[1]);
      ctx.beginPath();
      ctx.moveTo(...a.slice(0, 2));
      ctx.lineTo(...b.slice(0, 2));
      ctx.stroke();
    }
  }
  let faces = [];
  function box(pos, size, rot, color) {
    let vertices = [];
    for (let z of [-1, 1])
      for (let y of [-1, 1])
        for (let x of [-1, 1]) {
          let v = [(x * size[0]) / 2, (y * size[1]) / 2, (z * size[2]) / 2],
            r = rot || [1, 0, 0, 0, 1, 0, 0, 0, 1];
          vertices.push(
            proj([
              pos[0] + r[0] * v[0] + r[1] * v[1] + r[2] * v[2],
              pos[1] + r[3] * v[0] + r[4] * v[1] + r[5] * v[2],
              pos[2] + r[6] * v[0] + r[7] * v[1] + r[8] * v[2],
            ]),
          );
        }
    for (let ids of [
      [0, 1, 3, 2],
      [4, 5, 7, 6],
      [0, 1, 5, 4],
      [2, 3, 7, 6],
      [0, 2, 6, 4],
      [1, 3, 7, 5],
    ])
      faces.push({ pts: ids.map((i) => vertices[i]), color });
  }
  function cylinder(pos, rot) {
    let rings = [[], []];
    for (let side = 0; side < 2; side++)
      for (let i = 0; i < 20; i++) {
        let angle = (i * 2 * Math.PI) / 20,
          v = [
            state.parameters.wheel_radius_m * Math.cos(angle),
            state.parameters.wheel_radius_m * Math.sin(angle),
            (side - 0.5) * state.parameters.wheel_width_m,
          ],
          r = rot;
        rings[side].push(
          proj([
            pos[0] + r[0] * v[0] + r[1] * v[1] + r[2] * v[2],
            pos[1] + r[3] * v[0] + r[4] * v[1] + r[5] * v[2],
            pos[2] + r[6] * v[0] + r[7] * v[1] + r[8] * v[2],
          ]),
        );
      }
    for (let ring of rings) faces.push({ pts: ring, color: "#33414c" });
    for (let i = 0; i < 20; i++) {
      let j = (i + 1) % 20;
      faces.push({
        pts: [rings[0][i], rings[0][j], rings[1][j], rings[1][i]],
        color: i % 2 ? "#171e27" : "#25313b",
      });
    }
  }
  box([1.8, 0, 0.1], [0.3, 1.2, 0.2], null, "#ba682a");
  if (state.parameters) {
    const p = state.parameters;
    box(car, [p.chassis_length_m, p.chassis_width_m, p.chassis_height_m], t.orientation, "#249ac8");
  }
  for (let wheel of t.wheels || []) cylinder(wheel.position, wheel.orientation);
  faces.sort(
    (a, b) =>
      a.pts.reduce((s, v) => s + v[2], 0) / a.pts.length -
      b.pts.reduce((s, v) => s + v[2], 0) / b.pts.length,
  );
  for (let f of faces) {
    ctx.beginPath();
    f.pts.forEach((v, i) =>
      i ? ctx.lineTo(v[0], v[1]) : ctx.moveTo(v[0], v[1]),
    );
    ctx.closePath();
    ctx.fillStyle = f.color;
    ctx.fill();
    ctx.strokeStyle = "#a2c5d544";
    ctx.stroke();
  }
  ctx.fillStyle = "#b7d0df";
  ctx.fillText(
    "LIVE · Physikposition aus Webots · Ansicht frei drehbar",
    18,
    26,
  );
  requestAnimationFrame(render);
}
render();
