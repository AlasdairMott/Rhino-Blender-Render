import Rhino
import scriptcontext
import System
import Rhino.UI
import Eto.Drawing as drawing
import Eto.Forms as forms

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

		self.render_engine = forms.ComboBox()						#0
		self.render_engine.DataStore = ["CYCLES", "EEVEE"]
		self.render_engine.SelectedIndex = 0
		self.render_scale = forms.NumericUpDown()					#1
		self.render_samples = forms.NumericStepper()				#2
		self.render_bouncesTotal = forms.NumericStepper()			#3
		self.render_bouncesDiffuse = forms.NumericStepper()			#4
		self.render_bouncesGlossy = forms.NumericStepper()			#5
		self.render_bouncesTransparency = forms.NumericStepper()	#6
		self.render_bouncesTransmission = forms.NumericStepper()	#7
		self.render_bouncesVolume = forms.NumericStepper()			#8
		self.render_clampingDirect = forms.NumericUpDown()			#9
		self.render_clampingDirect.DecimalPlaces = 2
		self.render_clampingDirect.Increment = 0.01
		self.render_clampingDirect.MinValue = 0.00
		self.render_clampingIndirect = forms.NumericUpDown()		#10
		self.render_clampingIndirect.DecimalPlaces = 2
		self.render_clampingIndirect.MinValue = 0.00
		self.render_Denoising = forms.CheckBox()					#11
		self.save = forms.CheckBox()								#12
		self.showRender = forms.CheckBox()

		if settings:
			self.render_engine.SelectedIndex 		= self.render_engine.DataStore.index(settings["settings"]["render_engine"])
			self.render_scale.Value					= float(settings["settings"]["render_scale"])
			self.render_samples.Value				= int(settings["settings"]["render_samples"])
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
		
		
		"""Box 1"""
		box_1 = forms.GroupBox()
		box_1.Padding = drawing.Padding(1)
		box_1_layout = forms.DynamicLayout()
		box_1_layout.Spacing = drawing.Size(3, 3)
		box_1.Content = box_1_layout
		
		box_1_layout.AddRow("render_engine", self.render_engine)
		box_1_layout.AddRow("render_scale", self.render_scale)
		box_1_layout.AddRow("samples", self.render_samples)
		
		"""Box 2"""
		box_2 = forms.GroupBox(Text = 'Sampling')
		box_2.Padding = drawing.Padding(1)
		box_2_layout = forms.DynamicLayout()
		box_2_layout.Spacing = drawing.Size(3, 3)
		box_2.Content = box_2_layout
		
		box_2_layout.AddRow("bouncesTotal", self.render_bouncesTotal)
		box_2_layout.AddRow("bouncesDiffuse", self.render_bouncesDiffuse)
		box_2_layout.AddRow("bouncesGlossy", self.render_bouncesGlossy)
		box_2_layout.AddRow("bouncesTransparency", self.render_bouncesTransparency)
		box_2_layout.AddRow("bouncesTransmission", self.render_bouncesTransmission)
		box_2_layout.AddRow("bouncesVolume", self.render_bouncesVolume)
		box_2_layout.AddRow("clampingDirect", self.render_clampingDirect)
		box_2_layout.AddRow("clampingIndirect", self.render_clampingIndirect)
		
		"""Box 3"""
		box_3 = forms.GroupBox(Text = 'Output')
		box_3.Padding = drawing.Padding(1)
		box_3_layout = forms.DynamicLayout()
		box_3_layout.Spacing = drawing.Size(3, 3)
		box_3.Content = box_3_layout
		
		box_3_layout.AddRow("Denoising", self.render_Denoising)
		box_3_layout.AddRow("Save File", self.save)
		box_3_layout.AddRow("Show Render", self.showRender)
		
		#Add the group boxes to the main interface
		layout.AddRow(box_1)
		layout.AddRow(box_2)
		layout.AddRow(box_3)
		layout.AddSeparateRow(self.DefaultButton, None, self.AbortButton)

		self.Content = layout

	def readSettings(self):
		dirname=os.path.dirname
		script_path = dirname(os.path.realpath(__file__)) + "\\"
		json_filename = script_path + "BlenderRender-Settings.json"
		
		if os.path.exists(json_filename):
			with open(json_filename) as f: return json.load(f)
		else: return None

	"""
	def GetText(self):
		return None
	"""
	
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
			"showRender":					dialog.showRender.Checked,
			"render_settingWindowPosition": dialog.Location.ToString()
			}
		
		new_entry = {"settings" : settings}
		with open(json_filename, 'w') as f: json.dump(new_entry, f, indent = 4, sort_keys=True)
		
		return dialog.showRender.Checked

if __name__ == "__main__":
	RequestBlenderRenderSettingsDialog()
