"""
A module containing a variety of methods for statistical analyses.
"""

from random import shuffle

from matplotlib import pyplot as plt
import numpy as np
from tools import show_or_save

def permutation_test(partition, summary, number, progress):
    """
    Checks whether the differences in the SUMMARY statistic over the two PARITIONs of the data are
        real or merely the result of random chance. Takes NUMBER samples.
    """
    value = summary(partition.group_a, partition.group_b)
    distribution = [summary(a, b)
                    for a, b in _permute(partition.group_a, partition.group_b, number, progress)]
    return PermutationReport(value, distribution, p_value(value, distribution))

def p_value(value, distribution):
    """
    Returns a p value of a given value against a given distribution. I.e., returns 2 times the
        size of the tail (with the given value included as if it were not already in the
        distribution).
    """
    n_greater = len([x for x in distribution if x >= value])
    n_smaller = len([x for x in distribution if x <= value])
    p_val = (1 + min(n_greater, n_smaller)) * 2 / (1 + len(distribution))
    return min(p_val, 1)

class PermutationReport:
    """
    Represents a report to be delivered about a permutation test.
    """
    def __init__(self, value, distribution, p_val):
        self.__val = value
        self.__distr = distribution
        self.__p = p_val
    def report(self, summary_name, title=None, path=None):
        """
        Perform the report.
        """
        if all(np.isnan(self.__distr)): # pylint: disable=E1101
            return
        plt.hist(self.__distr, label="Permutation Distribution", color="green")
        plt.axvline(self.__val, label="Actual Sample", color="red")
        if title is not None:
            title = title + ": "
        else:
            title = ""
        plt.title("%sPermutation test: P-value=%.4f" % (title, self.__p))
        plt.xlabel(summary_name)
        plt.ylabel("Frequency")
        lgd = plt.legend(bbox_to_anchor=(1.4, 1))
        show_or_save(path, lgd)
    @property
    def p_value(self):
        """
        Get the p-value for the difference in distributions.
        """
        return self.__p
    def __repr__(self):
        return "PermutationReport({}, {}, {})".format(self.__val, self.__distr, self.__p)

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

def _permute(sample_a, sample_b, number, progress):
    p_bar = progress(number)
    combined = list(sample_a) + list(sample_b)
    for index in range(number):
        p_bar.update(index)
        shuffle(combined)
        yield combined[:len(sample_a)], combined[len(sample_a):]
