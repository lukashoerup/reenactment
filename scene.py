"""Cold-open re-enactment, 'Det Brændende Lig' 01:34.5-01:59.3.

Builds a rainy beech forest at dusk with a bonfire in a hollow, two children in
rain gear, and renders one shot as multilayer EXR (Combined + Mist).

usage: bvenv/bin/python scene.py SHOT [--frames a b] [--samples n] [--scale pct] [--out dir]
"""
import bpy, bmesh, math, random, sys, os, argparse
from mathutils import Vector, Euler

ROOT = os.path.dirname(os.path.abspath(__file__))
FPS = 24
FIRE_DIR = os.path.join(ROOT, "elements", "fire45676")

# --------------------------------------------------------------------------- ground
def ground_h(x, y):
    """Terrain height: a shallow hollow around the fire plus gentle undulation."""
    hollow = -0.55 * math.exp(-(x * x + y * y) / (2 * 3.2 ** 2))
    und = 0.18 * math.sin(x * 0.21 + 1.3) * math.cos(y * 0.17 + 0.4) + 0.07 * math.sin(x * 0.63 - y * 0.41)
    # the track the children walk on is a little lower and flatter
    track = -0.06 * math.exp(-(x * x) / (2 * 0.9 ** 2)) if y < -2 else 0.0
    return hollow + und * (1 - math.exp(-(x * x + y * y) / 30)) + track


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import addon_utils
    addon_utils.enable("cycles", default_set=True)


def mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree.nodes, m.node_tree.links


def principled(nodes):
    return nodes.get("Principled BSDF")


def make_ground():
    size, n = 170.0, 230
    me = bpy.data.meshes.new("ground")
    verts, faces = [], []
    for j in range(n + 1):
        for i in range(n + 1):
            x = -size / 2 + size * i / n
            y = -size / 2 + size * j / n
            verts.append((x, y, ground_h(x, y)))
    for j in range(n):
        for i in range(n):
            a = j * (n + 1) + i
            faces.append((a, a + 1, a + n + 2, a + n + 1))
    me.from_pydata(verts, [], faces)
    me.update()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new("ground", me)
    bpy.context.scene.collection.objects.link(ob)

    m, nd, ln = mat("wet_litter")
    p = principled(nd)
    tc = nd.new("ShaderNodeTexCoord")
    sep = nd.new("ShaderNodeSeparateXYZ"); ln.new(tc.outputs["Object"], sep.inputs[0])
    # leaf litter colour variation
    n1 = nd.new("ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = 3.0; n1.inputs["Detail"].default_value = 4
    ln.new(tc.outputs["Object"], n1.inputs["Vector"])
    ramp = nd.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.016, 0.011, 0.007, 1)
    ramp.color_ramp.elements[1].color = (0.060, 0.034, 0.018, 1)
    # beech leaves: cells of lighter copper-brown
    vl = nd.new("ShaderNodeTexVoronoi"); vl.inputs["Scale"].default_value = 26; vl.inputs["Randomness"].default_value = 1
    ln.new(tc.outputs["Object"], vl.inputs["Vector"])
    leaf = nd.new("ShaderNodeMapRange"); leaf.inputs["From Min"].default_value = 0.55; leaf.inputs["From Max"].default_value = 0.95
    ln.new(vl.outputs["Color"], leaf.inputs["Value"])
    lmix = nd.new("ShaderNodeMath"); lmix.operation = "MULTIPLY"
    ln.new(leaf.outputs[0], lmix.inputs[0]); ln.new(n1.outputs["Fac"], lmix.inputs[1])
    ln.new(lmix.outputs[0], ramp.inputs["Fac"])
    # puddles: low-frequency noise mask, stronger on the track
    n2 = nd.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 0.8; n2.inputs["Detail"].default_value = 4
    ln.new(tc.outputs["Object"], n2.inputs["Vector"])
    trk = nd.new("ShaderNodeMath"); trk.operation = "ABSOLUTE"; ln.new(sep.outputs["X"], trk.inputs[0])
    trk2 = nd.new("ShaderNodeMapRange"); trk2.inputs["From Min"].default_value = 0.4; trk2.inputs["From Max"].default_value = 1.4
    trk2.inputs["To Min"].default_value = 0.12; trk2.inputs["To Max"].default_value = 0.0
    ln.new(trk.outputs[0], trk2.inputs["Value"])
    add = nd.new("ShaderNodeMath"); add.operation = "ADD"
    ln.new(n2.outputs["Fac"], add.inputs[0]); ln.new(trk2.outputs[0], add.inputs[1])
    pm = nd.new("ShaderNodeMapRange"); pm.inputs["From Min"].default_value = 0.60; pm.inputs["From Max"].default_value = 0.70
    ln.new(add.outputs[0], pm.inputs["Value"])  # 0 = litter, 1 = puddle
    rough = nd.new("ShaderNodeMapRange"); rough.inputs["To Min"].default_value = 0.42; rough.inputs["To Max"].default_value = 0.02
    ln.new(pm.outputs[0], rough.inputs["Value"])
    ln.new(rough.outputs[0], p.inputs["Roughness"])
    darken = nd.new("ShaderNodeMix"); darken.data_type = "RGBA"
    ln.new(pm.outputs[0], darken.inputs["Factor"])
    ln.new(ramp.outputs["Color"], darken.inputs["A"])
    darken.inputs["B"].default_value = (0.004, 0.004, 0.005, 1)
    ln.new(darken.outputs["Result"], p.inputs["Base Color"])
    # surface: coarse litter bump, and rain ripples animated in the puddles
    n3 = nd.new("ShaderNodeTexNoise"); n3.inputs["Scale"].default_value = 30; n3.inputs["Detail"].default_value = 2
    ln.new(tc.outputs["Object"], n3.inputs["Vector"])
    ripmap = nd.new("ShaderNodeMapping")
    ln.new(tc.outputs["Object"], ripmap.inputs["Vector"])
    ripmap.inputs["Location"].default_value = (0, 0, 0)
    ripmap.inputs["Location"].keyframe_insert("default_value", frame=1)
    ripmap.inputs["Location"].default_value = (0.0, 0.0, 40.0)
    ripmap.inputs["Location"].keyframe_insert("default_value", frame=1000)
    for fcu in m.node_tree.animation_data.action.fcurves:
        for kk in fcu.keyframe_points:
            kk.interpolation = "LINEAR"
    rip = nd.new("ShaderNodeTexNoise"); rip.inputs["Scale"].default_value = 14; rip.inputs["Detail"].default_value = 1
    ln.new(ripmap.outputs["Vector"], rip.inputs["Vector"])
    bmix = nd.new("ShaderNodeMix"); bmix.data_type = "FLOAT"
    ln.new(pm.outputs[0], bmix.inputs["Factor"])
    ln.new(n3.outputs["Fac"], bmix.inputs["A"])
    ln.new(rip.outputs["Fac"], bmix.inputs["B"])
    bump = nd.new("ShaderNodeBump"); bump.inputs["Distance"].default_value = 0.02
    bstr = nd.new("ShaderNodeMapRange"); bstr.inputs["To Min"].default_value = 0.35; bstr.inputs["To Max"].default_value = 0.06
    ln.new(pm.outputs[0], bstr.inputs["Value"]); ln.new(bstr.outputs[0], bump.inputs["Strength"])
    ln.new(bmix.outputs["Result"], bump.inputs["Height"])
    ln.new(bump.outputs["Normal"], p.inputs["Normal"])
    spec = nd.new("ShaderNodeMapRange"); spec.inputs["To Min"].default_value = 0.22; spec.inputs["To Max"].default_value = 0.8
    ln.new(pm.outputs[0], spec.inputs["Value"]); ln.new(spec.outputs[0], p.inputs["Specular IOR Level"])
    ob.data.materials.append(m)
    return ob


# --------------------------------------------------------------------------- trees
def bark_material():
    m, nd, ln = mat("beech_bark")
    p = principled(nd)
    tc = nd.new("ShaderNodeTexCoord")
    n1 = nd.new("ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = 2.5; n1.inputs["Detail"].default_value = 4
    ln.new(tc.outputs["Object"], n1.inputs["Vector"])
    ramp = nd.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.022, 0.024, 0.022, 1)
    ramp.color_ramp.elements[1].color = (0.085, 0.086, 0.080, 1)
    oi = nd.new("ShaderNodeObjectInfo")
    tone = nd.new("ShaderNodeMath"); tone.operation = "MULTIPLY_ADD"
    tone.inputs[1].default_value = 0.45; tone.inputs[2].default_value = 0.3
    ln.new(oi.outputs["Random"], tone.inputs[0])
    fac = nd.new("ShaderNodeMath"); fac.operation = "MULTIPLY"
    ln.new(n1.outputs["Fac"], fac.inputs[0]); ln.new(tone.outputs[0], fac.inputs[1])
    fac2 = nd.new("ShaderNodeMath"); fac2.operation = "MULTIPLY"; fac2.inputs[1].default_value = 1.4
    ln.new(fac.outputs[0], fac2.inputs[0])
    ln.new(fac2.outputs[0], ramp.inputs["Fac"])
    # wet green-dark streaks running down one side
    sep = nd.new("ShaderNodeSeparateXYZ"); ln.new(tc.outputs["Normal"], sep.inputs[0])
    moss = nd.new("ShaderNodeMapRange"); moss.inputs["From Min"].default_value = -0.2; moss.inputs["From Max"].default_value = 0.9
    ln.new(sep.outputs["Y"], moss.inputs["Value"])
    mix = nd.new("ShaderNodeMix"); mix.data_type = "RGBA"
    ln.new(moss.outputs[0], mix.inputs["Factor"])
    ln.new(ramp.outputs["Color"], mix.inputs["A"])
    mix.inputs["B"].default_value = (0.016, 0.022, 0.012, 1)
    ln.new(mix.outputs["Result"], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.38
    n2 = nd.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 14; n2.inputs["Detail"].default_value = 2
    ln.new(tc.outputs["Object"], n2.inputs["Vector"])
    bump = nd.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.25
    ln.new(n2.outputs["Fac"], bump.inputs["Height"]); ln.new(bump.outputs["Normal"], p.inputs["Normal"])
    return m


def trunk_mesh(name, r0, r1, h, segs=14, rings=0, flare=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r0, radius2=r1, depth=h)
    for v in bm.verts:
        v.co.z += h / 2
    if rings:
        side = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > h * 0.5]
        bmesh.ops.subdivide_edges(bm, edges=side, cuts=rings, use_grid_fill=False)
    if flare:
        for v in bm.verts:
            z = v.co.z / h
            s_ = 1 + flare * math.exp(-z * 40)
            v.co.x *= s_; v.co.y *= s_
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    return me


def make_forest(seed=7):
    rnd = random.Random(seed)
    bark = bark_material()
    base = trunk_mesh("trunk", 1.0, 0.72, 1.0, rings=12, flare=0.6)
    base.materials.append(bark)
    placed = []
    col = bpy.data.collections.new("forest"); bpy.context.scene.collection.children.link(col)
    tries = 0
    while len(placed) < 190 and tries < 20000:
        tries += 1
        x, y = rnd.uniform(-40, 40), rnd.uniform(-40, 40)
        if x * x + y * y < 5.5 ** 2:
            continue
        if y < -2 and abs(x) < 2.2:
            continue
        if any((x - px) ** 2 + (y - py) ** 2 < 3.2 ** 2 for px, py, _ in placed):
            continue
        r = rnd.choice([0.14, 0.18, 0.22, 0.26, 0.3, 0.36, 0.42])
        placed.append((x, y, r))
    for i, (x, y, r) in enumerate(placed):
        ob = bpy.data.objects.new(f"trunk{i}", base)
        ob.location = (x, y, ground_h(x, y) - 0.15)
        ob.scale = (r, r, rnd.uniform(16, 24))
        ob.rotation_euler = (rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05), rnd.uniform(0, 6.28))
        bend = ob.modifiers.new("bend", "SIMPLE_DEFORM"); bend.deform_method = "BEND"
        bend.angle = rnd.uniform(-0.25, 0.25); bend.deform_axis = "X"
        col.objects.link(ob)
    # undergrowth: thin saplings and dead sticks
    twig = trunk_mesh("twig", 1.0, 0.3, 1.0, segs=6); twig.materials.append(bark)
    for i in range(260):
        x, y = rnd.uniform(-30, 30), rnd.uniform(-30, 30)
        if x * x + y * y < 4.5 ** 2 or (y < -1 and abs(x) < 1.4):
            continue
        ob = bpy.data.objects.new(f"twig{i}", twig)
        ob.location = (x, y, ground_h(x, y) - 0.05)
        rr = rnd.uniform(0.008, 0.025)
        ob.scale = (rr, rr, rnd.uniform(0.6, 2.8))
        ob.rotation_euler = (rnd.uniform(-0.35, 0.35), rnd.uniform(-0.35, 0.35), 0)
        col.objects.link(ob)
    return placed


# --------------------------------------------------------------------------- fire
def fire_card(name, loc, w, h, strength, crop=(0.23, 0.66), frame_offset=0, alpha_gain=3.0, vcrop=(0.0, 1.0), seq=FIRE_DIR):
    """A billboard carrying the filmed bonfire, keyed on luminance."""
    me = bpy.data.meshes.new(name)
    u0, u1 = crop
    me.from_pydata([(-w / 2, 0, 0), (w / 2, 0, 0), (w / 2, 0, h), (-w / 2, 0, h)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new()
    v0, v1 = vcrop
    for li, (u, v) in zip(range(4), [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]):
        uv.data[li].uv = (u, v)
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    bpy.context.scene.collection.objects.link(ob)
    ob.visible_shadow = False
    ob.visible_diffuse = False  # real lights do the lighting; the card is for eyes and reflections
    m, nd, ln = mat(name + "_m")
    for n in list(nd):
        nd.remove(n)
    out = nd.new("ShaderNodeOutputMaterial")
    img = bpy.data.images.load(os.path.join(seq, "f_0001.png"))
    img.source = "SEQUENCE"
    tex = nd.new("ShaderNodeTexImage"); tex.image = img
    tex.image_user.frame_duration = 480
    tex.image_user.frame_start = 1
    tex.image_user.frame_offset = 0
    tex.image_user.use_cyclic = True
    tex.image_user.use_auto_refresh = True
    tex.extension = "CLIP"
    em = nd.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = strength
    ln.new(tex.outputs["Color"], em.inputs["Color"])
    tr = nd.new("ShaderNodeBsdfTransparent")
    bw = nd.new("ShaderNodeRGBToBW"); ln.new(tex.outputs["Color"], bw.inputs[0])
    gain = nd.new("ShaderNodeMath"); gain.operation = "MULTIPLY"; gain.use_clamp = True
    gain.inputs[1].default_value = alpha_gain
    ln.new(bw.outputs[0], gain.inputs[0])
    mix = nd.new("ShaderNodeMixShader")
    ln.new(gain.outputs[0], mix.inputs[0]); ln.new(tr.outputs[0], mix.inputs[1]); ln.new(em.outputs[0], mix.inputs[2])
    ln.new(mix.outputs[0], out.inputs["Surface"])
    ob.data.materials.append(m)
    return ob


def track_to(ob, target, lock_z=True):
    c = ob.constraints.new("DAMPED_TRACK" if not lock_z else "LOCKED_TRACK")
    c.target = target
    if lock_z:
        c.track_axis = "TRACK_NEGATIVE_Y"
        c.lock_axis = "LOCK_Z"
    return c


def fire_lights(seed=3, frames=(1, 800)):
    rnd = random.Random(seed)
    lights = []
    gz = ground_h(0, 0)
    for i, (off, pw) in enumerate([((0, 0.55, gz + 1.5), 3200), ((0.6, 0.85, gz + 2.3), 2200), ((-0.55, 0.45, gz + 1.1), 2000),
                                   ((0.1, -0.75, gz + 0.35), 160)]):
        ld = bpy.data.lights.new(f"fire{i}", "POINT")
        ld.color = (1.0, 0.42, 0.11)
        ld.shadow_soft_size = 0.7
        ob = bpy.data.objects.new(f"fire{i}", ld)
        ob.location = off
        bpy.context.scene.collection.objects.link(ob)
        # smoothed random flicker
        v = 1.0
        for f in range(frames[0], frames[1] + 1, 2):
            v = 0.7 * v + 0.3 * rnd.uniform(0.55, 1.35)
            ld.energy = pw * v
            ld.keyframe_insert("energy", frame=f)
        lights.append(ob)
    return lights


def logs_and_bundle():
    rnd = random.Random(11)
    char, nd, ln = mat("charred")
    p = principled(nd)
    p.inputs["Base Color"].default_value = (0.004, 0.0035, 0.003, 1)
    p.inputs["Roughness"].default_value = 0.85
    p.inputs["Specular IOR Level"].default_value = 0.2
    tc = nd.new("ShaderNodeTexCoord")
    nz = nd.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 9; nz.inputs["Detail"].default_value = 4
    ln.new(tc.outputs["Object"], nz.inputs["Vector"])
    em = nd.new("ShaderNodeMapRange"); em.inputs["From Min"].default_value = 0.62; em.inputs["From Max"].default_value = 0.75
    ln.new(nz.outputs["Fac"], em.inputs["Value"])
    p.inputs["Emission Color"].default_value = (1.0, 0.25, 0.04, 1)
    emx = nd.new("ShaderNodeMath"); emx.operation = "MULTIPLY"; emx.inputs[1].default_value = 6.0
    ln.new(em.outputs[0], emx.inputs[0]); ln.new(emx.outputs[0], p.inputs["Emission Strength"])
    bump = nd.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.6
    ln.new(nz.outputs["Fac"], bump.inputs["Height"]); ln.new(bump.outputs["Normal"], p.inputs["Normal"])
    log = trunk_mesh("log", 1.0, 0.9, 1.0, segs=10); log.materials.append(char)
    for i in range(10):
        ob = bpy.data.objects.new(f"log{i}", log)
        a = rnd.uniform(0, 6.28)
        rr = rnd.uniform(0.04, 0.11)
        L = rnd.uniform(0.9, 2.2)
        ob.scale = (rr, rr, L)
        ob.location = (math.cos(a) * 1.1, math.sin(a) * 1.1, ground_h(0, 0) - 0.05)
        # lean inward like a pile
        ob.rotation_euler = Euler((rnd.uniform(0.9, 1.3), 0, a + math.pi / 2), "XYZ")
        ob.rotation_euler = (Vector((0, 0, 1)).rotation_difference(Vector((-math.cos(a), -math.sin(a), rnd.uniform(0.3, 0.9)))).to_euler())
        bpy.context.scene.collection.objects.link(ob)
    # the bundle: roughly 70 cm, blanket-wrapped, partly burnt, melted plastic
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=6, use_grid_fill=True)
    for v in bm.verts:
        v.co = v.co.normalized() * 0.5 * 0.55 + v.co * 0.45
    me = bpy.data.meshes.new("bundle"); bm.to_mesh(me); bm.free()
    for pz in me.polygons:
        pz.use_smooth = True
    ob = bpy.data.objects.new("bundle", me)
    ob.scale = (0.72, 0.36, 0.26)
    ob.rotation_euler = (0.08, -0.12, 0.5)
    ob.location = (0.05, -0.15, ground_h(0, 0) + 0.28)
    bpy.context.scene.collection.objects.link(ob)
    disp = ob.modifiers.new("folds", "DISPLACE")
    tx = bpy.data.textures.new("folds", "CLOUDS"); tx.noise_scale = 0.25
    disp.texture = tx; disp.strength = 0.09
    ob.modifiers.new("sub", "SUBSURF").levels = 2
    bm_m, nd, ln = mat("blanket_burnt")
    p = principled(nd)
    tc = nd.new("ShaderNodeTexCoord")
    wv = nd.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 3.0; wv.inputs["Distortion"].default_value = 6
    ln.new(tc.outputs["Object"], wv.inputs["Vector"])
    nz = nd.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 7; nz.inputs["Detail"].default_value = 6
    ln.new(tc.outputs["Object"], nz.inputs["Vector"])
    burnt = nd.new("ShaderNodeMapRange"); burnt.inputs["From Min"].default_value = 0.40; burnt.inputs["From Max"].default_value = 0.50
    ln.new(nz.outputs["Fac"], burnt.inputs["Value"])
    col = nd.new("ShaderNodeMix"); col.data_type = "RGBA"
    ln.new(burnt.outputs[0], col.inputs["Factor"])
    col.inputs["A"].default_value = (0.035, 0.020, 0.013, 1)  # scorched wool, brownish
    col.inputs["B"].default_value = (0.008, 0.007, 0.007, 1)  # char
    ln.new(col.outputs["Result"], p.inputs["Base Color"])
    rough = nd.new("ShaderNodeMapRange"); rough.inputs["To Min"].default_value = 0.85; rough.inputs["To Max"].default_value = 0.12
    plastic = nd.new("ShaderNodeMapRange"); plastic.inputs["From Min"].default_value = 0.70; plastic.inputs["From Max"].default_value = 0.72
    ln.new(wv.outputs["Fac"], plastic.inputs["Value"])
    ln.new(plastic.outputs[0], rough.inputs["Value"]); ln.new(rough.outputs[0], p.inputs["Roughness"])
    ember = nd.new("ShaderNodeMapRange"); ember.inputs["From Min"].default_value = 0.585; ember.inputs["From Max"].default_value = 0.60
    ember.inputs["To Max"].default_value = 2.2
    ln.new(nz.outputs["Fac"], ember.inputs["Value"])
    emb2 = nd.new("ShaderNodeMath"); emb2.operation = "MULTIPLY"
    ln.new(ember.outputs[0], emb2.inputs[0])
    inv = nd.new("ShaderNodeMapRange"); inv.inputs["From Min"].default_value = 0.60; inv.inputs["From Max"].default_value = 0.615
    inv.inputs["To Min"].default_value = 1.0; inv.inputs["To Max"].default_value = 0.0
    ln.new(nz.outputs["Fac"], inv.inputs["Value"]); ln.new(inv.outputs[0], emb2.inputs[1])
    p.inputs["Emission Color"].default_value = (1.0, 0.28, 0.05, 1)
    ln.new(emb2.outputs[0], p.inputs["Emission Strength"])
    bump = nd.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.5
    ln.new(wv.outputs["Fac"], bump.inputs["Height"]); ln.new(bump.outputs["Normal"], p.inputs["Normal"])
    ob.data.materials.append(bm_m)
    return ob


# --------------------------------------------------------------------------- children
def capsule(name, r0, r1, length, origin_top=True, segs=16):
    """Tapered capsule along -Z from its origin (joint at the origin)."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r1, radius2=r0, depth=length)
    for v in bm.verts:
        v.co.z -= length / 2
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    s = ob.modifiers.new("s", "SUBSURF"); s.levels = 2; s.render_levels = 2
    return ob


def blob(name, radius, scale=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=16, radius=radius)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    ob.scale = scale
    bpy.context.scene.collection.objects.link(ob)
    return ob


def rain_gear(name, rgb):
    m, nd, ln = mat(name)
    p = principled(nd)
    p.inputs["Base Color"].default_value = (*rgb, 1)
    p.inputs["Roughness"].default_value = 0.45
    p.inputs["Coat Weight"].default_value = 0.35
    p.inputs["Coat Roughness"].default_value = 0.12
    tc = nd.new("ShaderNodeTexCoord")
    # creases: stretched noise so the fabric folds run downward
    mp = nd.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (22, 22, 5)
    ln.new(tc.outputs["Object"], mp.inputs["Vector"])
    nz = nd.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0; nz.inputs["Detail"].default_value = 4
    ln.new(mp.outputs["Vector"], nz.inputs["Vector"])
    bump = nd.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.35
    ln.new(nz.outputs["Fac"], bump.inputs["Height"]); ln.new(bump.outputs["Normal"], p.inputs["Normal"])
    ln.new(bump.outputs["Normal"], p.inputs["Coat Normal"])
    return m


def boot_mat(rgb):
    m, nd, ln = mat("boot")
    p = principled(nd); p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = 0.18
    return m


def make_child(name, height, coat_rgb, boot_rgb):
    """Rain-suited child built from soft primitives, rigged by parenting.

    Joints: root (feet on ground) -> pelvis -> torso -> hood; pelvis -> legs -> boots;
    torso -> arms. Scale everything from a 1.20 m reference child.
    """
    k = height / 1.20
    coat = rain_gear(name + "_coat", coat_rgb)
    bootm = boot_mat(boot_rgb)
    root = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(root)
    pelvis = bpy.data.objects.new(name + "_pelvis", None); bpy.context.scene.collection.objects.link(pelvis)
    pelvis.parent = root; pelvis.location = (0, 0, 0.56 * k)
    torso = capsule(name + "_torso", 0.135 * k, 0.21 * k, 0.56 * k)  # coat flares at the hem
    torso.parent = pelvis; torso.location = (0, 0, 0.52 * k)
    torso.data.materials.append(coat)
    hood = blob(name + "_hood", 0.125 * k, (1.0, 1.12, 1.08)); hood.parent = torso; hood.location = (0, 0.02 * k, 0.08 * k)
    hood.data.materials.append(coat)
    peak = blob(name + "_peak", 0.06 * k, (1.4, 0.8, 0.5)); peak.parent = hood; peak.location = (0, -0.1 * k, 0.07 * k)
    peak.data.materials.append(coat)
    shade = blob(name + "_shade", 0.1 * k, (0.9, 0.5, 0.9)); shade.parent = hood; shade.location = (0, -0.07 * k, -0.01 * k)
    dm, nd, ln = mat("hood_dark"); principled(nd).inputs["Base Color"].default_value = (0.004, 0.003, 0.003, 1)
    principled(nd).inputs["Roughness"].default_value = 0.9
    shade.data.materials.append(dm)
    parts = {"root": root, "pelvis": pelvis, "torso": torso, "hood": hood}
    for side, sx in (("L", 1), ("R", -1)):
        arm = capsule(f"{name}_arm{side}", 0.05 * k, 0.045 * k, 0.40 * k)
        arm.parent = torso; arm.location = (sx * 0.15 * k, 0, -0.02 * k)
        arm.rotation_euler = (0, sx * -0.12, 0)
        arm.data.materials.append(coat)
        leg = capsule(f"{name}_leg{side}", 0.07 * k, 0.06 * k, 0.44 * k)
        leg.parent = pelvis; leg.location = (sx * 0.075 * k, 0, 0)
        leg.data.materials.append(coat)
        boot = capsule(f"{name}_boot{side}", 0.055 * k, 0.06 * k, 0.16 * k)
        boot.parent = leg; boot.location = (0, 0, -0.38 * k)
        boot.data.materials.append(bootm)
        toe = blob(f"{name}_toe{side}", 0.05 * k, (1.0, 1.9, 0.75)); toe.parent = boot; toe.location = (0, -0.05 * k, -0.15 * k)
        toe.data.materials.append(bootm)
        parts["arm" + side] = arm; parts["leg" + side] = leg
    return parts


def animate_walk(parts, path, f0, f1, step_len=0.40, stride_deg=26, phase=0.0, idle_after=None, facing=None):
    """Keyframe a walk along path(t)->(x,y); t in [0,1] over frames f0..f1.

    Leg phase is driven by distance travelled, so feet never skate when the
    children slow down near the fire.
    """
    root = parts["root"]
    dist = 0.0
    prev = path(0.0)
    heading = facing if facing is not None else 0.0
    for f in range(f0, f1 + 1):
        t = (f - f0) / max(1, (f1 - f0))
        x, y = path(t)
        step = math.hypot(x - prev[0], y - prev[1])
        dist += step
        speed = step * FPS
        if facing is None and step > 1e-5:
            heading = math.atan2(x - prev[0], -(y - prev[1]))
        prev = (x, y)
        root.location = (x, y, ground_h(x, y))
        root.rotation_euler = (0, 0, heading)
        root.keyframe_insert("location", frame=f)
        root.keyframe_insert("rotation_euler", frame=f)
        walking = (idle_after is None or f < idle_after) and speed > 0.05
        ph = math.pi * dist / step_len + phase
        amp = math.radians(stride_deg) * min(1.0, speed / 0.6) if walking else 0.0
        sw = amp * math.sin(ph)
        parts["legL"].rotation_euler = (sw, 0, 0); parts["legR"].rotation_euler = (-sw, 0, 0)
        parts["armL"].rotation_euler = (-0.55 * sw, -0.06, 0); parts["armR"].rotation_euler = (0.55 * sw, 0.06, 0)
        bob = 0.02 * abs(math.sin(ph)) * (amp / math.radians(stride_deg) if stride_deg else 0) + 0.004 * math.sin(f / FPS * 1.7)
        parts["pelvis"].location.z = parts["_pelvis_h"] + bob
        parts["pelvis"].rotation_euler = (0.05 if walking else 0.025, 0.03 * math.sin(ph) * (1 if walking else 0), 0)
        for n in ("legL", "legR", "armL", "armR"):
            parts[n].keyframe_insert("rotation_euler", frame=f)
        parts["pelvis"].keyframe_insert("location", frame=f)
        parts["pelvis"].keyframe_insert("rotation_euler", frame=f)


# --------------------------------------------------------------------------- world, camera, render
def world():
    w = bpy.data.worlds.new("dusk"); bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.020, 0.028, 0.042, 1)
    bg.inputs["Strength"].default_value = 1.0
    sky = bpy.data.lights.new("sky", "AREA"); sky.energy = 350; sky.size = 60; sky.color = (0.55, 0.68, 0.9)
    ob = bpy.data.objects.new("sky", sky); ob.location = (0, 0, 30)
    bpy.context.scene.collection.objects.link(ob)


def camera(name, lens=32, fstop=2.8, sensor=36):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.sensor_width = sensor
    cd.dof.use_dof = True; cd.dof.aperture_fstop = fstop
    cd.clip_end = 400
    ob = bpy.data.objects.new(name, cd); bpy.context.scene.collection.objects.link(ob)
    bpy.context.scene.camera = ob
    return ob


def aim(cam, eye, target, roll=0.0):
    cam.location = eye
    d = Vector(target) - Vector(eye)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    cam.rotation_euler.rotate_axis("Z", roll)


def handheld(f, amp=1.0, seed=0.0):
    t = f / FPS
    return (amp * (0.004 * math.sin(1.3 * t + seed) + 0.002 * math.sin(3.7 * t + 2 * seed)),
            amp * (0.003 * math.sin(1.1 * t + 1 + seed) + 0.0015 * math.sin(4.1 * t + seed)),
            amp * (0.002 * math.sin(0.7 * t + 2 + seed)))


def key_cam(cam, f, eye, target, focus, amp=1.0, seed=0.0):
    aim(cam, eye, target)
    j = handheld(f, amp, seed)
    cam.rotation_euler.x += j[0]; cam.rotation_euler.z += j[1]; cam.rotation_euler.y += j[2]
    cam.data.dof.focus_distance = focus
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
    cam.data.dof.keyframe_insert("focus_distance", frame=f)


def render_setup(samples, scale, frames, outdir):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.05
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    sc.cycles.max_bounces = 3; sc.cycles.diffuse_bounces = 1; sc.cycles.glossy_bounces = 1
    sc.cycles.use_fast_gi = True; sc.cycles.ao_bounces_render = 1
    sc.cycles.transmission_bounces = 2; sc.cycles.volume_bounces = 0; sc.cycles.transparent_max_bounces = 8
    sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
    sc.cycles.sample_clamp_indirect = 4.0
    sc.render.use_persistent_data = True
    sc.render.resolution_x, sc.render.resolution_y = 1280, 536
    sc.render.resolution_percentage = scale
    sc.render.fps = FPS
    sc.render.use_motion_blur = False  # too slow on 2 cores; streaks come from the post pass
    sc.frame_start, sc.frame_end = frames
    sc.render.image_settings.file_format = "OPEN_EXR_MULTILAYER"
    sc.render.image_settings.color_depth = "16"
    sc.render.image_settings.exr_codec = "ZIP"
    sc.view_layers[0].use_pass_mist = True
    sc.world.mist_settings.start = 2.0
    sc.world.mist_settings.depth = 45.0
    sc.world.mist_settings.falloff = "QUADRATIC"
    sc.render.filepath = os.path.join(outdir, "f_####")
    sc.view_settings.view_transform = "Standard"


# --------------------------------------------------------------------------- shots
# Global timeline: frame 1 == 01:34.500 in the episode. Shot boundaries in seconds from there.
T0 = 94.5
def fr(t_episode):
    return int(round((t_episode - T0) * FPS)) + 1

SHOTS = {
    "S1": (94.5, 101.9), "S3": (106.0, 108.45), "S4": (108.45, 111.0), "S5": (111.0, 112.8),
    "S6": (112.8, 115.15), "S7": (115.15, 116.6), "S8": (116.6, 119.35),
}

KID_A = dict(name="kidA", height=1.24, coat_rgb=(0.72, 0.50, 0.03), boot_rgb=(0.03, 0.07, 0.03))  # yellow
KID_B = dict(name="kidB", height=1.08, coat_rgb=(0.05, 0.09, 0.22), boot_rgb=(0.20, 0.02, 0.02))  # navy, red boots
STAND_A, STAND_B = (-0.35, -3.3), (0.45, -3.65)   # where they stop, ~3 m from the fire


def build(shot):
    clear()
    sc = bpy.context.scene
    world()
    make_ground()
    make_forest()
    f_all = (1, fr(119.5) + 2)
    fire_lights(frames=f_all)
    logs_and_bundle()
    from kid_meta import make_child_meta
    dm, nd, ln = mat("hood_inside"); principled(nd).inputs["Base Color"].default_value = (0.003, 0.003, 0.003, 1)
    principled(nd).inputs["Roughness"].default_value = 0.95
    kids = []
    for spec in (KID_A, KID_B):
        p = make_child_meta(spec["name"], spec["height"], rain_gear(spec["name"] + "_gear", spec["coat_rgb"]),
                            boot_mat(spec["boot_rgb"]), dm)
        kids.append(p)
    cam = camera("cam")
    # fire cards (billboards aimed at the camera, Z locked)
    back = fire_card("fire_back", (0, 0.25, ground_h(0, 0) - 0.25), 3.3, 4.4, 9.0)
    front = fire_card("fire_front", (0.1, -0.55, ground_h(0, 0) - 0.05), 1.9, 1.4, 6.0, alpha_gain=2.2, vcrop=(0.0, 0.55),
                      seq=FIRE_DIR + "_b")
    for c in (back, front):
        track_to(c, cam)

    a, b = kids
    fs, fe = fr(SHOTS["S1"][0]), fr(119.5)
    # The walk: they come up the track from far back, slow as they near the fire, stop.
    stop_f = fr(104.2)
    def pathA(t):
        y = -14.0 + (STAND_A[1] + 14.0) * (1 - (1 - t) ** 1.4)
        return (STAND_A[0] + 0.12 * math.sin(t * 3) * (1 - t), y)
    def pathB(t):
        y = -14.9 + (STAND_B[1] + 14.9) * (1 - (1 - t) ** 1.4)
        return (STAND_B[0] + 0.1 * math.sin(t * 2.3 + 1) * (1 - t), y)
    animate_walk(a, pathA, fs, stop_f, step_len=0.42, stride_deg=26)
    animate_walk(b, pathB, fs, stop_f, step_len=0.36, stride_deg=27, phase=1.3)
    # hold still (idle sway) after stopping; face the fire
    for p, st in ((a, STAND_A), (b, STAND_B)):
        face = math.atan2(0 - st[0], -(0 - st[1]))
        animate_walk(p, lambda t, st=st: st, stop_f + 1, fe, idle_after=stop_f, facing=face)

    # B steps back on "Affald?" (S7): slide root back a little with one leg move
    s7a, s7b = fr(117.0), fr(118.1)
    for f in range(s7a, s7b + 1):
        t = (f - s7a) / (s7b - s7a)
        e = 0.5 - 0.5 * math.cos(math.pi * t)
        x, y = STAND_B[0], STAND_B[1] - 0.32 * e
        b["root"].location = (x, y, ground_h(x, y)); b["root"].keyframe_insert("location", frame=f)
        b["legR"].rotation_euler = (math.radians(-24) * math.sin(math.pi * t), 0, 0)
        b["legR"].keyframe_insert("rotation_euler", frame=f)

    # ---------------- cameras per shot
    s0, s1 = SHOTS[shot]
    f0, f1 = fr(s0), fr(s1)
    if shot == "S1":
        for f in range(f0, f1 + 1):
            t = (f - f0) / (f1 - f0)
            ay = pathA(min(1, (f - fs) / (stop_f - fs)))[1]
            cy = -19.2 + (ay + 14.0) * 0.55
            eye = (0.12 - 0.08 * t, cy, 1.08)
            key_cam(cam, f, eye, (0.1, 0, 0.95), focus=abs(eye[1] - ay) + 0.2, amp=1.0)
        cam.data.lens = 32; cam.data.dof.aperture_fstop = 2.2
    elif shot == "S3":
        for f in range(f0, f1 + 1):
            t = (f - f0) / (f1 - f0)
            eye = (0.10, -7.6 + 0.3 * t, 1.02)
            key_cam(cam, f, eye, (0.05, -0.2, 0.25), focus=7.4 - 0.3 * t, amp=0.8, seed=2)
        cam.data.lens = 45; cam.data.dof.aperture_fstop = 2.2
    elif shot in ("S4", "S6"):
        base = (1.2, -3.6, 0.85) if shot == "S4" else (-1.35, -2.9, 0.35)
        for f in range(f0, f1 + 1):
            t = (f - f0) / (f1 - f0)
            k = 0.10 * t
            eye = (base[0] * (1 - k), base[1] * (1 - k), base[2] - 0.05 * t)
            tgt = (0.05, -0.15, ground_h(0, 0) + 0.3)
            key_cam(cam, f, eye, tgt, focus=(Vector(eye) - Vector(tgt)).length, amp=0.6, seed=4 if shot == "S4" else 7)
        cam.data.lens = 85 if shot == "S4" else 100; cam.data.dof.aperture_fstop = 2.0
    elif shot == "S5":
        for f in range(f0, f1 + 1):
            t = (f - f0) / (f1 - f0)
            eye = (-1.1 + 0.15 * t, -8.6 + 0.2 * t, 0.30)
            key_cam(cam, f, eye, (0.0, -1.2, 1.25), focus=(Vector(eye) - Vector((0.0, -3.5, 0.8))).length, amp=0.7, seed=5)
        cam.data.lens = 35; cam.data.dof.aperture_fstop = 2.4
    elif shot == "S7":
        for f in range(f0, f1 + 1):
            t = (f - f0) / (f1 - f0)
            eye = (0.55 - 0.05 * t, -2.7 + 0.12 * t, -0.25)
            tgt = (0.05, -0.15, ground_h(0, 0) + 0.25)
            key_cam(cam, f, eye, tgt, focus=(Vector(eye) - Vector(tgt)).length, amp=0.5, seed=9)
        cam.data.lens = 85; cam.data.dof.aperture_fstop = 1.8
    elif shot == "S8":
        for f in range(f0, f1 + 1):
            t = (f - f0) / (f1 - f0)
            eye = (3.0, -24.0 + 0.3 * t, 1.5)
            key_cam(cam, f, eye, (0.2, 0, 1.2), focus=21.0, amp=0.35, seed=11)
        cam.data.lens = 50; cam.data.dof.aperture_fstop = 4.0
    return (f0, f1), cam


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("shot")
    ap.add_argument("--frames", nargs=2, type=int)
    ap.add_argument("--samples", type=int, default=16)
    ap.add_argument("--scale", type=int, default=100)
    ap.add_argument("--out", default=None)
    ap.add_argument("--save", default=None)
    ap.add_argument("--step", type=int, default=1)
    a = ap.parse_args(argv)
    (f0, f1), cam = build(a.shot)
    if a.frames:
        f0, f1 = a.frames
    out = a.out or os.path.join(ROOT, "render", a.shot)
    os.makedirs(out, exist_ok=True)
    render_setup(a.samples, a.scale, (f0, f1), out)
    bpy.context.scene.frame_step = a.step
    if a.save:
        bpy.ops.wm.save_as_mainfile(filepath=a.save)
    # where the fire is on screen, per frame, for the post pass
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    meta = {}
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        p = world_to_camera_view(sc, cam, Vector((0, 0, ground_h(0, 0) + 1.0)))
        meta[str(f)] = [p.x, p.y, p.z]
    import json
    json.dump(meta, open(os.path.join(out, "meta.json"), "w"))
    import time
    t = time.time()
    bpy.ops.render.render(animation=True)
    print(f"RENDERED {a.shot} {f0}-{f1} in {time.time() - t:.1f}s")


if __name__ == "__main__":
    main()
