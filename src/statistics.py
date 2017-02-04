"""
A module containing a variety of methods for statistical analyses.
"""

from random import shuffle
from enum import Enum

from matplotlib import pyplot as plt
import numpy as np
from numpy.random import choice
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

class Bootstrap:
    """
    Represents a bootstrap, a way to estimate a confidence interval of the mean.

    Inputs:
        data:       the set to get the mean and confidence interval from
        n_trials:   the number of times to repeat the sampling with replacement
        ci_amt:     the size of the confidence interval to calculate.
    """
    def __init__(self, data, n_trials, ci_amt=None, ci_above=None, ci_below=None):
        if ci_amt is not None:
            ci_above = (100 + ci_amt) / 2
            ci_below = (100 - ci_amt) / 2
        if ci_above is None or ci_below is None:
            raise RuntimeError("Invaild arguments")
        self.data = data
        self.distribution = list(Bootstrap._n_means(data, n_trials))
        self.mean = np.mean(self.distribution)
        self.ci_top = np.percentile(self.distribution, ci_above)
        self.ci_bot = np.percentile(self.distribution, ci_below)
    def plot_data(self):
        """
        Plots the data, along with a 95% CI of the mean.
        """
        self._plot_ci(self.data)
    def plot_mean(self):
        """
        Plots the mean, along with a 95% CI.
        """
        self._plot_ci(self.distribution)
    def _plot_ci(self, dataset):
        plt.hist(dataset)
        plt.axvspan(self.ci_bot, self.ci_top, alpha=0.5, color="green")
    @staticmethod
    def _n_means(data, n_trials):
        for _ in range(n_trials):
            yield np.mean(choice(data, len(data), replace=True))
    @staticmethod
    def plot_errorbars(bootstraps, xvals=None, **kwargs):
        """
        Plots the given set of bootstraps as a set of error bars.

        bootstraps: a list of Bootstrap objects
        xvals:      the x values to use, or range(len(bootstraps)) if none is provided
        kwargs:     additional arguments, to pass onto errobar
        """
        if xvals is None:
            xvals = np.arange(len(bootstraps))
        plt.errorbar(xvals, [x.mean for x in bootstraps],
                     yerr=[[x.mean-x.ci_bot for x in bootstraps],
                           [x.ci_top - x.mean for x in bootstraps]],
                     **kwargs)

def matched_differences_bootstrap(exams, seating_charts, adjacency_type,
                                  gambler_limits, similarity_fn, bootstrap_count):
    """
    Generates a list of bootstraps for matched differences.

    exams: a dictionary from exam name -> graded exam
    seating_charts: a dictionary from exam name -> seating chart
    adjacency_type: the type of adjacency to use
    gambler_limits: a list of gambler's fallacy allowable limits to try
    similarity_fn: a function (evaluation, evaluation) -> R representing similarity
    bootstrap_count: the number of bootstrap iterations to perform

    Output: an iterable ((exam name, gambler fallacy limit), bootstrap of matched differences)
    """
    for exam in exams:
        for gfal in gambler_limits:
            matched_diff = []
            chart = seating_charts[exam]
            for email in exams[exam].emails:
                one_apart, two_apart \
                    = chart.similarity_layers(email, 2, adjacency_type,
                                              exams[exam],
                                              similarity_fn,
                                              gambler_fallacy_allowable_limit=gfal)
                diff = one_apart - two_apart
                if np.isnan(diff):
                    continue
                matched_diff.append(diff)
            yield (exam, gfal), Bootstrap(matched_diff, bootstrap_count, ci_above=100, ci_below=5)
