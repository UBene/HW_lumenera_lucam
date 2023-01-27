'''
Created on Dec 9, 2022

@author: Benedikt Ursprung
'''
from functools import partial
import ctypes

from ScopeFoundry.hardware import HardwareComponent


from .lucam import LucamEnumCameras, Lucam, CAMERA_MODEL


class LucamHW(HardwareComponent):

    def __init__(self, app, debug=False, name=None):
        HardwareComponent.__init__(self, app, debug=debug, name=name)

    name = 'lucam'

    def setup(self):

        S = self.settings
        S.New('camera_number', int, initial=1)
        S.New('camera_model', str, ro=True)
        choices = [(k, v) for k, v in Lucam.PIXEL_FORMAT.items()]
        S.New('pixel_format',
              int,
              choices=choices,
              initial=2,
              description='if number, is bits used per pixel and color channel')
        S.New('x_offset', int, initial=0, unit='px')
        S.New('y_offset', int, initial=0, unit='px')
        S.New('x_binning', int, initial=1, unit='px')
        S.New('y_binning', int, initial=1, unit='px')
        S.New('width', int, vmin=8, initial=8, unit='px')
        S.New('height', int, vmin=8, initial=8, unit='px')
        S.New('frame_rate', initial=100.0,
              choices=[], description='for streaming')

        for name, value in Lucam.PROPERTY.items():
            S.New(name, type(value), initial=value)

        self.add_operation('snapshot', self.read_snapshot)
        self.add_operation('write format', self.write_format)
        self.add_operation('read format', self.read_format)

    def connect(self):

        S = self.settings

        if S['debug_mode']:
            print(self.name, 'found cameras\n',
                  *[f"{i+1} {cam.serialnumber}" for i, cam in enumerate(LucamEnumCameras())])

        self.dev = lucam = Lucam(S['camera_number'])

        S.frame_rate.change_choice_list(self.get_available_frame_rates())

        for name in Lucam.PROPERTY:
            S.get_lq(name).connect_to_hardware(partial(lucam.GetProperty, name),
                                               partial(lucam.SetProperty, name))

        S.get_lq('camera_model').connect_to_hardware(self.get_camera_model)
        S.get_lq('camera_model').read_from_hardware()

        for d in ('width', 'height'):
            value, _ = lucam.GetProperty(f'max_{d}')
            S.get_lq(d).change_min_max(8, value)

        self.read_format()

    def get_format(self):
        return self.dev.GetFormat()[0]

    def get_available_frame_rates(self):
        return self.dev.EnumAvailableFrameRates()

    def get_camera_model(self):
        return CAMERA_MODEL[self.dev.GetCameraId()]

    def start_streaming(self, callback_func):
        '''
        callback_func must be have 3 parameters:
            callback_func(context, frame_pointer, frame_size)
        returns a callback id
        '''
        self.dev.StreamVideoControl('start_streaming')
        return self.dev.AddStreamingCallback(callback_func)

    def stop_streaming(self, callback_id):
        self.dev.StreamVideoControl('stop_streaming')
        self.dev.RemoveStreamingCallback(callback_id)

    def disconnect(self):
        if not hasattr(self, 'dev'):
            return
        self.dev.CameraClose()

    def convert_to_rgb24(self, frame_pointer):
        '''RGB images can only be obtained with conversion?'''
        return self.dev.ConvertFrameToRgb24(self.get_format(), frame_pointer)[:, :, ::-1]

    def read_snapshot(self):
        frame_pointer = self.dev.TakeSnapshot().ctypes.data_as(
            ctypes.POINTER(ctypes.c_byte))
        image = self.convert_to_rgb24(frame_pointer)
        return image

    def read_format(self):
        frame_format, rate = self.dev.GetFormat()
        self.settings['width'] = frame_format.width
        self.settings['height'] = frame_format.height
        self.settings['pixel_format'] = frame_format.pixelFormat
        self.settings['x_offset'] = frame_format.xOffset
        self.settings['y_offset'] = frame_format.yOffset
        self.settings['x_binning'] = frame_format.binningX
        self.settings['y_binning'] = frame_format.binningY
        self.settings['frame_rate'] = rate
        return frame_format

    def write_format(self):
        self.dev.StreamVideoControl('stop_streaming')
        S = self.settings
        self.dev.SetFormat(
            Lucam.FrameFormat(S['x_offset'],
                              S['y_offset'],
                              S['width'],
                              S['height'],
                              S['pixel_format'],
                              flagsX=0,
                              flagsY=0,
                              subSampleX=1,
                              subSampleY=1,
                              binningX=S['x_binning'],
                              binningY=S['y_binning']
                              ),
            framerate=S['frame_rate'])
