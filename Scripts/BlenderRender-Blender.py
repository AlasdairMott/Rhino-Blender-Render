import bpy
import os
import math
import random
import sys
import json
from mathutils import Vector

#Hide Splash Screen on Startup
bpy.context.preferences.view.show_splash = False

scene = bpy.context.scene

dirname=os.path.dirname
filepath = dirname(os.path.realpath(__file__)) + "\\"

def ReadData(filename):
    try:
        with open(filepath + filename, 'r') as f:
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
    obj_name = d_camera["object"]
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
    camera_loc = [float(l) for l in d_camera["camera"]["camera_location"].split(",")]
    camera_rot = [float(l) for l in d_camera["camera"]["camera_rotation"].split(",")]

    bpy.ops.object.camera_add(enter_editmode=False, align='VIEW', location=camera_loc, rotation=camera_rot ) #((90*pi)/180, 0, (270*pi)/180)

    currentCameraObj = bpy.data.objects[bpy.context.active_object.name]
    scene.camera = currentCameraObj

    if d_camera["camera"]["camera_lensType"] == "Orthographic":
        currentCameraObj.data.type = 'ORTHO' #data.type
        currentCameraObj.data.ortho_scale = float(d_camera["camera"]["camera_lensLength"])
    else:
        #scene_camera.data.sensor_fit = "HORIZONTAL"
        #scene_camera.data.sensor_width = 35
        #scene_camera.data.lens = float(d_camera["camera"]["camera_lensLength"])
        currentCameraObj.data.lens_unit = 'FOV'
        currentCameraObj.data.angle = float(d_camera["camera"]["camera_lensLength"])

    #Align View to Main Camera
    area = next(area for area in bpy.context.screen.areas if area.type == 'VIEW_3D')
    area.spaces[0].region_3d.view_perspective = 'CAMERA'

    #Exposure
    scene.view_settings.exposure = float(d_settings["camera"]["camera_exposure"])

    #Transparency
    if bool(d_settings["camera"]["camera_transparent"]): scene.render.film_transparent = True

    #Clipping
    clippingNear = float(d_camera["camera"]["camera_clippingNear"])
    clippingFar = float(d_camera["camera"]["camera_clippingFar"])
    currentCameraObj.data.clip_start = clippingNear
    currentCameraObj.data.clip_end = clippingFar

    #Add Sun
    if bool(d_camera["world"]["sun_enabled"]):
        light_data = bpy.data.lights.new(name="Sun", type='SUN')
        light_data.energy = 2.5
        light_data.angle = math.radians(2.5)
        light_object = bpy.data.objects.new(name="Sun", object_data=light_data)
        bpy.context.collection.objects.link(light_object)
        bpy.context.view_layer.objects.active = light_object

        sun_direction = [float(l) for l in d_camera["world"]["sun_vector"].split(",")]
        sun_direction = Vector(sun_direction)
        light_object.rotation_mode = 'QUATERNION'
        light_object.rotation_quaternion = sun_direction.to_track_quat('Z','Y')

    #Skylight
    if bool(d_camera["world"]["ambientocclusion_enabled"]):
        bpy.context.scene.world.light_settings.use_ambient_occlusion = True
        bpy.context.scene.world.light_settings.ao_factor = 0.1
        bpy.context.scene.world.light_settings.distance = 1000

    #Add Ground Plane
    if bool(d_camera["world"]["groundplane_enabled"]):
        bpy.ops.mesh.primitive_plane_add()
        plane = bpy.context.selected_objects[0]
        plane.location = (0.0, 0.0, float(d_camera["world"]["groundplane_height"]))
        plane.scale = (100000,100000,100000)

    #Sky
    if d_settings["world"]["world_HDRI"] != "Colour":
        hdri_filepath = filepath + "HDRI\\" + d_settings["world"]["world_HDRI"]
        scene.world.use_nodes = True
        world = bpy.data.worlds["World"]
        nodes = world.node_tree.nodes
        links = world.node_tree.links

        world_HDRIPower =  float(d_settings["world"]["world_HDRIPower"])
        bg_node = world.node_tree.nodes['Background']
        bg_node.inputs[1].default_value = world_HDRIPower

        env_node = world.node_tree.nodes.new('ShaderNodeTexEnvironment')
        env_node.image = bpy.data.images.load(hdri_filepath)
        env_node.location = (bg_node.location.x -300 ,bg_node.location.y)
        links.new(env_node.outputs['Color'], bg_node.inputs['Color'])

        world_rotation = float(d_settings["world"]["world_HDRIRotation"])
        map_node = world.node_tree.nodes.new('ShaderNodeMapping')
        map_node.inputs[2].default_value[2] = math.radians(world_rotation)
        map_node.location = (env_node.location.x -200 ,env_node.location.y)
        links.new(map_node.outputs['Vector'], env_node.inputs['Vector'])

        world_HDRIBlur = float(d_settings["world"]["world_HDRIBlur"])
        add_node = world.node_tree.nodes.new('ShaderNodeMixRGB')
        add_node.blend_type = "ADD"
        add_node.inputs[0].default_value = world_HDRIBlur
        add_node.location = (map_node.location.x -200 ,map_node.location.y)
        links.new(add_node.outputs['Color'], map_node.inputs['Vector'])

        subtract_node = world.node_tree.nodes.new('ShaderNodeMixRGB')
        subtract_node.blend_type = "SUBTRACT"
        subtract_node.inputs[0].default_value = 1.0
        subtract_node.location = (add_node.location.x -200 ,add_node.location.y - 200)
        links.new(subtract_node.outputs['Color'], add_node.inputs['Color2'])

        noise_node = world.node_tree.nodes.new('ShaderNodeTexNoise')
        noise_node.inputs[2].default_value = 10000
        noise_node.location = (subtract_node.location.x -200 ,subtract_node.location.y)
        links.new(noise_node.outputs['Color'], subtract_node.inputs['Color2'])

        text_node = world.node_tree.nodes.new('ShaderNodeTexCoord')
        text_node.location = (noise_node.location.x -200 ,noise_node.location.y + 200)
        links.new(text_node.outputs['Generated'], add_node.inputs['Color1'])
        links.new(text_node.outputs['Generated'], noise_node.inputs['Vector'])

def RenderSettings():
    bpy.context.scene.render.resolution_percentage          = float(d_settings["settings"]["render_scale"])
    bpy.context.scene.render.resolution_y                   = float(d_camera["camera"]["camera_height"])
    bpy.context.scene.render.resolution_x                   = float(d_camera["camera"]["camera_width"])
    bpy.context.scene.cycles.samples                        = float(d_settings["settings"]["render_samples"])
    bpy.context.scene.cycles.diffuse_bounces                = float(d_settings["settings"]["render_bouncesDiffuse"])
    bpy.context.scene.cycles.glossy_bounces                 = float(d_settings["settings"]["render_bouncesGlossy"])
    bpy.context.scene.cycles.transparent_max_bounces        = float(d_settings["settings"]["render_bouncesTransparency"])
    bpy.context.scene.cycles.transmission_bounces           = float(d_settings["settings"]["render_bouncesTransmission"])
    bpy.context.scene.cycles.volume_bounces                 = float(d_settings["settings"]["render_bouncesVolume"])
    bpy.context.scene.view_layers[0].cycles.use_denoising   = bool(d_settings["settings"]["render_Denoising"])
    if d_settings["settings"]["render_engine"] == "EEVEE":
        bpy.context.scene.render.engine = 'BLENDER_EEVEE'

def RenderScene(r_name):
    bpy.ops.render.render()
    save_path = d_camera["savepath"]

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

d_settings = ReadData("BlenderRender-Settings.json")
d_camera = ReadData("BlenderRender-Camera.json")

render_name = d_camera["rendername"]

if d_settings and d_camera:
    ClearAll()
    Import()
    SetupScene()
    RenderSettings()

    if bool(d_settings["settings"]["render"]):
        RenderScene(render_name)

    if bool(d_settings["settings"]["save"]):
        print ("Saving file")
        save_path = d_camera["savepath"]
        bpy.ops.wm.save_as_mainfile(filepath= str(save_path + render_name + ".blend"))
