'''
Created on Apr 14, 2022

@author: Benedikt Ursprung
'''
import numpy as np
from random import shuffle

from qtpy.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QLabel,
)
import pyqtgraph as pg
from pyqtgraph.dockarea.DockArea import DockArea

from ScopeFoundry import Measurement
from ScopeFoundry import h5_io
from odmr_measurements.T1_pulse_program_generator import T1PulseProgramGenerator
from odmr_measurements.contrast import ContrastModes, calculate_contrast


class T1(Measurement):

    name = "T1"

    def setup(self):

        S = self.settings

        self.range = S.New_Range(
            "t_pi_pulses", initials=[4.5e1, 5e3, 200], unit="us", si=True
        )
        S.New("N_samples", int, initial=1000)
        S.New("N_sweeps", int, initial=1)
        S.New("randomize", bool, initial=False,
              description='probe t_pi_pulses in a random order.')
        S.New("shotByShotNormalization", bool, initial=False)
        S.New(
            "contrast_mode",
            str,
            initial="signalOverReference",
            choices=ContrastModes,
        )
        S.New("save_h5", bool, initial=True)

        self.data = {
            "t_pi_pulses": np.arange(10) * 1e-9,
            # emulates N_sweeps=2
            "signal_raw": np.random.rand(20).reshape(2, -1),
            "reference_raw": np.random.rand(20).reshape(2, -1),
        }
        self.i_sweep = 0

        self.pulse_generator = T1PulseProgramGenerator(self)

    def setup_figure(self):
        self.ui = DockArea()

        widget = QWidget()
        self.plot_dock = self.ui.addDock(
            name=self.name, widget=widget, position='right')
        self.layout = QVBoxLayout(widget)

        settings_layout = QHBoxLayout()
        self.layout.addLayout(settings_layout)
        settings_layout.addWidget(self.range.New_UI(True))
        settings_layout.addWidget(self.settings.New_UI(include=[
                                  "contrast_mode", "N_samples", "N_sweeps", "randomize", "save_h5"], style='form'))

        start_layout = QVBoxLayout()
        SRS = self.app.hardware["srs_control"]
        start_layout.addWidget(QLabel('<b>SRS control</b>'))
        start_layout.addWidget(SRS.settings.New_UI(
            ['connected', 'amplitude', 'frequency']))
        start_layout.addWidget(self.settings.activation.new_pushButton())
        settings_layout.addLayout(start_layout)

        # Signal/reference Plots
        self.graph_layout = pg.GraphicsLayoutWidget(border=(100, 100, 100))
        self.layout.addWidget(self.graph_layout)
        self.plot = self.graph_layout.addPlot(title=self.name)
        self.plot.addLegend()
        self.plot.setLabel('bottom', 't_pi_pulses', 's')

        self.plot_lines = {}
        self.plot_lines["signal"] = self.plot.plot(
            pen="g", symbol="o", symbolBrush="g")
        self.plot_lines["reference"] = self.plot.plot(
            pen="r", symbol="o", symbolBrush="r")

        # contrast Plots
        self.contrast_plot = self.graph_layout.addPlot(
            title='contrast', row=1, col=0)
        self.plot_lines['contrast'] = self.contrast_plot.plot(
            name=self.data["signal_raw"], pen='w')

        self.ui.addDock(
            dock=self.pulse_generator.New_dock_UI(), position='left')
        self.update_display()

    def update_display(self):
        x = self.data["t_pi_pulses"] / 1e9

        signal = self.data["signal_raw"][0:self.i_sweep + 1, :].mean(0)
        reference = self.data["reference_raw"][0:self.i_sweep + 1, :].mean(0)

        self.plot_lines["signal"].setData(x, signal)
        self.plot_lines["reference"].setData(x, reference)

        S = self.settings
        contrast = calculate_contrast(S["contrast_mode"], signal, reference)
        self.plot_lines['contrast'].setData(x, contrast)

    def pre_run(self):
        self.pulse_generator.update_pulse_plot()
        self.pulse_generator.settings['enable_pulse_plot_update'] = False

    def run(self):
        S = self.settings

        SRS = self.app.hardware["srs_control"]
        if not SRS.settings['connected']:
            pass
            # raise RuntimeError('SRS_control hardware not connected')
        PB = self.app.hardware["pulse_blaster"]
        DAQ = self.app.hardware['pulse_width_counters']

        self.data['t_pi_pulses'] = t_pi_pulses = self.range.sweep_array

        N = len(t_pi_pulses)
        N_sweeps = S["N_sweeps"]

        try:
            SRS.connect()
            SRS.settings["modulation"] = False
            SRS.settings["output"] = True

            PB.connect()
            self.pulse_generator.program_pulse_blaster_and_start()

            DAQ.restart(S['N_samples'])

            # data arrays
            self.data["signal_raw"] = np.zeros((N_sweeps, N))
            self.data["reference_raw"] = np.zeros_like(self.data["signal_raw"])

            # Run experiment
            for i_sweep in range(N_sweeps):
                self.i_sweep = i_sweep
                if self.interrupt_measurement_called:
                    break
                self.log.info(f"sweep {i_sweep + 1} of {N_sweeps}")
                if S["randomize"]:
                    if i_sweep > 0:
                        shuffle(t_pi_pulses)
                self.indices = np.argsort(t_pi_pulses)

                for j, t_pi_pulse in enumerate(t_pi_pulses):
                    if self.interrupt_measurement_called:
                        break
                    pct = 100 * (i_sweep * N + j) / (N_sweeps * N)
                    self.set_progress(pct)

                    self.pulse_generator.settings['t_pi'] = t_pi_pulse
                    self.pulse_generator.program_pulse_blaster_and_start()

                    # Update data arrays
                    jj = self.indices[j]
                    DAQ.restart(S['N_samples'])
                    #time.sleep(S['N_samples'] * self.pulse_generator.pulse_program_duration/1e9)
                    self.data["signal_raw"][i_sweep][jj] = np.mean(
                        DAQ.read_sig_counts(S['N_samples']))
                    self.data["reference_raw"][i_sweep][jj] = np.mean(
                        DAQ.read_ref_counts(S['N_samples']))

        finally:
            SRS.settings["output"] = False
            SRS.settings["modulation"] = False
            DAQ.close_tasks()
            PB.write_close()

    def post_run(self):
        self.pulse_generator.settings['enable_pulse_plot_update'] = True
        if self.settings['save_h5']:
            self.save_h5_data()

    def save_h5_data(self):
        self.h5_file = h5_io.h5_base_file(app=self.app, measurement=self)
        self.h5_meas_group = h5_io.h5_create_measurement_group(
            self, self.h5_file)
        reference = self.data['reference_raw'].mean(0)
        signal = self.data['signal_raw'].mean(0)
        self.h5_meas_group['reference'] = reference
        self.h5_meas_group['signal'] = signal
        self.h5_meas_group['t_pi_pulses'] = self.data['t_pi_pulses']
        for cm in ContrastModes:
            self.h5_meas_group[cm] = calculate_contrast(cm, signal, reference)
        for k, v in self.data.items():
            self.h5_meas_group[k] = v
        self.pulse_generator.save_to_h5(self.h5_meas_group)
        self.h5_file.close()
