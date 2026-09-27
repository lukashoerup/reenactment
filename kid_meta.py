"""Children in rain gear as metaball families: one blob object per joint, all
named <base>.NNN so Blender fuses them into a single smooth surface."""
import bpy, math

def _mb(base, idx, parent, loc=(0, 0, 0), res=0.018):
    name = base if idx == 0 else f"{base}.{idx:03d}"
    mb = bpy.data.metaballs.new(name)
    mb.resolution = res; mb.render_resolution = res * 0.6
    mb.threshold = 0.45
    ob = bpy.data.objects.new(name, mb)
    bpy.context.scene.collection.objects.link(ob)
    ob.parent = parent; ob.location = loc
    return ob, mb

R = 1.42  # field radius / visible surface radius at threshold 0.45, stiffness 3.5

def _el(mb, kind, co, radius, size=(1, 1, 1), rot=None, stiff=3.5, neg=False):
    e = mb.elements.new(type=kind)
    e.co = co; e.radius = radius * R; e.stiffness = stiff
    e.use_negative = neg
    if kind in ("ELLIPSOID", "CAPSULE", "CUBE", "PLANE"):
        e.size_x, e.size_y, e.size_z = size
    if rot is not None:
        e.rotation = rot
    return e

def make_child_meta(name, height, coat_mat, boot_mat, dark_mat):
    k = height / 1.20
    root = bpy.data.objects.new(name + "_root", None); bpy.context.scene.collection.objects.link(root)
    pelvis = bpy.data.objects.new(name + "_pelvis", None); bpy.context.scene.collection.objects.link(pelvis)
    pelvis.parent = root; pelvis.location = (0, 0, 0.55 * k)
    base = name + "_coat"
    # torso + coat + hood in one blob object (index 0 carries the material)
    body, mb = _mb(base, 0, pelvis)
    mb.materials.append(coat_mat)
    _el(mb, "ELLIPSOID", (0, 0.0, 0.10 * k), 0.26 * k, (0.80, 0.62, 0.92))     # coat skirt, flares
    _el(mb, "ELLIPSOID", (0, 0.0, 0.34 * k), 0.24 * k, (0.80, 0.60, 0.95))     # chest
    _el(mb, "ELLIPSOID", (0, 0.01 * k, 0.50 * k), 0.20 * k, (1.05, 0.62, 0.45)) # shoulders
    _el(mb, "BALL", (0, 0.015 * k, 0.66 * k), 0.17 * k)                         # hood
    _el(mb, "ELLIPSOID", (0, -0.035 * k, 0.72 * k), 0.10 * k, (0.8, 0.9, 0.7))  # hood peak/brim
    for sx in (1, -1):  # carve the neck so the hood reads as a hood, not a pillar
        _el(mb, "BALL", (sx * 0.15 * k, 0.0, 0.575 * k), 0.05 * k, neg=True)
    _el(mb, "ELLIPSOID", (0, 0, -0.30 * k), 0.07 * k, (0.5, 1.2, 2.2), neg=True)  # between the legs
    arms, legs = {}, {}
    for side, sx in (("L", 1), ("R", -1)):
        sh = bpy.data.objects.new(f"{name}_sh{side}", None); bpy.context.scene.collection.objects.link(sh)
        sh.parent = pelvis; sh.location = (sx * 0.15 * k, 0, 0.50 * k)
        a, amb = _mb(base, 1 if sx > 0 else 2, sh)
        _el(amb, "ELLIPSOID", (sx * 0.02 * k, 0, -0.17 * k), 0.13 * k, (0.48, 0.48, 1.35))   # sleeve
        _el(amb, "BALL", (sx * 0.035 * k, -0.01 * k, -0.36 * k), 0.065 * k)                     # mitten/cuff
        arms[side] = sh
        hip = bpy.data.objects.new(f"{name}_hip{side}", None); bpy.context.scene.collection.objects.link(hip)
        hip.parent = pelvis; hip.location = (sx * 0.085 * k, 0, 0.0)
        l, lmb = _mb(base, 3 if sx > 0 else 4, hip)
        _el(lmb, "ELLIPSOID", (0, 0, -0.22 * k), 0.13 * k, (0.50, 0.54, 1.50))  # rain trousers
        legs[side] = hip
        # rubber boot: separate blob family so it gets its own material
        bb, bmb = _mb(f"{name}_boot{side}", 0, hip)
        bmb.materials.append(boot_mat)
        _el(bmb, "ELLIPSOID", (0, 0, -0.43 * k), 0.10 * k, (0.62, 0.66, 1.25))
        _el(bmb, "ELLIPSOID", (0, -0.045 * k, -0.53 * k), 0.085 * k, (0.75, 1.35, 0.55))
    # the dark inside of the hood (only seen from the front)
    face, fmb = _mb(name + "_face", 0, pelvis)
    fmb.materials.append(dark_mat)
    _el(fmb, "ELLIPSOID", (0, -0.125 * k, 0.645 * k), 0.085 * k, (0.8, 0.28, 1.0))
    return {"root": root, "pelvis": pelvis, "armL": arms["L"], "armR": arms["R"],
            "legL": legs["L"], "legR": legs["R"], "_pelvis_h": pelvis.location.z}
