// Camera angle View.js

import {
    app
} from "../../../scripts/app.js";

let presets = {
    Target: [{
        name: "Human"
    }, {
        name: "Product"
    }, {
        name: "Place"
    }],
    Angle: [{
        name: "Custom",
        min_angle: "-",
        max_angle: "-",
        min: "-",
        max: "-"
    }],
    "360Angle": [{
        name: "Custom",
        min_angle: "-",
        max_angle: "-",
        min: "-",
        max: ""
    }],
    AOV: [{
        name: "None",
        min: "-",
        max: "-"
    }],
    APT: [{
        name: "None",
        min: "-",
        max: "-"
    }]
};
try {
    const response = await fetch(new URL("./presets.json", import.meta.url));
    if (response.ok) presets = await response.json();
} catch (e) {
    console.warn("Camera Angle View: presets.json fallback active", e);
}
const defaults = {
    Target: "Human",
    Angle: "Custom",
    "360Angle": "Custom",
    AOV: "인물 스냅",
    APT: "중간 개방",
    height: 100,
    angle: 0,
    azimuth: 0,
    focal: 50,
    aperture: 6,
    distance: "1.0",
    language: "en",
    profile: "krea2",
    roll: 0,
    blur: false
};
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const trunc = v => Math.trunc(Number(v)) || 0;
const round = v => Math.round(v * 100) / 100;
const azimuth = v => ((trunc(v) % 360) + 360) % 360;
const rad = v => v * Math.PI / 180;
const limits = {
    height: [0, 100000],
    angle: [-90, 90],
    azimuth: [0, 359],
    focal: [1, 5000],
    aperture: [0.1, 128],
    roll: [-30, 30]
};

function normalizeDistance(value) {
    const s = String(value).trim();
    if (!/^(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)$/.test(s)) throw new Error("Invalid distance");
    const [whole = "", fraction = ""] = s.split(".");
    let tenths = BigInt(whole || "0") * 10n + BigInt(fraction[0] || "0");
    if ((fraction[1] || "0") >= "5") tenths += 1n;
    if (tenths <= 0n) throw new Error("Distance must round to at least 0.1 m");
    return `${tenths/10n}.${tenths%10n}`;
}

function validDistance(value) {
    try {
        normalizeDistance(value);
        return true;
    } catch {
        return false;
    }
}

function heightFromDistance(value) {
    const [whole, fraction] = normalizeDistance(value).split(".");
    const cm = BigInt(whole) * 100n + BigInt(fraction) * 10n;
    return cm <= BigInt(Number.MAX_SAFE_INTEGER) ? Number(cm) : cm.toString();
}

function distanceVisual(value) {
    const n = Number(value);
    return {
        clamped: Math.max(0.1, Math.min(10, n)),
        outside: n < 0.1 || n > 10
    };
}

function distanceFromX(x, near, far) {
    const raw = 0.1 + clamp((near - x) / (near - far), 0, 1) * 9.9;
    return Math.max(0.1, Math.min(10, Math.round(raw))).toFixed(1);
}

function normalizeLanguage(v) {
    v = String(v ?? "").trim().toLowerCase().replaceAll("_", "-");
    return ["ko", "kor", "korean", "한국어"].includes(v) || v.startsWith("ko-") ? "ko" : "en";
}

function detectLanguage() {
    let v;
    try {
        v = app.extensionManager?.setting?.get?.("Comfy.Locale");
    } catch {}
    if (!v) {
        try {
            v = app.ui?.settings?.getSettingValue?.("Comfy.Locale");
        } catch {}
    }
    if (["", "auto", "default", "system", "auto-detect", "auto-detect browser language"].includes(String(v ?? "").trim().toLowerCase())) v = navigator.language || navigator.languages?.[0] || "en";
    return normalizeLanguage(v);
}
const words = {
    ko: {
        labels: {
            Target: "피사체 유형 - Target",
            Angle: "카메라 앵글 - Angle",
            "360Angle": "360° 앵글 - 360Angle",
            AOV: "렌즈 초점거리 - Angle Of View",
            APT: "조리개 - Aperture"
        },
        fields: {
            height: "카메라 높이 (cm)",
            angle: "카메라 앵글 (°)",
            azimuth: "360° 앵글 (°)",
            focal: "렌즈 초점거리 (mm)",
            aperture: "조리개 (f/)"
        },
        side: "측면 보기 - SIDE VIEW",
        top: "상단 보기 - TOP VIEW",
        custom: "사용자 설정",
        manual: "직접 설정",
        output: "촬영 구도",
        front: "정면 · 0°",
        back: "후면 · 180°",
        distance: "피사체와의 거리 (m)",
        distanceTitle: "거리 - Distance",
        rollTitle: "더치 앵글 - Roll",
        blurLabel: "배경 흐림 (Blur)",
        drag: "드래그 0.1–10.0 m · 1m 단위",
        outside: "드래그 범위 밖 · 수동값 유지",
        invalid: "단위 없이 0.1m로 반올림 가능한 양수를 입력하세요. 소수 첫째 자리로 확정됩니다. 예: 1.4, 12.3",
        near: "가까움",
        far: "멀리",
        subject: "피사체",
        options: {
            Human: "인물",
            Product: "제품",
            Place: "장소",
            Custom: "직접 설정",
            None: "지정 안 함",
            "Bird's-eye-View": "조감 앵글",
            "High Angle": "하이 앵글",
            "Slight High Angle": "약한 하이 앵글",
            "Eye Level": "아이 레벨",
            "Slight Low Angle": "약한 로우 앵글",
            "Low Angle": "로우 앵글",
            "Worm's-eye-View": "웜스아이 앵글",
            Front: "정면",
            "Front-Right": "우측 전방",
            Right: "우측",
            "Rear-Right": "우측 후방",
            Back: "후면",
            "Rear-Left": "좌측 후방",
            Left: "좌측",
            "Front-Left": "좌측 전방"
        }
    },
    en: {
        labels: {
            Target: "Subject Type - Target",
            Angle: "Camera Angle - Angle",
            "360Angle": "360° Angle - 360Angle",
            AOV: "Lens Focal Length - Angle Of View",
            APT: "Aperture"
        },
        fields: {
            height: "Camera Height (cm)",
            angle: "Camera Angle (degrees)",
            azimuth: "360 Angle (degrees)",
            focal: "Lens Focal Length (mm)",
            aperture: "Aperture (f/)"
        },
        side: "SIDE VIEW",
        top: "TOP VIEW - 360 Angle",
        custom: "Customizing",
        manual: "Custom value",
        output: "Camera Composition",
        front: "FRONT · 0°",
        back: "BACK · 180°",
        distance: "Subject Distance (m)",
        distanceTitle: "Distance",
        rollTitle: "Dutch Angle - Roll",
        blurLabel: "Background Blur",
        drag: "Drag 0.1–10.0 m · 1m steps",
        outside: "Outside drag range · manual value kept",
        invalid: "Enter a positive decimal rounding to at least 0.1m; stored to one decimal place, e.g. 1.4 or 12.3.",
        near: "Near",
        far: "Far",
        subject: "Subject",
        options: {
            "광각 스냅": "Wide-angle Snapshot",
            "인물 스냅": "Portrait Snapshot",
            "초광각": "Ultra-wide Angle",
            "망원": "Telephoto",
            "초망원": "Super-telephoto",
            "최대 개방": "Wide Open",
            "중간 개방": "Moderate Aperture",
            "조리개 조임": "Stopped Down",
            Custom: "Custom",
            None: "None"
        }
    }
};

const descriptionsEN = {
    None: "Use prompt settings.",
    "광각 스냅": "Snapshots, documentary and landscapes.",
    "인물 스냅": "Natural rendering for portraits and everyday snapshots.",
    "초광각": "Wide spaces and dramatic perspective for landscapes and architecture.",
    "망원": "Emphasize subjects for portraits and performances.",
    "초망원": "Distant subjects, wildlife and sports.",
    "최대 개방": "Night scenes, portraits and interiors.",
    "중간 개방": "General-purpose snapshots, still life, portraits and landscapes.",
    "조리개 조임": "Landscapes and starburst light effects."
};

function numeric(text, base) {
    if (!text || text === "-") return null;
    if (text.includes("(A)")) {
        const m = text.match(/\(A\)\s*([+-])\s*([\d.]+)/);
        return m ? base + (m[1] === "+" ? 1 : -1) * Number(m[2]) : base;
    }
    return Number(text.replace("15°'-", "-15").replace(/[^\d.+-]/g, ""));
}

function midpoint(a, b, base) {
    const x = numeric(a, base),
        y = numeric(b, base);
    return x == null ? y : y == null ? x : (x + y) / 2;
}

function geometry(canvas) {
    const w = canvas.width,
        h = canvas.height;
    return {
        w,
        h,
        cx: w / 2,
        cy: h / 2,
        r: Math.max(20, Math.min(w, h) / 2 - 44)
    };
}

function css(el, s) {
    Object.assign(el.style, s);
    return el;
}

app.registerExtension({
    name: "Sia.CameraAngleView",
    getCustomWidgets() {
        return {
            CAV_STATE(node, name, inputData) {
                const widget = node.addCustomWidget({
                    name,
                    type: "CAV_STATE",
                    value: inputData[1]?.default ?? JSON.stringify(defaults),
                    options: {
                        serialize: true
                    },
                    computeSize: () => [0, 0],
                    draw() {}
                });
                return {
                    widget
                };
            }
        };
    },
    nodeCreated(node) {
        if (node.comfyClass !== "CameraAngleView") return;
        const widget = node.widgets.find(w => w.name === "camera_state");
        if (!widget) return;
        const lang = detectLanguage(),
            t = words[lang];
        let state = {
            ...defaults,
            language: lang
        };
        const controls = {},
            descs = {},
            views = [];
        node.color = "#2C2C2C";
        node.bgcolor = "#2C2C2C";

        const host = document.createElement("div");
        host.dataset.cavUiVersion = "060";
        host.style.cssText = "width:100%;height:100%;box-sizing:border-box;background:#2C2C2C;color:#111;padding:12px;font:12px Arial,sans-serif;overflow:visible;";
        host.addEventListener("pointerdown", e => e.stopPropagation());
        host.addEventListener("wheel", e => e.stopPropagation());
        const outer = document.createElement("div");
        outer.style.cssText = "display:grid;grid-template-rows:minmax(0,1fr) 112px 28px;gap:10px;width:100%;height:100%;min-height:0;";
        host.append(outer);
        const upper = document.createElement("div");
        upper.style.cssText = "display:grid;grid-template-columns:minmax(0,1.88fr) minmax(0,1fr);gap:10px;min-height:0;";
        outer.append(upper);
        const left = document.createElement("div");
        left.style.cssText = "display:grid;grid-template-rows:minmax(0,1fr) minmax(0,1fr);gap:18px;min-height:0;";
        upper.append(left);
        const right = document.createElement("div");
        right.style.cssText = "display:flex;flex-direction:column;gap:8px;min-width:0;background:#f5f5f5;border:1px solid #aaa;padding:6px;box-sizing:border-box;";
        upper.append(right);

        function panel(parent, title) {
            const box = document.createElement("div");
            box.style.cssText = "display:flex;flex-direction:column;min-width:0;min-height:0;background:white;border:2px solid #139fca;box-sizing:border-box;overflow:hidden;";
            const heading = document.createElement("div");
            heading.textContent = title;
            heading.style.cssText = "background:#139fca;color:white;font:bold 13px Arial,sans-serif;height:30px;flex:0 0 30px;box-sizing:border-box;padding:6px 9px;white-space:nowrap;";
            const canvas = document.createElement("canvas");
            canvas.width = 350;
            canvas.height = 300;
            canvas.style.cssText = "display:block;width:100%;height:0;flex:1 1 0;min-height:0;background:white;touch-action:none;cursor:crosshair;";
            box.append(heading, canvas);
            parent.append(box);
            return canvas;
        }
        views.push(panel(left, t.side), panel(left, t.top));
        const bottomRow = document.createElement("div");
        bottomRow.style.cssText = "display:grid;grid-template-columns:1fr 1fr;gap:10px;min-height:0;";
        outer.append(bottomRow);
        const distanceCanvas = panel(bottomRow, t.distanceTitle);
        const rollCanvas = panel(bottomRow, t.rollTitle);
        const profileBar = document.createElement("div");
        profileBar.style.cssText = "display:flex;align-items:center;justify-content:flex-end;gap:6px;";
        const profileBtns = {};
        for (const [pKey, pLabel] of [
                ["krea2", "Krea2"],
                ["standard", "SD / ZTB / Qwen"]
            ]) {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.textContent = pLabel;
            btn.style.cssText = "height:24px;padding:0 10px;font:bold 11px Arial,sans-serif;border:1px solid #139fca;border-radius:3px;cursor:pointer;";
            btn.onpointerdown = e => e.stopPropagation();
            btn.onclick = () => {
                state.profile = pKey;
                commit();
            };
            profileBar.append(btn);
            profileBtns[pKey] = btn;
        }
        outer.append(profileBar);

        const blurWrap = document.createElement("div");
        blurWrap.style.cssText = "margin-top:auto;padding-top:8px;border-top:1px solid #ddd;display:flex;align-items:center;justify-content:center;order:99;";
        const blurBtn = document.createElement("button");
        blurBtn.type = "button";
        blurBtn.style.cssText = "width:100%;height:30px;padding:0 10px;font:bold 11px Arial,sans-serif;border:1.5px solid #111;border-radius:6px;cursor:pointer;background:#777;color:#fff;display:flex;align-items:center;justify-content:space-between;gap:8px;";
        const blurText = document.createElement("span");
        blurText.textContent = t.blurLabel;
        blurText.style.cssText = "flex:1;text-align:center;line-height:1.1;";
        const blurLed = document.createElement("span");
        blurLed.style.cssText = "width:16px;height:16px;border-radius:50%;border:2px solid #fff;background:#e50000;flex-shrink:0;box-sizing:border-box;";
        blurBtn.append(blurText, blurLed);
        blurBtn.onpointerdown = e => e.stopPropagation();
        blurBtn.onclick = e => {
            e.stopPropagation();
            state.blur = !state.blur;
            blurLed.style.background = state.blur ? "#2ee645" : "#e50000";
            commit();
        };
        blurWrap.append(blurBtn);
        right.append(blurWrap);

        function field(parent, label, key, values) {
            const wrap = document.createElement("label");
            wrap.style.cssText = "display:flex;flex-direction:column;gap:3px;min-width:0;";
            const cap = document.createElement("span");
            cap.textContent = label;
            cap.style.cssText = "font-size:10px;font-weight:bold;line-height:12px;overflow-wrap:anywhere;";
            const input = document.createElement(values ? "select" : "input");
            input.style.cssText = "box-sizing:border-box;width:100%;min-width:0;height:24px;min-height:24px;background:white;color:#333;border:1px solid #bbb;padding:1px 3px;font:12px Arial,sans-serif;text-align:center;text-align-last:center;";
            if (values) {
                for (const value of values) {
                    const op = document.createElement("option");
                    op.value = value;
                    op.textContent = t.options[value] ?? value;
                    op.style.textAlign = "center";
                    input.append(op);
                }
            } else if (key === "distance") {
                input.type = "text";
                input.inputMode = "decimal";
                input.autocomplete = "off";
                input.spellcheck = false;
            } else {
                input.type = "number";
                input.step = ["angle", "azimuth"].includes(key) ? "1" : "0.01";
                [input.min, input.max] = limits[key];
            }
            wrap.append(cap, input);
            parent.append(wrap);
            controls[key] = input;
            return {
                wrap,
                input
            };
        }
        const presetPanel = document.createElement("div");
        presetPanel.style.cssText = "display:flex;flex-direction:column;gap:6px;";
        right.append(presetPanel);
        for (const key of ["Target", "Angle", "360Angle", "AOV", "APT"]) {
            const choices = presets[key].map(p => p.name);
            if (["AOV", "APT"].includes(key)) choices.push("Custom");
            const {
                wrap,
                input
            } = field(presetPanel, t.labels[key], key, choices);
            if (["AOV", "APT"].includes(key)) {
                const d = document.createElement("div");
                d.style.cssText = "font-size:10px;line-height:11px;max-height:22px;display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;overflow:hidden;overflow-wrap:anywhere;color:#555;";
                wrap.append(d);
                descs[key] = d;
            }
            input.onchange = () => {
                state[key] = input.value;
                if (key === "Target") {
                    state.height = base();
                    if (state.Angle !== "Custom") applyPreset("Angle");
                } else applyPreset(key);
                commit();
            };
        }
        const custom = document.createElement("div");
        custom.style.cssText = "display:flex;flex-direction:column;gap:7px;border-top:1px solid #c6a68f;padding-top:8px;";
        right.append(custom);
        const customTitle = document.createElement("div");
        customTitle.textContent = t.custom;
        customTitle.style.cssText = "font-weight:bold;font-size:11px;line-height:14px;";
        custom.append(customTitle);
        for (const [key, label] of Object.entries(t.fields)) {
            const {
                input
            } = field(custom, label, key);
            input.onchange = () => {
                const n = Number(input.value);
                if (input.value === "" || !Number.isFinite(n)) {
                    sync();
                    return;
                }
                state[key] = key === "angle" ? clamp(trunc(n), -90, 90) : key === "azimuth" ? azimuth(n) : round(clamp(n, ...limits[key]));
                if (["height", "angle"].includes(key)) state.Angle = "Custom";
                if (key === "azimuth") state["360Angle"] = "Custom";
                if (key === "focal") state.AOV = "Custom";
                if (key === "aperture") state.APT = "Custom";
                commit();
            };
        }

        const {
            input: distanceInput
        } = field(custom, t.distance, "distance");
        distanceInput.title = t.invalid;
        distanceInput.oninput = () => {
            const valid = validDistance(distanceInput.value);
            distanceInput.setCustomValidity(valid ? "" : t.invalid);
            distanceInput.style.borderColor = valid ? "#bbb" : "#c22";
        };

        function finishDistance() {
            if (!validDistance(distanceInput.value)) {
                distanceInput.setCustomValidity(t.invalid);
                distanceInput.reportValidity();
                return;
            }
            state.distance = normalizeDistance(distanceInput.value);
            distanceInput.value = state.distance;
            distanceInput.setCustomValidity("");
            distanceInput.style.borderColor = "#bbb";
            commit();
        }
        distanceInput.onchange = finishDistance;
        distanceInput.onblur = () => {
            if (validDistance(distanceInput.value)) finishDistance();
        };
        controls.height.readOnly = true;
        controls.height.style.background = "#e9e9e9";
        controls.height.title = lang === "ko" ? "피사체와의 거리에서 자동 계산됩니다. m × 100 = cm" : "Calculated from subject distance: m × 100 = cm";

        function base() {
            return state.Target === "Product" ? 20 : 190;
        }

        function applyPreset(key) {
            const p = presets[key]?.find(p => p.name === state[key]);
            if (!p || ["Custom", "None"].includes(state[key])) return;
            if (key === "Angle") {
                state.angle = clamp(trunc(midpoint(p.min_angle, p.max_angle, base())), -90, 90);
                state.height = round(Math.max(0, midpoint(p.min, p.max, base())));
            }
            if (key === "360Angle") state.azimuth = azimuth(numeric(p.min, base()));
            if (key === "AOV") state.focal = round(midpoint(p.min, p.max, base()));
            if (key === "APT") state.aperture = round(midpoint(p.min, p.max, base()));
        }

        function sync() {
            for (const [key, input] of Object.entries(controls)) {
                if (key === "distance" && document.activeElement === input) continue;
                input.value = state[key];
            }
            for (const key of ["AOV", "APT"]) {
                const p = presets[key].find(p => p.name === state[key]);
                const text = lang === "ko" ? (p?.description || t.manual) : (descriptionsEN[state[key]] || t.manual);
                descs[key].textContent = text;
                descs[key].title = text;
            }
            draw();
        }

        function enforceDistance() {
            state.distance = normalizeDistance(state.distance);
            state.height = heightFromDistance(state.distance);
        }

        function commit() {
            enforceDistance();
            state.angle = clamp(trunc(state.angle), -90, 90);
            state.azimuth = azimuth(state.azimuth);
            state.language = lang;
            widget.value = JSON.stringify(state);
            sync();
            node.graph?.change?.();
            node.setDirtyCanvas(true, true);
        }

        widget.serializeValue = () => {
            const value = distanceInput.value.trim();
            if (!validDistance(value)) throw new Error(`Camera Angle View: ${t.invalid}`);
            state.distance = normalizeDistance(value);
            enforceDistance();
            distanceInput.value = state.distance;
            state.language = lang;
            widget.value = JSON.stringify(state);
            sync();
            return widget.value;
        };

        function drawSubject(ctx, x, y, scale = 1) {
            ctx.save();
            ctx.translate(x, y);
            ctx.scale(scale, scale);
            ctx.fillStyle = "#111";
            if (state.Target === "Human") {
                ctx.translate(0, -4);
                ctx.beginPath();
                ctx.arc(0, -25, 8, 0, Math.PI * 2);
                ctx.fill();
                ctx.fillRect(-8, -14, 16, 31);
                ctx.fillRect(-8, 17, 6, 24);
                ctx.fillRect(2, 17, 6, 24);
                ctx.fillRect(-15, -11, 7, 27);
                ctx.fillRect(8, -11, 7, 27);
            } else if (state.Target === "Product") {
                ctx.beginPath();
                ctx.ellipse(-6, 0, 11, 17, -0.2, 0, Math.PI * 2);
                ctx.ellipse(6, 0, 11, 17, 0.2, 0, Math.PI * 2);
                ctx.fill();
                ctx.fillRect(-1, -27, 3, 12);
            } else {
                ctx.fillStyle = "#b93232";
                ctx.fillRect(-4, -42, 8, 84);
            }
            ctx.restore();
        }

        function drawCamera(ctx, x, y, cx, cy, scale = 1) {
            ctx.strokeStyle = "#7596a3";
            ctx.setLineDash([3, 5]);
            ctx.beginPath();
            ctx.moveTo(x, y);
            ctx.lineTo(cx, cy);
            ctx.stroke();
            ctx.setLineDash([]);

            ctx.save();
            ctx.translate(x, y);
            ctx.rotate(Math.atan2(cy - y, cx - x));
            ctx.scale(scale, scale);
            ctx.fillStyle = "#206c80";
            ctx.fillRect(-13, -9, 23, 18);
            ctx.beginPath();
            ctx.moveTo(10, -6);
            ctx.lineTo(18, 0);
            ctx.lineTo(10, 6);
            ctx.closePath();
            ctx.fill();
            ctx.restore();
            for (const [pKey, btn] of Object.entries(profileBtns)) {
                const active = (state.profile || "krea2") === pKey;
                btn.style.background = active ? "#139fca" : "#e0e0e0";
                btn.style.color = active ? "#fff" : "#333";
                btn.style.borderColor = active ? "#0d7ea1" : "#aaa";
            }
        }

        function fit(canvas) {
            const w = canvas.clientWidth,
                h = canvas.clientHeight;
            if (w > 0 && h > 0) {
                if (canvas.width !== w) canvas.width = w;
                if (canvas.height !== h) canvas.height = h;
                return true;
            }
            return false;
        }

        function distanceGeometry() {
            const w = distanceCanvas.width,
                h = distanceCanvas.height;
            const subject = w - 116,
                far = 28,
                near = subject - 34;
            return {
                w,
                h,
                subject,
                far,
                near,
                y: h / 2 - 2
            };
        }

        function drawRoll() {
            const canvas = rollCanvas;
            if (!fit(canvas)) return;
            const ctx = canvas.getContext("2d"),
                w = canvas.width,
                h = canvas.height,
                cx = w / 2 - 8,
                cy = h / 2 - 4;
            const roll = clamp(trunc(state.roll ?? 0), -30, 30);
            ctx.fillStyle = "white";
            ctx.fillRect(0, 0, w, h);
            ctx.save();
            ctx.translate(cx, cy);
            ctx.rotate(rad(roll));
            ctx.strokeStyle = "#206c80";
            ctx.lineWidth = 1.5;
            ctx.setLineDash([4, 3]);
            ctx.beginPath();
            ctx.moveTo(-38, 0);
            ctx.lineTo(38, 0);
            ctx.stroke();
            ctx.setLineDash([]);
            ctx.fillStyle = "#111";
            ctx.fillRect(-16, -10, 32, 22);
            ctx.fillRect(-7, -14, 14, 5);
            ctx.fillStyle = "#fff";
            ctx.beginPath();
            ctx.arc(0, 1, 7, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = "#111";
            ctx.beginPath();
            ctx.arc(0, 1, 4.5, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
            const topY = 12,
                botY = h - 12;
            ctx.strokeStyle = "#333";
            ctx.lineWidth = 1.2;
            ctx.font = "10px Arial,sans-serif";
            ctx.textAlign = "right";
            ctx.textBaseline = "middle";
            for (let deg = -30; deg <= 30; deg += 10) {
                const ty = topY + ((deg + 30) / 60) * (botY - topY);
                const active = deg === roll;
                ctx.strokeStyle = active ? "#139fca" : "#555";
                ctx.lineWidth = active ? 2 : 1;
                ctx.beginPath();
                ctx.moveTo(w - 20, ty);
                ctx.lineTo(w - 6, ty);
                ctx.stroke();
                if (deg === -30 || deg === 0 || deg === 30) {
                    ctx.fillStyle = active ? "#139fca" : "#333";
                    ctx.fillText(deg > 0 ? `+${deg}` : `${deg}`, w - 24, ty);
                }
            }
            ctx.textBaseline = "alphabetic";
            ctx.textAlign = "center";
            ctx.fillStyle = "#111";
            ctx.font = "bold 11px Arial,sans-serif";
            ctx.fillText(`${roll}°`, cx, h - 5);
        }

        function drawDistance() {
            const canvas = distanceCanvas;
            if (!fit(canvas)) return;
            const ctx = canvas.getContext("2d"),
                g = distanceGeometry(),
                v = distanceVisual(state.distance);
            ctx.fillStyle = "white";
            ctx.fillRect(0, 0, g.w, g.h);
            const x = g.near - (g.near - g.far) * (v.clamped - 0.1) / 9.9;
            drawCamera(ctx, x, g.y, g.subject, g.y);
            drawSubject(ctx, g.subject, g.y, 0.62);
            ctx.fillStyle = "#555";
            ctx.font = "10px Arial,sans-serif";
            ctx.textAlign = "left";
            ctx.fillText(`${t.far} 10 m`, g.far - 10, g.h - 7);
            ctx.textAlign = "right";
            ctx.fillText(`${t.near} 0.1 m`, g.near + 18, g.h - 7);
            const separator = g.subject + 21;
            ctx.strokeStyle = "#139fca";
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(separator, 7);
            ctx.lineTo(separator, g.h - 21);
            ctx.stroke();
            ctx.textAlign = "center";
            ctx.fillStyle = "#111";
            ctx.font = "bold 12px Arial,sans-serif";
            const text = state.distance + " m",
                center = (separator + g.w) / 2;
            ctx.fillText(text, center, g.y + 2, Math.max(10, g.w - separator - 8));
            ctx.font = "9px Arial,sans-serif";
            ctx.fillText(t.subject, center, g.y - 13, Math.max(10, g.w - separator - 8));
            if (v.outside) {
                ctx.textAlign = "center";
                ctx.fillStyle = "#a44c00";
                ctx.font = "9px Arial,sans-serif";
                ctx.fillText(t.outside, g.w / 2, 10, g.w - 12);
            }
            canvas.title = `${state.distance} m | ${t.drag}${v.outside?" | "+t.outside:""}`;
        }

        function draw() {
            views.forEach((canvas, index) => {
                if (!fit(canvas)) return;
                const g = geometry(canvas),
                    ctx = canvas.getContext("2d");
                const viewScale = Math.max(0.35, Math.min(g.w, g.h) / 220);
                ctx.fillStyle = "white";
                ctx.fillRect(0, 0, g.w, g.h);

                ctx.strokeStyle = "#ccc";
                ctx.lineWidth = 1.3;
                ctx.beginPath();
                ctx.moveTo(28, g.cy);
                ctx.lineTo(g.w - 28, g.cy);
                ctx.moveTo(g.cx, 28);
                ctx.lineTo(g.cx, g.h - 28);
                ctx.stroke();

                ctx.strokeStyle = "#e4a5a5";
                ctx.setLineDash([5, 4]);
                ctx.beginPath();
                ctx.arc(g.cx, g.cy, g.r, index === 0 ? Math.PI / 2 : 0, index === 0 ? 3 * Math.PI / 2 : Math.PI * 2);
                ctx.stroke();
                ctx.setLineDash([]);

                drawSubject(ctx, g.cx, g.cy, viewScale);
                ctx.fillStyle = "#555";
                ctx.font = "10px Arial,sans-serif";
                ctx.textAlign = "center";

                let x, y;
                if (index === 0) {
                    x = g.cx - g.r * Math.cos(rad(state.angle));
                    y = g.cy + g.r * Math.sin(rad(state.angle));
                    ctx.fillText(`${state.angle}° | ${state.height} cm`, g.cx, g.h - 9);
                } else {
                    x = g.cx + g.r * Math.sin(rad(state.azimuth));
                    y = g.cy - g.r * Math.cos(rad(state.azimuth));
                    ctx.fillText(t.front, g.cx, 16);
                    ctx.fillText(t.back, g.cx, g.h - 9);
                    ctx.fillText("270° (L)", 24, g.cy);
                    ctx.fillText("90° (R)", g.w - 24, g.cy);
                }
                drawCamera(ctx, x, y, g.cx, g.cy, viewScale);
            });
            drawDistance();
            drawRoll();
        }

        function drag(canvas, move) {
            let active = false;
            canvas.onpointerdown = e => {
                e.preventDefault();
                e.stopPropagation();
                active = true;
                canvas.setPointerCapture(e.pointerId);
                move(e);
            };
            canvas.onpointermove = e => {
                if (active) {
                    e.preventDefault();
                    e.stopPropagation();
                    move(e);
                }
            };
            canvas.onpointerup = e => {
                active = false;
                if (canvas.hasPointerCapture(e.pointerId)) canvas.releasePointerCapture(e.pointerId);
            };
            canvas.onpointercancel = () => {
                active = false;
            };
            canvas.onlostpointercapture = () => {
                active = false;
            };
        }
        views.forEach((canvas, index) => drag(canvas, e => {
            const b = canvas.getBoundingClientRect(),
                g = geometry(canvas),
                x = (e.clientX - b.left) * g.w / b.width - g.cx,
                y = (e.clientY - b.top) * g.h / b.height - g.cy;
            if (Math.hypot(x, y) < 8) return;
            if (index === 0) {
                state.angle = clamp(trunc(Math.atan2(y, Math.max(0, -x)) * 180 / Math.PI), -90, 90);
                state.Angle = "Custom";
            } else {
                state.azimuth = azimuth(Math.atan2(x, -y) * 180 / Math.PI);
                state["360Angle"] = "Custom";
            }
            commit();
        }));
        drag(rollCanvas, e => {
            const b = rollCanvas.getBoundingClientRect(),
                w = rollCanvas.width,
                h = rollCanvas.height;
            const x = (e.clientX - b.left) * w / Math.max(1, b.width),
                y = (e.clientY - b.top) * h / Math.max(1, b.height);
            if (e.type === "pointerdown" && Math.hypot(x - (w / 2 - 8), y - (h / 2 - 4)) <= 18) {
                state.roll = 0;
                commit();
                return;
            }
            const topY = 12,
                botY = h - 12;
            const ratio = clamp((y - topY) / Math.max(1, botY - topY), 0, 1);
            state.roll = clamp(Math.round((ratio * 60 - 30) / 10) * 10, -30, 30);
            commit();
        });
        drag(distanceCanvas, e => {
            const b = distanceCanvas.getBoundingClientRect(),
                g = distanceGeometry(),
                x = (e.clientX - b.left) * g.w / b.width;
            state.distance = distanceFromX(x, g.near, g.far);
            distanceInput.value = state.distance;
            distanceInput.setCustomValidity("");
            distanceInput.style.borderColor = "#bbb";
            commit();
        });

        node.addDOMWidget("camera_controls", "CAV_UI", host, {
            serialize: false,
            hideOnZoom: false,
            getMinHeight: () => 850,
            getHeight: () => 850,
            getMaxHeight: () => 850
        });
        const observer = new ResizeObserver(() => draw());
        [...views, distanceCanvas, rollCanvas].forEach(c => observer.observe(c));
        const oldRemoved = node.onRemoved;
        node.onRemoved = function (...args) {
            observer.disconnect();
            return oldRemoved?.apply(this, args);
        };

        function restore() {
            let saved = {};
            try {
                saved = JSON.parse(widget.value);
            } catch {}
            state = {
                ...defaults,
                ...(saved && typeof saved === "object" && !Array.isArray(saved) ? saved : {}),
                language: lang
            };
            for (const key of Object.keys(limits)) {
                const n = Number(state[key]);
                state[key] = Number.isFinite(n) ? n : defaults[key];
                state[key] = key === "azimuth" ? azimuth(state[key]) : key === "angle" ? clamp(trunc(state[key]), -90, 90) : round(clamp(state[key], ...limits[key]));
            }
            for (const key of Object.keys(presets))
                if (!Array.from(controls[key].options).some(o => o.value === state[key])) state[key] = defaults[key];
            if (!validDistance(state.distance)) {
                console.warn("Camera Angle View: invalid saved distance; reset to 1.0 m");
                state.distance = defaults.distance;
            }
            enforceDistance();
            distanceInput.value = state.distance;
            distanceInput.setCustomValidity("");
            if (node.outputs?.[0]) {
                node.outputs[0].name = t.output;
                node.outputs[0].label = t.output;
            }
            widget.value = JSON.stringify(state);
            sync();
        }
        const oldConfigure = node.onConfigure;
        node.onConfigure = function (...args) {
            const result = oldConfigure?.apply(this, args);
            restore();
            return result;
        };
        restore();
        node.setSize([540, 930]);
    }
});
