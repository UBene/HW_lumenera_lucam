from __future__ import division, print_function
from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import logging

logging.basicConfig(level='WARNING')  # , filename='m3_log.txt')
logging.getLogger("ipykernel").setLevel(logging.WARNING)
logging.getLogger('PyQt4').setLevel(logging.WARNING)
logging.getLogger('PyQt5').setLevel(logging.WARNING)
logging.getLogger('LoggedQuantity').setLevel(logging.CRITICAL)
logging.getLogger('pyvisa').setLevel(logging.WARNING)


class NikonMicroscope(BaseMicroscopeApp):

    name = 'nikon_microscope'

    def setup(self):

        print("Adding Hardware Components")

        from ScopeFoundryHW.thorlabs_powermeter import ThorlabsPowerMeterHW
        self.add_hardware(ThorlabsPowerMeterHW(self))
        self.add_hardware(ThorlabsPowerMeterHW(self, name='thorlabs_powermeter_2'))
        from ScopeFoundryHW.thorlabs_powermeter import PowerMeterOptimizerMeasure
        self.add_measurement(PowerMeterOptimizerMeasure(self))        
        # from ScopeFoundryHW.thorlabs_powermeter import ThorlabsPowerMeterAnalogReadOut
        # self.add_hardware(ThorlabsPowerMeterAnalogReadOut(self))
        
        from ScopeFoundryHW.flip_mirror_arduino import FlipMirrorHW
        self.add_hardware(FlipMirrorHW(self, name='flip_mirror'))
        
        from ScopeFoundryHW.powerwheel_arduino import PowerWheelArduinoHW
        self.add_hardware(PowerWheelArduinoHW(self, name='main_beam_power_wheel', conv=3200.0 / 360))
        self.add_hardware(PowerWheelArduinoHW(self, name='side_beam_power_wheel', conv=3200.0 / 360))
                
        self.settings.New('select_power_wheel', str, choices=('power_wheel', 'power_wheel_2'))
                
        from ScopeFoundryHW.thorlabs_integrated_stepper import ThorlabsIntegratedStepperMottorHW
        self.add_hardware(ThorlabsIntegratedStepperMottorHW(self))

        # Pi spectro meter
        from ScopeFoundryHW.pi_spec import PISpectrometerHW
        self.add_hardware(PISpectrometerHW(self))

        # from ScopeFoundryHW.acton_spec import ActonSpectrometerHW
        # self.add_hardware(ActonSpectrometerHW(self))
        
        from confocal_measure.calibration_sweep import CalibrationSweep
        self.add_measurement(CalibrationSweep(self, 'calibration_sweep',
                                              'picam_readout', 'pi_spectrometer',))

        from ScopeFoundryHW.dli_powerswitch.dlipower_hardware import DLIPowerSwitchHW
        self.add_hardware(DLIPowerSwitchHW(self))
        
        from ScopeFoundryHW.thorlabs_ell6k_dual_position_slider import ELL6KDualPositionSliderHW
        self.add_hardware(ELL6KDualPositionSliderHW(self, name='dual_position_slider',
                                                    choices=(('open', 1),
                                                             ('closed', 0))))
        
        # PI stage
        from ScopeFoundryHW.pi_xyz_stage.pi_xyz_stage_hw import PIXYZStageHW
        self.add_hardware(PIXYZStageHW(self))

        v_limits = h_limits = (0, 100)
        h_unit = v_unit = 'um'
        stage_inits = dict(h_limits=h_limits, v_limits=v_limits,
                           h_unit=h_unit, v_unit=v_unit)

        # APD
        from ScopeFoundryHW.ni_daq.hw.ni_freq_counter_callback import NI_FreqCounterCallBackHW
        self.add_hardware(NI_FreqCounterCallBackHW(self, name='apd_counter'))
        from confocal_measure.apd_optimizer_cb import APDOptimizerCBMeasurement
        self.add_measurement(APDOptimizerCBMeasurement(self))
        from confocal_measure.pi_xyz_scans.pi_xyz_2d_apd_slow_scan import PIXYZ2DAPDSlowScan
        self.add_measurement(PIXYZ2DAPDSlowScan(self, **stage_inits))

        # picam
        from ScopeFoundryHW.picam.picam_hw import PicamHW
        self.add_hardware(PicamHW(self))
        from ScopeFoundryHW.picam import PicamReadoutMeasure
        self.add_measurement(PicamReadoutMeasure(self))
        from confocal_measure.pi_xyz_scans.pi_xyz_2d_picam_slow_scan import PIXYZ2DPICAMSlowScan
        self.add_measurement(PIXYZ2DPICAMSlowScan(self, **stage_inits))

        # # Timeharp
        # from ScopeFoundryHW.picoquant.timeharp_260_hw import TimeHarp260HW
        # from ScopeFoundryHW.picoquant.timeharp_optimizer import TimeHarpOptimizerMeasure
        # from ScopeFoundryHW.picoquant.timeharp_260_hist_measure import TimeHarpHistogramMeasure
        #
        # self.add_hardware(TimeHarp260HW(self))
        # self.add_measurement(TimeHarpOptimizerMeasure(self))
        # self.add_measurement(TimeHarpHistogramMeasure(self))
                
        # Hydraharp
        from ScopeFoundryHW.picoquant.hydraharp_hw import HydraHarpHW
        self.add_hardware(HydraHarpHW(self))
        from ScopeFoundryHW.picoquant.hydraharp_optimizer import HydraHarpOptimizerMeasure
        self.add_measurement(HydraHarpOptimizerMeasure(self))
        from ScopeFoundryHW.picoquant.hydraharp_hist_measure import HydraHarpHistogramMeasure
        self.add_measurement(HydraHarpHistogramMeasure(self))

        # Picoharp
        # from ScopeFoundryHW.picoquant.hydraharp_optimizer import HydraHarpOptimizerMeasure
        # self.add_measurement(HydraHarpOptimizerMeasure(self))
        
        # from ScopeFoundryHW.picoquant.hydraharp_hist_measure import HydraHarpHistogramMeasure
        # self.add_measurement(HydraHarpHistogramMeasure(self))

        from confocal_measure.pi_xyz_scans.pi_xyz_2d_histogram_slow_scan import PIXYZ2DHistogramSlowScan
        self.add_measurement(PIXYZ2DHistogramSlowScan(self, **stage_inits))

        def connect_scan_params(scan_a, scan_b):
            for lq_name in ['h0', 'h1', 'v0', 'v1', 'Nh', 'Nv']:
                scan_b.settings.get_lq(
                    lq_name).connect_to_lq(scan_a.settings.get_lq(lq_name))
        connect_scan_params(self.measurements['apd_2d_map'], self.measurements['picam_2d_map'])
        connect_scan_params(self.measurements['apd_2d_map'], self.measurements['histogram_2d_map'])
        
        # from ScopeFoundryHW.chameleon_compact_opo.chameleon_compact_opo_hw import ChameleonCompactOPOHW
        # self.add_hardware(ChameleonCompactOPOHW(self))

        # from ScopeFoundryHW.keithley_sourcemeter.keithley_sourcemeter_hc import KeithleySourceMeterComponent
        # self.add_hardware(KeithleySourceMeterComponent(self))

        # from ScopeFoundryHW.thorlabs_elliptec.elliptec_hw import ThorlabsElliptecSingleHW
        # self.add_hardware(ThorlabsElliptecSingleHW(self, name='polarizer'))

        from confocal_measure.power_scan import PowerScanMeasure
        p = 'hardware/dual_position_slider/position'
        self.add_measurement(PowerScanMeasure(self,
                                              shutter_open_lq_path=p))

        # from measurements.laser_line_writer import LaserLineWriter
        # self.add_measurement(LaserLineWriter(self))

        # from ScopeFoundryHW.keithley_sourcemeter.iv_base_measurement import IVBaseMeasurement,IVTRPL
        # self.add_measurement(IVBaseMeasurement(self))
        # self.add_measurement(IVTRPL(self))

        # from ScopeFoundryHW.crystaltech_aotf.crystaltech_aotf_hc import CrystalTechAOTF
        # self.add_hardware(CrystalTechAOTF(self))

        from ScopeFoundryHW.toupcam.toupcam_hw import ToupCamHW
        self.add_hardware(ToupCamHW(self))

        from confocal_measure.toupcam_spot_optimizer import ToupCamSpotOptimizer
        self.add_measurement(ToupCamSpotOptimizer(self))
        
        from confocal_measure.sequencer import SweepSequencer
        self.add_measurement(SweepSequencer(self))

        from ScopeFoundryHW.dynamixel_servo.dynamixel_x_servo_hw import DynamixelXServosHW
        from ScopeFoundryHW.dynamixel_servo.dynamixel_single_hw import DynamixelServoHW
        self.add_hardware(DynamixelXServosHW(self, devices=dict(focus_knob=50,
                                                                power_wheel=51)))
        self.add_hardware(DynamixelServoHW(self, name='focus_knob',
                                           lq_kwargs={'spinbox_decimals':3,
                                                      'unit':'um'}))       
        self.add_hardware(DynamixelServoHW(self, name='power_wheel'))       

        from ScopeFoundryHW.lakeshore_335.lakeshore_hw import Lakeshore335HW
        self.add_hardware(Lakeshore335HW(self))
        from ScopeFoundryHW.lakeshore_335.lakeshore_measure import LakeshoreMeasure
        self.add_measurement(LakeshoreMeasure(self))
                
        from confocal_measure.generic_sweep import GenericSweeper
        self.add_measurement(GenericSweeper(self))
        
        from confocal_measure.ranged_optimization import RangedOptimization
        self.add_measurement(RangedOptimization(self, name='auto_focus'))
        
    def setup_ui(self):
        '''sets up a quickbar'''
        Q = self.add_quickbar(load_qt_ui_file(sibling_path(__file__, 'quickbar.ui')))
        
        # Dual position slider
        DS = self.hardware.dual_position_slider.settings
        DS.connected.connect_to_widget(Q.shutter_connected_checkBox)
        DS.position.connect_to_widget(Q.shutter_open_comboBox)

        # Flip mirror
        FS = self.hardware.flip_mirror.settings
        FS.connected.connect_to_widget(Q.flip_mirror_connected_checkBox)
        FS.position.connect_to_widget(Q.flip_mirror_position_checkBox)
        
        # DLI Power switch
        widget = self.hardware.dli_powerswitch.new_mini_Widget()
        Q.additional_widgets.addWidget(widget)
        
        # Power wheel
        # n = 'main_beam_power_wheel'
        n = 'power_wheel'
        PW = self.hardware[n]
        PWS = self.hardware[n].settings        
        PWS.connected.connect_to_widget(Q.power_wheel_connected_checkBox)
        Q.power_wheel_jog_forward_pushButton.clicked.connect(lambda x:PW.jog_fwd())            
        PWS.jog.connect_to_widget(Q.power_wheel_jog_doubleSpinBox)
        Q.power_wheel_jog_backward_pushButton.clicked.connect(lambda x:PW.jog_bkwd())        
        PWS.position.connect_to_widget(Q.power_wheel_position_label)
        PWS.target_position.connect_to_widget(Q.power_wheel_target_position_doubleSpinBox)
        update_value = PWS.target_position.update_value
        Q.power_wheel_0_pushButton.clicked.connect(lambda x: update_value(0.1))
        Q.power_wheel_90_pushButton.clicked.connect(lambda x: update_value(90))
        Q.power_wheel_180_pushButton.clicked.connect(lambda x: update_value(180))
        Q.power_wheel_270_pushButton.clicked.connect(lambda x: update_value(270))
        Q.power_wheel_zero_encoder_pushButton.setVisible(False)
        # Q.power_wheel_zero_encoder_pushButton.clicked.connect(lambda x:PW.zero_encoder())            
        
        # Picam
        S = self.hardware['picam'].settings
        S.connected.connect_to_widget(Q.picam_connected_checkBox)
        
        S.ExposureTime.connect_to_widget(Q.picam_exposuretime_doubleSpinBox)
        M = self.measurements['picam_readout']
        M.settings.continuous.connect_to_widget(Q.picam_continuous_checkBox)
        M.settings.activation.connect_to_pushButton(Q.picam_start_stop_pushButton)
        M.settings.count_rate.connect_to_widget(Q.picam_count_rate_doubleSpinBox)
        Q.picam_show_ui_pushButton.clicked.connect(M.show_ui)

        # Spectrometer        
        S = self.hardware['pi_spectrometer'].settings
        S.connected.connect_to_widget(Q.spectrometer_connected_checkBox)
        S.center_wl.connect_to_widget(Q.spectrometer_center_wavelength_doubleSpinBox)
            
        # APD
        from ScopeFoundry.helper_funcs import replace_widget_in_layout
        import pyqtgraph as pg
        S = self.hardware.apd_counter.settings
        S.connected.connect_to_widget(Q.apd_connected_checkBox)
        W = replace_widget_in_layout(Q.apd_count_rate_doubleSpinBox,
                                     pg.widgets.SpinBox.SpinBox())
        S.count_rate.connect_to_widget(W)
        M = self.measurements['apd_optimizer']
        Q.apd_show_ui_pushButton.clicked.connect(M.show_ui)
        
        # Power meter
        n = 'thorlabs_powermeter'
        PMS = self.hardware[n].settings
        PMS.connected.connect_to_widget(Q.power_meter_connected_checkBox)
        PMS.wavelength.connect_to_widget(Q.power_meter_wavelength_doubleSpinBox)        
        W = replace_widget_in_layout(Q.power_meter_power_label,
                                     pg.widgets.SpinBox.SpinBox())
        PMS.power.connect_to_widget(W)
        if 'powermeter_optimizer' in self.measurements:
            M = self.measurements['powermeter_optimizer']
            M.settings.activation.connect_to_pushButton(Q.power_meter_activation_pushButton)
            Q.power_meter_show_ui_pushButton.clicked.connect(M.show_ui)

        TS = self.hardware.toupcam.settings
        TS.connected.connect_to_widget(Q.toupcam_connected_checkBox)
        M = self.measurements['toupcam_spot_optimizer']
        M.settings.activation.connect_to_widget(Q.toupcam_live_checkBox)
        Q.toupcam_show_ui_pushButton.clicked.connect(M.show_ui)
        
        knob = self.hardware.focus_knob
        S = knob.settings
        S.connected.connect_to_widget(Q.focus_wheel_connected_checkBox)
        S.position.connect_to_widget(Q.focus_wheel_position_doubleSpinBox)
        S.target_position.connect_to_widget(Q.focus_wheel_target_position_doubleSpinBox)
        S.jog.connect_to_widget(Q.focus_wheel_jog_doubleSpinBox)
        Q.focus_wheel_foreward_pushButton.clicked.connect(knob.jog_fwd)
        Q.focus_wheel_backward_pushButton.clicked.connect(knob.jog_bkwd)

    def link_2D_scan_params(self, parent_scan_name='apd_asi',
                            children_scan_names=['hyperspec_asi', 'asi_trpl_2d_scan']):
        '''call this function to link equivalent settings of children scans to a parent scan'''
        lq_names = ['h0', 'h1', 'v0', 'v1', 'Nh', 'Nv']

        parent_scan = self.measurements[parent_scan_name]
        for scan in children_scan_names:
            child_scan = self.measurements[scan]
            for lq_name in lq_names:
                master_scan_lq = parent_scan.settings.get_lq(lq_name)
                child_scan.settings.get_lq(lq_name).connect_to_lq(master_scan_lq)

                
if __name__ == '__main__':
    import sys
    app = NikonMicroscope(sys.argv)
    app.settings_load_ini('defaults.ini')
    app.load_window_positions_json(r'window_positions.json')
    sys.exit(app.exec_())
