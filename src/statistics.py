"""
A module containing a variety of methods for statistical analyses.
"""

from random import shuffle
from enum import Enum

from matplotlib import pyplot as plt
import numpy as np
from tools import show_or_save

class TailType(Enum):
    """
    Represents a type of permutation test tail pattern.

    UNKNOWN means we have no prior understanding of what direction the anomaly is in.

    KNOWN_HIGH means we expect it to be higher, KNOWN_LOW means we expect it to be lower.
    """
    UNKNOWN = 1
    KNOWN_HIGH = 2
    KNOWN_LOW = 3
    def p_value(self, greater, smaller, total):
        """
        Gets the p-value under the given model for a permutation test.

        Input:
            greater, the number of elements greater than or equal to the actual value
            smaller, the number of elements smaller than or equal to the actual value
            total, the total number of elements
        """
        greater += 1
        smaller += 1
        total += 1
        return {
            TailType.UNKNOWN : min(1, 2 * min(greater, smaller) / total),
            TailType.KNOWN_HIGH : greater / total,
            TailType.KNOWN_LOW : smaller / total
        }[self]

def permutation_test(partition, summary, number, progress, tail_type=TailType.UNKNOWN):
    """
    Checks whether the differences in the SUMMARY statistic over the two PARITIONs of the data are
        real or merely the result of random chance. Takes NUMBER samples.
    """
    value = summary(partition.group_a, partition.group_b)
    distribution = [summary(a, b)
                    for a, b in _permute(partition.group_a, partition.group_b, number, progress)]
    return PermutationReport(value, distribution, tail_type)

def p_value(value, distribution, tail_type):
    """
    Returns a p value of a given value against a given distribution. I.e., returns 2 times the
        size of the tail (with the given value included as if it were not already in the
        distribution).
    """
    n_greater = len([x for x in distribution if x >= value])
    n_smaller = len([x for x in distribution if x <= value])
    return tail_type.p_value(n_greater, n_smaller, len(distribution))

class PermutationReport:
    """
    Represents a report to be delivered about a permutation test.
    """
    def __init__(self, value, distribution, tail_type):
        self.__val = value
        self.__distr = distribution
        self.__tail_type = tail_type
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
        plt.title("%sPermutation test: P-value=%.4f" % (title, self.p_value))
        plt.xlabel(summary_name)
        plt.ylabel("Frequency")
        lgd = plt.legend(bbox_to_anchor=(1.4, 1))
        show_or_save(path, lgd)
    @property
    def p_value(self):
        """
        Get the p-value for the difference in distributions.
        """
        return p_value(self.__val, self.__distr, self.__tail_type)
    def __repr__(self):
        return "PermutationReport({}, {}, {})".format(self.__val, self.__distr, self.__tail_type)

class Partition:
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
