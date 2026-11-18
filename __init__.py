"""Camera Angle View v1.0.0: 
카메라 앵글 조정 노드 : Krea2 최적화 / Standard(SD/ZTB/Qwen)
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
}

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


def shot_scale(distance_m, focal_mm, target):
    frame_h = float(distance_m) * 24.0 / float(focal_mm)
    if target == "Human":
        if frame_h >= 15.0:
            return ("Extreme wide long shot", "the subject appears as a tiny, distant figure surrounded by vast open space")
        if frame_h >= 6.0:
            return ("Wide full-body shot", "the subject is seen head-to-toe as a small figure with expansive surroundings around them")
        if frame_h >= 2.0:
            return ("Full-body shot", "the entire figure from head to toe is visible with ample space around them")
        if frame_h >= 1.2:
            return ("Medium three-quarter shot", "framed from the knees up with balanced headroom")
        if frame_h >= 0.7:
            return ("Medium close-up shot", "framed from the chest up")
        return ("Close-up shot", "tightly framed on the head and shoulders")
    if target == "Product":
        if frame_h >= 6.0:
            return ("Wide shot", "the object sits small in the distance with expansive supporting surroundings")
        if frame_h >= 1.5:
            return ("Full product shot", "the entire object is visible resting on its supporting surface with room around it")
        if frame_h >= 0.5:
            return ("Medium close-up shot", "framed closely on the object showing its form and surface details")
        return ("Macro close-up shot", "tightly framed on the object's surface texture and details")
    if frame_h >= 15.0:
        return ("Extreme wide establishing shot", "capturing the vast architectural or environmental expanse")
    if frame_h >= 4.0:
        return ("Wide shot", "showing the full spatial layout and surrounding structure")
    return ("Medium architectural shot", "framed on the main structure, wall, or window opening")


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


def dof_description(focal_mm, aperture_f, distance_m):
    coc = 0.03
    d_mm = float(distance_m) * 1000.0
    if d_mm <= focal_mm:
        return f"Shot at f/{fmt(aperture_f)}: shallow depth of field, very narrow focus range; the background is softly blurred."
    hyperfocal = (focal_mm ** 2) / (aperture_f * coc) + focal_mm
    near_mm = (hyperfocal * d_mm) / (hyperfocal + (d_mm - focal_mm))
    if d_mm >= hyperfocal:
        return f"Shot at f/{fmt(aperture_f)}: deep depth of field, everything from the subject to the far background is in focus, no background blur."
    far_mm = (hyperfocal * d_mm) / (hyperfocal - (d_mm - focal_mm))
    total_dof_m = (far_mm - near_mm) / 1000.0
    if total_dof_m >= 10.0:
        return f"Shot at f/{fmt(aperture_f)}: deep depth of field, everything from the subject to the far background is in focus, no background blur."
    if total_dof_m < 0.8:
        return f"Shot at f/{fmt(aperture_f)}: shallow depth of field, the subject is sharp within about {total_dof_m:.1f} meters; the background is softly blurred."
    return f"Shot at f/{fmt(aperture_f)}: moderate depth of field, the subject is sharp within about {total_dof_m:.1f} meters; the background is slightly soft."


def make_prompt(value):
    state = parse_state(value)
    target = state.get("Target", DEFAULT["Target"])
    distance = distance_text(state.get("distance", DEFAULT["distance"]))
    tilt, azimuth = angles(state)
    focal = read_number(state, "focal", 1, 5000)
    profile = state.get("profile", DEFAULT["profile"])

    if profile == "standard":
        degree = "degree" if abs(tilt) == 1 else "degrees"
        base_h = 0.5 if target == "Product" else 1.6
        cam_h_m = max(0.0, base_h - float(distance) * math.sin(math.radians(tilt)))
        height_cm = fmt(cam_h_m * 100.0)
        if tilt < 0:
            ang_str = f"Camera tilted downward at {abs(tilt)} {degree} from horizontal"
        elif tilt > 0:
            ang_str = f"Camera tilted upward at {tilt} {degree} from horizontal"
        else:
            ang_str = "Camera directed horizontally at 0 degrees"
        parts = [
            f"{ang_str}, positioned {height_cm} cm above the ground.",
            f"Subject azimuth {azimuth} degrees, {distance} meters from the camera, centered in the frame.",
        ]
        if state.get("AOV", DEFAULT["AOV"]) != "None":
            parts.append(f"Focal length {fmt(focal)}mm.")
        if state.get("APT", DEFAULT["APT"]) != "None":
            parts.append(f"Aperture f/{fmt(read_number(state, 'aperture', 0.1, 128))}.")
    else:
        ref = "scene" if target == "Place" else ("object" if target == "Product" else "subject")
        is_custom_angle = state.get("Angle", DEFAULT["Angle"]) == "Custom"
        shot_title, shot_detail = shot_scale(distance, focal, target)

        if is_custom_angle:
            if tilt == 0:
                angle_lead = "at a level 0-degree angle"
                angle_desc = f"The camera is upright with a level horizon, aimed horizontally toward the {ref}."
            elif tilt < 0:
                if tilt <= -60:
                    angle_lead = f"from a steep {abs(tilt)}-degree high angle looking down from above"
                    angle_desc = (
                        f"The camera looks steeply downward at {abs(tilt)} degrees from above the {ref}; "
                        "the top surfaces are clearly visible and the table or ground surface fills the background."
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
                        f"so the {ref} rises above against the sky or ceiling."
                    )
                else:
                    angle_lead = f"from a {tilt}-degree low angle looking upward"
                    angle_desc = (
                        f"The camera is tilted upward at {tilt} degrees looking up toward the {ref}."
                    )
        else:
            if tilt == -90:
                angle_lead = "from a direct top-down overhead angle"
                angle_desc = f"The camera points straight down at 90 degrees, perpendicular to the ground, showing the {ref} from directly above."
            elif tilt <= -75:
                angle_lead = "from a near-overhead high angle"
                angle_desc = f"The camera looks steeply down at the {ref} from above, with the ground or table surface filling the background."
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
                angle_desc = f"The camera is on the ground looking steeply upward, making the {ref} rise above with pronounced upward foreshortening."

        parts = [f"{shot_title} {angle_lead}.", angle_desc]
        orientation = target_orientation(azimuth, tilt, target)
        parts.append(f"The {ref} is {orientation}, centered in the frame; {shot_detail}.")

        if state.get("AOV", DEFAULT["AOV"]) != "None":
            if focal <= 28:
                parts.append(f"Shot with a {fmt(focal)}mm wide-angle lens.")
            elif focal >= 70:
                parts.append(f"Shot with a {fmt(focal)}mm telephoto lens.")
            else:
                parts.append(f"Shot with a {fmt(focal)}mm lens.")

        if state.get("APT", DEFAULT["APT"]) != "None":
            aperture = read_number(state, "aperture", 0.1, 128)
            parts.append(dof_description(focal, aperture, distance))

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
        try:
            st = json.loads(camera_state) if isinstance(camera_state, str) else (camera_state or {})
        except Exception:
            st = {}
        prof = str(st.get("profile", "krea2")).lower()
        roll = int(round(float(st.get("roll", 0) or 0)))
        blur = bool(st.get("blur", False))
        extra = []
        if roll != 0:
            r_deg = "degree" if abs(roll) == 1 else "degrees"
            side = "left" if roll < 0 else "right"
            strength = "strongly " if abs(roll) >= 20 else ""
            if prof == "krea2":
                prompt_str = prompt_str.replace(
                    "The camera is upright with a level horizon, ",
                    f"Dutch angle, canted frame with a {strength}tilted diagonal horizon slanted {abs(roll)} {r_deg} to the {side} and tilted vertical lines; the camera is "
                ).replace(
                    "The camera is upright with a level horizon.",
                    f"Dutch angle, canted frame with a {strength}tilted diagonal horizon slanted {abs(roll)} {r_deg} to the {side} and tilted vertical lines."
                )
                if "Dutch angle" not in prompt_str:
                    extra.append(f"Dutch angle, canted frame with a {strength}tilted diagonal horizon slanted {abs(roll)} {r_deg} to the {side} and tilted vertical lines.")
            else:
                extra.append(f"Dutch angle, {strength}tilted horizon, camera rolled {abs(roll)} {r_deg} {'counterclockwise' if roll < 0 else 'clockwise'}")
        if blur:
            prompt_str = prompt_str.replace(", no background blur.", ".").replace(", no background blur", "")
            if prof == "krea2":
                extra.append("Softly blurred background with shallow depth of field.")
            else:
                extra.append("blurred background, shallow depth of field")
        if extra:
            sep = " " if prof == "krea2" else ", "
            prompt_str = f"{prompt_str}{sep}{sep.join(extra)}"
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
