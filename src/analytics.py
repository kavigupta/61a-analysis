import numpy as np

def unusualness(grader, question):
    overall_mean = question.mean_rubric
    overall_std = question.std_rubric
    by_grader = question.for_grader(grader)
    return np.mean(np.abs(by_grader.mean_rubric - overall_mean) / overall_std)

def identify_problematic_ranges(evals, z_thresh):
    for _, graded_question in evals:
        for grader in graded_question.graders:
            if unusualness(grader, graded_question) > z_thresh:
                yield from graded_question.for_grader(grader).emails

def compensate_for_grader_means(evals, z_thresh=1):
    problematic = set(identify_problematic_ranges(evals, z_thresh))
    filt = evals.remove(problematic)
    zeroed = filt.zero_meaned()
    return zeroed