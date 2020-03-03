# Rhino-Blender-Render

A script for Rhino to export and render objects externally using Blender.

## Setup
Before running the script make sure to adjust the Blender Installation path in BlenderRender-Rhino.py. (args = ["C:\\Program Files\\Blender Foundation\\Blender 2.81\\blender.exe","--background", "--python", python_script, "--",   self.render_name])

Place the scripts into Rhino's script folder
C:\Users\USER\AppData\Roaming\McNeel\Rhinoceros\6.0\scripts

## Running
Add the following Alias to Rhino
Alias: RenderBlender
Command Macro: NoEcho _-RunPythonScript ("Render/BlenderRender-Rhino.py")

Use the command RenderBlender to adjust the render settings and start the render. The progress will be displayed in a console window.
