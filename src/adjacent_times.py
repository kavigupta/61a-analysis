"""
Find adjacently graded exams in a graded exam dictionary.
"""
from evaluations import GradedMidterm

def find_adjacent_times(graded_exams):
    """
    Inputs
        graded_exams: a dictionary: Run_Count -> Graded_Exam
    Output
        a list from question number -> [(Evaluation A , Evaluation B)] where A and B are adjacent
    """
    exam_list = [graded_exams[x] for x in range(len(graded_exams))]
    for question in range(len(exam_list[0].evals)):
        adjacents = []
        for prev, curr in zip(exam_list, exam_list[1:]):
            prev_q, curr_q = prev.evals[question], curr.evals[question]
            if prev_q.grader == curr_q.grader:
                prev_grade = GradedMidterm(prev.name, prev.email, prev_q)
                curr_grade = GradedMidterm(curr.name, curr.email, curr_q)
                adjacents.append((prev_grade, curr_grade))
        yield adjacents
