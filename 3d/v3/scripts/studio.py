"""Shared studio setup for Dexteria v3 renders (stills + animation).

Light cream look: the cream backdrop is NOT rendered. Frames are rendered with a
transparent film + shadow catcher floor, then post.py lays them over the exact
brand cream (#F0EBE4) with a soft vignette and fine grain. That keeps the page
background colour exact and avoids any hard gradient or banding.
"""
import bpy, math, os
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.dirname(HERE)                     # .../3d/v3
ROOT3D = os.path.dirname(V3)                   # .../3d
HDR = os.path.join(ROOT3D, "handoff", "assets", "studio_small_03_1k.hdr")


def srgb(h):
    h = h.lstrip('#'); c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def engine(sc, samples=128, w=1920, h=1080, threshold=0.015):
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'METAL'; prefs.get_devices()
    for d in prefs.devices:
        d.use = (d.type == 'METAL')
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'GPU'
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = threshold
    sc.cycles.use_denoising = True
    try: sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    except Exception: pass
    try: sc.cycles.denoising_use_gpu = True
    except Exception: pass
    sc.cycles.max_bounces = 10; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 4
    sc.cycles.transmission_bounces = 10; sc.cycles.transparent_max_bounces = 24
    sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
    sc.cycles.blur_glossy = 0.5
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    try: sc.cycles.film_transparent_glass = True
    except Exception: pass
    sc.render.use_persistent_data = True
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.exposure = -0.45
    try: sc.view_settings.look = 'AgX - Base Contrast'
    except Exception: pass
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.render.image_settings.color_depth = '16'
    sc.render.film_transparent = True
    sc.cycles.pixel_filter_type = 'BLACKMAN_HARRIS'; sc.cycles.filter_width = 1.5


def world(sc, strength=0.30):
    w = bpy.data.worlds.get("Studio_v3") or bpy.data.worlds.new("Studio_v3")
    sc.world = w; w.use_nodes = True
    nt = w.node_tree; N = nt.nodes; L = nt.links
    for n in list(N): N.remove(n)
    out = N.new("ShaderNodeOutputWorld"); bg = N.new("ShaderNodeBackground")
    env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(HDR, check_existing=True)
    mp = N.new("ShaderNodeMapping"); tc = N.new("ShaderNodeTexCoord")
    mp.inputs["Rotation"].default_value = (0, 0, math.radians(200))
    L.new(tc.outputs["Generated"], mp.inputs["Vector"]); L.new(mp.outputs["Vector"], env.inputs["Vector"])
    # warm the HDRI towards the cream studio so reflections match the page
    mix = N.new("ShaderNodeMix"); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
    mix.inputs[0].default_value = 0.6
    L.new(env.outputs["Color"], [s for s in mix.inputs if s.name == "A" and s.enabled][0])
    [s for s in mix.inputs if s.name == "B" and s.enabled][0].default_value = (*srgb("#F3EADB"), 1)
    L.new([s for s in mix.outputs if s.name == "Result" and s.enabled][0], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    L.new(bg.outputs[0], out.inputs["Surface"])
    try: w.visible_camera = False
    except Exception: pass
    return w


def studio(sc, floor_z=-1.0, col_name="Studio_v3"):
    """Cream floor/cyc as shadow catcher + soft area lights. Returns the collection."""
    import bmesh
    if col_name in bpy.data.collections:
        return bpy.data.collections[col_name]
    col = bpy.data.collections.new(col_name); sc.collection.children.link(col)
    bm = bmesh.new()
    prof = [(-40, 0.0)] + [(10 + 8*math.sin(t*math.pi/2), 8 - 8*math.cos(t*math.pi/2)) for t in [i/24 for i in range(25)]] + [(18, 40)]
    rows = [[bm.verts.new((x, y, z + floor_z)) for x in (-60, 60)] for y, z in prof]
    for r1, r2 in zip(rows[:-1], rows[1:]): bm.faces.new((r1[0], r1[1], r2[1], r2[0]))
    me = bpy.data.meshes.new("cyc"); bm.to_mesh(me); bm.free()
    cyc = bpy.data.objects.new("Cyclorama", me); col.objects.link(cyc)
    for p in me.polygons: p.use_smooth = True
    m = bpy.data.materials.new("Cyc_Cream"); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*srgb("#ECE6D9"), 1); b.inputs["Roughness"].default_value = 0.95
    me.materials.append(m)
    cyc.is_shadow_catcher = True

    def area(name, loc, size, energy, color="#FFFFFF", sy=None, target=(0, 0, -0.2)):
        ld = bpy.data.lights.new(name, 'AREA'); ld.shape = 'RECTANGLE'
        ld.size = size; ld.size_y = sy or size; ld.energy = energy; ld.color = srgb(color)
        try: ld.spread = math.radians(120)
        except Exception: pass
        lo = bpy.data.objects.new(name, ld); col.objects.link(lo); lo.location = loc
        lo.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        return lo
    # big soft key, top-left-front (matches the reference photo)
    area("Key", (-3.5, -4.5, 8.5), 6.0, 640, "#FFF3E4")
    # broad front fill so shadows on the ball stay soft
    area("Fill", (2.0, -9.0, 1.2), 7.0, 120, "#FFFFFF")
    # gentle cool rim from back-right for the silhouette
    area("Rim", (6.5, 3.0, 3.0), 3.0, 240, "#EEF2FF", sy=7)
    # top bounce card
    area("Top", (0.0, 1.0, 8.0), 6.0, 120, "#FFF8EE")
    return col


def camera(sc, name="Cam"):
    cam = bpy.data.objects.get(name)
    if cam is None:
        cd = bpy.data.cameras.new(name); cam = bpy.data.objects.new(name, cd); sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.sensor_width = 36
    return cam


def aim(cam, target, direction, dist, lens=100, fstop=None, focus=None, focus_pt=None):
    t = Vector(target); d = Vector(direction).normalized()
    cam.location = t + d * dist
    cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens
    if fstop:
        cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = fstop
        cam.data.dof.focus_distance = focus if focus else dist
        if focus_pt is not None:
            fwd = (t - cam.location).normalized()
            cam.data.dof.focus_distance = (Vector(focus_pt) - cam.location).dot(fwd)
        cam.data.dof.aperture_blades = 7; cam.data.dof.aperture_rotation = math.radians(10)
    else:
        cam.data.dof.use_dof = False
