"""Dexteria v5.1: one continuous scroll film, told through the team's 6 features.

v5.1 = v5 re-timed so it flows like one camera move: every transition gets 2 to 3 times more
frames, the camera starts moving before the previous action ends (overlapping action),
and every hold has a slow drift, so the picture is never completely still.

  ch  frames    feature                      what happens
  0   1-24      intro                        closed ball resting on the floor, slow push in
  1   25-62     grip (FR2, FR6, FR7)         ball floats up, the cutaway slides out sideways,
                                             the soft layers squeeze (50-56) and relax (56-62)
  2   63-114    movement + tremor (FR3, FR4) dive to the motion sensor, pull back while the cutaway
                                             slides back in, steady arc (98-106), shaky return (106-114)
  3   115-150   guided games (FR5,18,25)     ball settles, power button close-up, press, LEDs light up,
                                             the ball squeezes (142-146) and relaxes (146-150)
  4   151-184   progress (FR20, FR22)        ball lifts, dock slides in, ball drops onto the dock
  5   185-236   difficulty (FR8, FR10, FR11) ball turns in its dock, the top half opens on the
                                             mould parting line, the firmness insert is swapped
  6   237-266   sharing (FR26, FR27, FR32)   ball turns back, wide closing shot

How "nothing passes through anything" is guaranteed:
  - the cutaway pieces only slide in the direction that keeps them inside their own quarter
  - the parting-line halves only lift along the parting-line axis, outer layers always above
    inner layers
  - the squeeze pivot sits at the electronics, so the bladder moves away from the boards

Run:  Blender -b --python film51.py
Saves 3d/v5/film51.blend and 3d/v5/anchors51.json (per-frame screen positions for the website).
"""
import bpy, bmesh, sys, os, math, json
from mathutils import Vector, Quaternion
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
V5 = os.path.dirname(HERE)
ROOT3D = os.path.dirname(V5)
sys.path.insert(0, os.path.join(ROOT3D, "v3", "scripts"))
import studio

W, H = 1920, 1080
N = 266
CH = [(1, 24), (25, 62), (63, 114), (115, 150), (151, 184), (185, 236), (237, 266)]

bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT3D, "v3", "dexteria-ball-v3.blend"))
sc = bpy.context.scene
OB = bpy.data.objects
COL = bpy.data.collections["Dexteria_Ball"]

PAD_DIR = Vector((-0.40, -1.0, 0.04)).normalized()   # logo panel axis = normal of the parting line
BTN_DIR = Vector((0.66, -0.58, 0.50)).normalized()
DZ = -1.0 - 0.02
FLOOR = DZ - 0.255                                    # one floor for the whole film (dock height)
REST = -0.275                                         # ball centre height when resting on the floor

for o in list(OB):
    if o.type in ('LIGHT', 'CAMERA') or o.name.startswith("Cyclorama"):
        OB.remove(o)
if "Studio_v3" in bpy.data.collections:
    bpy.data.collections.remove(bpy.data.collections["Studio_v3"])


# ------------------------------------------------------------------ helpers
def reparent(o, p):
    mw = o.matrix_world.copy(); o.parent = p; o.matrix_world = mw

def empty(name, loc=(0, 0, 0), parent=None):
    e = OB.new(name, None); COL.objects.link(e); e.location = loc
    if parent: reparent(e, parent)
    return e

def key(o, path, frame, value):
    setattr(o, path, value); o.keyframe_insert(path, frame=frame)

def keys(o, path, pairs):
    for f, v in pairs: key(o, path, f, v)

def all_fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    act = ad.action
    if hasattr(act, "fcurves") and len(getattr(act, "fcurves", [])): return list(act.fcurves)
    out = []
    for layer in act.layers:
        for strip in layer.strips:
            for cb in strip.channelbags: out += list(cb.fcurves)
    return out

def interp(idb, mode, lo=-1e9, hi=1e9, path=None):
    for fc in all_fcurves(idb):
        if path and path not in fc.data_path: continue
        for kp in fc.keyframe_points:
            if lo <= kp.co.x <= hi:
                kp.interpolation = mode
                if mode == 'BEZIER': kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
        fc.update()

def smooth(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)

def hide_keys(objs, pairs):
    """pairs: (frame, hidden). Applied to the objects and all their children."""
    done = set()
    for o in objs:
        for x in [o] + list(o.children_recursive):
            if x.name in done or x.name == "Chassis_Lid": continue   # the clear lid stays off (it reads as a white veil)
            done.add(x.name)
            for f, h in pairs:
                x.hide_render = h; x.keyframe_insert("hide_render", frame=f)

def split(o, normal):
    """Cut a closed mesh on the plane through the origin with this normal (capped, solid)."""
    def cutter():
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=6.0)
        me = bpy.data.meshes.new("cut"); bm.to_mesh(me); bm.free()
        c = OB.new("tmp_cut", me); sc.collection.objects.link(c)
        c.rotation_mode = 'QUATERNION'; c.rotation_quaternion = normal.to_track_quat('Z', 'Y')
        c.location = normal * 3.0
        return c
    base = o.name
    plus = o.copy(); plus.data = o.data.copy()
    for c in o.users_collection: c.objects.link(plus)
    for obj, op in ((plus, 'INTERSECT'), (o, 'DIFFERENCE')):
        c = cutter()
        m = obj.modifiers.new("split", 'BOOLEAN'); m.operation = op; m.object = c
        try: m.solver = 'MANIFOLD'
        except TypeError: m.solver = 'EXACT'
        bpy.context.view_layer.objects.active = obj
        with bpy.context.temp_override(object=obj, active_object=obj):
            bpy.ops.object.modifier_apply(modifier=m.name)
        OB.remove(c)
    plus.name = base + "_Top"; o.name = base + "_Bottom"
    return plus, o


# ------------------------------------------------------------------ materials: no chapter glow, honest TPU
for o in OB:
    if "glow" in o.keys(): o["glow"] = 0.0
bm_ = bpy.data.materials.get("Air_Bladder_TPU_v3")
if bm_:
    b = next(n for n in bm_.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    if not b.inputs["Base Color"].is_linked: b.inputs["Base Color"].default_value = (*studio.srgb("#E8EBE2"), 1)
    for nm, v in (("Transmission Weight", 0.6), ("Roughness", 0.26)):
        if nm in b.inputs and not b.inputs[nm].is_linked: b.inputs[nm].default_value = v


# ------------------------------------------------------------------ hierarchy
root = empty("Ball_Root")
for o in list(COL.objects):
    if o.parent is None and o is not root and o.name != "Dock":
        reparent(o, root)
root.rotation_mode = 'QUATERNION'
dock = OB["Dock"]

# 1. cut shell + outer foam + mid foam (and their cutaway quarters) on the parting line
P = {}
for layer in ("Shell", "Foam_Outer", "Foam_Mid"):
    for n in (layer, layer + "_Wedge"):
        t, b = split(OB[n], PAD_DIR)
        P[n + "_Top"] = t; P[n + "_Bottom"] = b

# 2. squeeze pivot: at the electronics (x) and the ball bottom (z)
sq = empty("Squash", (0.2, 0.0, -1.0), root)

# 3. top halves lift on the parting line; the cutaway quarters slide inside their own groups
lift_shell = empty("Lift_Shell", (0, 0, 0), sq)
lift_outer = empty("Lift_Outer", (0, 0, 0), sq)
ins_old = empty("Insert_Old", (0, 0, 0), sq)
ins_new = empty("Insert_New", (0, 0, 0), sq)
slides = {}
def slide_group(name, parent, objs):
    e = empty(name, (0, 0, 0), parent)
    for o in objs: reparent(o, e)
    slides[name] = e
    return e

for o in (P["Shell_Top"], OB["Power_Button"], OB["Power_Button_Switch"]): reparent(o, lift_shell)
slide_group("Slide_Shell_T", lift_shell, [P["Shell_Wedge_Top"]])
reparent(P["Foam_Outer_Top"], lift_outer); slide_group("Slide_Outer_T", lift_outer, [P["Foam_Outer_Wedge_Top"]])
reparent(P["Foam_Mid_Top"], ins_old); slide_group("Slide_Mid_T", ins_old, [P["Foam_Mid_Wedge_Top"]])
for n in ("Shell_Bottom", "Foam_Outer_Bottom", "Foam_Mid_Bottom"): reparent(P[n], sq)
slide_group("Slide_Shell_B", sq, [P["Shell_Wedge_Bottom"]])
slide_group("Slide_Outer_B", sq, [P["Foam_Outer_Wedge_Bottom"]])
slide_group("Slide_Mid_B", sq, [P["Foam_Mid_Wedge_Bottom"]])
slide_group("Slide_Liner", sq, [OB["Foam_Liner_Wedge"]])
for n in ("Foam_Liner", "Air_Bladder", "Contact_1", "Contact_2", "Button_Flex_Cable"):
    reparent(OB[n], sq)

# 4. the new, firmer insert: same shape as the mid foam top, sage foam
mid = P["Foam_Mid_Top"].active_material
firm = mid.copy(); firm.name = "Foam_Insert_Firm"
nt = firm.node_tree; bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
hs = nt.nodes.new("ShaderNodeHueSaturation")
hs.inputs["Hue"].default_value = 0.69; hs.inputs["Saturation"].default_value = 0.85; hs.inputs["Value"].default_value = 0.42
if bsdf.inputs["Base Color"].is_linked: nt.links.new(bsdf.inputs["Base Color"].links[0].from_socket, hs.inputs["Color"])
else: hs.inputs["Color"].default_value = bsdf.inputs["Base Color"].default_value
nt.links.new(hs.outputs["Color"], bsdf.inputs["Base Color"])
for o in (P["Foam_Mid_Top"], P["Foam_Mid_Wedge_Top"]):
    c = o.copy(); c.data = o.data.copy(); c.name = o.name.replace("Foam_Mid", "Insert_Firm")
    for col in o.users_collection: col.objects.link(c)
    c.data.materials.clear(); c.data.materials.append(firm)
    for p in c.data.polygons: p.material_index = 0
    reparent(c, ins_new)


# ================================================================== animation
sc.frame_start, sc.frame_end = 1, N
sc.render.fps = 24
V = Vector

# ---- ball root: rest, float (grip + movement), settle, lift onto the dock, turn (difficulty)
keys(root, "location", [(1, V((0, 0, REST))), (24, V((0, 0, REST))), (36, V((0, 0, REST + 0.3))), (97, V((0, 0, REST + 0.3)))])
# movement: one key per frame (steady arc 98-106, shaky return 106-114)
for f in range(98, 115):
    if f <= 106:
        t = smooth((f - 98) / 8); x = 0.5 * t; wob = V((0, 0, 0)); wr = 0.0
    else:
        t = smooth((f - 106) / 8); x = 0.5 * (1 - t)
        ph = (f - 106) * 2 * math.pi / 2.6
        env = math.sin(math.pi * (f - 106) / 8)
        wob = V((0.03 * math.sin(ph), 0.012 * math.sin(ph * 1.7 + 1), 0.026 * math.sin(ph * 1.3 + 2))) * env
        wr = math.radians(2.4) * math.sin(ph * 1.1 + 0.5) * env
    z = REST + 0.3 + 0.2 * math.sin(math.pi * x / 0.5)
    key(root, "location", f, V((x, 0.1 * math.sin(math.pi * x / 0.5), z)) + wob)
    key(root, "rotation_quaternion", f, Quaternion((0, 0, 1), math.radians(18) * x / 0.5) @ Quaternion((1, 0, 0), wr))
key(root, "rotation_quaternion", 1, Quaternion()); key(root, "rotation_quaternion", 97, Quaternion())
key(root, "rotation_quaternion", 124, Quaternion())
keys(root, "location", [(124, V((0, 0, REST))), (151, V((0, 0, REST))), (161, V((0, 0, 0.75))), (164, V((0, 0, 0.75))),
                        (169, V((0, 0, 0.0))), (171, V((0, 0, 0.035))), (173, V((0, 0, 0.0))), (N, V((0, 0, 0.0)))])
ROT = Quaternion((0, 0, 1), math.radians(-35)) @ PAD_DIR.rotation_difference(V((0, 0, 1)))
keys(root, "rotation_quaternion", [(185, Quaternion()), (197, ROT), (236, ROT), (251, Quaternion()), (N, Quaternion())])
interp(root, 'BEZIER')
interp(root, 'LINEAR', 98, 114)
interp(root, 'QUAD', 164, 164, path="location")      # the drop accelerates like a real fall
for fc in all_fcurves(root):
    if "location" in fc.data_path:
        for kp in fc.keyframe_points:
            if kp.co.x == 164: kp.easing = 'EASE_IN'

# ---- cutaway quarters slide out to the right (grip, 12 frames) and back (movement, 9 frames)
DW = V((1.0, -0.25, -0.08)).normalized()      # stays inside the quarter: +x, -y, -z only
for names, dist, out0, back0 in (
        (("Slide_Shell_T", "Slide_Shell_B"), 4.8, 30, 88),
        (("Slide_Outer_T", "Slide_Outer_B"), 4.4, 31, 87),
        (("Slide_Mid_T", "Slide_Mid_B"), 4.0, 32, 86),
        (("Slide_Liner",), 3.6, 33, 85)):
    for n in names:
        e = slides[n]
        keys(e, "location", [(1, V((0, 0, 0))), (out0, V((0, 0, 0))), (out0 + 12, DW * dist),
                             (back0, DW * dist), (back0 + 9, V((0, 0, 0)))])
        interp(e, 'BEZIER')

# ---- squeeze: grip (50-56-62) and games (142-146-150)
FULL = V((0.90, 1.035, 1.035))
keys(sq, "scale", [(1, V((1, 1, 1))), (50, V((1, 1, 1))), (56, FULL), (62, V((1, 1, 1))),
                   (142, V((1, 1, 1))), (146, FULL), (150, V((1, 1, 1)))])
interp(sq, 'BEZIER')

# ---- difficulty: top halves lift on the parting line, old insert out, new insert in, close
side = ROT.inverted() @ V((1.0, 0.35, 0.0)).normalized()     # screen-right, in ball space
def lift(g, pairs):
    for f, h, s in pairs: key(g, "location", f, PAD_DIR * h + side * s)
    interp(g, 'BEZIER')
lift(lift_shell, [(1, 0, 0), (198, 0, 0), (208, 1.55, 0), (225, 1.55, 0), (234, 0, 0)])
lift(lift_outer, [(1, 0, 0), (199, 0, 0), (209, 0.95, 0), (225, 0.95, 0), (232, 0, 0)])
lift(ins_old,    [(1, 0, 0), (206, 0, 0), (211, 0.45, 0), (218, 0.75, 3.6)])
lift(ins_new,    [(1, 0.75, -3.4), (213, 0.75, -3.4), (220, 0.45, 0), (225, 0, 0)])

# ---- power button: pressed once (games), LEDs light up
cap = OB["Power_Button"]
keys(cap, "location", [(1, cap.location.copy()), (127, cap.location.copy()),
                       (129, cap.location - BTN_DIR * 0.012), (131, cap.location.copy())])
led = bpy.data.materials["Button_LED_Dot"]; lb = next(n for n in led.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
lb.inputs["Emission Color"].default_value = (*studio.srgb("#6FD69A"), 1)   # saturated mint, so it reads green, not white
for f, v in ((1, 0.3), (128, 0.3), (131, 9.0), (148, 9.0), (156, 2.0), (237, 2.0), (250, 6.0)):
    lb.inputs["Emission Strength"].default_value = v; lb.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
lens = bpy.data.materials["Button_Lens"]; ln = next(n for n in lens.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
ln.inputs["Emission Color"].default_value = (*studio.srgb("#6FD69A"), 1)
for f, v in ((1, 0.0), (128, 0.0), (131, 3.0), (148, 3.0), (156, 0.0)):
    ln.inputs["Emission Strength"].default_value = v; ln.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)

# ---- dock slides in under the lifted ball, ring glows once the ball sits on it
keys(dock, "location", [(1, V((9, 0, 0))), (152, V((9, 0, 0))), (163, V((0, 0, 0)))])
interp(dock, 'BEZIER')
ring = bpy.data.materials["Charge_Glow"]; rb = next(n for n in ring.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
for f, v in ((1, 0.0), (170, 0.0), (178, 6.0), (N, 4.5)):
    rb.inputs["Emission Strength"].default_value = v; rb.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)

# ---- what is rendered when (hidden parts cost nothing and can never poke out)
inside = [OB[n] for n in ("Electronics", "Air_Bladder", "Air_Bladder_Outlet", "Air_Tube", "Air_Tube_Clamp",
                          "Pogo_Pin_1", "Pogo_Pin_2", "Button_Flex_Cable", "Power_Button_Switch")]
foams = [OB["Foam_Liner"], OB["Foam_Liner_Wedge"]] + [P[k] for k in P if k.startswith(("Foam_Outer", "Foam_Mid"))]
hide_keys(inside, [(1, True), (30, False), (98, True)])
hide_keys(foams, [(1, True), (30, False), (98, True), (197, False), (236, True)])
hide_keys([ins_new], [(1, True), (213, False), (236, True)])
hide_keys([ins_old], [(1, True), (30, False), (98, True), (197, False), (219, True)])
OB["Chassis_Lid"].hide_render = True
hide_keys([dock], [(1, True), (151, False)])


# ------------------------------------------------------------------ studio + camera
studio.engine(sc, 48, W, H, threshold=0.02)
studio.world(sc)
studio.studio(sc, floor_z=FLOOR)
cam = studio.camera(sc, "FilmCam")
focus = OB.new("Focus", None); sc.collection.objects.link(focus)
cam.data.dof.use_dof = True; cam.data.dof.focus_object = focus
cam.data.dof.aperture_blades = 7; cam.data.dof.aperture_rotation = math.radians(10)

R0 = REST; RF = REST + 0.3                     # ball centre z: resting / floating
MS = V((0.255, 0.02, -0.325))                  # motion sensor chip, ball space
MSW = MS + V((0, 0, RF))                       # ... in the world while the ball floats
BTW = BTN_DIR + V((0, 0, R0))                  # power button in the world (ball resting)
SHOTS = [
    # frame, target, direction, distance, lens, f-stop, focus point, shift_x
    # intro: slow push in
    (1,   (0, 0, R0 + 0.05), (0.08, -1, 0.20), 17.5, 90, 5.0, (0, -0.8, R0), -0.12),
    (24,  (0, 0, R0 + 0.08), (0.20, -1, 0.22), 15.0, 90, 4.5, (0, -0.8, R0), -0.12),
    # grip: follow the ball up, settle on the cutaway, drift during the squeeze
    (36,  (0.12, 0, RF - 0.12), (0.34, -1, 0.26), 15.6, 95, 3.4, (0.2, -0.5, RF - 0.2), -0.10),
    (46,  (0.12, 0, RF - 0.16), (0.40, -1, 0.26), 15.2, 100, 2.6, (0.25, -0.45, RF - 0.3), -0.09),
    (62,  (0.12, 0, RF - 0.16), (0.33, -1, 0.24), 14.7, 100, 2.6, (0.25, -0.45, RF - 0.3), -0.10),
    # movement: dive in (two steps so the speed is even), hold, pull back while the cutaway closes
    (69,  tuple(MSW * 0.6 + V((0.12, 0, RF - 0.16)) * 0.4), (0.24, -1, 0.14), 8.0, 100, 1.9, tuple(MSW), -0.17),
    (76,  tuple(MSW), (0.16, -1, 0.04), 4.6, 100, 1.4, tuple(MSW), -0.21),
    (84,  tuple(MSW), (0.10, -1, 0.03), 4.2, 100, 1.4, tuple(MSW), -0.21),
    (91,  (0.18, 0, RF - 0.05), (0.10, -1, 0.12), 10.0, 92, 3.5, (0.2, -0.7, RF), -0.15),
    (98,  (0.2, 0, RF + 0.1), (0.10, -1, 0.20), 17.0, 85, 5.6, (0.2, -0.8, RF), -0.12),
    (114, (0.2, 0, RF + 0.1), (0.13, -1, 0.21), 16.6, 85, 5.6, (0.2, -0.8, RF), -0.12),
    # games: the ball settles while the camera swings round to the button, press, pull back
    (122, (0.2, -0.05, R0 + 0.12), (0.36, -0.95, 0.32), 12.5, 85, 3.5, tuple(BTW), -0.10),
    (129, tuple(BTN_DIR * 0.9 + V((0, 0, R0))), (0.62, -0.8, 0.46), 6.4, 85, 2.0, tuple(BTW), -0.06),
    (134, tuple(BTN_DIR * 0.9 + V((0, 0, R0))), (0.57, -0.82, 0.44), 6.1, 85, 2.0, tuple(BTW), -0.06),
    (139, (0.1, -0.05, R0), (0.12, -1, 0.28), 10.5, 95, 2.6, (0, -0.9, R0), -0.11),
    (143, (0, 0, R0 - 0.05), (-0.20, -1, 0.24), 13.2, 100, 2.8, (-0.25, -0.9, R0), -0.12),
    (150, (0, 0, R0 - 0.05), (-0.16, -1, 0.24), 13.0, 100, 2.8, (-0.25, -0.9, R0), -0.12),
    # progress: widen as the ball lifts and the dock arrives, then a slow orbit
    (161, (0, 0, 0.0), (0.06, -1, 0.24), 18.5, 90, 5.0, (0, -0.8, 0.2), -0.12),
    (173, (0, 0, -0.3), (-0.10, -1, 0.22), 16.0, 90, 4.0, (-0.2, -0.9, -0.2), -0.12),
    (184, (0, 0, -0.3), (0.02, -1, 0.18), 14.8, 90, 4.0, (-0.1, -0.9, -0.2), -0.12),
    # difficulty: rise up to see the opening, slow drift while it opens and closes
    (198, (0, 0, 0.55), (0.30, -1, 0.42), 20.5, 90, 4.5, (0, -0.6, 0.5), -0.12),
    (236, (0, 0, 0.5), (0.22, -1, 0.39), 19.8, 90, 4.5, (0, -0.6, 0.5), -0.12),
    # sharing: orbit to the button side, wide closing shot
    (252, (0, 0, -0.25), (0.52, -1, 0.34), 15.5, 90, 4.0, (0.4, -0.7, 0.0), -0.12),
    (266, (0, 0, -0.25), (0.30, -1, 0.26), 17.0, 90, 4.5, (0.2, -0.8, 0.0), -0.12),
]
prev = None
for f, tgt, d, dist, lensmm, fs, fp, shx in SHOTS:
    t = V(tgt); dd = V(d).normalized()
    cam.location = t + dd * dist
    q = (t - cam.location).to_track_quat('-Z', 'Y')
    e = q.to_euler('XYZ', prev) if prev else q.to_euler('XYZ'); prev = e
    cam.rotation_euler = e
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
    key(cam.data, "lens", f, lensmm); key(cam.data, "shift_x", f, shx)
    cam.data.dof.aperture_fstop = fs; cam.data.dof.keyframe_insert("aperture_fstop", frame=f)
    key(focus, "location", f, V(fp))
for idb in (cam, cam.data, focus):
    interp(idb, 'BEZIER')


# ------------------------------------------------------------------ per-frame screen positions for the website
def centre(o):
    vs = o.data.vertices
    return sum((o.matrix_world @ v.co for v in vs), V()) / len(vs)
ins_pt = (PAD_DIR * 0.3 + ROT.inverted() @ V((0.30, -1.0, 0.0)).normalized()).normalized() * 0.87
ANCH = {
    "ball": lambda: root.matrix_world.translation.copy(),
    "bladder": lambda: OB["Air_Bladder"].matrix_world @ V((0.35, -0.6, 0.25)),
    "pressure": lambda: centre(OB["Pressure_Sensor_Body"]),
    "motion": lambda: centre(OB["Motion_Sensor_IMU"]),
    "button": lambda: OB["Power_Button"].matrix_world @ V((0, 0, 0.02)),
    "dock": lambda: V((0.0, -0.69, DZ - 0.215)) + dock.location,
    "insert": lambda: ins_new.matrix_world @ ins_pt,
}
data = {"frames": N, "width": W, "height": H, "chapters": CH, "points": {k: [] for k in ANCH}, "radius": []}
for f in range(1, N + 1):
    sc.frame_set(f)
    for k, fn in ANCH.items():
        p = world_to_camera_view(sc, cam, fn())
        data["points"][k].append([round(p.x, 4), round(1 - p.y, 4)])
    c = root.matrix_world.translation
    right = cam.matrix_world.to_quaternion() @ V((1, 0, 0))
    a = world_to_camera_view(sc, cam, c); b = world_to_camera_view(sc, cam, c + right)
    data["radius"].append(round(abs(b.x - a.x), 4))
json.dump(data, open(os.path.join(V5, "anchors51.json"), "w"))
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(V5, "film51.blend"), compress=True)
print("FILM SAVED", N)
