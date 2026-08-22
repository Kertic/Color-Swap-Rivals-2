Set objShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
objShell.CurrentDirectory = scriptDir

' Always use the tool's OWN local Python, never the user's system install.
' Recent system Pythons break the UI (e.g. Python 3.14 / Tcl 9) or lack a
' working tkinter/Pillow. setup.bat installs this local copy.
pythonExe = scriptDir & "\python-3.12.6.amd64\python.exe"

If fso.FileExists(pythonExe) Then
    objShell.Run """" & pythonExe & """ """ & scriptDir & "\couleur.py""", 1, True
Else
    MsgBox "The tool's local Python was not found." & vbCrLf & vbCrLf & _
           "Run setup.bat once to install it, then launch Start.vbs again.", _
           vbExclamation, "Color Swap Rivals 2"
End If
