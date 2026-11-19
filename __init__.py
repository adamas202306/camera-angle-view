"""Camera Angle View v0.3.0:
카메라 앵글 조정 노드 : Krea2 최적화 / Standard(SD/ZTB/Qwen)
- 화면 점유율(subject_ratio) 기반 거리감 및 shot_scale 알고리즘 수정.
- 거리 우선 자동 초점거리(AOV) 추천 로직 (Custom/None 수동 유지, 백엔드 자동 동기화) 처리.
- 매크로/초근접(Macro / Close-up, 90mm) 렌즈 모드 추가
created by ACKMAN in Jeju-island"""
import hashlib
import json
import logging
import math
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext

LOGGER = logging.getLogger(__name__)
DEFAULT = {
    "Target": "Human",
    "Angle": "Custom",
    "360Angle": "Custom",
    "AOV": "인물 스냅",
    "APT": "중간 개방",
    "height": 100,
    "angle": 0,
    "azimuth": 0,
    "focal": 50,
    "aperture": 6,
    "distance": "1.0",
    "language": "en",
    "profile": "krea2",
    "roll": 0,
    "blur": False,
}

MACRO_AOV_NAMES = ("매크로/초근접", "Macro / Close-up", "매크로", "Macro")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Camera Angle View: duplicate JSON key {key!r}")
        result[key] = value
    return result


def parse_state(value):
    if isinstance(value, str):
        try:
            value = json.loads(value, object_pairs_hook=unique_object)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Camera Angle View: invalid state JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("Camera Angle View: state must be a JSON object")
    if value.get("Target", DEFAULT["Target"]) not in ("Human", "Product", "Place"):
        raise ValueError("Camera Angle View: unknown Target")
    return value


def read_number(state, key, lo, hi):
    raw = state.get(key, DEFAULT[key])
    if isinstance(raw, bool) or not isinstance(raw, (int, float, str)):
        raise ValueError(f"Camera Angle View: invalid number for {key}")
    try:
        value = float(raw)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(f"Camera Angle View: {key} must be a number without units") from exc
    if not math.isfinite(value) or not lo <= value <= hi:
        raise ValueError(f"Camera Angle View: invalid {key}, expected {lo}..{hi}")
    return value


def distance_text(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError("Camera Angle View: distance must be a positive decimal in meters")
    if not isinstance(value, str):
        try:
            value = format(Decimal(str(value)), "f")
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("Camera Angle View: invalid distance") from exc
    value = value.strip()
    if not re.fullmatch(r"(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)", value):
        raise ValueError("Camera Angle View: enter distance as a decimal without units")
    with localcontext() as ctx:
        ctx.prec = max(28, len(value) + 10)
        rounded = Decimal(value).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    if rounded <= 0:
        raise ValueError("Camera Angle View: distance must round to at least 0.1 m")
    return format(rounded, ".1f")


def fmt(value):
    return f"{value:.2f}".rstrip("0").rstrip(".")


def angles(state):
    return (
        math.trunc(read_number(state, "angle", -90, 90)),
        math.trunc(read_number(state, "azimuth", -100000, 100000)) % 360,
    )


def recommend_lens_for_distance(distance_m, target):
    """거리 우선 자동 초점거리(AOV) 추천 로직."""
    d = float(distance_m)
    if d <= 0.6:
        return ("매크로/초근접", 90.0)
    if target == "Place":
        if d <= 3.0:
            return ("초광각", 20.0)
        if d <= 8.0:
            return ("광각 스냅", 28.0)
        return ("인물 스냅", 50.0)
    if d <= 1.8:
        return ("광각 스냅", 35.0)
    if d <= 4.5:
        return ("인물 스냅", 50.0)
    if d <= 12.0:
        return ("망원", 105.0)
    return ("초망원", 200.0)


def resolve_focal(state, distance_m, target):
    """Custom/None 수동 설정은 그대로 유지.
    일반 프리셋 상태에서는 백엔드에서도 거리 우선 추천 렌즈를 안전하게 동기화."""
    aov = state.get("AOV", DEFAULT["AOV"])
    focal = read_number(state, "focal", 1, 5000)
    if aov in ("Custom", "None"):
        return aov, focal, False
    rec_aov, rec_focal = recommend_lens_for_distance(distance_m, target)
    return rec_aov, rec_focal, True


def camera_geometry(distance_m, tilt_deg, target):
    d = float(distance_m)
    rad = math.radians(tilt_deg)
    base_h = 0.5 if target == "Product" else 1.6
    cam_h_m = max(0.0, base_h - d * math.sin(rad))
    horiz_m = abs(d * math.cos(rad))
    return cam_h_m, horiz_m


def shot_scale(distance_m, focal_mm, target, is_macro=False):
    d = float(distance_m)
    frame_h = d * 24.0 / float(focal_mm)
    subj_h = 1.65 if target == "Human" else (0.35 if target == "Product" else 4.0)
    ratio = subj_h / max(frame_h, 1e-6)

    if is_macro or (d <= 0.6 and ratio >= 1.8):
        if target == "Human":
            return (
                "Extreme macro close-up shot",
                "tightly filling the entire frame with fine skin, eye, or facial details from very close range",
                ratio,
                "macro",
            )
        return (
            "Extreme macro close-up shot",
            "tightly framed on fine surface textures and intricate details filling almost the entire frame",
            ratio,
            "macro",
        )

    if target == "Human":
        if ratio <= 0.18:
            return (
                "Extreme distant long shot",
                "the subject appears as a tiny distant figure occupying less than one-fifth of the frame height, surrounded by vast empty open space and wide margins on all sides",
                ratio,
                "distant",
            )
        if ratio <= 0.42:
            return (
                "Distant wide full-body shot",
                "the entire figure from head to toe appears as a small figure occupying roughly one-third of the frame height, with expansive surroundings and wide empty margins around them",
                ratio,
                "distant",
            )
        if ratio <= 0.72:
            return (
                "Wide full-body shot",
                "the entire figure from head to toe is clearly visible occupying about half to two-thirds of the frame height, with generous breathing room and open environment around them",
                ratio,
                "wide",
            )
        if ratio <= 1.05:
            return (
                "Full-body shot",
                "the full figure from head to toe fills most of the frame height with balanced margins above and below",
                ratio,
                "medium",
            )
        if ratio <= 1.55:
            return (
                "Medium three-quarter shot",
                "framed from the knees up with balanced headroom",
                ratio,
                "medium",
            )
        if ratio <= 2.40:
            return (
                "Medium close-up shot",
                "framed from the chest up, filling the frame closely",
                ratio,
                "close",
            )
        return (
            "Close-up portrait shot",
            "tightly framed on the head and shoulders filling the frame",
            ratio,
            "close",
        )

    if target == "Product":
        if ratio <= 0.25:
            return ("Distant wide shot", "the object sits small in the distance occupying a small portion of the frame with expansive supporting surroundings", ratio, "distant")
        if ratio <= 0.60:
            return ("Wide product shot", "the entire object is visible with wide surrounding space and ample margins around it", ratio, "wide")
        if ratio <= 1.15:
            return ("Full product shot", "the entire object rests cleanly in the frame with balanced room around it", ratio, "medium")
        return ("Close-up product shot", "framed closely on the object showing its form and surface details", ratio, "close")

    if ratio <= 0.30:
        return ("Extreme wide establishing shot", "capturing the vast architectural or environmental expanse from far away", ratio, "distant")
    if ratio <= 0.85:
        return ("Wide establishing shot", "showing the full spatial layout and expansive surrounding structure", ratio, "wide")
    return ("Medium architectural shot", "framed closely on the main structure, wall, or opening", ratio, "medium")


def target_orientation(azimuth, tilt, target):
    if tilt == -90:
        return "seen from directly above"
    idx = int((azimuth + 22.5) // 45) % 8
    if target == "Human":
        table = (
            "square on to the camera, facing it directly",
            "turned in a three-quarter view, right side nearer the camera, angled toward the right",
            "in right-side profile, facing toward the right edge of the frame",
            "in a rear three-quarter view, the camera behind and to the right",
            "seen from directly behind, facing away from the camera",
            "in a rear three-quarter view, the camera behind and to the left",
            "in left-side profile, facing toward the left edge of the frame",
            "turned in a three-quarter view, left side nearer the camera, angled toward the left",
        )
    elif target == "Product":
        table = (
            "viewed straight-on from the front",
            "viewed in a front-right three-quarter angle, angled toward the right",
            "in right-side profile, facing toward the right edge of the frame",
            "viewed from a rear-right three-quarter angle",
            "viewed straight-on from behind",
            "viewed from a rear-left three-quarter angle",
            "in left-side profile, facing toward the left edge of the frame",
            "viewed in a front-left three-quarter angle, angled toward the left",
        )
    else:
        table = (
            "viewed straight-on from the front",
            "viewed obliquely from the front-right, angled toward the right",
            "viewed from the right side, oriented toward the right edge of the frame",
            "viewed obliquely from the rear-right",
            "viewed from the opposite side",
            "viewed obliquely from the rear-left",
            "viewed from the left side, oriented toward the left edge of the frame",
            "viewed obliquely from the front-left, angled toward the left",
        )
    return table[idx]


def compute_dof(focal_mm, aperture_f, distance_m):
    coc = 0.03
    d_mm = float(distance_m) * 1000.0
    if d_mm <= focal_mm:
        return 0.0
    hyperfocal = (focal_mm ** 2) / (aperture_f * coc) + focal_mm
    if d_mm >= hyperfocal:
        return float("inf")
    near_mm = (hyperfocal * d_mm) / (hyperfocal + (d_mm - focal_mm))
    far_mm = (hyperfocal * d_mm) / (hyperfocal - (d_mm - focal_mm))
    return (far_mm - near_mm) / 1000.0


def krea2_distance_elevation_phrase(distance_m, cam_h_m, tilt, focal, ref, distance_tier, is_macro):
    d_val = float(distance_m)
    h_str = f"{cam_h_m:.1f}"

    if distance_tier == "distant":
        dist_cue = f"Captured from far away (about {distance_m} meters from the {ref}), leaving wide open negative space around the small {ref}"
    elif distance_tier == "wide":
        dist_cue = f"Photographed from a generous distance of {distance_m} meters from the {ref}, with ample surrounding space visible"
    elif distance_tier == "macro":
        dist_cue = f"Captured at extreme close-up macro range ({distance_m} meters from the {ref}), magnifying fine micro-details"
    elif distance_tier == "close":
        dist_cue = f"Photographed at close range ({distance_m} meters from the {ref})"
    else:
        dist_cue = f"Photographed from a camera-to-{ref} distance of {distance_m} meters"

    if tilt <= -10:
        if cam_h_m >= 4.0:
            elev = f"from a high elevated vantage point about {h_str} meters above the ground"
        elif cam_h_m >= 2.2:
            elev = f"from an elevated camera position about {h_str} meters above the ground"
        else:
            elev = f"from a slightly raised camera height about {h_str} meters off the ground"
    elif tilt >= 10:
        if cam_h_m <= 0.4:
            elev = "from near ground level"
        else:
            elev = f"from a low camera position about {h_str} meters above the ground"
    else:
        elev = f"at a camera height of about {h_str} meters"

    if is_macro:
        persp = "with true 1:1 macro optical magnification and ultra-fine detail rendering"
    elif focal >= 85 and d_val >= 4.0:
        persp = "with strong telephoto perspective compression flattening the background"
    elif focal >= 70:
        persp = "with noticeable telephoto compression"
    elif focal <= 28:
        persp = "with pronounced wide-angle spatial depth and expanded surroundings"
    else:
        persp = "with natural perspective proportions"

    return f"{dist_cue}, {elev}, {persp}."


def dof_description_krea2(focal_mm, aperture_f, distance_m, distance_tier, blur_override=False):
    total_dof_m = compute_dof(focal_mm, aperture_f, distance_m)
    f_str = fmt(aperture_f)

    if blur_override:
        if distance_tier == "distant":
            return (
                f"Shot at f/{f_str}, keeping the distant subject crisp while the far background "
                f"softens gently without losing the wide sense of distance."
            )
        return (
            f"Shot at f/{f_str} with shallow depth of field, keeping the subject in crisp focus "
            f"while rendering the background in soft creamy bokeh."
        )

    if total_dof_m == 0.0:
        return (
            f"Shot at f/{f_str} with razor-thin shallow depth of field, "
            f"crisp focus on the subject and a softly blurred background."
        )
    if math.isinf(total_dof_m) or total_dof_m >= 10.0:
        return (
            f"Shot at f/{f_str} with deep depth of field, keeping both the subject "
            f"and the distant background sharply resolved across the frame."
        )
    if total_dof_m < 0.8:
        return (
            f"Shot at f/{f_str} with shallow depth of field (focus zone about {total_dof_m:.1f} meters), "
            f"isolating the subject sharply against a softly blurred background."
        )
    return (
        f"Shot at f/{f_str} with moderate depth of field (focus zone about {total_dof_m:.1f} meters), "
        f"keeping the subject sharp while the far background gently softens."
    )


def dof_tags_standard(focal_mm, aperture_f, distance_m, distance_tier, blur_override=False):
    if blur_override:
        if distance_tier == "distant":
            return "distant subject in focus, slightly soft far background"
        return "shallow depth of field, blurred background, bokeh"
    total_dof_m = compute_dof(focal_mm, aperture_f, distance_m)
    if total_dof_m == 0.0 or total_dof_m < 0.8:
        return "shallow depth of field, blurred background"
    if math.isinf(total_dof_m) or total_dof_m >= 10.0:
        return "deep depth of field, sharp background"
    return "moderate depth of field, slightly soft background"


def make_prompt(value):
    state = parse_state(value)
    target = state.get("Target", DEFAULT["Target"])
    distance = distance_text(state.get("distance", DEFAULT["distance"]))
    tilt, azimuth = angles(state)
    profile = str(state.get("profile", DEFAULT["profile"])).lower()
    roll = int(round(float(state.get("roll", 0) or 0)))
    blur = bool(state.get("blur", False))

    aov, focal, _ = resolve_focal(state, distance, target)
    is_macro = aov in MACRO_AOV_NAMES

    cam_h_m, _ = camera_geometry(distance, tilt, target)
    shot_title, shot_detail, ratio, distance_tier = shot_scale(distance, focal, target, is_macro=is_macro)

    if profile == "standard":
        degree = "degree" if abs(tilt) == 1 else "degrees"
        height_cm = fmt(cam_h_m * 100.0)
        if tilt < 0:
            ang_str = f"Camera tilted downward at {abs(tilt)} {degree} from horizontal"
        elif tilt > 0:
            ang_str = f"Camera tilted upward at {tilt} {degree} from horizontal"
        else:
            ang_str = "Camera directed horizontally at 0 degrees"

        dist_tag = ""
        if distance_tier == "distant":
            dist_tag = "far away, small distant subject, wide empty margins, "
        elif distance_tier == "macro":
            dist_tag = "macro photography, extreme close-up, "

        parts = [
            f"{shot_title}, {dist_tag}{ang_str}, positioned {height_cm} cm above the ground.",
            f"Subject azimuth {azimuth} degrees, {distance} meters from the camera, centered in the frame.",
        ]
        if aov != "None":
            if is_macro:
                parts.append(f"Focal length {fmt(focal)}mm macro lens.")
            else:
                parts.append(f"Focal length {fmt(focal)}mm.")
        if state.get("APT", DEFAULT["APT"]) != "None":
            aperture = read_number(state, "aperture", 0.1, 128)
            parts.append(f"Aperture f/{fmt(aperture)}, {dof_tags_standard(focal, aperture, distance, distance_tier, blur)}.")
        elif blur:
            parts.append(
                "slightly soft far background." if distance_tier == "distant" else "blurred background, shallow depth of field."
            )

        if roll != 0:
            r_deg = "degree" if abs(roll) == 1 else "degrees"
            strength = "strongly " if abs(roll) >= 20 else ""
            parts.append(
                f"Dutch angle, {strength}tilted horizon, camera rolled {abs(roll)} {r_deg} "
                f"{'counterclockwise' if roll < 0 else 'clockwise'}."
            )

        text = " ".join(" ".join(part.split()) for part in parts if part.strip())
    else:
        ref = "scene" if target == "Place" else ("object" if target == "Product" else "subject")
        is_custom_angle = state.get("Angle", DEFAULT["Angle"]) == "Custom"

        if is_custom_angle:
            if tilt == 0:
                angle_lead = "at a level 0-degree angle"
                angle_desc = f"The camera is upright with a level horizon, aimed horizontally toward the {ref}."
            elif tilt < 0:
                if tilt <= -60:
                    angle_lead = f"from a steep {abs(tilt)}-degree high angle looking down from above"
                    angle_desc = (
                        f"The camera looks steeply downward at {abs(tilt)} degrees from above the {ref}; "
                        "the top surfaces are clearly visible and the supporting ground surface fills the background."
                    )
                elif tilt <= -30:
                    angle_lead = f"from a {abs(tilt)}-degree high angle looking down"
                    angle_desc = (
                        f"The camera is elevated and tilted downward at {abs(tilt)} degrees, "
                        f"showing the upper planes of the {ref} and the supporting surface behind it."
                    )
                else:
                    angle_lead = f"from a slight {abs(tilt)}-degree downward tilt"
                    angle_desc = (
                        f"The camera is upright, tilted slightly downward at {abs(tilt)} degrees "
                        f"looking gently down toward the {ref}."
                    )
            else:
                if tilt >= 60:
                    angle_lead = f"from a steep {tilt}-degree low angle looking up from below"
                    angle_desc = (
                        f"The camera looks steeply upward at {tilt} degrees from below, "
                        f"so the {ref} rises prominently against the upper background."
                    )
                else:
                    angle_lead = f"from a {tilt}-degree low angle looking upward"
                    angle_desc = f"The camera is tilted upward at {tilt} degrees looking up toward the {ref}."
        else:
            if tilt == -90:
                angle_lead = "from a direct top-down overhead angle"
                angle_desc = f"The camera points straight down at 90 degrees, perpendicular to the ground, showing the {ref} from directly above."
            elif tilt <= -75:
                angle_lead = "from a near-overhead high angle"
                angle_desc = f"The camera looks steeply down at the {ref} from above, with the ground surface filling the background."
            elif tilt <= -45:
                angle_lead = "from a strong high angle"
                angle_desc = f"The camera is elevated and looks down at {abs(tilt)} degrees at the {ref}, showing its upper surfaces."
            elif tilt < 0:
                angle_lead = "from a slight high angle"
                angle_desc = f"The camera is upright, tilted slightly downward at {abs(tilt)} degrees looking gently down toward the {ref}."
            elif tilt == 0:
                angle_lead = "at eye level" if target == "Human" else "at a level angle"
                angle_desc = f"The camera is upright with a level horizon, pointing straight at the {ref} with natural proportions."
            elif tilt < 45:
                angle_lead = "from a low angle"
                angle_desc = f"The camera is tilted upward at {tilt} degrees looking up at the {ref}."
            elif tilt < 75:
                angle_lead = "from a strong low angle"
                angle_desc = f"The camera looks steeply upward at {tilt} degrees toward the {ref}."
            else:
                angle_lead = "from an extreme worm's-eye view"
                angle_desc = f"The camera is near the ground looking steeply upward, making the {ref} rise above with pronounced upward foreshortening."

        if roll != 0:
            r_deg = "degree" if abs(roll) == 1 else "degrees"
            side = "left" if roll < 0 else "right"
            strength = "strongly " if abs(roll) >= 20 else ""
            dutch_desc = (
                f"Dutch angle, canted frame with a {strength}tilted diagonal horizon slanted "
                f"{abs(roll)} {r_deg} to the {side} and tilted vertical lines"
            )
            if "The camera is upright with a level horizon, " in angle_desc:
                angle_desc = angle_desc.replace(
                    "The camera is upright with a level horizon, ",
                    f"{dutch_desc}; the camera is ",
                )
            else:
                angle_desc = f"{angle_desc} {dutch_desc}."

        orientation = target_orientation(azimuth, tilt, target)
        parts = [
            f"{shot_title} {angle_lead}.",
            angle_desc,
            krea2_distance_elevation_phrase(distance, cam_h_m, tilt, focal, ref, distance_tier, is_macro),
            f"The {ref} is {orientation}, centered in the frame; {shot_detail}.",
        ]

        if aov != "None":
            if is_macro:
                parts.append(f"Shot with a {fmt(focal)}mm macro lens.")
            elif focal <= 28:
                parts.append(f"Shot with a {fmt(focal)}mm wide-angle lens.")
            elif focal >= 70:
                parts.append(f"Shot with a {fmt(focal)}mm telephoto lens.")
            else:
                parts.append(f"Shot with a {fmt(focal)}mm lens.")

        if state.get("APT", DEFAULT["APT"]) != "None":
            aperture = read_number(state, "aperture", 0.1, 128)
            parts.append(dof_description_krea2(focal, aperture, distance, distance_tier, blur))
        elif blur:
            parts.append(
                "Soft distant background separation." if distance_tier == "distant" else "Shallow depth of field with a softly blurred background."
            )

        text = " ".join(" ".join(part.split()) for part in parts if part.strip())

    if not text.isascii():
        raise ValueError("Camera Angle View: internal non-ASCII output")
    return text


def fragment(text, name):
    if not isinstance(text, str):
        raise ValueError(f"{name} must be STRING")
    if any(ord(c) < 32 and c not in "\n\r\t" for c in text):
        raise ValueError(f"{name} contains control characters")
    return text.strip().strip(",").strip()


def join_prompts(camera_prompt, scene_prompt):
    camera, scene = fragment(camera_prompt, "camera_prompt"), fragment(scene_prompt, "scene_prompt")
    if not camera:
        raise ValueError("Camera prompt is empty")
    return camera + ("\n" + scene if scene else "")


class CameraAngleView:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"camera_state": ("CAV_STATE", {"default": json.dumps(DEFAULT, ensure_ascii=False)})}}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("Camera Composition",)
    FUNCTION = "generate"
    CATEGORY = "Camera"

    def generate(self, camera_state):
        prompt_str = make_prompt(camera_state)
        return (prompt_str,)


class CameraPromptJoinInspect:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "camera_prompt": ("STRING", {"forceInput": True}),
                "scene_prompt": ("STRING", {"default": "", "multiline": True}),
            },
            "hidden": {"unique_id": "UNIQUE_ID", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("combined_prompt",)
    FUNCTION = "combine"
    CATEGORY = "Camera/Diagnostics"

    def combine(self, camera_prompt, scene_prompt, unique_id=None, extra_pnginfo=None):
        text = join_prompts(camera_prompt, scene_prompt)
        record = {
            "stage": "joined_before_encoder_NOT_proof_of_encoder_input",
            "text": text,
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
            "characters": len(text),
        }
        if isinstance(extra_pnginfo, dict):
            bucket = extra_pnginfo.setdefault("camera_angle_view_debug", {})
            if not isinstance(bucket, dict):
                raise ValueError("Metadata key occupied")
            bucket[str(unique_id or "join")] = record
        LOGGER.info("Camera join node=%s chars=%d sha256=%s", unique_id, len(text), record["sha256"])
        return (text,)


NODE_CLASS_MAPPINGS = {
    "CameraAngleView": CameraAngleView,
    "CameraPromptJoinInspect": CameraPromptJoinInspect,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "CameraAngleView": "Camera Angle View",
    "CameraPromptJoinInspect": "Camera Prompt Join & Inspect",
}
WEB_DIRECTORY = "./web"
