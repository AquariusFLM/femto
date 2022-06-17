import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

from femto import Marker, PGMCompiler, Trench, TrenchColumn, Waveguide


class Cell(PGMCompiler):
    def __init__(self, param, dim=(None, None)):
        super(Cell, self).__init__(param)
        self.dim = dim
        self.waveguides = []
        self.markers = []
        self.trench_cols = []
        self.trenches = []

    def add(self, obj):
        if isinstance(obj, Marker):
            self.markers.append(obj)
        elif isinstance(obj, Waveguide):
            self.waveguides.append(obj)
        elif isinstance(obj, Trench):
            self.trenches.append(obj)
        elif isinstance(obj, TrenchColumn):
            for trc in obj:
                self.add(trc)
            self.trench_cols.append(obj)
        else:
            raise TypeError(f'The object must be a Waveguide, Marker or Trench object. {type(obj)} was given.')

    def plot2d(self, shutter_close=True, aspect='auto', wg_style=None, sc_style=None, mk_style=None, tc_style=None):
        if tc_style is None:
            tc_style = {}
        if mk_style is None:
            mk_style = {}
        if sc_style is None:
            sc_style = {}
        if wg_style is None:
            wg_style = {}
        default_wgargs = {'linestyle': '-', 'color': 'b', 'linewidth': 2.0}
        wgargs = {**default_wgargs, **wg_style}
        default_scargs = {'linestyle': ':', 'color': 'b', 'linewidth': 0.5}
        scargs = {**default_scargs, **sc_style}
        default_mkargs = {'linestyle': '-', 'color': 'k', 'linewidth': 2.0}
        mkargs = {**default_mkargs, **mk_style}
        default_tcargs = {}
        tcargs = {**default_tcargs, **tc_style}

        fig, ax = plt.subplots()
        ax.set_xlabel('X [mm]')
        ax.set_ylabel('Y [mm]')
        for wg in self.waveguides:
            p = np.array(self.transform_points(wg.points)).T
            xo, yo, _ = self._shutter_mask(p, shutter=1)
            ax.plot(xo, yo, **wgargs)
            if shutter_close:
                xc, yc, _ = self._shutter_mask(p, shutter=0)
                ax.plot(xc, yc, **scargs)
        for mk in self.markers:
            p = np.array(self.transform_points(mk.points)).T
            xo, yo, _ = self._shutter_mask(p, shutter=1)
            ax.plot(xo, yo, **mkargs)
        for tr in self.trenches:
            ax.add_patch(tr.patch)

        # Glass
        if self.xsample is not None:
            ax.axvline(x=0.0 - self.new_origin[0])
            ax.axvline(x=self.xsample - self.new_origin[0])

        # Origin
        ax.plot(0.0, 0.0, 'or')
        ax.annotate('(0,0)', (0.0, 0.0), textcoords="offset points", xytext=(0, 10), ha='left', color='r')
        if isinstance(aspect, str) and aspect.lower() not in ['auto', 'equal']:
            raise ValueError(f'aspect must be either `auto` or `equal`. Given {aspect.lower()}.')
        ax.set_aspect(aspect)

    def plot3d(self, shutter_close=True, wg_style=None, sc_style=None, mk_style=None, tc_style=None):
        if tc_style is None:
            tc_style = {}
        if mk_style is None:
            mk_style = {}
        if sc_style is None:
            sc_style = {}
        if wg_style is None:
            wg_style = {}
        default_wgargs = {'linestyle': '-', 'color': 'b', 'linewidth': 2.0}
        wgargs = {**default_wgargs, **wg_style}
        default_scargs = {'linestyle': ':', 'color': 'b', 'linewidth': 0.5}
        scargs = {**default_scargs, **sc_style}
        default_mkargs = {'linestyle': '-', 'color': 'k', 'linewidth': 2.0}
        mkargs = {**default_mkargs, **mk_style}
        default_tcargs = {}
        tcargs = {**default_tcargs, **tc_style}

        fig = plt.figure()
        fig.clf()
        ax = Axes3D(fig, auto_add_to_figure=False)
        fig.add_axes(ax)
        ax.set_xlabel('X [mm]')
        ax.set_ylabel('Y [mm]')
        ax.set_zlabel('Z [mm]')
        for wg in self.waveguides:
            xo, yo, zo = self._shutter_mask(wg.points, shutter=1)
            ax.plot(xo, yo, zo, **wgargs)
            if shutter_close:
                xc, yc, zc = self._shutter_mask(wg.points, shutter=0)
                ax.plot(xc, yc, zc, **scargs)
        for mk in self.markers:
            xo, yo, zo = self._shutter_mask(mk.points, shutter=1)
            ax.plot(xo, yo, zo, **mkargs)
        for tr in self.trenches:
            pass
            # ax.add_patch(patch_2d_to_3d(tr.patch))
        ax.set_box_aspect(aspect=(2, 1, 0.25))
        ax.plot(0.0, 0.0, 0.0, 'or')

    # Private interface
    @staticmethod
    def _shutter_mask(points, shutter: int = 1):
        if shutter not in [0, 1]:
            raise ValueError(f'Shutter must be either OPEN (1) or CLOSE (0). Given {shutter}.')
        x, y, z, _, s = points.T
        if shutter == 1:
            # # or even mask all the values with shutter OFF
            ym = np.where(s == 1, y, np.nan)
            zm = np.where(s == 1, z, np.nan)
        else:
            # # or even mask all the values with shutter ON
            ym = np.where(s == 0, y, np.nan)
            zm = np.where(s == 0, z, np.nan)
        return x, ym, zm


def _example():
    from femto.helpers import dotdict

    PARAMETERS_GC = dotdict(
        filename='testMarker.pgm',
        lab='CAPABLE',
        new_origin=(1.0, -0.2),
        samplesize=(25, 25),
        angle=0.0,
    )

    PARAMETERS_WG = dotdict(
        scan=6,
        speed=20,
        radius=15,
        pitch=0.080,
        int_dist=0.007,
        lsafe=3,
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
            .spline_bridge((-1) ** index * 0.08, (-1) ** index * 0.015) \
            .sin_mzi((-1) ** (index + 1) * wg.dy_bend) \
            .linear(increment)
        wg.end()
        c.add(wg)

    c.plot2d()
    plt.show()


if __name__ == '__main__':
    _example()
