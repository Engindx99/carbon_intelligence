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
' Nothing else is imported by hand: `reload` brings in drawings.bas and
' pid.bas (MODULES) and saves the project.
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

Dim logText As String


Sub reload()
    Dim vbe As Object, proj As Object, comp As Object
    Dim names() As String, i As Long, path As String

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

    names = Split(MODULES, ",")
    For i = 0 To UBound(names)
        path = MACROS & names(i) & ".bas"
        If Dir(path) = "" Then Say "RESULT: FAILED - missing " & path: Flush: Exit Sub
        ' a removed module goes only when the running code ends, so rename
        ' it first: the import then keeps its own name, not "pid1"
        Set comp = Nothing
        Set comp = proj.VBComponents(names(i))
        Err.Clear
        If Not comp Is Nothing Then
            comp.Name = names(i) & "_old" & Format(Timer * 100, "0")
            proj.VBComponents.Remove comp
            If Err.Number <> 0 Then Say "remove " & names(i) & ": " & Err.Description: Err.Clear
        End If
        proj.VBComponents.Import path
        If Err.Number <> 0 Then
            Say "RESULT: FAILED - import " & path & ": " & Err.Description
            Flush
            Exit Sub
        End If
        Say "imported " & path & " (" & FileDateTime(path) & ")"
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
