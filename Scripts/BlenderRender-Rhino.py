import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import System

import json
import os
import subprocess
from datetime import date
import time

#ETO imports
import Rhino.UI
import Eto.Drawing as drawing
import Eto.Forms as forms

class BlenderRender:

	def __init__(self, objects_to_render):
		self.objects_to_render = objects_to_render

		dirname=os.path.dirname
		self.script_path = dirname(os.path.realpath(__file__)) + "\\"

		filepath = rs.DocumentPath()
		if not filepath: self.filepath = self.script_path
		else: self.filepath = str(os.path.splitext(str(filepath))[0]) + "\\"

		doc_name = rs.DocumentName()
		if not doc_name: doc_name = "Render_"
		else: doc_name = os.path.splitext(doc_name)[0]
		
		self.render_name = doc_name + date.today().strftime("%y%m%d") + "_" + time.strftime("%Hh%Mm%Ss")

		print "Filepath: " + self.filepath
		print "Rendername: " + self.render_name

		self.camera_data = None
		
		#Default Material
		self.materials = []
		default_material_index = sc.doc.Materials.Add()
		default_material = sc.doc.Materials[default_material_index]
		default_material.Name = "Default"
		default_material.Shine = 0
		default_material.CommitChanges()
		self.materials.append(default_material_index)

	def GetCameraProperties(self):
		view = sc.doc.Views.ActiveView
		view_port = view.ActiveViewport

		width = view.Size.Width
		height = view.Size.Height

		if view_port.IsPerspectiveProjection:
			lens_type = "Perspective"
			#lens_length = view_port.Camera35mmLensLength * 1.18099983184
			lens_length = view_port.GetCameraAngle()[3]*2

		else:
			lens_type = "Orthographic"
			nearRect = view_port.GetNearRect()
			dx = nearRect[0].DistanceTo(nearRect[1])
			lens_length = dx


		camera_location = view_port.CameraLocation

		clipping_near = view_port.GetFrustumNearPlane()[1].Origin
		clipping_near = clipping_near.DistanceTo(camera_location)

		clipping_far = view_port.GetFrustumFarPlane()[1].Origin
		clipping_far = clipping_far.DistanceTo(camera_location)

		camera_rot_plane = Rhino.Geometry.Plane(
			Rhino.Geometry.Point3d.Origin,
			view_port.CameraX,
			view_port.CameraY)

		transformed_plane =  Rhino.Geometry.Plane.WorldXY
		rot_transform = Rhino.Geometry.Transform.ChangeBasis(camera_rot_plane, transformed_plane)

		camera_rotation = (Rhino.Geometry.Transform.GetYawPitchRoll(rot_transform)[1:])
		camera_rotation = (camera_rotation[2], camera_rotation[1], camera_rotation[0])
		camera_rotation = str(camera_rotation)
		camera_rotation = camera_rotation[1:-1]

		self.camera_data = [width, height, lens_type, lens_length, camera_location.ToString(), camera_rotation, clipping_near, clipping_far]
		print self.camera_data

	def MeshObjects(self):
		ml_doc = []

		objects = [rs.coercerhinoobject(o) for o in self.objects_to_render]
		for o in objects:
			obj_ref = Rhino.DocObjects.ObjRef(o)
			attr = obj_ref.Object().Attributes
			
			if attr.MaterialSource == Rhino.DocObjects.ObjectMaterialSource.MaterialFromLayer:
				layer = sc.doc.Layers[attr.LayerIndex]
				material_index = layer.RenderMaterialIndex
			else:
				material_index = attr.MaterialIndex
			
			if material_index == -1:
				attr.MaterialSource = Rhino.DocObjects.ObjectMaterialSource.MaterialFromObject
				attr.MaterialIndex = self.materials[0]
				#attr.CommitChanges()
			elif material_index not in self.materials:
				self.materials.append(material_index)
				
			p = o.GetRenderMeshParameters()
			obrefs = Rhino.DocObjects.RhinoObject.GetRenderMeshes([o], True, True)
			mainmesh = Rhino.Geometry.Mesh()
			for obref in obrefs:
				obm = obref.Mesh()
				mainmesh.Append(obm)
			
			
			ml_doc.append(sc.doc.Objects.AddMesh(mainmesh, attr))

		rs.SelectObjects(ml_doc)
				
		return ml_doc

	def ExportObj(self):
		rs.EnableRedraw(False)

		meshes = self.MeshObjects()

		doc = sc.doc.ActiveDoc
		write_options = Rhino.FileIO.FileWriteOptions()
		write_options.WriteSelectedObjectsOnly	= True

		obj_options = Rhino.FileIO.FileObjWriteOptions(write_options)
		obj_options.MeshParameters = Rhino.Geometry.MeshingParameters.FastRenderMesh
		obj_options.MapZtoY = True
		obj_options.UseSimpleDialog = True
		obj_options.ExportMaterialDefinitions = True

		Rhino.FileIO.FileObj.Write(self.script_path + self.render_name + ".obj", doc, obj_options)

		rs.DeleteObjects(meshes)

		rs.EnableRedraw(True)

	def Render(self):
		python_script = self.script_path + "BlenderRender-Blender.py"

		args = ["C:\\Program Files\\Blender Foundation\\Blender 2.81\\blender.exe",
				"--background", "--python", python_script, "--", self.render_name]
		try:
			subprocess.call(args)
		except subprocess.CalledProcessError:
			print ("Render Failed")

	def WriteJson(self):
		json_filename = self.script_path + "BlenderRenderSettings.json"

		#Clear File
		with open(json_filename, 'w') as f: json.dump({}, f)

		camera = {
                  "camera_width": self.camera_data[0],
                  "camera_height": self.camera_data[1],
                  "camera_lensType": self.camera_data[2],
                  "camera_lensLength": self.camera_data[3],
                  "camera_location": self.camera_data[4],
                  "camera_rotation": self.camera_data[5],
                  "camera_clippingNear" : self.camera_data[6],
                  "camera_clippingFar" : self.camera_data[7]
                  }

		settings = {
                  "render_engine": "CYCLES",
                  "render_scale": 50,
                  "render_samples": 16,
                  "render_bouncesTotal": 2,
                  "render_bouncesDiffuse": 2,
                  "render_bouncesGlossy": 0,
                  "render_bouncesTransparency": 0,
                  "render_bouncesTransmission": 0,
                  "render_bouncesVolume": 0,
                  "render_clampingDirect": 0.05,
                  "render_clampingIndirect": 10,
                  "render_Denoising": True,
				  "save": True
                   }

		world = {
				"groundplane_enabled" : sc.doc.GroundPlane.Enabled,
				"groundplane_height" : sc.doc.GroundPlane.Altitude,
				"sun_enabled" : sc.doc.Lights.Sun.Enabled,
				"sun_vector" : (sc.doc.Lights.Sun.Vector*-1).ToString(),
				"ambientocclusion_enabled" : sc.doc.Lights.Skylight.Enabled,
				"ambientocclusion_factor" : sc.doc.Lights.Skylight.ShadowIntensity
				}

		new_entry = {"savepath" : self.filepath, "object": self.render_name + ".obj", "camera" : camera, "settings" : settings, "world" : world}

		with open(json_filename, 'w') as f: json.dump(new_entry, f)

	def ExportMaterials(self):
		materials_file = open(self.script_path + self.render_name + ".mtl","w+")
		
		materials_file.write("# Rhino" + "\n")
		
		for m_index in self.materials:
			material = sc.doc.Materials[m_index]
			
			diffuse = [float(material.DiffuseColor.R), float(material.DiffuseColor.G), float(material.DiffuseColor.B)]
			diffuse = [str('%.4f' % (i/255)) for i in diffuse]
			
			emmission = [float(material.EmissionColor.R), float(material.EmissionColor.G), float(material.EmissionColor.B)]
			emmission = [str('%.4f' % (i/255)) for i in emmission]
			
			materials_file.write("newmtl " + material.Name + "\n")
			materials_file.write("Ka 0.0000 0.0000 0.0000\n")
			materials_file.write("Kd " + diffuse[0] + " " + diffuse[1] + " " + diffuse[2] + "\n")
			materials_file.write("Ks 0.5000 0.5000 0.5000\n") #Specular Colour
			#materials_file.write("Tf 0.0000 0.0000 0.0000\n")
			materials_file.write("Ke " + emmission[0] + " " + emmission[1] + " " + emmission[2] + "\n")
			#materials_file.write("Pr " + str('%.4f' % (material.Shine/255)) + "\n")
			#materials_file.write("Pr " + str(material.ReflectionGlossiness) + "\n") #Gloss
			#materials_file.write("Pr " + str(material.Reflectivity) + "\n") #Roughness
			#materials_file.write("Pm " + str(material.Shine) + "\n")
			materials_file.write("d 1.0000\n") #Transparency
			materials_file.write("Ns "+ str('%.4f' % (material.Shine*(900/255))) + "\n")
			#materials_file.write("Ns 0.5000\n") #Specular amount
			
		materials_file.close()

class DisplayRenderETO(forms.Dialog[bool]):
	def __init__(self, image_path):
		self.Title = 'Render Blender'
		self.Padding = drawing.Padding(5)
		self.Resizable = True
		
		self.image = None
		if os.path.exists(image_path):
			img = System.Drawing.Image.FromFile(image_path)
		else: 
			return None
		
		self.image = forms.ImageView()
		self.image.Image = Rhino.UI.EtoExtensions.ToEto(img)
		self.image.Size = drawing.Size(img.Width/2, img.Height/2)
		
		self.DefaultButton = forms.Button(Text = 'Save')
		self.DefaultButton.Click += self.OnOKButtonClick
		
		self.AbortButton = forms.Button(Text = 'Cancel')
		self.AbortButton.Click += self.OnCloseButtonClick
		
		layout = forms.DynamicLayout()
		layout.Spacing = drawing.Size(5, 5)
		layout.AddRow(self.image)
		layout.AddSeparateRow(None, self.DefaultButton, self.AbortButton)
 
		self.Content = layout

	def OnCloseButtonClick(self, sender, e):
		self.Close(False)

	def OnOKButtonClick(self, sender, e):
		self.Close(True)

def DisplayRender(path):
	dialog = DisplayRenderETO(path);
	if not dialog.image: 
		print "Render Failed"
		return None
	result = dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)
	if result == False:
		os.remove(path)

objects_to_render = rs.GetObjects("Choose Objects to Render", preselect=True)
rs.UnselectAllObjects()

if objects_to_render:
	render_instance = BlenderRender(objects_to_render)
	render_instance.GetCameraProperties()
	render_instance.WriteJson()
	render_instance.ExportObj()
	render_instance.ExportMaterials()
	#render_instance.Render()
	DisplayRender(render_instance.filepath + render_instance.render_name + '.png')
