import bpy
import os
import math
import random
import sys
import json
from mathutils import Vector

argv = sys.argv
render_name = argv[argv.index("--") + 1:][0]

scene = bpy.context.scene

dirname=os.path.dirname
filepath = dirname(os.path.realpath(__file__)) + "\\"

def ReadData():
    try:
        with open(filepath + "BlenderRenderSettings.json", 'r') as f:
            datastore = json.load(f)
            return datastore
    except IOError:
        print ("Reading Failed")

def ClearAll():
    #Remove all objects
    override = bpy.context.copy()
    override['selected_objects'] = list(bpy.context.scene.objects)
    bpy.ops.object.delete(override)

def Import():
    #Import Objs
    obj_name = d["object"]
    imported_object = bpy.ops.import_scene.obj(filepath=filepath+obj_name)

    #Modify Material
    """
    obj_objects = bpy.context.selected_objects[:]
    for obj in obj_objects:
        #bpy.context.scene.objects.active = obj
        obj.active_material_index = 0
        for i in range(len(obj.material_slots)):
            bpy.ops.object.material_slot_remove({'object': obj})
    """
    materials_name = os.path.splitext(obj_name)[0] + ".mtl"

    os.remove(filepath+obj_name)
    os.remove(filepath+materials_name)

def SetupScene():
    #Add Camera
    pi = math.pi
    camera_loc = [float(l) for l in d["camera"]["camera_location"].split(",")]
    camera_rot = [float(l) for l in d["camera"]["camera_rotation"].split(",")]

    bpy.ops.object.camera_add(enter_editmode=False, align='VIEW', location=camera_loc, rotation=camera_rot ) #((90*pi)/180, 0, (270*pi)/180)

    currentCameraObj = bpy.data.objects[bpy.context.active_object.name]
    scene.camera = currentCameraObj

    if d["camera"]["camera_lensType"] == "Orthographic":
        currentCameraObj.data.type = 'ORTHO' #data.type
        currentCameraObj.data.ortho_scale = float(d["camera"]["camera_lensLength"])
    else:
        #scene_camera.data.sensor_fit = "HORIZONTAL"
        #scene_camera.data.sensor_width = 35
        #scene_camera.data.lens = float(d["camera"]["camera_lensLength"])
        currentCameraObj.data.lens_unit = 'FOV'
        currentCameraObj.data.angle = float(d["camera"]["camera_lensLength"])

    #Clipping
    clippingNear = float(d["camera"]["camera_clippingNear"])
    clippingFar = float(d["camera"]["camera_clippingFar"])
    currentCameraObj.data.clip_start = clippingNear
    currentCameraObj.data.clip_end = clippingFar

    #Add Sun
    if bool(d["world"]["sun_enabled"]):
        light_data = bpy.data.lights.new(name="Sun", type='SUN')
        light_data.energy = 2.5
        light_data.angle = math.radians(2.5)
        light_object = bpy.data.objects.new(name="Sun", object_data=light_data)
        bpy.context.collection.objects.link(light_object)
        bpy.context.view_layer.objects.active = light_object

        sun_direction = [float(l) for l in d["world"]["sun_vector"].split(",")]
        sun_direction = Vector(sun_direction)
        light_object.rotation_mode = 'QUATERNION'
        light_object.rotation_quaternion = sun_direction.to_track_quat('Z','Y')

    #Skylight
    if bool(d["world"]["ambientocclusion_enabled"]):
        bpy.context.scene.world.light_settings.use_ambient_occlusion = True
        bpy.context.scene.world.light_settings.ao_factor = 0.1
        bpy.context.scene.world.light_settings.distance = 1000

    #Add Ground Plane
    if bool(d["world"]["groundplane_enabled"]):
        bpy.ops.mesh.primitive_plane_add()
        plane = bpy.context.selected_objects[0]
        plane.location = (0.0, 0.0, float(d["world"]["groundplane_height"]))
        plane.scale = (1000000,1000000,1000000)

def RenderSettings():
    bpy.context.scene.render.resolution_percentage          = float(d["settings"]["render_scale"])
    bpy.context.scene.render.resolution_y                   = float(d["camera"]["camera_height"])
    bpy.context.scene.render.resolution_x                   = float(d["camera"]["camera_width"])
    bpy.context.scene.cycles.samples                        = float(d["settings"]["render_samples"])
    bpy.context.scene.cycles.diffuse_bounces                = float(d["settings"]["render_bouncesDiffuse"])
    bpy.context.scene.cycles.glossy_bounces                 = float(d["settings"]["render_bouncesGlossy"])
    bpy.context.scene.cycles.transparent_max_bounces        = float(d["settings"]["render_bouncesTransparency"])
    bpy.context.scene.cycles.transmission_bounces           = float(d["settings"]["render_bouncesTransmission"])
    bpy.context.scene.cycles.volume_bounces                 = float(d["settings"]["render_bouncesVolume"])
    bpy.context.scene.view_layers[0].cycles.use_denoising   = bool(d["settings"]["render_Denoising"])

def RenderScene(r_name):
    bpy.ops.render.render()
    save_path = d["savepath"]

    ext = scene.render.file_extension

    #save render
    for img in bpy.data.images :
        i = 1
        if img.type == 'RENDER_RESULT' :
            print(img.name)
            img.render_slots.active_index = 0
            try :
                img.save_render(save_path + r_name + ".png") #ext
                print("slot %d saved"%i)
            except :
                print("Slot %d is empty"%i)

d = ReadData()

if d:
    ClearAll()
    Import()
    SetupScene()
    RenderSettings()
    RenderScene(render_name)

    if bool(d["settings"]["save"]):
        print ("Saving file")
        save_path = d["savepath"]
        bpy.ops.wm.save_as_mainfile(filepath= str(save_path + render_name + ".blend"))
