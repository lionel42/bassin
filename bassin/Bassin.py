#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bassin optimization file.

Created on Fri Sep 20 21:54:10 2019

@author: lionel
"""

import numpy as np
import matplotlib.pyplot as plt


class Bassin:
    """A Bassin object that represent a catch basin or a dam.

    This class can optimize the water flow out of the bassin based
    on some pumps in the output.
    """

    def __init__(self, dic):
        """Initialize the bassin from an input dictionary."""
        self.V_min = dic["Minimum Volume (m3)"]
        self.V_max = dic["Maximum Volume (m3)"]
        self.V_0 = dic["Initial Volume (m3)"]
        self.V_f = dic["Final Volume(m3)"]
        self.timeAxis = dic["Time axis (np.datetime)"]
        self.Q_in = dic["Incoming Flow (m3/int)"]
        self.Price = dic["Price (EURO/MWh) "]
        self.P_dic = dic["Pumping levels dictionary"]

        # Physical assertions on the inputs
        assert self.V_min >= 0
        assert self.V_max > self.V_min
        # assert(self.V_0 <= self.V_max and self.V_0 >= self.V_min)
        # assert(self.V_f <= self.V_max and self.V_f >= self.V_min)
        assert len(self.Q_in) > 1
        assert np.all(self.Q_in >= 0)
        assert len(self.Q_in) == len(self.Price)
        assert len(self.Price) == len(self.timeAxis)

        self.V_t = np.zeros_like(self.Q_in)
        self.V_t[0] = self.V_0
        self.V_t = np.array(np.cumsum(self.Q_in + self.V_t))
        self.V_loss = np.zeros_like(self.Q_in)

        self.is_available = np.ones(len(self.Q_in), dtype=bool)

        # Tead the pumping dictionary
        self.level_max = self.P_dic["Number of levels"]
        self.P_cap = np.array(self.P_dic["Flow capacity of pumping"])
        self.P_cons = np.array(self.P_dic["Consumption of pumping"])

        assert isinstance(self.level_max, int)
        assert self.level_max == len(self.P_cap)
        assert self.level_max == len(self.P_cons)

        self.P_levels = np.zeros(len(self.Q_in), dtype=np.int)
        self.max_levels = self.level_max * np.ones(
            len(self.Q_in), dtype=np.int
        )

        # initalize a matrix [time by n_levels] of the cost for a m3 of jumping
        # to the next level of pumping
        self.P_C_m3 = self.Price.reshape(-1, 1) * np.array(
            [
                (self.P_cons[i + 1] - self.P_cons[i])
                / (self.P_cap[i + 1] - self.P_cap[i])
                for i in range(self.level_max - 1)
            ]
        )

    def make_pump_unavailable(self, interval):
        """make a pump unavailable for a time period
        - interval list of two ints (start and end)"""
        self.max_levels[interval[0]: interval[1]] -= 1

    # helper functions
    def can_pump_at(self, t):
        """Check if it is possible to pump at time t.

        check if the next pumping level is available or
        if it won't empty too much the bassin"""
        cur_lv_ = self.P_levels[t]
        if cur_lv_ + 1 == self.max_levels[t]:
            return False
        pump_influence_ = np.zeros_like(self.V_t)
        pump_influence_[t] = self.P_cap[cur_lv_ + 1] - self.P_cap[cur_lv_]
        if np.all(self.V_t[t:] - np.cumsum(pump_influence_)[t:] >= self.V_min):
            return True
        else:
            return False

    #    def deactivate_unpumpable(self):
    #        """make unpumpable periods unavailable"""
    #        try :
    #            P_diff_ = self.P_cap[self.P_levels + 1] - self.P_cap[self.P_levels]
    #            till = np.where(self.V_t - P_diff_ < self.V_min)[0][-1]
    #            self.is_available[:till+1] = False
    #        except IndexError : pass

    def activateIfPossible(self, t):
        """
        activates the pump at the given time if it is possible to pump at that
        time, or make it unavailable at that time if is is not possible
        """
        if self.can_pump_at(t):
            self.activate_pump_and_modify_bassin_at(t)
        else:
            self.is_available[t] = False

    def find_cheapest_possibility(self, position):
        """Return the cheapest possibility of pumping till the position."""
        # list of available indexes
        e_ = np.where(self.is_available[:position])[0]
        if e_.size == 0:
            return None
        return e_[np.argmin(self.P_C_m3[e_, self.P_levels[e_]])]

    def activate_pump_and_modify_bassin_at(self, index):
        time_ = index
        # sets the pump to used
        self.P_levels[time_] += 1
        # update the bassin
        P_diff_ = (
            self.P_cap[self.P_levels[time_]]
            - self.P_cap[self.P_levels[time_] - 1]
        )
        self.V_t[time_:] -= P_diff_
        # set unavailable
        if self.P_levels[time_] + 1 == self.max_levels[time_]:
            self.is_available[time_] = False

    def overflow_at(self, time_index):
        """Create an overflow at the desired time.

        Check if it is possible to overflow the Bassin and proceed to
        an overflow."""
        assert self.V_t[time_index] > self.V_max  # overflow
        overflow_ = self.V_t[time_index] - self.V_max
        self.V_loss[time_index] += overflow_
        self.V_t[time_index:] -= overflow_

    # optimization

    def optimizer_step_at(self, t):
        # self.deactivate_unpumpable()
        while (
            self.V_t[t] >= self.V_max
            and np.sum(self.is_available[:t+1]) > 0
        ):  # loops back on all the past possible pumping times
            # search where is the optimal pumping time can add a pumping time
            # locates the cheapest pump available and available
            cheapest_P_t = self.find_cheapest_possibility(t+1)
            # removes the filling value and the next ones by this value
            # if it is possible
            if (cheapest_P_t is None):
                # No available index before now, all is unavailable
                self.is_available[:t+1] = False
            elif self.can_pump_at(cheapest_P_t):
                # If we can pump at this index
                self.activate_pump_and_modify_bassin_at(cheapest_P_t)
            else:
                self.is_available[cheapest_P_t] = False

        if self.V_t[t] > self.V_max:
            self.overflow_at(t)

    def set_to_final_value(self):

        V_max = self.V_max

        if self.V_f < self.V_min:
            print(
                "Impossible to set the final volume to ",
                self.V_f,
                " because it is smaller than the minimum volume limit ",
                self.V_min,
            )
            self.V_f = self.V_min

        # Temporarily replace V max to V f
        self.V_max = self.V_f
        self.optimizer_step_at(len(self.V_t) - 1)
        self.V_max = V_max
        if self.V_loss[-1] > 0:
            print("Could not find enough pumping power to set to ", self.V_f)

    def optimize(self):
        """Optimization algo.

        Will activate pumps and remove the water from the bassin
        based on the optimal pumping periods.
        """
        # starts the algo to pump the water and remove it
        # first part to avoid having a overfull bassin, loops across time
        for index in range(len(self.V_t)):
            # print(index)
            self.optimizer_step_at(index)
        self.set_to_final_value()

    def costOfPumping(self):
        """Return the total cost of pumping.
        """
        return np.sum(self.P_cons[self.P_levels] * self.Price)

    def Q_Pumped(self):
        """Return the total volume that has been pumped.
        """
        return np.sum(self.P_cap[self.P_levels])

    def plot(self):
        """Plot the optimization result."""
        fig, ax = plt.subplots(figsize=(16,9))
        ax.plot(self.timeAxis, self.V_t, label="Volume (m^3)")
        ax.set_ylabel("m^3 , EURO/MWh")
        ax.set_xlabel("time")
        ax.legend(loc='upper right')
        axbis = ax.twinx()
        axbis.plot(self.timeAxis, self.Price, "black", label="Price (EUR/MWh)")
        axbis.legend(loc='upper center')
        axthree = axbis.twinx()
        axthree.plot(
            self.timeAxis, self.Q_in, "g", label="Incoming Flow (m^3/int)"
        )
        axthree.plot(
            self.timeAxis,
            self.P_cap[self.P_levels],
            ".r",
            label="Pumped Flow (m^3/int)",
        )
        axthree.plot(
            self.timeAxis, self.V_loss, "pink", label="Over Flow (m^3/int)"
        )
        axthree.set_ylabel("m^3")
        axthree.legend(loc='upper left')
        return fig, [ax, axbis, axthree]

    def tests(self):
        """All the tests defined for a bassin.

        Make sure that the optimization algorithm worked as expected.
        """
        # test that we did not go over the maximum pumping levels
        assert np.all(
            np.logical_and(0 <= self.P_levels, self.P_levels < self.max_levels)
        )
        # test the filling of the bassin
        assert np.all(
            np.logical_and(self.V_min <= self.V_t, self.V_t <= self.V_max)
        )
        # test no water was lost : q_here + q_arriving = q_lost + q_pumped + q_left
        tol = 10e-5
        assert tol > (
            np.abs(self.V_0 + np.sum(self.Q_in))
            - (np.sum(self.V_loss + self.P_cap[self.P_levels]) + self.V_t[-1])
        )
