import time

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from descartes import PolygonPatch
from femto import Marker, PGMCompiler, PGMTrench, Trench, TrenchColumn, Waveguide
from femto.helpers import listcast, nest_level
from mpl_toolkits.mplot3d import Axes3D
from shapely.affinity import rotate, translate
from shapely.geometry import Point


class Cell(PGMCompiler):
    def __init__(self, param):
        super(Cell, self).__init__(param)
        self._param = param
        self.waveguides = []
        self.markers = []
        self.trench_cols = []
        self.trenches = []
        self.fig = None
        self.ax = None

    def append(self, obj):
        if isinstance(obj, Marker):
            self.markers.append(obj)
        elif isinstance(obj, Waveguide) or (isinstance(obj, list) and all(isinstance(x, Waveguide) for x in obj)):
            self.waveguides.append(obj)
        elif isinstance(obj, Trench):
            self.trenches.append(obj)
        elif isinstance(obj, TrenchColumn):
            for trc in obj:
                self.append(trc)
            self.trench_cols.append(obj)
        else:
            raise TypeError(f'The object must be a Waveguide, Marker or Trench object. {type(obj)} was given.')

    def plot2d(self, shutter_close: bool = True, aspect: str = 'auto', wg_style=None, sc_style=None, mk_style=None,
               tc_style=None, pc_style=None, tight: bool = True, gold_layer: bool = False):
        if wg_style is None:
            wg_style = dict()
        if sc_style is None:
            sc_style = dict()
        if mk_style is None:
            mk_style = dict()
        if tc_style is None:
            tc_style = dict()
        if pc_style is None:
            pc_style = dict()
        default_wgargs = {'linestyle': '-', 'color': 'b', 'linewidth': 2.0}
        wgargs = {**default_wgargs, **wg_style}
        default_scargs = {'linestyle': ':', 'color': 'b', 'linewidth': 0.5}
        scargs = {**default_scargs, **sc_style}
        default_mkargs = {'linestyle': '-', 'color': 'k', 'linewidth': 1.0}
        mkargs = {**default_mkargs, **mk_style}
        default_tcargs = {'facecolor': 'k', 'edgecolor': None, 'alpha': 1, 'zorder': 1}
        tcargs = {**default_tcargs, **tc_style}
        if gold_layer:
            default_pcargs = {'facecolor': '#FFD7004D', 'edgecolor': 'b', 'linewidth': 2, 'zorder': 0,}
        else:
            default_pcargs = {'facecolor': '#ADD8E64D', 'edgecolor': 'b', 'linewidth': 2, 'zorder': 0,}
        pcargs = {**default_pcargs, **pc_style}

        self.fig, self.ax = plt.subplots()
        self.ax.set_xlabel('X [mm]')
        self.ax.set_ylabel('Y [mm]')
        for bunch in self.waveguides:
            for wg in listcast(bunch):
                p = np.array(self.transform_points(wg.points)).T
                xo, yo, _ = self._shutter_mask(p, shutter=1)
                self.ax.plot(xo, yo, **wgargs)
                if shutter_close:
                    xc, yc, _ = self._shutter_mask(p, shutter=0)
                    self.ax.plot(xc, yc, **scargs)
        for mk in self.markers:
            p = np.array(self.transform_points(mk.points)).T
            xo, yo, _ = self._shutter_mask(p, shutter=1)
            self.ax.plot(xo, yo, **mkargs)
        for tr in self.trenches:
            shape = translate(tr.block, xoff=-self.new_origin[0], yoff=-self.new_origin[1])
            shape = rotate(shape, angle=self.angle, use_radians=True, origin=Point(0, 0))
            self.ax.add_patch(PolygonPatch(shape, **tcargs))

        # Origin
        self.ax.plot(0.0, 0.0, 'or')
        self.ax.annotate('(0,0)', (0.0, 0.0), textcoords="offset points", xytext=(0, 10), ha='left', color='r')
        if isinstance(aspect, str) and aspect.lower() not in ['auto', 'equal']:
            raise ValueError(f'aspect must be either `auto` or `equal`. Given {aspect.lower()}.')
        self.ax.set_aspect(aspect)
        if tight: plt.tight_layout()

        rect = patches.Rectangle((0, 0), self.xsample, self.ysample, **pcargs)
        self.ax.add_patch(rect)
        self.ax.autoscale_view()

        # # Glass
        # if self.xsample is not None:
        #     self.ax.axvline(x=0.0 - self.new_origin[0])
        #     self.ax.axvline(x=self.xsample - self.new_origin[0])

        plt.show()

    def plot3d(self, shutter_close=True, wg_style=None, sc_style=None, mk_style=None):
        if wg_style is None:
            wg_style = dict()
        if sc_style is None:
            sc_style = dict()
        if mk_style is None:
            mk_style = dict()
        default_wgargs = {'linestyle': '-', 'color': 'b', 'linewidth': 2.0}
        wgargs = {**default_wgargs, **wg_style}
        default_scargs = {'linestyle': ':', 'color': 'b', 'linewidth': 0.5}
        scargs = {**default_scargs, **sc_style}
        default_mkargs = {'linestyle': '-', 'color': 'k', 'linewidth': 2.0}
        mkargs = {**default_mkargs, **mk_style}

        self.fig = plt.figure()
        self.fig.clf()
        self.ax = Axes3D(self.fig, auto_add_to_figure=False)
        self.fig.add_axes(self.ax)
        self.ax.set_xlabel('X [mm]')
        self.ax.set_ylabel('Y [mm]')
        self.ax.set_zlabel('Z [mm]')
        for bunch in self.waveguides:
            for wg in listcast(bunch):
                xo, yo, zo = self._shutter_mask(wg.points, shutter=1)
                self.ax.plot(xo, yo, zo, **wgargs)
                if shutter_close:
                    xc, yc, zc = self._shutter_mask(wg.points, shutter=0)
                    self.ax.plot(xc, yc, zc, **scargs)
        for mk in self.markers:
            xo, yo, zo = self._shutter_mask(mk.points, shutter=1)
            self.ax.plot(xo, yo, zo, **mkargs)
        self.ax.set_box_aspect(aspect=(2, 1, 0.25))
        self.ax.plot(0.0, 0.0, 0.0, 'or')

    def save(self, filename='device_scheme.pdf', bbox_inches='tight'):
        self.fig.savefig(filename, bbox_inches=bbox_inches)

    def pgm(self, verbose: bool = True, waveguide: bool = True, marker: bool = True, trench: bool = True):
        if waveguide:
            self._wg_pgm(verbose=verbose)
        if marker:
            self._mk_pgm(verbose=verbose)
        if trench:
            self._tc_pgm(verbose=verbose)

    def _wg_pgm(self, verbose: bool = True):

        if nest_level(self.waveguides) > 2:
            raise ValueError(f'The waveguide list has too many nested levels ({nest_level(self.waveguides)}. '
                             'The maximum value is 2.')
        if not self.waveguides:
            return

        _wg_fab_time = 0.0
        self.filename = self.filename.split('.')[0]
        wg_filename = self.filename.split('.')[0] + '_WG.pgm'

        self.header()
        self.dwell(1.0)

        for bunch in self.waveguides:
            with self.repeat(listcast(bunch)[0].scan):
                for wg in listcast(bunch):
                    _wg_fab_time += wg.wtime
                    self.write(wg.points)
        self.homing()

        with open(wg_filename, 'w') as f:
            f.write(''.join(self._instructions))
        if verbose:
            print('G-code compilation completed.')
            print('Estimated fabrication time of the optical device: ',
                  time.strftime('%H:%M:%S', time.gmtime(_wg_fab_time + self._total_dwell_time)))
        self._instructions.clear()
        self._total_dwell_time = 0.0

    def _mk_pgm(self, verbose: bool = True):

        if nest_level(self.markers) > 1:
            raise ValueError(f'The markers list has too many nested levels ({nest_level(self.markers)}. '
                             'The maximum value is 1.')
        if not self.markers:
            return

        _mk_fab_time = 0.0
        self.filename = self.filename.split('.')[0]
        mk_filename = self.filename.split('.')[0] + '_MARKERS.pgm'

        self.header()
        self.dwell(1.0)

        for bunch in self.markers:
            with self.repeat(listcast(bunch)[0].scan):
                for mk in listcast(bunch):
                    _mk_fab_time += mk.wtime
                    self.write(mk.points)
        self.homing()

        with open(mk_filename, 'w') as f:
            f.write(''.join(self._instructions))
        if verbose:
            print('G-code compilation completed.')
            print('Estimated fabrication time of the markers: ',
                  time.strftime('%H:%M:%S', time.gmtime(_mk_fab_time + self._total_dwell_time)))
        self._instructions.clear()
        self._total_dwell_time = 0.0

    def _tc_pgm(self, verbose: bool = True):
        t_writer = PGMTrench(self._param, self.trench_cols)
        t_writer.write()

        if verbose:
            _tc_fab_time = 0.0
            for col in self.trench_cols:
                _tc_fab_time += col.wtime

            print('G-code compilation completed.')
            print('Estimated fabrication time of the isolation trencehs: ',
                  time.strftime('%H:%M:%S', time.gmtime(_tc_fab_time + t_writer._total_dwell_time)))
        del t_writer

    # Private interface
    @staticmethod
    def _shutter_mask(points, shutter: int = 1):
        if shutter not in [0, 1]:
            raise ValueError(f'Shutter must be either OPEN (1) or CLOSE (0). Given {shutter}.')
        x, y, z, _, s = points.T
        ym = np.where(s == shutter, y, np.nan)
        zm = np.where(s == shutter, z, np.nan)
        return x, ym, zm


def _example():
    from femto.helpers import dotdict

    PARAMETERS_GC = dotdict(
            filename='testMarker.pgm',
            lab='CAPABLE',
            new_origin=(1.0, -0.0),
            samplesize=(25, 25),
            angle=0.0,
    )

    PARAMETERS_WG = dotdict(
            scan=6,
            speed=20,
            radius=15,
            pitch=0.080,
            int_dist=0.007,
            lsafe=5,
    )

    increment = [PARAMETERS_WG.lsafe, 0, 0]
    c = Cell(PARAMETERS_GC)

    # Calculations
    mzi = [Waveguide(PARAMETERS_WG) for _ in range(2)]
    for index, wg in enumerate(mzi):
        [xi, yi, zi] = [-2, -wg.pitch / 2 + index * wg.pitch, 0.035]

        wg.start([xi, yi, zi]) \
            .linear(increment) \
            .sin_mzi((-1) ** index * wg.dy_bend) \
            .linear([5, 0, 0]) \
            .sin_mzi((-1) ** index * wg.dy_bend) \
            .linear([27, yi, zi], mode='ABS')
        wg.end()
        c.append(wg)

    c.plot2d()
    c.save('circuit_scheme.pdf')
    c.pgm()


if __name__ == '__main__':
    _example()
