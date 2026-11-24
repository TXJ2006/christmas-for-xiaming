"""Offline render for the Christmas site's miniature short. Run with Blender -b -P."""
import bpy
import math
import random
import sys
from mathutils import Vector
from math import sin, cos, pi

args = sys.argv[sys.argv.index("--") + 1:]
target = args[0]
preview = int(args[1]) if len(args) > 1 else 0
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
try:
    scene.render.engine = 'BLENDER_EEVEE'
except TypeError:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.eevee.taa_render_samples = 16
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.fps = 16
scene.frame_end = 448
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.world = bpy.data.worlds.new("Winter sky")
scene.world.use_nodes = True
sky = scene.world.node_tree.nodes.get('Background')
sky.inputs['Color'].default_value = (.17, .245, .36, 1)
sky.inputs['Strength'].default_value = .42

def material(name, color, rough=.65, grain=0, metal=0, emit=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    nodes = m.node_tree.nodes
    bs = nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Roughness'].default_value = rough
    bs.inputs['Metallic'].default_value = metal
    bs.inputs['Emission Color'].default_value = (*color, 1)
    bs.inputs['Emission Strength'].default_value = emit
    if grain:
        noise = nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = grain
        noise.inputs['Detail'].default_value = 3
        bump = nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = .28
        bump.inputs['Distance'].default_value = .025
        m.node_tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
        m.node_tree.links.new(bump.outputs['Normal'], bs.inputs['Normal'])
    return m

snow = material("Crystalline snow", (.65,.79,.82), .76, 85)
slate = material("Wet cobblestone", (.065,.1,.12), .25, 19)
wood = material("Cedar", (.19,.094,.054), .63, 24)
dark = material("Wet bark", (.065,.043,.035), .7, 29)
pine = [material("Needles %d" % i, c, .77, 30) for i,c in enumerate([
    (.055,.20,.165),(.081,.26,.205),(.105,.29,.238)])]
skin = material("Painted porcelain", (.87,.52,.36), .37, 94)
cheek = material("Warm cheeks", (.87,.267,.228), .52)
hair = material("Chestnut", (.093,.044,.037), .40, 32)
hairlit = material("Chestnut strands", (.155,.079,.054), .40)
coat = material("Mulberry wool", (.39,.064,.086), .79, 110)
lining = material("Ivory fleece", (.81,.69,.52), .84, 120)
scarf = material("Vermilion yarn", (.63,.128,.084), .76, 130)
boot = material("Brown leather", (.098,.06,.046), .43, 34)
gold = material("Aged brass", (.72,.44,.135), .28, 0, .56)
cork = material("Cork", (.44,.22,.086), .71, 53)
eye = material("Lacquered eyes", (.025,.015,.022), .17)
white = material("Catchlight", (.97,.88,.73), .32, 0, 0, .2)
amber = material("Lantern filament", (1,.45,.105), .26, 0, 0, 4)
glass = material("Blue-green glass", (.15,.65,.58), .2, 18, .17)
water = material("Bottled light", (.32,.87,.70), .27, 0, .22, .4)
steel = material("Tin blue", (.09,.19,.22), .4, 0, .45)

def finish(obj, mat, parent=None, smooth=True):
    obj.data.materials.append(mat)
    if smooth and obj.type == 'MESH':
        for p in obj.data.polygons:
            p.use_smooth = True
    obj.parent = parent
    return obj

def ball(p, s, mat, parent=None, segments=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=segments//2, location=p)
    obj=bpy.context.object
    obj.scale=s
    return finish(obj,mat,parent)

def box(p, s, mat, parent=None, bevel=.035):
    bpy.ops.mesh.primitive_cube_add(size=1, location=p)
    obj=bpy.context.object
    obj.dimensions=s
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=obj.modifiers.new("Soft corners", 'BEVEL')
        mod.width=bevel
        mod.segments=2
        obj.modifiers.new("Weighted highlights", 'WEIGHTED_NORMAL')
    return finish(obj,mat,parent,False)

def lathe(profile, mat, parent=None, n=32, ripple=0):
    vertices=[]
    for j,(z,rx,ry) in enumerate(profile):
        for i in range(n):
            a=2*pi*i/n
            f=1+ripple*(sin(5*a+j*.48)+.45*cos(9*a-j*.63))
            vertices.append((rx*cos(a)*f,ry*sin(a)*f,z))
    faces=[tuple(reversed(range(n)))]
    faces.extend((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i)
                 for j in range(len(profile)-1) for i in range(n))
    faces.append(tuple((len(profile)-1)*n+i for i in range(n)))
    mesh=bpy.data.meshes.new(mat.name)
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    obj=bpy.data.objects.new(mat.name,mesh)
    scene.collection.objects.link(obj)
    return finish(obj,mat,parent)

def tube(points, radius, mat, parent=None, resolution=8):
    curve=bpy.data.curves.new(mat.name,'CURVE')
    curve.dimensions='3D'
    curve.resolution_u=resolution
    curve.bevel_depth=radius
    curve.bevel_resolution=2
    spline=curve.splines.new('BEZIER')
    spline.bezier_points.add(len(points)-1)
    for bp,p in zip(spline.bezier_points,points):
        bp.co=p
        bp.handle_left_type=bp.handle_right_type='AUTO'
    obj=bpy.data.objects.new(mat.name,curve)
    scene.collection.objects.link(obj)
    return finish(obj,mat,parent)

def empty(name, location=(0,0,0), parent=None):
    obj=bpy.data.objects.new(name,None)
    scene.collection.objects.link(obj)
    obj.parent=parent
    obj.location=location
    return obj

def doll():
    root=empty("Xiaming")
    torso=empty("Coat and shoulders",parent=root)
    lathe([(0.37,.225,.15),(.405,.29,.185),(.48,.29,.185),(.71,.205,.145),
           (.92,.158,.12),(1.00,.15,.128),(1.075,.20,.14),(1.135,.12,.11)],coat,torso,ripple=.04)
    lathe([(.384,.23,.16),(.398,.292,.188),(.435,.294,.192),(.45,.281,.183)],lining,torso,ripple=.04)
    tube([(.014,-.146,.56),(.016,-.15,.77),(.016,-.143,1.042)],.012,scarf,torso)
    for z in [.62,.74,.86,.97]:
        ball((.045,-.161 if z>.68 else -.18,z),(.029,.014,.028),gold,torso,12)
    for sign in [-1,1]:
        leg=empty("Boot pivot",(sign*.112,0,.47),root)
        ball((0,.0,-.17),(.098,.1,.245),boot,leg)
        ball((0,-.068,-.381),(.118,.189,.093),boot,leg)
        ball((0,-.072,-.425),(.118,.191,.04),dark,leg)
        lathe([(-.246,.103,.11),(-.21,.105,.11),(-.176,.101,.105)],lining,leg)
    shoulders=[]
    for sign in [-1,1]:
        arm=empty("Mitten pivot",(sign*.179,0,1.005),torso)
        arm.rotation_euler.y=-sign*.30
        ball((0,0,-.179),(.090,.094,.227),coat,arm)
        ball((0,-.007,-.321),(.094,.096,.046),lining,arm,16)
        ball((0,-.016,-.391),(.087,.076,.101),scarf,arm,20)
        ball((-sign*.057,-.049,-.357),(.045,.043,.047),scarf,arm,16)
        shoulders.append(arm)
    lathe([(1.05,.12,.119),(1.07,.20,.156),(1.17,.203,.166),(1.207,.12,.123)],scarf,torso)
    tail=empty("Loose scarf end",(.114,-.078,1.126),torso)
    for i in range(6):
        tube([(i*.023-.055,0,0),(i*.023-.065,-.047,-.15),
              (i*.023-.087,-.03,-.31),(i*.023-.073,-.053,-.44)],.016,scarf,tail)
    for i in range(6):
        tube([(i*.022-.071,-.049,-.422),(i*.023-.083,-.051,-.492)],.009,scarf,tail)
    head=empty("Head tilt",(0,0,1.164),torso)
    ball((0,.044,.269),(.346,.29,.361),hair,head,40)
    ball((0,-.058,.228),(.303,.248,.29),skin,head,40)
    ball((0,-.283,.204),(.038,.043,.037),skin,head)
    eyes = []
    for sign in [-1,1]:
        ball((sign*.291,-.088,.226),(.055,.061,.072),skin,head)
        ball((sign*.172,-.252,.158),(.062,.018,.038),cheek,head)
        eyelid=empty("Blink",(sign*.105,-.292,.249),head)
        eyes.append(eyelid)
        pupil=ball((0,0,0),(.052,.032,.071),eye,eyelid)
        pupil.rotation_euler.y=sign*.12
        ball((-.013,-.027,.024),(.018,.009,.021),white,eyelid,16)
        ball((.015,-.029,-.017),(.008,.006,.009),white,eyelid,12)
        tube([(sign*.151,-.290,.335),(sign*.103,-.306,.353),(sign*.062,-.301,.340)],.011,hair,head)
        hairlock=ball((sign*.243,-.035,.10),(.106,.205,.264),hair,head)
        hairlock.rotation_euler.y=sign*.16
    tube([(-.050,-.290,.128),(0,-.304,.104),(.045,-.292,.126)],.010,boot,head)
    for i in range(7):
        x=-.233+i*.072
        bang=ball((x,-.167+abs(x)*.19,.441+sin(i*.32)*.036),(.099,.135,.150),hair if i%3 else hairlit,head,24)
        bang.rotation_euler.y=-.55+i*.12
    for i in range(4):
        tube([(-.20+i*.082,-.172,.541),(-.25+i*.088,-.224,.492),
              (-.292+i*.088,-.21,.429)],.008,hairlit,head)
    for angle in [0,2*pi/3,4*pi/3]:
        petal=ball((.232+cos(angle)*.026,-.254,.433+sin(angle)*.026),(.036,.015,.029),gold,head,16)
        petal.rotation_euler.y=angle
    ball((.232,-.269,.433),(.016,.012,.016),scarf,head,16)
    return root, torso, head, shoulders, tail, eyes

girl, torso, head, arms, scarf_tail, eyes = doll()
bottle=empty("Aquarius")
lathe([(0,.142,.132),(.035,.189,.174),(.105,.214,.190),(.255,.224,.19),
       (.36,.211,.18),(.44,.169,.142),(.507,.105,.091),(.586,.086,.083),
       (.610,.107,.1),(.642,.107,.10),(.654,.083,.081)],glass,bottle,n=48,ripple=.02)
bs=glass.node_tree.nodes.get('Principled BSDF')
bs.inputs['Coat Weight'].default_value=.65
bs.inputs['Transmission Weight'].default_value=.24
lathe([(.10,.201,.18),(.15,.216,.187),(.263,.221,.19),(.298,.214,.186)],water,bottle,n=48,ripple=.025)
lathe([(.61,.102,.098),(.626,.107,.102),(.656,.105,.1)],gold,bottle)
lathe([(.646,.076,.074),(.695,.09,.085),(.727,.085,.083)],cork,bottle)
bottle_tie=empty("A piece of the red scarf",(0,0,.61),bottle)
tube([(-.11,.018,.012),(-.078,-.096,.004),(.009,-.127,0),(.093,-.102,-.006),(.111,.028,.015)],.021,scarf,bottle_tie)
tube([(.104,-.054,.013),(.175,-.095,-.058),(.16,-.123,-.167)],.014,scarf,bottle_tie)
ball((0,-.197,.229),(.071,.024,.071),gold,bottle)
for z in [.214,.249]:
    tube([(-.045,-.216,z),(-.025,-.219,z+.016),(.0,-.222,z),(.025,-.219,z+.016),(.045,-.216,z)],.006,steel,bottle)

def light(name, typ, p, color, energy, size):
    ls=bpy.data.lights.new(name,typ)
    ls.color=color
    ls.energy=energy
    if typ=='AREA': ls.shape='DISK'; ls.size=size
    else: ls.shadow_soft_size=size
    obj=bpy.data.objects.new(name,ls)
    scene.collection.objects.link(obj)
    obj.location=p
    return obj

def aim(obj,p):
    obj.rotation_euler=(Vector(p)-obj.location).to_track_quat('-Z','Y').to_euler()

lamp=light("Bottle bounce",'POINT',(0,-.27,.32),(1,.62,.24),13,.16)
lamp.parent=bottle
key=light("Window key",'AREA',(-2,-4,5),(1,.77,.59),630,4)
aim(key,(0,0,1))
rim=light("Winter skylight",'AREA',(2,3.5,6),(.51,.76,1),900,5)
aim(rim,(0,0,1))
fill=light("Soft fill",'AREA',(3,-1,3),(.56,.75,1),170,3)
aim(fill,(0,0,1))

rng=random.Random(72)
box((0,3,-.17),(100,100,.3),snow,bevel=0)
for i in range(26):
    x=(i%3-1)*.57+rng.uniform(-.19,.19)
    y=i*.43-4
    cobble=box((x,y,-.006),(rng.uniform(.34,.58),.40,.075),slate,bevel=.048)
    cobble.rotation_euler.z=rng.uniform(-.35,.35)
for i in range(32):
    x=rng.choice([-1,1])*rng.uniform(1.45,12)
    y=rng.uniform(-2,18)
    mound=ball((x,y,-.045),(rng.uniform(.38,1.9),rng.uniform(.55,1.5),rng.uniform(.07,.30)),snow,segments=12)

def tree(x,y,h,decorate=False):
    root=empty("Spruce",(x,y,.04))
    root.scale=(h/3,)*3
    lathe([(0,.115,.114),(.24,.12,.107),(2.4,.07,.068)],wood,root,n=12)
    for i in range(7):
        z=.30+i*.30
        r=1.04-i*.125
        layer=lathe([(z,r*.74,r*.70),(z+.03,r,r*.94),(z+.17,r*.94,r*.87),
                     (z+.49,r*.54,r*.47),(z+.76,.04,.045)],pine[i%3],root,n=20,ripple=.105)
        layer.rotation_euler.z=i*.76
        powder=lathe([(z+.19,r*.88,r*.82),(z+.26,r*.82,r*.75),(z+.49,r*.55,r*.47),
                      (z+.785,.028,.03)],snow,root,n=20,ripple=.088)
        powder.rotation_euler.z=i*.76
        if decorate:
            for j in range(6):
                a=j*2*pi/6+i*.83
                ball((cos(a)*r*.91,sin(a)*r*.90,z+.12),(.055,)*3,amber,root,12)
    return root

holiday=tree(1.76,1.66,3.14,True)
for i in range(37):
    x=rng.choice([-1,1])*rng.uniform(2.9,18)
    y=rng.uniform(2.25,23)
    tree(x,y,rng.uniform(2.3,6.2))

house=empty("Window at the bend",(-2.9,4.08,0))
box((0,0,.64),(1.8,1.4,1.3),wood,house)
for i in range(9):
    box((0,-.697,.10+i*.137),(1.82,.083,.092),dark,house,.024)
for sign in [-1,1]:
    roof=box((sign*.498,0,1.53),(1.20,1.76,.135),wood,house)
    roof.rotation_euler.y=sign*.50
    cap=box((sign*.505,0,1.61),(1.25,1.83,.105),snow,house)
    cap.rotation_euler.y=sign*.50
box((.46,-.76,1.0),(.52,.06,.51),dark,house)
box((.46,-.805,1.0),(.43,.04,.41),amber,house,.007)
box((.46,-.837,1.0),(.045,.04,.43),dark,house,.006)
box((.46,-.837,1.0),(.43,.04,.045),dark,house,.006)
box((-.42,-.77,.48),(.53,.08,.96),dark,house)

kite=empty("Paper kite")
def paper(vertices,faces,mats,ids,parent):
    mesh=bpy.data.meshes.new("Paper folded along the spine")
    mesh.from_pydata(vertices,[],faces)
    obj=bpy.data.objects.new(mesh.name,mesh)
    scene.collection.objects.link(obj)
    obj.parent=parent
    for mat in mats: mesh.materials.append(mat)
    for polygon,i in zip(mesh.polygons,ids): polygon.material_index=i
    return obj
paper([(0,0,.33),(.28,0,0),(0,0,-.31),(-.28,0,0),(0,-.08,0)],
      [(0,4,1),(1,4,2),(2,4,3),(3,4,0)],[scarf,lining],[1,0,1,0],kite)
tube([(0,0,-.26),(-.13,.03,-.59),(.11,.07,-.91),(.05,.15,-1.16)],.015,scarf,kite)

camera=bpy.data.objects.new("Camera",bpy.data.cameras.new("Portrait lens"))
scene.collection.objects.link(camera)
scene.camera=camera
camera.data.dof.use_dof=True
camera.data.dof.aperture_fstop=2.5
camera.data.clip_end=100

# Shared particle mesh keeps instanced snow and rain inexpensive.
flake=ball((0,0,0),(.014,)*3,white,segments=8)
flakes=[]
for i in range(106):
    p=flake.copy()
    scene.collection.objects.link(p)
    flakes.append((p,rng.uniform(-6,6),rng.uniform(-4,6),rng.uniform(0,5),rng.uniform(.65,1.46),rng.random()*6))
bpy.data.objects.remove(flake,do_unlink=True)

def ramp(t,a,b):
    u=max(0,min(1,(t-a)/(b-a)))
    return u*u*(3-2*u)

def interp(a,b,u):
    return tuple(x+(y-x)*u for x,y in zip(a,b))

def shot(f):
    t=(f-1)/16
    rain=11.75 <= t < 20.25
    night=t>=11.75
    key.data.energy=255 if rain else 490 if night else 630
    key.data.color=(.65,.80,1) if rain else (1,.76,.51)
    rim.data.energy=900 if not rain else 630
    lamp.data.energy=4
    water.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=.12
    girl.scale=(.76,)*3
    torso.rotation_euler=(0,0,0)
    head.scale=(.87,.89,.91) if night else (1,)*3
    bottle_tie.scale=(ramp(t,5.1,6.4),)*3
    girl.rotation_euler=(0,0,0)
    head.rotation_euler=(0,0,0)
    arms[0].rotation_euler=(0,.32,0)
    arms[1].rotation_euler=(0,-.32,0)
    scarf_tail.rotation_euler=(.11*sin(t*3),.05*sin(t*4),0)
    bottle.scale=(.78,)*3
    bottle.rotation_euler=(0,.08*sin(t*3),0)
    kite.location=(0,0,-8)
    lens=49
    if t < 4:
        u=ramp(t,0,4)
        girl.location=(-1.02+u*.30,.24,0)
        bottle.location=(.43,-.03,.055)
        head.rotation_euler=(.13,-.14,.25)
        camera_pos=interp((3.8,-6.5,2.36),(3.02,-5.5,1.98),u)
        focus=(0,.11,.88)
        if t >= 2.8:
            u=ramp(t,2.8,4)
            camera_pos=interp((.81,-1.9,.68),(.73,-1.69,.61),u)
            focus=(.43,-.03,.37)
            lens=64
    elif t < 8:
        u=ramp(t,4.1,7.3)
        girl.location=(-.48+.19*u,.03,0)
        torso.rotation_euler.x=.14*u
        head.rotation_euler=(.14*u,-.11,.36)
        arms[1].rotation_euler=(-.75*u,-1.24*u-.21,.12*u)
        bottle.location=(.40-.15*u,-.22,.06+.51*u)
        bottle.rotation_euler.y=-.22*u
        lamp.data.energy=4+15*u
        camera_pos=interp((1.65,-3.28,1.37),(1.2,-2.84,1.25),ramp(t,4,8))
        focus=(.015,-.10,.79)
        lens=50
    elif t < 11.75:
        u=(t-8)/3.75
        step=sin(t*10)
        girl.location=(-1.27+u*1.57,.03,.05+abs(step)*.075)
        girl.rotation_euler.z=.29
        arms[0].rotation_euler.x=step*.51
        arms[1].rotation_euler=(-.31,-1.37,.12)
        bottle.location=(girl.location.x+.73,.10,.49+.18*sin(t*5))
        kite.location=(girl.location.x+.99,.37,2.18+.16*sin(t*4))
        kite.rotation_euler=(.12,.18*sin(t*5),.14)
        focus=(girl.location.x+.33,0,1.13)
        camera_pos=(focus[0]+.62,-5.10,1.61)
        lens=43
    elif t < 16:
        girl.scale=(.99,.99,1.10)
        girl.location=(-.57,.09,0)
        head.rotation_euler=(.23,-.11,-.05)
        torso.rotation_euler.x=.09
        bottle.location=(.49,.06,.11)
        focus=(-.15,-.08,1.04)
        camera_pos=interp((2.16,-4.87,2.09),(1.72,-4.39,1.76),ramp(t,11.75,16))
    elif t < 20.25:
        u=ramp(t,16.25,19)
        girl.scale=(.99,.99,1.10)
        girl.location=(-.38,.09,0)
        head.rotation_euler=(.25*(1-u)-.06,-.12,.4*u)
        arms[1].rotation_euler=(-.39*u,-.34-1.01*u,.05)
        bottle.location=(.63-.38*u,-.13,.25+.63*u)
        bottle.scale=(1.0,)*3
        lamp.data.energy=7+70*u
        water.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=.18+2.4*u
        focus=(.005,-.15,1.10)
        camera_pos=interp((1.50,-3.95,1.83),(.90,-3.72,1.65),u)
        lens=45
    else:
        u=ramp(t,20.25,26.75)
        girl.scale=(.99,.99,1.10)
        girl.location=(-.41+.14*u,.03+.38*u,0)
        head.rotation_euler=(.04,-.15,.36)
        arms[1].rotation_euler=(-.43,-1.31,.17)
        bottle.location=(.22+.14*u,-.23+.38*u,.84+sin(t*2.5)*.027)
        bottle.scale=(1.0,)*3
        lamp.data.energy=43
        water.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=1.4
        focus=(.25,.19,1.18)
        camera_pos=interp((.23,-5.75,1.80),(-.36,-7.95,2.42),u)
        lens=47
    blink = min(abs(t - mark) for mark in [2.18, 5.65, 9.2, 14.2, 18.6, 23.4])
    for eyelid in eyes:
        eyelid.scale.z = .16 + .84 * ramp(blink,0,.13)
    for i,leg in enumerate(obj for obj in girl.children if obj.name.startswith("Boot pivot")):
        leg.rotation_euler.x=(sin(t*10+i*pi)*.36 if 8 <= t < 11.75 else 0)
    camera.location=camera_pos
    aim(camera,focus)
    camera.data.lens=lens
    camera.data.dof.focus_distance=(camera.location-Vector(focus)).length
    for p,x,y,z,s,phase in flakes:
        p.location=(x+(sin(t*.75+phase)*.24 if not rain else ((t*1.1+phase)%1)*.4),y,(z-t*(3.7 if rain else .35)*s)%5)
        p.scale=(s*.0056,s*.0056,s*.0854) if rain else (s*.014,)*3
        p.rotation_euler.y=-.22 if rain else 0

def sync_shot(s, *unused):
    shot(s.frame_current)

bpy.app.handlers.frame_change_pre.append(sync_shot)
if preview:
    scene.frame_set(preview)
    shot(preview)
    bpy.context.view_layer.update()
    scene.render.image_settings.file_format='JPEG'
    scene.render.image_settings.quality=92
    scene.render.filepath=target
    bpy.ops.render.render(write_still=True)
else:
    scene.render.image_settings.file_format='FFMPEG'
    scene.render.ffmpeg.format='MPEG4'
    scene.render.ffmpeg.codec='H264'
    scene.render.ffmpeg.constant_rate_factor='MEDIUM'
    scene.render.filepath=target
    scene.frame_set(1)
    bpy.ops.render.render(animation=True)
