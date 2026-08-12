Set objShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
objShell.CurrentDirectory = scriptDir

pythonExe = ""

' 1. Embedded Python shipped alongside the tool
embedded = scriptDir & "\python-3.12.6.amd64\python.exe"
If fso.FileExists(embedded) Then
    pythonExe = embedded
End If

' 2. Interpreter recorded by setup.bat (avoids the Microsoft Store stub on PATH)
If pythonExe = "" Then
    recorded = scriptDir & "\python_path.txt"
    If fso.FileExists(recorded) Then
        On Error Resume Next
        Set stream = fso.OpenTextFile(recorded, 1, False, -1)
        If Err.Number = 0 Then
            candidate = Trim(stream.ReadLine)
            stream.Close
            If candidate <> "" And fso.FileExists(candidate) Then
                pythonExe = candidate
            End If
        End If
        Err.Clear
        On Error Goto 0
    End If
End If

' 3. The py launcher resolves real installs and never the Store placeholder
If pythonExe = "" Then
    launcher = objShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & _
               "\Programs\Python\Launcher\py.exe"
    If Not fso.FileExists(launcher) Then
        launcher = objShell.ExpandEnvironmentStrings("%WINDIR%") & "\py.exe"
    End If
    If fso.FileExists(launcher) Then
        objShell.Run """" & launcher & """ -3 """ & scriptDir & "\couleur.py""", 1, True
        WScript.Quit
    End If
End If

If pythonExe <> "" Then
    objShell.Run """" & pythonExe & """ """ & scriptDir & "\couleur.py""", 1, True
Else
    MsgBox "Python was not found." & vbCrLf & vbCrLf & _
           "Run setup.bat first to install the prerequisites." & vbCrLf & _
           "(If you already did, open a new window and run setup.bat again " & _
           "so it can record the interpreter.)", _
           vbExclamation, "Color Swap ROA 2"
End If
