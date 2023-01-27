'''
Created on Dec 9, 2022

@author: Benedikt Ursprung
'''
import logging

from ScopeFoundry import BaseMicroscopeApp

level = 'DEBUG'
logging.basicConfig(level='DEBUG')
logging.getLogger('LoggedQuantity').setLevel(logging.DEBUG)


class TestApp(BaseMicroscopeApp):

    name = 'lucam_test_app'

    def setup(self):

        from ScopeFoundryHW.lumenera_lucam import LucamHW, LucamMeasure
        self.add_hardware(LucamHW(self))
        self.add_measurement(LucamMeasure(self))


if __name__ == '__main__':
    import sys
    app = TestApp(sys.argv)
    sys.exit(app.exec_())
