"""
A module containing a variety of methods for statistical analyses.
"""

from random import shuffle

from matplotlib import pyplot as plt
import numpy as np

def permutation_test(partition, summary, number):
    value = summary(partition.group_A, partition.group_B)
    distribution = [summary(a, b) for a, b in permute(partition.group_A, partition.group_B, number)]
    n_greater = len([x for x in distribution if x > value])
    n_smaller = len([x for x in distribution if x > value])
    p_value = (1 + min(n_greater, n_smaller)) * 2 / (1 + number)
    return PermutationReport(value, distribution, p_value)

class PermutationReport:
    def __init__(self, value, distribution, p_value):
        self.__val = value
        self.__distr = distribution
        self.__p = p_value
    def report(self, title=None):
        if all(np.isnan(self.__distr)):
            return
        plt.hist(self.__distr)
        plt.axvline(self.__val)
        if title is not None:
            title = title + ": "
        else:
            title = ""
        plt.title("%sPermutation test: P-value=%.4f" % (title, self.__p))
        plt.show()

class Partition:
    def __init__(self, group_A, group_B):
        self.group_A = group_A
        self.group_B = group_B
    @staticmethod
    def partition(population, decision):
        return Partition([x for x in population if decision(x)],
                         [x for x in population if not decision(x)])

def permute(sample_a, sample_b, number):
    combined = list(sample_a) + list(sample_b)
    for _ in range(number):
        print("*", end="")
        shuffle(combined)
        yield combined[:len(sample_a)], combined[len(sample_a):]
