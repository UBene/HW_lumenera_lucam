import numpy as np
import matplotlib.pylab as plt

from utils.printing import print_pb_insts, print_flags
from utils.short_pulse_feature import has_short_pulses, short_pulse_feature
from utils.pb_typing import PBInstructions
from utils.plotting import make_plot_lines, matplotlib_plot


def make_test_pb_insts() -> PBInstructions:
    states = [
        0b000000000000000001101000,  # 0
        0b000000000000000001100000,  # 1
        0b000000000000000000100000,  # 2
        0b000000000000000000100100,  # 3
        0b000000000000000000100110,  # 4
        0b000000000000000001100110,  # 5
        0b000000000000000001100100,  # 6
        0b000000000000000001100000,  # 7
        0b000000000000000001100100,  # 8
        0b000000000000000000100100,  # 9
        0b000000000000000000100101,  # 10
        0b000000000000000000101100,  # 11
    ]
    inst_lengths = np.ones(len(states))*20
    return [(s, 0, 0, l) for s, l in zip(states, inst_lengths)]


def test_plotting():
    plot_lines = make_plot_lines(make_test_pb_insts())
    matplotlib_plot(plot_lines)
    plt.show()


def make_test_pb_insts_2() -> PBInstructions:
    return [
        (0b000000000000001000000001, 0, 0, 8),  # 0
        (0b000000000000001000000010, 0, 0, 10),  # 1
        (0b000000000000001000000011, 0, 0, 4),  # 2
        (0b000000000000001000000001, 0, 0, 2),  # 3
        (0b000000000000001000000001, 0, 0, 4),  # 4
        (0b000000000000001000000001, 0, 0, 6),  # 5
        (0b000000000000001000000001, 0, 0, 8),  # 6
        # (0b000000000000000000000000, 0, 0, 10),     # 7
        # (0b000000000000000000100111, 0, 0, 2),      # 8
        # (0b000000000000000001100111, 0, 0, 2),      # 9
        # (0b000000000000000001100101, 0, 0, 2),      # 10
        # (0b000000000000000001100001, 0, 0, 2),      # 11
        # (0b000000000000000001100101, 0, 0, 2),      # 12
        # (0b000000000000000000100101, 0, 0, 2),      # 13
        # (0b000000000000000000100101, 0, 0, 2),      # 14
        # (0b000000000000000000101101, 0, 0, 2),      # 15
    ]


def test_short_pulse_feature():

    print(has_short_pulses(make_test_pb_insts()))

    initial_insts = make_test_pb_insts_2()
    print(has_short_pulses(initial_insts))

    matplotlib_plot(make_plot_lines(initial_insts))
    print_pb_insts(initial_insts)

    final_insts = short_pulse_feature(initial_insts)
    print_pb_insts(final_insts)
    matplotlib_plot(make_plot_lines(final_insts), ax=None)
    plt.show()


if __name__ == "__main__":
    print_flags(2**13 ^ 2**15)
    print_flags(1 << 13 ^ 1 << 15)
    # test_plotting()
    test_short_pulse_feature()
