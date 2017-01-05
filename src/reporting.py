"""
A module containing a variety of methods for reporting
"""
from math import sqrt

from matplotlib import pyplot as plt
import numpy as np

from evaluations import proc_evaluations

def grader_comparison_report():
    evals = proc_evaluations('/home/kavi/data/real-data/Midterm_1_evaluations.zip')
    create_grader_report(evals, q_filter=lambda x: x == 1.3, path="report/grader-comparison.png")

def create_grader_report(evals, q_filter=lambda _: True, path=None):
    """
    Creates a report on grader anomalies for a given set of evaluations
    """
    for question_name, ques in evals:
        if not q_filter(question_name):
            continue
        plt.figure(figsize=(15, 3))
        plt.subplot(121)
        maximum = max([ques.score_for(x).complete_score.score for x in ques.emails])
        def _all_graders():
            # pylint: disable=W0640
            for grader in sorted(ques.graders, key=hash):
                question = ques.for_grader(grader)
                count = len(list(question.emails))
                if count < 20:
                    continue
                yield question.mean_score, question.std_score * 1.96 / sqrt(count)
        means_stds = list(_all_graders())
        for index, mean_std in enumerate(means_stds):
            mean, std = mean_std
            plt.scatter([index], [mean.score], color="black", label="Mean")
            plt.errorbar([index], [mean.score], yerr=[std.score], color="black", label="95% CI")
        plt.title("Average score by grader for Midterm 1, Problem %s" % question_name)
        plt.ylabel("Points")
        plt.xlabel("Grader #")
        plt.ylim(0, maximum)
        plt.subplot(122)
        xvals = list(range(len(means_stds[0][0].rubric_items)))
        for index, mean_std in enumerate(means_stds):
            mean, std = mean_std
            plt.errorbar(np.array(xvals) + 1,
                         100 * np.array(mean.rubric_items),
                         yerr=100 * np.array(std.rubric_items),
                         fmt='-', label="Grader #%s" % index)
        plt.xlim(xvals[0] + 0.5, xvals[-1] + 1.5)
        lgd = plt.legend(bbox_to_anchor=(1.4, 1))
        plt.gca().set_xticks(np.array(xvals) + 1)
        plt.title("Per Rubric Item for Midterm 1, Problem %s" % question_name)
        plt.ylabel("Percentage Selected")
        plt.xlabel("Rubric Item Number")
        if path is None:
            plt.show()
        else:
            plt.savefig(path, bbox_extra_artists=(lgd,), bbox_inches='tight')

if __name__ == '__main__':
    grader_comparison_report()
