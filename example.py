"""Shows an example usage of the bassin optimization.

Uses random values for the flow and the price.
"""
from datetime import timedelta, datetime
import math
import numpy as np

import matplotlib.pyplot as plt


from bassin.Bassin import Bassin


NUM_INTERVALS = 7 * 24

bassin = Bassin({
    "Minimum Volume (m3)": 10000,
    "Maximum Volume (m3)": 42000,
    "Initial Volume (m3)": 20000,
    "Final Volume(m3)": 25000,
    # Intervals are hours
    "Time axis (np.datetime)": np.array([
        datetime(2019, 1, 1) + timedelta(hours=i)
        for i in range(NUM_INTERVALS)
    ]),
    # Creates a random sin based flow always > 0
    # Adds a part where it is very high to that the basin overflow
    "Incoming Flow (m3/int)": np.clip(
            1400 * np.sin(np.linspace(0, 7*(2*math.pi), num=NUM_INTERVALS))
            + 2000 * np.linspace(1, 0, num=NUM_INTERVALS),
            0, None,
        )
    ,
    # Creates a random sin based price with different freq.
    "Price (EURO/MWh) ": (
            0.2 * np.sin(np.linspace(0, 11*(1.7*math.pi), num=NUM_INTERVALS))
        ),
    # Describes how the pumping capacity can be increased, level by level
    "Pumping levels dictionary": {
        "Number of levels": 3,
        "Flow capacity of pumping": [0, 800, 1350],  # m3/int
        "Consumption of pumping": [0, 0.42, 0.84]  # MWh/int
        }
})

bassin.optimize()

fig, axes = bassin.plot()
plt.show()
