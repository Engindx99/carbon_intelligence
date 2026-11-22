Attribute VB_Name = "kiln_lining"
'==================================================================
' Rotary kiln WALL as the twin models it  ->  SLDPRT + STEP (AP214)
'
' NOT a CFD input (the gas volume is kiln.bas). This part is the wall
' stack of physics/shell.py (DEFAULT_WALL_STACKS burning / transition, as
' burning.py / transition.py place it: r_inner = KILN_D / 2), built as
' separate bodies so the drawing and the twin describe the same wall:
'
'   brick        r R .. R + brick,   z L_b .. L - L_b  (one tube)
'   steel_shell  r .. + shell,       z 0 .. L          (one tube)
'
' R = KILN_D / 2 is the flow bore and the brick's hot face: the brick is
' the innermost layer and there is no clinker coating (user decisions 22
' Nov 2026: the 4.8 m bore kept, the layers outward, one wall over the
' tube, "no layer, in the drawings or in the twin, for now"). The twin's
' zones differ only in the brick grade (alumina z 0 .. transition_L,
' magnesia-spinel beyond): a model split, so the solid has NO joint there
' -- one brick tube and one shell tube (user, 22 Nov 2026: "one tube
' instead of joining two"; two rings meeting at the zone boundary also
' showed a jagged display seam).
'
' BRICKS (user request 22 Nov 2026: the bricks stand radially, "like
' teeth"): ISO 5417 rotary kiln bricks, cold face A on the shell side,
' length KILN_BRICK_L along the axis; a ring holds BRICK_N wedges of
' 2 pi / BRICK_N each (the two-shape mix that closes a real ring,
' averaged into one wedge). 60 000 bricks would choke the part, so the
' two END rings (z 0 .. L_b, L - L_b .. L) are built brick by brick and
' the brick between them is the one tube. The wedges fill the annulus
' exactly (joints and mortar not modelled), so the wall's volume is the
' twin's. Each wedge is centred on the x = 0 plane's profile (a mid-plane
' revolve), so no joint lies on the planes x = 0 or y = 0 (BRICK_N is
' divisible by 4) where the drawing cuts.
'   brick_ring_<k>_<iii>    ring k = 0 (back end) / 1 (hood end), wedge iii from +y towards -x
'
' Not modelled (no source, or no effect on the twin): tyres and their
' wrapper plates, girth gear, seals, joints, mortar, metal plates,
' castable at the kiln ends, wear. The slope is not built in (as
' kiln.bas): the tube's axis is z, back end z = 0, hood end z = L.
'
' SI ONLY. The SolidWorks API is always metres and radians.
'
' To run: python3 tools/sw_run.py kiln_lining_solid.main from WSL, or
' import this .bas in SolidWorks' VBA editor and run `main`.
' Outputs geometry\output\2500\kiln_lining.SLDPRT, .step and
' kiln_lining_build.log.
'==================================================================

Option Explicit

Const PART_NAME As String = "kiln_lining"
Const LINE_KEY As String = "2500"

' BEGIN GENERATED (tools/gen_geometry.py) -- do not edit by hand.
' From geometry/plant_geometry.yaml through geometry/plant_geometry.py;
' change the source and run: python3 tools/gen_geometry.py
Const KILN_D                       As Double  = 4.8          ' the flow (gas) bore: the brick's hot face, the whole tube (the twin's D) [published, kiln/kiln.md]
Const KILN_L                       As Double  = 74#          ' back end (z = 0) to hood end: the whole tube is lined [published, kiln/kiln.md]
Const KILN_SHELL_T                 As Double  = 0.03         ' steel shell plate [literature, kiln/kiln.md]
Const KILN_BRICK_T                 As Double  = 0.22         ' brick ring, both zones [literature, kiln/kiln.md]
Const V_SHELL                      As Double  = 36.754749    ' steel shell, one tube 0 .. L [m3] [derived]
Const KILN_BRICK_L                 As Double  = 0.198        ' brick length along the axis (ISO 5417): one ring [literature, kiln/kiln.md]
Const BRICK_N                      As Double  = 160          ' bricks per ring (both zones) [derived]
Const V_RING                       As Double  = 0.686976     ' one brick ring, all its bricks [m3] [derived]
Const V_BRICK                      As Double  = 255.374593   ' brick tube between the two brick-by-brick end rings [m3] [derived]
' END GENERATED

Const OUT_ROOT As String = "C:\Users\engin\carbon_intelligence\geometry\output\"

Const VOL_TOL  As Double = 0.001   ' relative, on each body's volume
Const BOX_TOL  As Double = 0.001   ' absolute [m]
Const DIR_TOL  As Double = 0.000001
Const PLANE_TOL As Double = 0.000001
Const PI As Double = 3.14159265358979
Const N_BODIES As Long = 2
Const N_RINGS As Long = 2

Dim swApp   As SldWorks.SldWorks
Dim swModel As SldWorks.ModelDoc2
Dim swPart  As SldWorks.PartDoc
Dim swFeat  As SldWorks.FeatureManager
Dim swSkMgr As SldWorks.SketchManager

Dim oldVerify As Boolean, oldInputDim As Boolean, prefsTouched As Boolean
Dim uSign As Double, vSign As Double
Dim uSignX As Double, vSignX As Double      ' the x = 0 plane, for the revolve profiles
Dim wRef As Double
Dim wRefSet As Boolean

Dim exportPrefsTouched As Boolean
Dim oldStepAP As Long, oldStepAppear As Boolean

' the two brick-by-brick end rings: radii, z range, count, volume
Dim gR0(N_RINGS - 1) As Double, gR1(N_RINGS - 1) As Double
Dim gZ0(N_RINGS - 1) As Double, gZ1(N_RINGS - 1) As Double
Dim gN(N_RINGS - 1) As Long, gV(N_RINGS - 1) As Double

' the layer bodies: name, radii, z range, expected volume, colour
Dim bName(N_BODIES - 1) As String
Dim bR0(N_BODIES - 1) As Double, bR1(N_BODIES - 1) As Double
Dim bZ0(N_BODIES - 1) As Double, bZ1(N_BODIES - 1) As Double
Dim bV(N_BODIES - 1) As Double
Dim bRGB(N_BODIES - 1, 2) As Double

Dim buildLog As String
Dim phase As String


'==================================================================
' main
'==================================================================
Sub main()

    Dim why As String

    buildLog = ""
    phase = "starting up"
    On Error GoTo Failed

    Set swApp = Application.SldWorks
    If swApp Is Nothing Then Fail "SolidWorks is not running."

    phase = "working out the layers"
    Layers
    phase = "building the bodies"
    Build
    phase = "verifying the bodies"
    Verify
    phase = "exporting"
    ExportFiles

    Restore
    WriteLog PART_NAME & " built, verified and exported"
    ' no message box when OUT_ROOT\quiet.flag exists (tools/sw_run.py)
    If Dir(OUT_ROOT & "quiet.flag") = "" Then
        MsgBox PART_NAME & " built, verified and exported." & vbLf & vbLf & buildLog, vbInformation, "Kiln lining"
    End If
    Exit Sub

Failed:
    why = Err.Description
    Restore
    WriteLog PART_NAME & " ABORTED while " & phase & ": " & why
    If Dir(OUT_ROOT & "quiet.flag") = "" Then
        MsgBox PART_NAME & " ABORTED -- nothing was exported." & vbLf & vbLf & _
               "while " & phase & ":" & vbLf & why & vbLf & vbLf & buildLog, vbCritical, "Kiln lining"
    End If
End Sub


'==================================================================
' Layers: the annuli from the generated thicknesses
'==================================================================
Private Sub Layers()
    Dim r As Double, rS As Double

    r = 0.5 * KILN_D
    rS = r + KILN_BRICK_T

    ' the brick tube runs between the two brick-by-brick end rings
    SetBody 0, "brick", r, rS, KILN_BRICK_L, KILN_L - KILN_BRICK_L, V_BRICK, 0.72, 0.5, 0.36
    SetBody 1, "steel_shell", rS, rS + KILN_SHELL_T, 0#, KILN_L, V_SHELL, 0.32, 0.34, 0.38

    SetRing 0, r, rS, 0#, CLng(BRICK_N), V_RING
    SetRing 1, r, rS, KILN_L - KILN_BRICK_L, CLng(BRICK_N), V_RING

    Note "flow bore D " & Fmt(KILN_D) & " m = brick hot face, both zones; shell OD " & Fmt(2# * (rS + KILN_SHELL_T)) & _
         " m over the whole " & Fmt(KILN_L) & " m; no coating"
End Sub


Private Sub SetRing(ByVal k As Long, ByVal r0 As Double, ByVal r1 As Double, ByVal z0 As Double, _
                    ByVal n As Long, ByVal vWant As Double)
    Dim vGeo As Double
    If n < 8 Or (n Mod 4) <> 0 Then Fail "ring " & k & ": " & n & " bricks; the macro needs a multiple of 4 (no joint on x = 0 or y = 0)."
    vGeo = PI * (r1 * r1 - r0 * r0) * KILN_BRICK_L
    If Abs(vGeo - vWant) > VOL_TOL * vWant Then _
        Fail "ring " & k & ": the radii give " & Fmt(vGeo) & " m3, the generated block says " & Fmt(vWant) & " m3."
    gR0(k) = r0: gR1(k) = r1: gZ0(k) = z0: gZ1(k) = z0 + KILN_BRICK_L
    gN(k) = n: gV(k) = vWant
    Note "brick ring " & k & ": z " & Fmt(gZ0(k)) & " .. " & Fmt(gZ1(k)) & " m, " & n & " wedges, cold face chord " & _
         Fmt(2# * r1 * Sin(PI / n)) & " m, hot face chord " & Fmt(2# * r0 * Sin(PI / n)) & " m"
End Sub


Private Function RingName(ByVal k As Long, ByVal i As Long) As String
    RingName = "brick_ring_" & k & "_" & Format(i, "000")
End Function


Private Sub SetBody(ByVal i As Long, ByVal nm As String, ByVal r0 As Double, ByVal r1 As Double, _
                    ByVal z0 As Double, ByVal z1 As Double, ByVal vWant As Double, _
                    ByVal cr As Double, ByVal cg As Double, ByVal cb As Double)
    Dim vGeo As Double

    If Not (r1 > r0 And r0 > 0# And z1 > z0) Then Fail "layer " & nm & " is empty or inside out."
    ' the generated volume and the one from the generated radii are the
    ' same number by two routes (plant_geometry.kiln vs here)
    vGeo = PI * (r1 * r1 - r0 * r0) * (z1 - z0)
    If Abs(vGeo - vWant) > VOL_TOL * vWant Then _
        Fail "layer " & nm & ": the radii give " & Fmt(vGeo) & " m3, the generated block says " & Fmt(vWant) & " m3."

    bName(i) = nm
    bR0(i) = r0: bR1(i) = r1
    bZ0(i) = z0: bZ1(i) = z1
    bV(i) = vWant
    bRGB(i, 0) = cr: bRGB(i, 1) = cg: bRGB(i, 2) = cb
End Sub


'==================================================================
' Build: each annulus an (r, z) rectangle revolved about the axis,
' NOT merged, then named and coloured
'==================================================================
Private Sub Build()
    Dim planeX0 As SldWorks.Feature
    Dim f As SldWorks.Feature
    Dim i As Long

    Set swModel = swApp.NewPart
    If swModel Is Nothing Then Fail "could not create a new part. Check the default part template."
    Set swPart = swModel
    Set swFeat = swModel.FeatureManager
    Set swSkMgr = swModel.SketchManager

    oldVerify = swApp.GetUserPreferenceToggle(swPerformanceVerifyOnRebuild)
    oldInputDim = swApp.GetUserPreferenceToggle(swInputDimValOnCreate)
    swApp.SetUserPreferenceToggle swPerformanceVerifyOnRebuild, True
    swApp.SetUserPreferenceToggle swInputDimValOnCreate, False
    prefsTouched = True

    swSkMgr.AddToDB = True
    swSkMgr.DisplayWhenAdded = False

    Set planeX0 = FindPlaneWithNormal(1#, 0#, 0#)
    If planeX0 Is Nothing Then Fail "could not find the default plane whose normal is X."
    CalibrateSketchAxes planeX0, 0#, 0#, 0#, uSignX, vSignX

    For i = 0 To N_BODIES - 1
        Set f = RevolveProfile(planeX0, Array( _
            bR0(i), bZ0(i), _
            bR1(i), bZ0(i), _
            bR1(i), bZ1(i), _
            bR0(i), bZ1(i)), False, False)
        If f Is Nothing Then Fail "FeatureRevolve2 failed on " & bName(i) & "."
        NameNewBody i
    Next i

    For i = 0 To N_RINGS - 1
        BuildRing planeX0, i
    Next i

    FineDisplay
End Sub


' Display only (the B-rep is exact): SolidWorks tessellates each body by a
' chord deviation relative to the part's 74 m box, so the 2.4 m bore came
' out as long chords, and two rings sharing an edge got different chords:
' a jagged seam at the zone joint. Ask for 0.1 mm; SolidWorks clamps it to
' its box-relative minimum (about 46 mm on this part), the finest it allows.
' Saved with the part.
Private Sub FineDisplay()
    Dim ext As SldWorks.ModelDocExtension
    Set ext = swModel.Extension
    ext.SetUserPreferenceInteger swImageQualityShaded, swDetailingNoOptionSpecified, swShadedImageQualityCustom
    ext.SetUserPreferenceDouble swImageQualityShadedDeviation, swDetailingNoOptionSpecified, 0.0001
    ext.SetUserPreferenceInteger swImageQualityWireframe, swDetailingNoOptionSpecified, swWireframeImageQualityCustom
    ext.SetUserPreferenceInteger swImageQualityWireframeValue, swDetailingNoOptionSpecified, 100
    ext.SetUserPreferenceToggle swImageQualityUseHighQualityEdgeSize, swDetailingNoOptionSpecified, True
    ext.SetUserPreferenceToggle swImageQualitySaveTesselationWithPartDoc, swDetailingNoOptionSpecified, True
    Note "display: shaded deviation " & Format(ext.GetUserPreferenceDouble(swImageQualityShadedDeviation, _
         swDetailingNoOptionSpecified) * 1000#, "0.000") & " mm, wireframe " & _
         ext.GetUserPreferenceInteger(swImageQualityWireframeValue, swDetailingNoOptionSpecified)
    swModel.GraphicsRedraw2
End Sub


' One brick-by-brick ring: a wedge of 2 pi / n revolved symmetrically about
' the x = 0 plane (centred on +y), then n - 1 copies turned about z by the
' same angle (Move/Copy Body). Each wedge is named by where it landed, read
' from its centroid: an index used twice, or a wedge off its slot, fails.
Private Sub BuildRing(planeX0 As SldWorks.Feature, ByVal k As Long)
    Dim f As SldWorks.Feature, th As Double, n As Long, nBefore As Long
    Dim bodies As Variant, body As SldWorks.Body2, base As SldWorks.Body2
    Dim mp As Variant, i As Long, idx As Long, ang As Double, hits As Long
    Dim used() As Boolean
    Dim shade As Double

    n = gN(k): th = 2# * PI / n
    bodies = swPart.GetBodies2(swSolidBody, True)
    nBefore = UBound(bodies) + 1

    Set f = RevolveProfile(planeX0, Array( _
        gR0(k), gZ0(k), _
        gR1(k), gZ0(k), _
        gR1(k), gZ1(k), _
        gR0(k), gZ1(k)), False, False, th)
    If f Is Nothing Then Fail "FeatureRevolve2 failed on brick ring " & k & "'s first wedge."

    bodies = swPart.GetBodies2(swSolidBody, True)
    If UBound(bodies) + 1 <> nBefore + 1 Then Fail "ring " & k & ": the first wedge merged (" & (UBound(bodies) + 1) & " bodies)."
    For i = 0 To UBound(bodies)
        Set body = bodies(i)
        If Not IsNamed(body.Name) Then Set base = body: hits = hits + 1
    Next i
    If hits <> 1 Then Fail "ring " & k & ": " & hits & " unnamed bodies after the first wedge, expected 1."
    mp = base.GetMassProperties(1#)
    If Abs(mp(0)) > 0.000001 Or mp(1) <= 0# Then _
        Fail "ring " & k & ": the first wedge's centroid is at x " & Fmt(mp(0)) & ", y " & Fmt(mp(1)) & _
             " -- the mid-plane revolve did not centre it on +y."
    If Abs(mp(3) - gV(k) / n) > VOL_TOL * gV(k) / n Then _
        Fail "ring " & k & ": a wedge is " & Fmt(mp(3)) & " m3, expected " & Fmt(gV(k) / n) & " m3."

    ' The copies: a temporary copy of the seed, turned about z by i th, made
    ' a body of the part. (Move/Copy Body needs the seed selected, and
    ' neither Body2.Select2 nor SelectByID2 SOLIDBODY took it on 22 Nov
    ' 2026; this path selects nothing. Where each copy lands is read back
    ' from its centroid below, whichever way the transform turns.)
    Dim mu As SldWorks.MathUtility, xf As SldWorks.MathTransform, tb As SldWorks.Body2
    Dim d(15) As Double, c As Double, s As Double
    Set mu = swApp.GetMathUtility
    base.Name = RingName(k, 0) & "_seed"
    For i = 1 To n - 1
        Set tb = base.Copy
        If tb Is Nothing Then Fail "ring " & k & ": Body2.Copy returned nothing."
        c = Cos(i * th): s = Sin(i * th)
        d(0) = c: d(1) = s: d(2) = 0#
        d(3) = -s: d(4) = c: d(5) = 0#
        d(6) = 0#: d(7) = 0#: d(8) = 1#
        d(9) = 0#: d(10) = 0#: d(11) = 0#
        d(12) = 1#: d(13) = 0#: d(14) = 0#: d(15) = 0#
        Set xf = mu.CreateTransform(d)
        tb.ApplyTransform xf
        Set f = swPart.CreateFeatureFromBody3(tb, False, 0)
        If f Is Nothing Then Fail "ring " & k & ": CreateFeatureFromBody3 failed on copy " & i & "."
    Next i

    bodies = swPart.GetBodies2(swSolidBody, True)
    If UBound(bodies) + 1 <> nBefore + n Then _
        Fail "ring " & k & ": " & (UBound(bodies) + 1 - nBefore) & " wedges after copying, expected " & n & "."
    ReDim used(n - 1)
    For i = 0 To UBound(bodies)
        Set body = bodies(i)
        If Not IsNamed(body.Name) Then
            mp = body.GetMassProperties(1#)
            ' from +y towards -x: a turn about +z
            ang = Atan2(-mp(0), mp(1))
            If ang < 0# Then ang = ang + 2# * PI
            idx = CLng(ang / th) Mod n
            If Abs(ang - idx * th) > 0.01 * th And Abs(ang - 2# * PI) > 0.01 * th Then _
                Fail "ring " & k & ": a wedge sits at " & Fmt(ang * 180# / PI) & " deg, off its slot."
            If used(idx) Then Fail "ring " & k & ": two wedges at slot " & idx & " (the copies did not step round)."
            used(idx) = True
            If Abs(mp(2) - 0.5 * (gZ0(k) + gZ1(k))) > BOX_TOL Then Fail "ring " & k & ": a wedge is off the ring's z."
            body.Name = RingName(k, idx)
            If body.Name <> RingName(k, idx) Then Fail "a wedge did not take the name " & RingName(k, idx) & "."
            ' alternate shades: the joints read as teeth
            shade = IIf(idx Mod 2 = 0, 1#, 0.82)
            If k = 0 Then   ' back end: the alumina grade
                PaintBody body, 0.86 * shade, 0.68 * shade, 0.46 * shade
            Else            ' hood end: magnesia-spinel
                PaintBody body, 0.6 * shade, 0.32 * shade, 0.26 * shade
            End If
        End If
    Next i
    Note "brick ring " & k & ": " & n & " wedges built, each in its own slot"
End Sub


' A layer's or a placed ring wedge's name (brick_ring_k_iii, 16 characters):
' given already. The seed (..._seed) and its copies are not.
Private Function IsNamed(ByVal nm As String) As Boolean
    Dim j As Long
    If Left(nm, 11) = "brick_ring_" And Len(nm) = 16 Then IsNamed = True: Exit Function
    For j = 0 To N_BODIES - 1
        If nm = bName(j) Then IsNamed = True: Exit Function
    Next j
End Function


Private Function Atan2(ByVal y As Double, ByVal x As Double) As Double
    If x > 0# Then
        Atan2 = Atn(y / x)
    ElseIf x < 0# Then
        Atan2 = Atn(y / x) + IIf(y >= 0#, PI, -PI)
    Else
        Atan2 = IIf(y >= 0#, 0.5 * PI, -0.5 * PI)
    End If
End Function


' The body the last revolve made: the one not yet given a layer name.
' It is named and its faces painted.
Private Sub NameNewBody(ByVal i As Long)
    Dim bodies As Variant, body As SldWorks.Body2
    Dim k As Long, j As Long, n As Long, taken As Boolean
    Dim found As SldWorks.Body2

    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail "no body after revolving " & bName(i) & "."
    If UBound(bodies) + 1 <> i + 1 Then _
        Fail "after " & bName(i) & " the part has " & (UBound(bodies) + 1) & " bodies, expected " & (i + 1) & _
             " (a revolve merged into its neighbour)."

    n = 0
    For k = 0 To UBound(bodies)
        Set body = bodies(k)
        taken = False
        For j = 0 To i - 1
            If body.Name = bName(j) Then taken = True
        Next j
        If Not taken Then
            Set found = body
            n = n + 1
        End If
    Next k
    If n <> 1 Then Fail "found " & n & " unnamed bodies after revolving " & bName(i) & ", expected 1."

    found.Name = bName(i)
    If found.Name <> bName(i) Then Fail "the body did not take the name " & bName(i) & "."
    PaintBody found, bRGB(i, 0), bRGB(i, 1), bRGB(i, 2)
End Sub


'==================================================================
' Verify: the layer bodies and the rings, each its own volume and box
'==================================================================
Private Sub Verify()
    Dim bodies As Variant, body As SldWorks.Body2
    Dim k As Long, i As Long, hit As Long
    Dim vSum As Double

    Dim nWant As Long, kr As Long, nRing As Long, vRing As Double, mp As Variant
    nWant = N_BODIES + gN(0) + gN(1)
    bodies = swPart.GetBodies2(swSolidBody, True)
    If IsEmpty(bodies) Then Fail "the part has no solid body."
    If UBound(bodies) + 1 <> nWant Then Fail "the part has " & (UBound(bodies) + 1) & " bodies, not " & nWant & "."

    For kr = 0 To N_RINGS - 1
        nRing = 0: vRing = 0#
        For k = 0 To UBound(bodies)
            Set body = bodies(k)
            If Left(body.Name, 13) = "brick_ring_" & kr & "_" Then
                mp = body.GetMassProperties(1#)
                nRing = nRing + 1
                vRing = vRing + mp(3)
            End If
        Next k
        If nRing <> gN(kr) Then Fail "ring " & kr & " has " & nRing & " wedges, expected " & gN(kr) & "."
        If Abs(vRing - gV(kr)) > VOL_TOL * gV(kr) Then Fail "ring " & kr & " is " & Fmt(vRing) & " m3, expected " & Fmt(gV(kr)) & " m3."
        Note "brick ring " & kr & ": " & nRing & " wedges, " & Fmt(vRing) & " m3 (expected " & Fmt(gV(kr)) & ")"
        vSum = vSum + vRing
    Next kr

    For i = 0 To N_BODIES - 1
        hit = 0
        For k = 0 To UBound(bodies)
            Set body = bodies(k)
            If body.Name = bName(i) Then
                hit = hit + 1
                CheckBody body, i
                vSum = vSum + bV(i)
            End If
        Next k
        If hit <> 1 Then Fail "found " & hit & " bodies named " & bName(i) & ", expected 1."
    Next i
    Note nWant & " bodies, " & Fmt(vSum) & " m3 of wall in all"
End Sub


Private Sub CheckBody(body As SldWorks.Body2, ByVal i As Long)
    Dim edges As Variant, edge As SldWorks.Edge, adj As Variant
    Dim mp As Variant, vGot As Double, e As Long
    Dim b(5) As Double, d(2) As Double, want(5) As Double
    Dim px As Double, py As Double, pz As Double
    Dim a As Long, sd As Long, nm As Variant

    edges = body.GetEdges
    If IsEmpty(edges) Then Fail bName(i) & " has no edges."
    For e = 0 To UBound(edges)
        Set edge = edges(e)
        adj = edge.GetTwoAdjacentFaces2
        If IsEmpty(adj) Then Fail bName(i) & ": edge " & e & " reports no adjacent faces; the body is not closed."
        If adj(0) Is Nothing Or adj(1) Is Nothing Then Fail bName(i) & ": edge " & e & " has one adjacent face; open shell."
    Next e

    mp = body.GetMassProperties(1#)
    vGot = mp(3)
    If Abs(vGot - bV(i)) > VOL_TOL * bV(i) Then _
        Fail bName(i) & " is " & Fmt(vGot) & " m3, expected " & Fmt(bV(i)) & " m3."

    nm = Array("x min", "y min", "z min", "x max", "y max", "z max")
    For a = 0 To 2
        For sd = -1 To 1 Step 2
            d(0) = 0#: d(1) = 0#: d(2) = 0#: d(a) = sd
            If Not body.GetExtremePoint(d(0), d(1), d(2), px, py, pz) Then Fail "GetExtremePoint failed on " & bName(i) & "."
            If sd < 0 Then b(a) = Choose(a + 1, px, py, pz) Else b(a + 3) = Choose(a + 1, px, py, pz)
        Next sd
    Next a
    want(0) = -bR1(i): want(1) = -bR1(i): want(2) = bZ0(i)
    want(3) = bR1(i): want(4) = bR1(i): want(5) = bZ1(i)
    For a = 0 To 5
        If Abs(b(a) - want(a)) > BOX_TOL Then _
            Fail bName(i) & "'s " & nm(a) & " is " & Fmt(b(a)) & " m but should be " & Fmt(want(a)) & " m."
    Next a

    Note "body " & bName(i) & ": r " & Fmt(bR0(i)) & " .. " & Fmt(bR1(i)) & " m, z " & Fmt(bZ0(i)) & " .. " & _
         Fmt(bZ1(i)) & " m, " & Fmt(vGot) & " m3 (expected " & Fmt(bV(i)) & "), closed, " & (UBound(edges) + 1) & " edges"
End Sub


'==================================================================
' Export: SLDPRT and STEP AP214 (the body colours); no STL, it is not
' a mesh input
'==================================================================
Private Sub ExportFiles()
    Dim outDir As String
    outDir = OUT_ROOT & LINE_KEY & "\"
    EnsureDir OUT_ROOT
    EnsureDir outDir

    oldStepAP = swApp.GetUserPreferenceIntegerValue(swStepAP)
    oldStepAppear = swApp.GetUserPreferenceToggle(swStepExportAppearances)
    exportPrefsTouched = True
    swApp.SetUserPreferenceIntegerValue swStepAP, 214
    swApp.SetUserPreferenceToggle swStepExportAppearances, True

    swModel.ForceRebuild3 False
    SaveOne outDir & PART_NAME & ".SLDPRT"
    SaveOne outDir & PART_NAME & ".step"
End Sub


Private Sub SaveOne(ByVal path As String)
    Dim errs As Long, warns As Long
    swModel.Extension.SaveAs path, swSaveAsCurrentVersion, swSaveAsOptions_Silent, Nothing, errs, warns
    If errs <> 0 Then Fail "could not write " & path & " (error " & errs & ", warning " & warns & ")."
    If Dir(path) = "" Then Fail "SolidWorks reported no error but " & path & " is not on disk."
    Note "wrote " & path
End Sub


Private Sub EnsureDir(ByVal path As String)
    If Dir(path, vbDirectory) = "" Then MkDir path
End Sub


' Every face of the body, through the property from a typed Double
' array, read back and checked (as kiln.bas paints its faces).
Private Sub PaintBody(body As SldWorks.Body2, ByVal r As Double, ByVal g As Double, ByVal b As Double)
    Dim faces As Variant, face As SldWorks.Face2
    Dim m(8) As Double, got As Variant, k As Long

    m(0) = r: m(1) = g: m(2) = b
    m(3) = 1#: m(4) = 1#: m(5) = 0.3: m(6) = 0.3: m(7) = 0#: m(8) = 0#
    faces = body.GetFaces
    If IsEmpty(faces) Then Fail "a body has no faces to paint."
    For k = 0 To UBound(faces)
        Set face = faces(k)
        face.MaterialPropertyValues = m
        got = face.MaterialPropertyValues
        If IsEmpty(got) Then Fail "a face reports no colour after one was set on it."
        If Abs(got(0) - r) > 0.01 Or Abs(got(1) - g) > 0.01 Or Abs(got(2) - b) > 0.01 Then _
            Fail "a face's colour did not hold."
    Next k
End Sub


'==================================================================
' Housekeeping
'==================================================================
Private Sub Restore()
    On Error Resume Next
    If Not swSkMgr Is Nothing Then
        swSkMgr.AddToDB = False
        swSkMgr.DisplayWhenAdded = True
    End If
    If prefsTouched Then
        swApp.SetUserPreferenceToggle swPerformanceVerifyOnRebuild, oldVerify
        swApp.SetUserPreferenceToggle swInputDimValOnCreate, oldInputDim
        prefsTouched = False
    End If
    If exportPrefsTouched Then
        swApp.SetUserPreferenceIntegerValue swStepAP, oldStepAP
        swApp.SetUserPreferenceToggle swStepExportAppearances, oldStepAppear
        exportPrefsTouched = False
    End If
End Sub


Private Sub Fail(ByVal msg As String)
    Err.Raise vbObjectError + 1, "kiln_lining", msg
End Sub


Private Function LogPath() As String
    LogPath = OUT_ROOT & LINE_KEY & "\kiln_lining_build.log"
End Function


Private Sub WriteLog(ByVal outcome As String)
    Dim fn As Integer
    On Error Resume Next
    If Dir(OUT_ROOT, vbDirectory) = "" Then MkDir OUT_ROOT
    If Dir(OUT_ROOT & LINE_KEY, vbDirectory) = "" Then MkDir OUT_ROOT & LINE_KEY
    fn = FreeFile
    Open LogPath() For Output As #fn
    Print #fn, outcome & vbLf & buildLog;
    Close #fn
End Sub


Private Sub Note(ByVal msg As String)
    buildLog = buildLog & msg & vbLf
End Sub


Private Function Fmt(ByVal v As Double) As String
    Fmt = Format(v, "0.######")
End Function


'==================================================================
' Sketch helpers, as in kiln.bas (calibrated at run time)
'==================================================================

' A closed profile in the x = 0 plane, given as r, z pairs, revolved
' 360 deg about the z axis. A profile clear of the axis gets one
' centreline on it. merge = False keeps the new body separate from
' the ones it touches.
Private Function RevolveProfile(planeX0 As SldWorks.Feature, pts As Variant, _
                                ByVal isCut As Boolean, ByVal merge As Boolean, _
                                Optional ByVal midAngle As Double = 0#) As SldWorks.Feature

    Dim n As Long, i As Long, j As Long
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim zLo As Double, zHi As Double
    Dim seg As SldWorks.SketchSegment
    Dim axisSeg As SldWorks.SketchSegment
    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature
    Dim selData As SldWorks.SelectData

    uSign = uSignX: vSign = vSignX

    n = (UBound(pts) + 1) \ 2
    zLo = pts(1): zHi = pts(1)
    For i = 0 To n - 1
        If pts(2 * i + 1) < zLo Then zLo = pts(2 * i + 1)
        If pts(2 * i + 1) > zHi Then zHi = pts(2 * i + 1)
    Next i

    swModel.ClearSelection2 True
    planeX0.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open a sketch on the x = 0 plane."
    wRefSet = False

    For i = 0 To n - 1
        j = (i + 1) Mod n
        G2S sk, 0#, pts(2 * i), pts(2 * i + 1), u0, v0
        G2S sk, 0#, pts(2 * j), pts(2 * j + 1), u1, v1
        Set seg = swSkMgr.CreateLine(u0, v0, 0#, u1, v1, 0#)
        If seg Is Nothing Then Fail "CreateLine failed on the revolve profile."
        If pts(2 * i) = 0# And pts(2 * j) = 0# Then Set axisSeg = seg
    Next i

    If axisSeg Is Nothing Then
        G2S sk, 0#, 0#, zLo, u0, v0
        G2S sk, 0#, 0#, zHi, u1, v1
        Set axisSeg = swSkMgr.CreateCenterLine(u0, v0, 0#, u1, v1, 0#)
        If axisSeg Is Nothing Then Fail "CreateCenterLine failed on the revolve axis."
    End If

    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    swModel.ClearSelection2 True
    Set selData = swModel.SelectionManager.CreateSelectData
    selData.Mark = 16
    axisSeg.Select4 False, selData
    skFeat.Select2 True, 0

    ' midAngle > 0: a wedge of that angle, symmetric about the sketch plane
    If midAngle > 0# Then
        Set RevolveProfile = swFeat.FeatureRevolve2( _
            True, True, False, isCut, False, False, _
            swEndCondMidPlane, 0, midAngle, 0#, _
            False, False, 0.01, 0.01, _
            0, 0#, 0#, _
            merge, True, True)
    Else
        Set RevolveProfile = swFeat.FeatureRevolve2( _
            True, True, False, isCut, False, False, _
            0, 0, 2# * PI, 0#, _
            False, False, 0.01, 0.01, _
            0, 0#, 0#, _
            merge, True, True)
    End If

    swModel.ClearSelection2 True

End Function


'==================================================================
' Sketch plane mapping -- copied from kiln.bas (cyclone.bas has the
' reasons in full).
'==================================================================
Private Sub G2S(sk As SldWorks.Sketch, ByVal gx As Double, ByVal gy As Double, ByVal gz As Double, _
                ByRef u As Double, ByRef v As Double)

    Dim a As Variant, s As Double, w As Double

    a = sk.ModelToSketchTransform.ArrayData
    s = a(12)
    u = ((a(0) * gx + a(1) * gy + a(2) * gz) * s + a(9)) * uSign
    v = ((a(3) * gx + a(4) * gy + a(5) * gz) * s + a(10)) * vSign
    w = (a(6) * gx + a(7) * gy + a(8) * gz) * s + a(11)

    If Not wRefSet Then
        wRef = w
        wRefSet = True
    ElseIf Abs(w - wRef) > PLANE_TOL Then
        Fail "point (" & Fmt(gx) & ", " & Fmt(gy) & ", " & Fmt(gz) & ") lies " & _
             Fmt(w - wRef) & " m off the plane of the other points in its sketch."
    End If

End Sub


Private Sub CalibrateSketchAxes(pl As SldWorks.Feature, _
                                ByVal bx As Double, ByVal by As Double, ByVal bz As Double, _
                                ByRef us As Double, ByRef vs As Double)

    If Not TryCalibrateSketchAxes(pl, bx, by, bz, us, vs) Then
        Fail "sketch axis calibration failed on plane " & pl.Name & ": no combination of " & _
             "sketch axis signs put a test block where it was asked for."
    End If

End Sub


Private Function TryCalibrateSketchAxes(pl As SldWorks.Feature, _
                                        ByVal bx As Double, ByVal by As Double, ByVal bz As Double, _
                                        ByRef us As Double, ByRef vs As Double) As Boolean

    Dim mx As Double, my As Double, mz As Double
    Dim i1 As Long, i2 As Long
    Dim p0(2) As Double, p1(2) As Double
    Dim k As Long

    PlaneNormal pl, mx, my, mz
    If Abs(mx) > 0.9 Then
        i1 = 1: i2 = 2
    ElseIf Abs(my) > 0.9 Then
        i1 = 0: i2 = 2
    ElseIf Abs(mz) > 0.9 Then
        i1 = 0: i2 = 1
    Else
        Fail "sketch axis calibration: the plane normal (" & Fmt(mx) & ", " & Fmt(my) & _
             ", " & Fmt(mz) & ") is not a model axis."
    End If

    p0(0) = bx: p0(1) = by: p0(2) = bz
    p1(0) = bx: p1(1) = by: p1(2) = bz
    p0(i1) = p0(i1) + 1#: p1(i1) = p1(i1) + 2#
    p0(i2) = p0(i2) + 3#: p1(i2) = p1(i2) + 5#

    For k = 0 To 3
        us = 1#: If (k And 1) <> 0 Then us = -1#
        vs = 1#: If (k And 2) <> 0 Then vs = -1#
        If ProbeLandsWhereAsked(pl, p0, p1, i1, i2, us, vs) Then
            Note "sketch axes on plane " & pl.Name & ": u x " & Fmt(us) & ", v x " & Fmt(vs)
            TryCalibrateSketchAxes = True
            Exit Function
        End If
    Next k

    TryCalibrateSketchAxes = False

End Function


Private Function ProbeLandsWhereAsked(pl As SldWorks.Feature, p0() As Double, p1() As Double, _
                                      ByVal i1 As Long, ByVal i2 As Long, _
                                      ByVal us As Double, ByVal vs As Double) As Boolean

    Dim sk As SldWorks.Sketch
    Dim skFeat As SldWorks.Feature, f As SldWorks.Feature
    Dim u0 As Double, v0 As Double, u1 As Double, v1 As Double
    Dim bodies As Variant, box As Variant
    Dim i3 As Long
    Dim ok As Boolean

    uSign = us: vSign = vs

    bodies = swPart.GetBodies2(swSolidBody, True)
    If Not IsEmpty(bodies) Then
        Fail "sketch axis calibration was asked to run with " & (UBound(bodies) + 1) & _
             " body/bodies already in the part; it only works on an empty one."
    End If

    swModel.ClearSelection2 True
    pl.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open the sketch axis calibration sketch."
    wRefSet = False

    G2S sk, p0(0), p0(1), p0(2), u0, v0
    G2S sk, p1(0), p1(1), p1(2), u1, v1
    swSkMgr.CreateLine u0, v0, 0#, u1, v0, 0#
    swSkMgr.CreateLine u1, v0, 0#, u1, v1, 0#
    swSkMgr.CreateLine u1, v1, 0#, u0, v1, 0#
    swSkMgr.CreateLine u0, v1, 0#, u0, v0, 0#
    swSkMgr.InsertSketch True
    Set skFeat = LastFeature("ProfileFeature")

    swModel.ClearSelection2 True
    skFeat.Select2 False, 0
    Set f = swFeat.FeatureExtrusion3( _
        True, False, False, _
        swEndCondBlind, swEndCondBlind, 0.5, 0.01, _
        False, False, False, False, 0#, 0#, _
        False, False, False, False, _
        True, True, True, _
        swStartSketchPlane, 0#, False)
    swModel.ClearSelection2 True

    If f Is Nothing Then
        ok = False
    Else
        bodies = swPart.GetBodies2(swSolidBody, True)
        If IsEmpty(bodies) Then
            ok = False
        Else
            box = bodies(0).GetBodyBox
            i3 = 3 - i1 - i2
            ok = Near(box(i1), p0(i1)) And Near(box(i1 + 3), p1(i1)) And _
                 Near(box(i2), p0(i2)) And Near(box(i2 + 3), p1(i2)) And _
                 (Near(box(i3), p0(i3)) Or Near(box(i3 + 3), p0(i3)))
        End If
        swModel.ClearSelection2 True
        f.Select2 False, 0
        swModel.EditDelete
        swModel.ClearSelection2 True
    End If

    swModel.ClearSelection2 True
    skFeat.Select2 False, 0
    swModel.EditDelete
    swModel.ClearSelection2 True

    bodies = swPart.GetBodies2(swSolidBody, True)
    If Not IsEmpty(bodies) Then
        Fail "a sketch axis calibration probe could not be removed; " & _
             (UBound(bodies) + 1) & " body/bodies are still in the part."
    End If

    ProbeLandsWhereAsked = ok

End Function


Private Function Near(ByVal a As Double, ByVal b As Double) As Boolean
    Near = (Abs(a - b) < 0.001)
End Function


Private Sub PlaneNormal(pl As SldWorks.Feature, ByRef mx As Double, ByRef my As Double, ByRef mz As Double)

    Dim sk As SldWorks.Sketch
    Dim a As Variant

    swModel.ClearSelection2 True
    pl.Select2 False, 0
    swSkMgr.InsertSketch True
    Set sk = swSkMgr.ActiveSketch
    If sk Is Nothing Then Fail "could not open a probe sketch on a reference plane."
    a = sk.ModelToSketchTransform.ArrayData
    mx = a(6): my = a(7): mz = a(8)
    swSkMgr.InsertSketch True
    swModel.ClearSelection2 True

End Sub


Private Function FindPlaneWithNormal(ByVal vx As Double, ByVal vy As Double, ByVal vz As Double) As SldWorks.Feature

    Dim f As SldWorks.Feature
    Dim mx As Double, my As Double, mz As Double

    Set f = swModel.FirstFeature
    Do While Not f Is Nothing
        If f.GetTypeName2 = "RefPlane" Then
            PlaneNormal f, mx, my, mz
            If Abs(Abs(mx * vx + my * vy + mz * vz) - 1#) < DIR_TOL Then
                Set FindPlaneWithNormal = f
                Exit Function
            End If
        End If
        Set f = f.GetNextFeature
    Loop

End Function


Private Function LastFeature(ByVal typeName As String) As SldWorks.Feature
    Dim f As SldWorks.Feature
    Set f = swModel.FeatureByPositionReverse(0)
    If f Is Nothing Then Fail "no feature was created where a " & typeName & " was expected."
    If f.GetTypeName2 <> typeName Then
        Fail "expected the last feature to be a " & typeName & ", found " & f.GetTypeName2 & "."
    End If
    Set LastFeature = f
End Function
