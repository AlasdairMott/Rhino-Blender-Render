# -*- encoding: utf-8 -*-

import Rhino
import scriptcontext
import System
import Rhino.UI
import Eto.Drawing as drawing
import Eto.Forms as forms
from System import Drawing as dw

import os
import json

class BlenderRenderSettingsDialog(forms.Dialog[bool]):
		# Dialog box Class initializer
	def __init__(self):
		
		# Initialize dialog box
		self.Title = 'Render Settings'
		self.Padding = drawing.Padding(5)
		self.Resizable = False

		settings = self.readSettings()

		dirname=os.path.dirname
		script_path = dirname(os.path.realpath(__file__)) + "\\"

		self.HDRIs = ["Colour"]
		for r, d, f in os.walk(script_path + "HDRI\\"):
			for file in f: 
				if '.hdr' in file: self.HDRIs.append(file)
		
		self.render_engine = forms.ComboBox()
		self.render_engine.DataStore = ["CYCLES", "EEVEE"]
		self.render_engine.SelectedIndex = 0
		self.render_scale = forms.NumericUpDown()
		self.render_samples = forms.NumericStepper()
		
		self.camera_exposure = forms.NumericUpDown()
		self.camera_exposure.DecimalPlaces = 3
		self.camera_exposure.Increment = 0.1
		self.camera_exposure.MinValue = -10.000
		self.camera_exposure.MaxValue = 10.000
		
		self.world_HDRI = forms.ComboBox()
		self.world_HDRI.DataStore = self.HDRIs
		self.world_HDRIRotation = forms.NumericStepper()
		self.world_HDRIRotation.DecimalPlaces = 2
		
		self.render_bouncesTotal = forms.NumericStepper()
		self.render_bouncesDiffuse = forms.NumericStepper()
		self.render_bouncesGlossy = forms.NumericStepper()
		self.render_bouncesTransparency = forms.NumericStepper()
		self.render_bouncesTransmission = forms.NumericStepper()
		self.render_bouncesVolume = forms.NumericStepper()
		self.render_clampingDirect = forms.NumericUpDown()
		self.render_clampingDirect.DecimalPlaces = 2
		self.render_clampingDirect.Increment = 0.01
		self.render_clampingDirect.MinValue = 0.00
		self.render_clampingIndirect = forms.NumericUpDown()
		self.render_clampingIndirect.DecimalPlaces = 2
		self.render_clampingIndirect.MinValue = 0.00
		self.render_Denoising = forms.CheckBox()
		
		self.save = forms.CheckBox()
		self.render = forms.CheckBox()
		self.showRender = forms.CheckBox()

		if settings:
			self.render_engine.SelectedIndex 		= self.render_engine.DataStore.index(settings["settings"]["render_engine"])
			self.render_scale.Value					= float(settings["settings"]["render_scale"])
			self.render_samples.Value				= int(settings["settings"]["render_samples"])
			
			self.camera_exposure.Value				= float(settings["camera"]["camera_exposure"])
			
			self.world_HDRI.SelectedIndex			= self.world_HDRI.DataStore.index(settings["world"]["world_HDRI"])
			self.world_HDRIRotation.Value			= float(settings["world"]["world_HDRIRotation"])
			
			self.render_bouncesTotal.Value			= int(settings["settings"]["render_bouncesTotal"])
			self.render_bouncesDiffuse.Value		= int(settings["settings"]["render_bouncesDiffuse"])
			self.render_bouncesGlossy.Value			= int(settings["settings"]["render_bouncesGlossy"])
			self.render_bouncesTransparency.Value	= int(settings["settings"]["render_bouncesTransparency"])
			self.render_bouncesTransmission.Value	= int(settings["settings"]["render_bouncesTransmission"])
			self.render_bouncesVolume.Value			= int(settings["settings"]["render_bouncesVolume"])
			self.render_clampingDirect.Value		= float(settings["settings"]["render_clampingDirect"])
			self.render_clampingIndirect.Value		= float(settings["settings"]["render_clampingIndirect"])
			self.render_Denoising.Checked			= bool(settings["settings"]["render_Denoising"])
			
			self.save.Checked						= bool(settings["settings"]["save"])
			self.render.Checked						= bool(settings["settings"]["render"])
			self.showRender.Checked					= bool(settings["settings"]["showRender"])
			
			loc = settings["settings"]["render_settingWindowPosition"]
			loc = loc.split(",")
			self.Location = drawing.Point(int(loc[0]), int(loc[1]))
		
		self.DefaultButton = forms.Button(Text = 'OK')
		self.DefaultButton.Click += self.OnOKButtonClick

		self.AbortButton = forms.Button(Text = 'Cancel')
		self.AbortButton.Click += self.OnCloseButtonClick

		layout = forms.DynamicLayout()
		layout.Spacing = drawing.Size(0, 1)
		
		"""Box 1: Render"""
		box_1 = forms.GroupBox()
		box_1.Padding = drawing.Padding(1)
		box_1_layout = forms.DynamicLayout()
		box_1_layout.Spacing = drawing.Size(3, 3)
		box_1.Content = box_1_layout
		
		box_1_layout.AddRow("render_engine", self.render_engine)
		box_1_layout.AddRow("render_scale", self.render_scale)
		box_1_layout.AddRow("samples", self.render_samples)
		
		
		"""Box 2: Camera"""
		box_2 = forms.GroupBox(Text = 'Camera')
		box_2.Padding = drawing.Padding(1)
		box_2_layout = forms.DynamicLayout()
		box_2_layout.Spacing = drawing.Size(3, 3)
		box_2.Content = box_2_layout
		
		box_2_layout.AddRow("Exposure", self.camera_exposure)
		
		"""Box 3: World"""
		box_3 = forms.GroupBox(Text = 'World')
		box_3.Padding = drawing.Padding(1)
		box_3_layout = forms.DynamicLayout()
		box_3_layout.Spacing = drawing.Size(3, 3)
		box_3.Content = box_3_layout
		
		box_3_layout.AddRow("HDRI", self.world_HDRI)
		box_3_layout.AddRow("HDRI Rotation", self.world_HDRIRotation)
		
		"""Box 4: Samples"""
		box_4 = forms.GroupBox(Text = 'Sampling')
		box_4.Padding = drawing.Padding(1)
		box_4_layout = forms.DynamicLayout()
		box_4_layout.Spacing = drawing.Size(3, 3)
		box_4.Content = box_4_layout
		
		self.box_4_hidden = forms.DynamicLayout(Visible = False)
		self.box_4_hidden.Spacing = drawing.Size(3, 3)
		
		self.box_4_hidden.AddRow("bouncesTotal", self.render_bouncesTotal)
		self.box_4_hidden.AddRow("bouncesDiffuse", self.render_bouncesDiffuse)
		self.box_4_hidden.AddRow("bouncesGlossy", self.render_bouncesGlossy)
		self.box_4_hidden.AddRow("bouncesTransparency", self.render_bouncesTransparency)
		self.box_4_hidden.AddRow("bouncesTransmission", self.render_bouncesTransmission)
		self.box_4_hidden.AddRow("bouncesVolume", self.render_bouncesVolume)
		self.box_4_hidden.AddRow("clampingDirect", self.render_clampingDirect)
		self.box_4_hidden.AddRow("clampingIndirect", self.render_clampingIndirect)
		
		self.dropdown_text = forms.Label(Text = "Show Sampling Properties")
		self.dropdown_samples = forms.Button(Size = drawing.Size(16,16))
		self.dropdown_samples.Text = "▼"
		self.dropdown_samples.Font = drawing.Font("Arial", 5)
		self.dropdown_samples.Click += self.dropdown_samples_Click
		
		box_4_layout.AddSeparateRow(None, self.dropdown_text, None, self.dropdown_samples, None)
		box_4_layout.AddRow(self.box_4_hidden)
		
		"""Box 5: Output"""
		box_5 = forms.GroupBox(Text = 'Output')
		box_5.Padding = drawing.Padding(1)
		box_5_layout = forms.DynamicLayout()
		box_5_layout.Spacing = drawing.Size(3, 3)
		box_5.Content = box_5_layout
		
		box_5_layout.AddRow("Denoising", self.render_Denoising)
		box_5_layout.AddRow("Save File", self.save)
		box_5_layout.AddRow("Render", self.render)
		box_5_layout.AddRow("Show Render", self.showRender)
		
		#Add the group boxes to the main interface
		layout.AddRow(box_1)
		layout.AddRow(box_2)
		layout.AddRow(box_3)
		layout.AddRow(box_4)
		layout.AddRow(box_5)
		layout.AddSeparateRow(self.DefaultButton, None, self.AbortButton)

		self.Content = layout

	def readSettings(self):
		dirname=os.path.dirname
		script_path = dirname(os.path.realpath(__file__)) + "\\"
		json_filename = script_path + "BlenderRender-Settings.json"
		
		if os.path.exists(json_filename):
			with open(json_filename) as f: return json.load(f)
		else: return None

	def dropdown_samples_Click(self, sender, e):
		if self.box_4_hidden.Visible:
			self.ClientSize = drawing.Size(self.ClientSize.Width, 406)
			self.box_4_hidden.Visible = False
			#self.dropdown_text.Visible = True
			self.dropdown_samples.Text = "▼"
		else:
			self.box_4_hidden.Visible = True
			#self.dropdown_text.Visible = False
			self.dropdown_samples.Text = "▲"
			#self.ClientSize = drawing.Size(max(self.ClientSize.Width, self.box_4_hidden.Width), self.ClientSize.Height + self.box_4_hidden.Height*2)
			self.ClientSize = drawing.Size(self.ClientSize.Width, 406 + 181)

	def OnCloseButtonClick(self, sender, e):
		self.Close(False)

	def OnOKButtonClick(self, sender, e):
		self.Close(True)


def RequestBlenderRenderSettingsDialog():
	dialog = BlenderRenderSettingsDialog();

	rc = dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)
	if (rc):
		#render_settings = dialog.GetText()
		
		dirname=os.path.dirname
		script_path = dirname(os.path.realpath(__file__)) + "\\"
		json_filename = script_path + "BlenderRender-Settings.json"

		#Clear File
		with open(json_filename, 'w') as f: json.dump({}, f)
		
		settings = {
			"render_engine": 				["CYCLES", "EEVEE"][dialog.render_engine.SelectedIndex],
			"render_scale": 				dialog.render_scale.Value,
			"render_samples": 				dialog.render_samples.Value,			
			"render_bouncesTotal": 			dialog.render_bouncesTotal.Value,
			"render_bouncesDiffuse": 		dialog.render_bouncesDiffuse.Value,
			"render_bouncesGlossy": 		dialog.render_bouncesGlossy.Value,
			"render_bouncesTransparency": 	dialog.render_bouncesTransparency.Value,
			"render_bouncesTransmission": 	dialog.render_bouncesTransmission.Value,
			"render_bouncesVolume":			dialog.render_bouncesVolume.Value,
			"render_clampingDirect": 		dialog.render_clampingDirect.Value,
			"render_clampingIndirect": 		dialog.render_clampingIndirect.Value,
			"render_Denoising": 			dialog.render_Denoising.Checked,
			"save": 						dialog.save.Checked,
			"render":						dialog.render.Checked,
			"showRender":					dialog.showRender.Checked,
			"render_settingWindowPosition": dialog.Location.ToString()
			}
			
		camera = {
			"camera_exposure": 				dialog.camera_exposure.Value
		}
		
		world = {
			"world_HDRI" :					dialog.HDRIs[dialog.world_HDRI.SelectedIndex],
			"world_HDRIRotation" :			dialog.world_HDRIRotation.Value
		}
		
		new_entry = {"settings" : settings, "camera" : camera, "world" : world}
		with open(json_filename, 'w') as f: json.dump(new_entry, f, indent = 4, sort_keys=True)
		
		return settings

if __name__ == "__main__":
	RequestBlenderRenderSettingsDialog()
