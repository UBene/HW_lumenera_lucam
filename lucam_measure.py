'''
Created on Dec 9, 2022

@author: Benedikt Ursprung
'''
from datetime import datetime
import time
import os

import pyqtgraph as pg
from qtpy import QtWidgets
import numpy as np

from ScopeFoundry import Measurement, h5_io
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file


class LucamMeasure(Measurement):

    name = "lucam"

    def setup(self):

        self.hw = self.app.hardware['lucam']
        S = self.settings
        S.New('save_png', bool, initial=False, ro=False)
        S.New('save_tif', bool, initial=False, ro=False)
        S.New('save_ini', bool, initial=False, ro=False)
        S.New('save_h5', bool, initial=True, ro=False)
        S.New('mode',
              str,
              choices=('streaming',
                       'averaging',
                       'averaging_bg',
                       'snapshot'),
              initial='streaming')
        S.New('bg_subtract', bool, initial=False)
        S.New('N_avg', int, initial=100)
        S.New('scale', float, initial=1.0, unit='um/px')
        S.get_lq('scale').add_listener(self.update_display)

        self.data = {'image': np.arange(4 * 4 * 3).reshape(4, 4, 3),
                     'bg_image': np.arange(4 * 4 * 3).reshape(4, 4, 3)}

        self.display_ready = False
        self._aquireing_bg = False

    def take_avg_snapshots(self, N, data_dest='image'):
        img = 0
        for i in range(N):
            if self.interrupt_measurement_called:
                break
            print('aquiring avg', i + 1)
            img += self.hw.read_snapshot()
            self.data[data_dest] = img / (i + 1)
            self.display_ready = True
            self.set_progress(100 * (i + 1) / N)

    def setup_figure(self):
        hw = self.hw
        HS = hw.settings
        S = self.settings

        ui_filename = sibling_path(__file__, "lucam.ui")
        self.ui = load_qt_ui_file(ui_filename)

        controls_layout = self.ui.controls.layout()
        ctr_widget = HS.New_UI(
            include=('connected', 'frame_rate', 'pixel_format', 'exposure'))
        controls_layout.addWidget(ctr_widget)

        # dimensions
        # dim_lay = QtWidgets.QGridLayout()
        # controls_layout.addLayout(dim_lay)
        # dim_lay.addWidget(HS.New_UI(include=('width', 'height')))

        # start stop
        channel_layout = QtWidgets.QGridLayout()
        controls_layout.addLayout(channel_layout)
        channel_layout.addWidget(
            S.New_UI(include=('mode', 'bg_subtract', 'N_avg')))
        channel_layout.addWidget(S.activation.new_pushButton())

        # imview
        self.imview = pg.ImageView(view=pg.PlotItem())
        self.ui.centralwidget.layout().addWidget(self.imview)
        # self.circle = pg.CircleROI((10, 10), size=30)
        # self.imview.view.addItem(self.circle)

    def run(self):

        S = self.settings

        self.hw.write_format()

        if S['mode'] == 'streaming':
            self.display_update_period = 0.01
            callback_id = self.hw.start_streaming(self.streaming_callback)
            time.sleep(0.050)
            self.display_ready = True
            while not self.interrupt_measurement_called:
                time.sleep(0.050)
            self.hw.stop_streaming(callback_id)

        if S['mode'] == 'snapshot':
            self.data['image'] = self.hw.read_snapshot()
            self.save_image()

        if S['mode'] == 'averaging':
            N = self.settings['N_avg']
            self.take_avg_snapshots(N, 'image')
            self.save_image()

        if S['mode'] == 'averaging_bg':
            self.settings['bg_subtract'] = False
            self._aquireing_bg = True
            N = self.settings['N_avg']
            self.take_avg_snapshots(N, 'bg_image')
            self.display_ready = False
            self._aquireing_bg = False
            self.settings['bg_subtract'] = True

    def streaming_callback(self, context, frame_pointer, frame_size):
        self.data['image'] = self.hw.convert_to_rgb24(frame_pointer)

    def update_display(self):
        if not self.display_ready:
            return

        S = self.settings

        if self._aquireing_bg:
            img = 1.0 * self.data['bg_image']
        else:
            img = 1.0 * self.data['image']

        if S['bg_subtract']:
            img -= self.data['bg_image']

        self.imview.setImage(img,
                             # autoLevels=True
                             )

        saturation = img[:, :, :3].max() / \
            2**(8 * (self.hw.settings['pixel_format'] + 1))
        self.imview.view.setTitle(f'max saturation value: {saturation:.0%}')

        # Nx, Ny = self.data['image'].shape[:2]
        # #i = self.imview.size()
        # #Nx, Ny = i.width(), i.height()
        # c = self.circle.size()
        # self.circle.setPos(((Nx - c[0]) / 2, (Ny - c[1]) / 2))

    def save_image(self):
        self.update_imshow_extent()

        print(self.name, 'save_image')
        S = self.settings
        t0 = time.time()
        f = self.app.settings['data_fname_format'].format(
            app=self.app,
            measurement=self,
            timestamp=datetime.fromtimestamp(t0),
            ext='h5')
        fname = os.path.join(self.app.settings['save_dir'], f)

        if S['save_ini']:
            self.app.settings_save_ini(fname.replace('h5', 'ini'))
        if S['save_png']:
            self.imview.export(fname.replace('h5', 'png'))
        if S['save_tif']:
            self.imview.export(fname.replace('h5', 'tif'))
        if S['save_h5']:
            if S['bg_subtract'] and 'bg_image' in self.data:
                self.data['image'] -= self.data['bg_image']
            self.save_h5(fname)

    def save_h5(self, fname=None):
        with h5_io.h5_base_file(app=self.app, fname=fname, measurement=self) as H:
            M = h5_io.h5_create_measurement_group(measurement=self, h5group=H)
            for name, data in self.data.items():
                M.create_dataset(name, data=data, compression='gzip')

    def update_imshow_extent(self):
        Nx, Ny = self.data['image'].shape[:2]
        self.data['imshow_extent'] = np.array(
            [-0.5, Nx - 0.5, -0.5, Ny - 0.5]) * self.settings['scale']
