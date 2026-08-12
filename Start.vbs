Set objShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
objShell.CurrentDirectory = scriptDir

embedded = scriptDir & "\python-3.12.6.amd64\python.exe"

If fso.FileExists(embedded) Then
    ' Release version: embedded Python bundled with the tool
    objShell.Run """" & embedded & """ .\couleur.py", 1, True
Else
    ' Repo version: use system Python (installed by setup.bat)
    On Error Resume Next
    ret = objShell.Run("python .\couleur.py", 1, True)
    If Err.Number <> 0 Then
        MsgBox "Python was not found." & vbCrLf & vbCrLf & _
               "Run setup.bat first to install the prerequisites.", _
               vbExclamation, "Color Swap ROA 2"
    End If
End If
