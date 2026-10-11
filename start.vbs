Option Explicit

Dim shell, fso, folder, command, result, python, scriptPath
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
folder = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = folder
scriptPath = Chr(34) & folder & "\downloader_gui.py" & Chr(34)

' Prefer the Python launcher; fall back to python.exe.
python = "py -3"
result = shell.Run("cmd /c " & python & " --version >nul 2>&1", 0, True)
If result <> 0 Then
    python = "python"
    result = shell.Run("cmd /c python --version >nul 2>&1", 0, True)
End If
If result <> 0 Then
    MsgBox "Python 3가 설치되어 있지 않거나 PATH에서 찾을 수 없습니다." & vbCrLf & "Python을 설치한 뒤 다시 실행해 주세요.", vbExclamation, "Python 확인"
    WScript.Quit 1
End If

' Check imports; install only when missing.
command = "cmd /c " & python & " -c ""import requests; import bs4; import tkinter"" >nul 2>&1"
result = shell.Run(command, 0, True)
If result <> 0 Then
    MsgBox "필수 패키지(requests, beautifulsoup4)를 확인하고, 누락된 패키지를 설치합니다." & vbCrLf & "설치 과정에서 인터넷 연결이 필요할 수 있습니다.", vbInformation, "패키지 설치"
    command = "cmd /c " & python & " -m pip install requests beautifulsoup4"
    result = shell.Run(command, 1, True)
    If result <> 0 Then
        MsgBox "패키지 설치에 실패했습니다. 표시된 오류를 확인해 주세요.", vbCritical, "설치 실패"
        WScript.Quit 1
    End If
End If

result = shell.Run("cmd /c " & python & " -c ""import requests; import bs4; import tkinter"" >nul 2>&1", 0, True)
If result <> 0 Then
    MsgBox "필수 모듈을 불러올 수 없습니다. Python 및 tkinter 설치를 확인해 주세요.", vbCritical, "실행 실패"
    WScript.Quit 1
End If

' Launch without a console window.
If python = "py -3" Then
    shell.Run "pyw -3 " & scriptPath, 0, False
Else
    shell.Run "pythonw " & scriptPath, 0, False
End If
