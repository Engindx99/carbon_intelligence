Attribute VB_Name = "sw_loader"
' loader.bas -- re-imports the repo's macro modules into this project, so a
' run started from WSL (tools/sw_run.py) uses the code on disk, not the copy
' last imported by hand.
'
' One-time setup (in SolidWorks): Tools > Macro > New, save it as
'   C:\Users\engin\carbon_intelligence\geometry\output\loader.swp
' then in the VBA editor File > Import File... this loader.bas, and save.
' The module is "sw_loader": VBA will not give a module its project's name
' (it imported as "loader1" beside the empty default module, 16 Nov 2026).
' Nothing else is imported by hand: `reload` brings in the modules listed in
' MODULES_FILE (geometry\macros\loader_modules.txt: one per line, the .bas
' name and, optionally, the module name to give it, e.g. "calciner
' calciner_solid" -- calciner.bas's own name would clash with drawings.bas's
' Sub calciner) and saves the project. Without that file, MODULES. A new
' macro then needs a line in the file, not a new import of this loader.
'
' SolidWorks' API gives no way to the VBA editor from outside (sw.VBE and
' GetVBE are not members, 16 Nov 2026); inside a macro `Application` is the
' VBA host, not SldWorks, and is tried for its VBE here. Every step is
' written to LOG_FILE, so the outcome can be read from WSL.
Option Explicit

Const ROOT     As String = "C:\Users\engin\carbon_intelligence\"
Const MACROS   As String = ROOT & "geometry\macros\"
Const LOG_FILE As String = ROOT & "geometry\output\loader.log"
Const MODULES  As String = "drawings,pid"
Const MODULES_FILE As String = MACROS & "loader_modules.txt"

Dim logText As String


Sub reload()
    Dim vbe As Object, proj As Object, comp As Object
    Dim names() As String, i As Long

    logText = "loader reload " & Format(Now, "yyyy-mm-dd hh:nn:ss") & vbCrLf
    On Error Resume Next

    ' late-bound: an early-bound .VBE would not compile where it is missing
    Set vbe = CallByName(Application, "VBE", VbGet)
    If vbe Is Nothing Then
        Say "Application.VBE: not reached (" & Err.Number & " " & Err.Description & ")"
        Err.Clear
        Set vbe = CallByName(Application.SldWorks, "VBE", VbGet)
        If vbe Is Nothing Then
            Say "SldWorks.VBE: not reached (" & Err.Number & " " & Err.Description & ")"
            Say "RESULT: FAILED - no VBA editor object"
            Flush
            Exit Sub
        End If
    End If
    Err.Clear
    Say "VBA editor reached; projects: " & vbe.VBProjects.Count

    ' this project: the one holding the module "sw_loader"
    For i = 1 To vbe.VBProjects.Count
        Set comp = Nothing
        Set comp = vbe.VBProjects(i).VBComponents("sw_loader")
        Err.Clear
        If Not comp Is Nothing Then Set proj = vbe.VBProjects(i): Exit For
    Next i
    If proj Is Nothing Then Say "RESULT: FAILED - own project not found": Flush: Exit Sub
    Say "project: " & proj.Name & " (" & proj.FileName & ")"

    names = ModuleList()
    For i = 0 To UBound(names)
        If Not ImportOne(proj, names(i)) Then Flush: Exit Sub
    Next i

    ' save the project (the editor's File > Save, control id 3), so a later
    ' RunMacro2 on this file finds the new modules even if it reloads it
    vbe.CommandBars.FindControl(ID:=3).Execute
    If Err.Number <> 0 Then
        Say "save: " & Err.Description & " (the modules stay in memory only)"
        Err.Clear
    Else
        Say "saved"
    End If
    Say "RESULT: OK"
    Flush
End Sub


' The modules to import: MODULES_FILE's non-empty lines (a "'" starts a
' comment), or MODULES when there is no such file.
Private Function ModuleList() As String()
    Dim f As Integer, ln As String, acc As String
    On Error Resume Next
    If Dir(MODULES_FILE) = "" Then
        Say "no " & MODULES_FILE & ": using MODULES"
        ModuleList = Split(MODULES, ",")
        Exit Function
    End If
    f = FreeFile
    Open MODULES_FILE For Input As #f
    Do While Not EOF(f)
        Line Input #f, ln
        If InStr(ln, "'") > 0 Then ln = Left(ln, InStr(ln, "'") - 1)
        ln = Trim(Replace(ln, vbTab, " "))
        If ln <> "" Then
            If acc <> "" Then acc = acc & ","
            acc = acc & ln
        End If
    Loop
    Close #f
    Say "modules from " & MODULES_FILE & ": " & acc
    ModuleList = Split(acc, ",")
End Function


' Import one entry, "file" or "file module": geometry\macros\<file>.bas,
' named <module> (default: the file's own). An old copy is renamed first:
' a removed module goes only when the running code ends, and the import
' would otherwise come in as "pid1".
Private Function ImportOne(proj As Object, ByVal entry As String) As Boolean
    Dim parts() As String, file As String, modName As String, path As String
    Dim comp As Object, c As Object, k As Long
    On Error Resume Next

    Do While InStr(entry, "  ") > 0: entry = Replace(entry, "  ", " "): Loop
    parts = Split(entry, " ")
    file = parts(0)
    modName = file
    If UBound(parts) >= 1 Then modName = parts(1)
    path = MACROS & file & ".bas"
    If Dir(path) = "" Then Say "RESULT: FAILED - missing " & path: Exit Function

    ' the module under its final name, and (renamed imports) a stray one under the file's
    For k = 0 To 1
        Set comp = Nothing
        Set comp = proj.VBComponents(IIf(k = 0, modName, file))
        Err.Clear
        If Not comp Is Nothing And (k = 0 Or modName <> file) Then
            comp.Name = IIf(k = 0, modName, file) & "_old" & Format(Timer * 100, "0")
            proj.VBComponents.Remove comp
            If Err.Number <> 0 Then Say "remove " & comp.Name & ": " & Err.Description: Err.Clear
        End If
    Next k

    Set c = proj.VBComponents.Import(path)
    If Err.Number <> 0 Or c Is Nothing Then
        Say "RESULT: FAILED - import " & path & ": " & Err.Description
        Exit Function
    End If
    If c.Name <> modName Then
        c.Name = modName
        If Err.Number <> 0 Then
            Say "RESULT: FAILED - rename " & c.Name & " to " & modName & ": " & Err.Description
            Exit Function
        End If
    End If
    Say "imported " & path & " as " & modName & " (" & FileDateTime(path) & ")"
    ImportOne = True
End Function


Private Sub Say(ByVal s As String)
    logText = logText & s & vbCrLf
End Sub


Private Sub Flush()
    Dim f As Integer
    f = FreeFile
    Open LOG_FILE For Output As #f
    Print #f, logText;
    Close #f
End Sub
