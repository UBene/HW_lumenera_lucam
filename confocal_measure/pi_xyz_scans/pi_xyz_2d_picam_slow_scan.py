from .pi_xyz_2d_slow_scan import PIXYZ2DSlowScan
import numpy as np


class PIXYZ2DPICAM2DSlowScan(PIXYZ2DSlowScan):
    
    name = 'pi_xyz_2d_picam_slow_scan'

    def __init__(self, app):
        PIXYZ2DSlowScan.__init__(self, app)        
        
    def setup(self):
        PIXYZ2DSlowScan.setup(self)
        self.stage = self.app.hardware['PI_xyz_stage']

        self.target_range = 0.050e-3  # um
        self.slow_move_timeout = 10.  # sec

    def collect_pixel(self, pixel_num, k, j, i):
        
        measure = self.app.measurements["picam_readout"]
        self.start_nested_measure_and_wait(measure, nested_interrupt=False)
        
        if pixel_num == 0:
            wls = measure.get_wavelengths()
            self.data_spape = (*self.scan_shape, len(wls)) 
            if self.settings['save_h5']:
                self.spec_map_h5 = self.h5_meas_group.create_dataset('spec_map',
                                                                   shape=self.data_spape,
                                                                   dtype=float,
                                                                   compression='gzip')
                self.h5_meas_group.create_dataset(
                    'wls',
                    data=wls
                    )

        spec = measure.get_spectrum()
        self.display_image_map[k, j, i] = np.sum(spec)
        if self.settings['save_h5']:
            self.spec_map_h5[k, j, i] = spec
