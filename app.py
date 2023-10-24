r"""
Citcomcu web animation visualization tool
基于trame和paraview的citcomcu输出数据的web动画可视化工具
"""

import paraview.web.venv  # Available in PV 5.10-RC2+
import os
import json
import asyncio

from trame.app import get_server, asynchronous
from trame.widgets import vuetify, paraview
from trame.ui.vuetify import SinglePageLayout

import paraview as pv
from paraview import simple

from w_cit_json import generate_json

# -----------------------------------------------------------------------------
# Trame setup
# -----------------------------------------------------------------------------

server = get_server()
state, ctrl = server.state, server.controller

# -----------------------------------------------------------------------------

animation_scene = simple.GetAnimationScene()
time_keeper = animation_scene.TimeKeeper

metadata = None
time_values = []
representation = None


def load_data(**kwargs):
    global time_values, representation
    # CLI
    args, _ = server.cli.parse_known_args()
    # full_path = os.path.abspath(args.data)
    # base_path = os.path.dirname(full_path)
    base_path = os.path.abspath(args.data)
    full_path = os.path.join(base_path, 'citcomcu.json')
    files = []
    reader_props = {}

    generate_json(base_path)

    with open(full_path, "r") as f:
        metadata = json.load(f)
        reader_props = metadata.get("reader_properties", {})
        fields = metadata.get("fields", [])
        for name in metadata.get("files", []):
            files.append(os.path.join(base_path, name))

    reader = simple.OpenDataFile(files)
    for key, value in reader_props.items():
        reader.GetProperty(key).SetData(value)

    reader.UpdatePipeline()
    representation = simple.Show(reader, view)

    representation.Representation = 'Outline'
    representation.ColorArrayName = ['POINTS', '']
    representation.SelectTCoordArray = 'None'
    representation.SelectNormalArray = 'None'
    representation.SelectTangentArray = 'None'
    representation.OSPRayScaleArray = 'temperature'
    representation.OSPRayScaleFunction = 'PiecewiseFunction'
    representation.SelectOrientationVectors = 'velocity'
    representation.ScaleFactor = 0.10078999996185303
    representation.SelectScaleArray = 'temperature'
    representation.GlyphType = 'Arrow'
    representation.GlyphTableIndexArray = 'temperature'
    representation.GaussianRadius = 0.005039499998092651
    representation.SetScaleArray = ['POINTS', 'temperature']
    representation.ScaleTransferFunction = 'PiecewiseFunction'
    representation.OpacityArray = ['POINTS', 'temperature']
    representation.OpacityTransferFunction = 'PiecewiseFunction'
    representation.DataAxesGrid = 'GridAxesRepresentation'
    representation.PolarAxes = 'PolarAxesRepresentation'
    representation.ScalarOpacityUnitDistance = 0.06113051150506313
    representation.OpacityArrayName = ['POINTS', 'temperature']
    # representation.ColorArray2Name = ['POINTS', 'temperature']
    representation.IsosurfaceValues = [0.5]
    representation.SliceFunction = 'Plane'
    representation.Slice = 8
    representation.SelectInputVectors = ['POINTS', 'velocity']
    representation.WriteLog = ''
	# init the 'Plane' selected for 'SliceFunction'
    representation.SliceFunction.Origin = [0.5, 0.5039499998092651, 0.31415000557899475]

    # create a new 'Glyph'
    glyph1 = simple.Glyph(registrationName='Glyph1', Input=reader,GlyphType='Arrow')
    glyph1.OrientationArray = ['POINTS', 'velocity']
    glyph1.ScaleArray = ['POINTS', 'temperature']
    glyph1.ScaleFactor = 0.10078999996185303
    glyph1.GlyphTransform = 'Transform2'

    # Properties modified on glyph1
    glyph1.ScaleArray = ['POINTS', 'No scale array']
    glyph1.ScaleFactor = 0.05140289998054505

    # show data in view
    glyph1Display = simple.Show(glyph1, view, 'GeometryRepresentation')

    # get color transfer function/color map for 'temperature'
    temperatureLUT = simple.GetColorTransferFunction('temperature')

    # trace defaults for the display properties.
    glyph1Display.Representation = 'Surface'
    glyph1Display.ColorArrayName = ['POINTS', 'temperature']
    glyph1Display.LookupTable = temperatureLUT
    glyph1Display.SelectTCoordArray = 'None'
    glyph1Display.SelectNormalArray = 'None'
    glyph1Display.SelectTangentArray = 'None'
    glyph1Display.OSPRayScaleArray = 'temperature'
    glyph1Display.OSPRayScaleFunction = 'PiecewiseFunction'
    glyph1Display.SelectOrientationVectors = 'velocity'
    glyph1Display.ScaleFactor = 0.10608302056789398
    glyph1Display.SelectScaleArray = 'temperature'
    glyph1Display.GlyphType = 'Arrow'
    glyph1Display.GlyphTableIndexArray = 'temperature'
    glyph1Display.GaussianRadius = 0.005304151028394699
    glyph1Display.SetScaleArray = ['POINTS', 'temperature']
    glyph1Display.ScaleTransferFunction = 'PiecewiseFunction'
    glyph1Display.OpacityArray = ['POINTS', 'temperature']
    glyph1Display.OpacityTransferFunction = 'PiecewiseFunction'
    glyph1Display.DataAxesGrid = 'GridAxesRepresentation'
    glyph1Display.PolarAxes = 'PolarAxesRepresentation'
    glyph1Display.SelectInputVectors = ['POINTS', 'velocity']
    glyph1Display.WriteLog = ''

    # show color bar/color legend
    glyph1Display.SetScalarBarVisibility(view, True)


    time_values = list(time_keeper.TimestepValues)

    update_color_by(0, fields, "remote")
    state.time_value = time_values[0]
    state.times = len(time_values) - 1
    state.fields = fields

    simple.ResetCamera()
    view.CenterOfRotation = view.CameraFocalPoint
    update_view("local")


ctrl.on_server_ready.add(load_data)

# -----------------------------------------------------------------------------
# ParaView pipeline
# -----------------------------------------------------------------------------

# Rendering setup
view = simple.GetRenderView()
view.UseColorPaletteForBackground = 0
view.Background = [0.8, 0.8, 0.8]
view.OrientationAxesVisibility = 0
view = simple.Render()

# -----------------------------------------------------------------------------
# Callbacks
# -----------------------------------------------------------------------------


@state.change("active_array")
def update_color_by(active_array, fields, viewMode="remote", **kwargs):
    if len(fields) == 0:
        return

    array = fields[active_array]
    simple.ColorBy(representation, (array.get("location"), array.get("text")))
    representation.RescaleTransferFunctionToDataRange(True, False)
    name = pv.make_name_valid(array.get("text"))
    lut = simple.GetColorTransferFunction(name)
    pwf = simple.GetOpacityTransferFunction(name)
    _min, _max = array.get("range")
    lut.RescaleTransferFunction(_min, _max)
    pwf.RescaleTransferFunction(_min, _max)
    update_view(viewMode)


@state.change("time")
def update_time(time, viewMode, **kwargs):
    if len(time_values) == 0:
        return

    if time >= len(time_values):
        time = 0
        state.time = time
    time_value = time_values[time]
    time_keeper.Time = time_value
    state.time_value = time_value
    update_view(viewMode)


@state.change("play")
@asynchronous.task
async def update_play(**kwargs):
    while state.play:
        with state:
            state.time += 1
            update_time(state.time, state.viewMode)

        await asyncio.sleep(0.1)


@state.change("viewMode")
def update_view(viewMode, **kwargs):
    ctrl.view_update_image()
    if viewMode == "local":
        ctrl.view_update_geometry()


# -----------------------------------------------------------------------------
# GUI
# -----------------------------------------------------------------------------

state.trame__title = "ParaView"

with SinglePageLayout(server) as layout:
    layout.title.set_text("Time")
    layout.icon.click = ctrl.view_reset_camera

    with layout.toolbar:
        vuetify.VSpacer()
        vuetify.VSelect(
            v_model=("active_array", 0),
            items=("fields", []),
            style="max-width: 200px",
            hide_details=True,
            dense=True,
        )
        vuetify.VTextField(
            v_model=("time_value", 0),
            disabled=True,
            hide_details=True,
            dense=True,
            style="max-width: 200px",
            classes="mx-2",
        )
        vuetify.VSlider(
            v_model=("time", 0),
            min=0,
            max=("times", 1),
            hide_details=True,
            dense=True,
            style="max-width: 200px",
        )

        vuetify.VCheckbox(
            v_model=("play", False),
            off_icon="mdi-play",
            on_icon="mdi-stop",
            hide_details=True,
            dense=True,
            classes="mx-2",
        )

        with vuetify.VBtn(icon=True, click=ctrl.view_reset_camera):
            vuetify.VIcon("mdi-crop-free")

        vuetify.VCheckbox(
            v_model=("viewMode", "remote"),
            true_value="remote",
            false_value="local",
            off_icon="mdi-rotate-3d",
            on_icon="mdi-video-image",
            hide_details=True,
            dense=True,
            classes="mx-2",
        )

        vuetify.VProgressLinear(
            indeterminate=True,
            absolute=True,
            bottom=True,
            active=("trame__busy",),
        )

    with layout.content:
        with vuetify.VContainer(fluid=True, classes="pa-0 fill-height"):
            html_view = paraview.VtkRemoteLocalView(view, namespace="view")
            ctrl.view_update = html_view.update
            ctrl.view_update_geometry = html_view.update_geometry
            ctrl.view_update_image = html_view.update_image
            ctrl.view_reset_camera = html_view.reset_camera


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    server.cli.add_argument("--data", help="Path to state file", dest="data")
    server.start()
