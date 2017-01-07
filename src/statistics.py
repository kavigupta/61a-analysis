"""
A module containing a variety of methods for statistical analyses.
"""

from random import shuffle

from matplotlib import pyplot as plt
import numpy as np
from tools import show_or_save

def permutation_test(partition, summary, number):
    """
    Checks whether the differences in the SUMMARY statistic over the two PARITIONs of the data are
        real or merely the result of random chance. Takes NUMBER samples.
    """
    value = summary(partition.group_a, partition.group_b)
    distribution = [summary(a, b)
                    for a, b in _permute(partition.group_a, partition.group_b, number)]
    n_greater = len([x for x in distribution if x > value])
    n_smaller = len([x for x in distribution if x > value])
    p_value = (1 + min(n_greater, n_smaller)) * 2 / (1 + number)
    return PermutationReport(value, distribution, p_value)

class PermutationReport:
    """
    Represents a report to be delivered about a permutation test.
    """
    def __init__(self, value, distribution, p_value):
        self.__val = value
        self.__distr = distribution
        self.__p = p_value
    def report(self, title=None, path=None):
        """
        Perform the report.
        """
        if all(np.isnan(self.__distr)): # pylint: disable=E1101
            return
        plt.hist(self.__distr)
        plt.axvline(self.__val)
        if title is not None:
            title = title + ": "
        else:
            title = ""
        plt.title("%sPermutation test: P-value=%.4f" % (title, self.__p))
        lgd = plt.legend()
        show_or_save(path, lgd)
    @property
    def p_value(self):
        """
        Get the p-value for the difference in distributions.
        """
        return self.__p


class Partition: # pylint: disable=R0903
    """
    A partition of a set of data into two groups.
    """
    def __init__(self, group_a, group_b):
        self.group_a = group_a
        self.group_b = group_b
    @staticmethod
    def partition(population, decision):
        """
        Partitions POPULATION into two groups A and B with the given decision function. Values x for
            which DECISION(x) is truthy, then it is placed in A and it is placed in B otherwise.
        """
        return Partition([x for x in population if decision(x)],
                         [x for x in population if not decision(x)])

def _permute(sample_a, sample_b, number):
    combined = list(sample_a) + list(sample_b)
    for _ in range(number):
        print("*", end="")
        shuffle(combined)
        yield combined[:len(sample_a)], combined[len(sample_a):]
