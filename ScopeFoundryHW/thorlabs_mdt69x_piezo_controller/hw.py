"""
Created on Mar 21, 2022

@author: Benedikt Ursprung
"""
from ScopeFoundry.hardware import HardwareComponent
from functools import partial


class HW(HardwareComponent):

    name = "mdt69x_piezo_controller"

    def setup(self):
        S = self.settings
        S.New("port", str, initial="COM8")
        for x in 'xyz':
            S.New(f'{x}_target_position', float, unit='V')
        for x in 'xyz':
            S.New(f'{x}_position', float, unit='V')

    def connect(self):
        S = self.settings

        if hasattr(self, 'dev'):
            print(self.name, 'is already connected')
            return

        from .dev import Dev
        self.dev = Dev(S["port"], debug=S['debug_mode'])

        for x in 'xyz':
            S.get_lq(f'{x}_target_position').connect_to_hardware(
                write_func=partial(self.write_position, axis=x))
            S.get_lq(f'{x}_position').connect_to_hardware(
                partial(self.read_position, axis=x))

        self.read_from_hardware()

    def disconnect(self):
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev

    def read_position(self, axis='x'):
        return self.dev.query_float(f'{axis.upper()}R?')

    def write_position(self, value, axis='x'):
        self.dev.write(f'{axis.upper()}V{value:.1f}')

    def read_min_position(self, axis='x'):
        return self.dev.query_float(f'{axis.upper()}L?')

    def write_min_position(self, value, axis='x'):
        self.dev.write(f'{axis.upper()}L{value:.1f}')

    def read_max_position(self, axis='x'):
        return self.dev.query_float(f'{axis.upper()}H?')

    def write_max_position(self, value, axis='x'):
        self.dev.write(f'{axis.upper()}H{value:.1f}')

    def move_x(self, voltage):
        self.settings['x_target_position'] = voltage

    def move_y(self, voltage):
        self.settings['y_target_position'] = voltage

    def move_z(self, voltage):
        self.settings['x_target_position'] = voltage

    def New_quick_UI(self, axes="xyz"):
        from qtpy import QtWidgets
        S = self.settings
        widget = QtWidgets.QGroupBox(title=self.name)
        main_layout = QtWidgets.QVBoxLayout(widget)
        main_layout.addWidget(self.settings.New_UI(('connected',)))
        h_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(h_layout)
        for axis in axes:
            layout = QtWidgets.QVBoxLayout()
            layout.addWidget(S.get_lq(f"{axis}_position").new_default_widget())
            layout.addWidget(
                S.get_lq(f"{axis}_target_position").new_default_widget())
            # for sign in ('+', '-'):
            #     name = f'{axis} jog {sign}'
            #     btn = QtWidgets.QPushButton(name)
            #     btn.clicked.connect(self.operations[name])
            #     layout.addWidget(btn)
            h_layout.addLayout(layout)
        widget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                             QtWidgets.QSizePolicy.Maximum)
        return widget

