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

bInterface = __import__("BlenderRender-Interface")

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

		self.render_name = doc_name + "_" + date.today().strftime("%y%m%d") + "_" + time.strftime("%Hh%Mm%Ss")

		#print "Filepath: " + self.filepath
		#print "Rendername: " + self.render_name

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
		json_filename = self.script_path + "BlenderRender-Camera.json"

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

		world = {
				"groundplane_enabled" : sc.doc.GroundPlane.Enabled,
				"groundplane_height" : sc.doc.GroundPlane.Altitude,
				"sun_enabled" : sc.doc.Lights.Sun.Enabled,
				"sun_vector" : (sc.doc.Lights.Sun.Vector*-1).ToString(),
				"ambientocclusion_enabled" : sc.doc.Lights.Skylight.Enabled,
				"ambientocclusion_factor" : sc.doc.Lights.Skylight.ShadowIntensity
				}

		new_entry = {"savepath" : self.filepath, "object": self.render_name + ".obj", "camera" : camera, "world" : world}

		with open(json_filename, 'w') as f: json.dump(new_entry, f, indent = 4, sort_keys=True)

	def ExportMaterials(self):
		materials_file = open(self.script_path + self.render_name + ".mtl","w+")

		materials_file.write("# Rhino" + "\n")
		
		for m_index in self.materials:
			
			material = sc.doc.Materials[m_index]
			materials_file.write("\n")
			materials_file.write("newmtl " + material.Name + "\n")												#Material Name
			materials_file.write("Ns "+ str('%.4f' % (material.Shine*(900/255))) + "\n")						#Glossiness
			materials_file.write("Ka 1.0000 1.0000 1.0000\n")
			
			
			if material.Reflectivity == 0: #Dialectric Material (Diffuse)
			
				diffuse = [float(material.DiffuseColor.R), float(material.DiffuseColor.G), float(material.DiffuseColor.B)]
				diffuse = [str('%.4f' % (i/255)) for i in diffuse]
	
				emmission = [float(material.EmissionColor.R), float(material.EmissionColor.G), float(material.EmissionColor.B)]
				emmission = [str('%.4f' % (i/255)) for i in emmission]
				
				materials_file.write("Kd " + diffuse[0] + " " + diffuse[1] + " " + diffuse[2] + "\n")			#Diffuse Colour
				materials_file.write("Ks 0.5000 0.5000 0.5000\n") 												#Specular (White, 0.5)
				materials_file.write("Ke " + emmission[0] + " " + emmission[1] + " " + emmission[2] + "\n") 	#Emission
				materials_file.write("illum 2\n")
				
			else: #Metallic Material
				
				refColor = [float(material.ReflectionColor.R), float(material.ReflectionColor.G), float(material.ReflectionColor.B)]
				refColor = [str('%.4f' % (i/255)) for i in refColor]
				
				materials_file.write("Kd " + refColor[0] + " " + refColor[1] + " " + refColor[2] + "\n")		#Reflection Colour
				materials_file.write("Ks 0.5000 0.5000 0.5000\n") 												#Specular (White, 0.5)
				materials_file.write("Ke 0.0000 0.0000 0.0000\n") 												#Emission
				#materials_file.write("Pm 1.0000" + "\n")														#Material is Metallic
				materials_file.write("illum 3\n")
				#Material.ReflectionGlossiness: 0.67104613781
			
			materials_file.write("Ni 1.4500" + "\n")															#IOR
			materials_file.write("d 1.0000\n") 																	#Transparency
			
		materials_file.close()

class DisplayRenderETO(forms.Dialog[bool]):
	def __init__(self, image_path):
		self.Title = 'Render Blender'
		self.Padding = drawing.Padding(5)
		self.Resizable = True

		self.image = None
		if os.path.exists(image_path):
			self.img = System.Drawing.Image.FromFile(image_path)
		else:
			return None

		self.image = forms.ImageView()
		self.image.Image = Rhino.UI.EtoExtensions.ToEto(self.img)
		self.image.Size = drawing.Size(self.img.Width/2, self.img.Height/2)

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
		self.img.Dispose()
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

def run():
	objects_to_render = rs.GetObjects("Choose Objects to Render", preselect=True)
	if not objects_to_render: return
	rs.UnselectAllObjects()

	settings = bInterface.RequestBlenderRenderSettingsDialog()
	if settings is None: return

	render_instance = BlenderRender(objects_to_render)
	render_instance.GetCameraProperties()
	render_instance.WriteJson()
	render_instance.ExportObj()
	render_instance.ExportMaterials()
	render_instance.Render()

	if settings["render"] == True and settings["showRender"] == True:
		DisplayRender(render_instance.filepath + render_instance.render_name + '.png')

run()
