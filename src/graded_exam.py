
import numpy as np

class ExamQuestion:
    def __init__(self, exam_grades, problem, pred=lambda x: True):
        self.__exam_grades = exam_grades
        self.__problem = problem
        self.__pred = pred
    def __filter(self, new_pred):
        return ExamQuestion(self.__exam_grades, self.__problem,
                            lambda x: self.__pred(x) and new_pred(x))
    def for_grader(self, grader):
        return self.__filter(lambda x: x.grader == grader)
    @property
    def evaluations(self):
        return (x for x in self.__exam_grades.question_scores_for(self.__problem) if self.__pred(x))
    @property
    def graders(self):
        return set(x.grader for x in self.evaluations)
    @property
    def mean_score(self):
        return np.mean([x.score for x in self.evaluations])
    @property
    def __rubrics(self):
        return [x.rubric_items for x in self.evaluations]
    @property
    def std_rubric(self):
        return np.std(self.__rubrics, axis=0)
    @property
    def mean_rubric(self):
        return np.mean(self.__rubrics, axis=0)
    @property
    def mean_adjustment(self):
        return np.mean([x.adjustment for x in self.evaluations])
    @property
    def emails(self):
        return (x.email for x in self.evaluations)

class ExamGrades:
    def __init__(self, problem_names, location_per_email, evaluation_per_email):
        self.__problem_names = problem_names
        self.__location_per_email = location_per_email
        self.__evaluation_per_email = evaluation_per_email
    @staticmethod
    def create(problem_names, grades_per_index):
        location_per_email = {e.email : i for i, e in grades_per_index.items()}
        evaluation_per_email = {e.email : e for i, e in grades_per_index.items()}
        return ExamGrades(problem_names, location_per_email, evaluation_per_email)
    def __iter__(self):
        return iter((name, ExamQuestion(self, name)) for name in self.__problem_names)
    def question_scores_for(self, problem):
        p_index = self.__problem_names.index(problem)
        for full_grade in self.__evaluation_per_email.values():
            yield full_grade.evals[p_index]
    @property
    def emails(self):
        return self.__location_per_email.keys()
    def evaluation_for(self, email):
        return self.__evaluation_per_email[email]
    def remove(self, emails):
        return ExamGrades(
            self.__problem_names,
            {x : y for x, y in self.__location_per_email.items() if x not in emails},
            {x : y for x, y in self.__evaluation_per_email.items() if x not in emails})
    def __replace(self, updater):
        return ExamGrades(
            self.__problem_names,
            self.__location_per_email,
            {x : updater(y) for x, y in self.__evaluation_per_email.items()})
    def zero_meaned(self):
        def mean_per_question_and_grader():
            for quest, grades in self:
                for grader in grades.graders:
                    by_grader = grades.for_grader(grader)
                    yield ((quest, grader), (by_grader.mean_score, by_grader.mean_rubric, by_grader.mean_adjustment))
        mpqag = dict(mean_per_question_and_grader())
        def updater(elem):
            def means():
                for que, eva in zip(self.__problem_names, elem.evals):
                    yield mpqag[(que, eva.grader)]
            return elem.zero_mean(means())
        return self.__replace(updater)
