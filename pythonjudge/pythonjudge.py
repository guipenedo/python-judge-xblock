import pkg_resources
import six
from xblock.completable import CompletableXBlockMixin
from xblock.scorable import ScorableXBlockMixin, Score
from xblock.core import XBlock
from xblock.fields import Scope, String, Float, Boolean, Integer
from xblock.validation import ValidationMessage
from xblockutils.studio_editable import StudioEditableXBlockMixin
from web_fragments.fragment import Fragment
import json
import epicbox
from xblockutils.resources import ResourceLoader
from submissions import api as submissions_api
from webob import Response
from common.djangoapps.student.models import user_by_anonymous_id
from openedx.core.djangoapps.course_groups.cohorts import get_cohort, is_course_cohorted, get_course_cohorts

loader = ResourceLoader(__name__)

ITEM_TYPE = "pyjudge"

epicbox.configure(
    profiles=[
        epicbox.Profile('python', 'python:3.10.0a2-alpine3.12')
    ]
)
limits = {'cputime': 1, 'memory': 64}


# Utils
def clean_stdout(std):
    try:
        std = std.decode('utf-8')
    except (UnicodeDecodeError, AttributeError):
        pass
    return str(std).strip(" \n").replace('\r', '\n')


def resource_string(path):
    """Handy helper for getting resources from our kit."""
    data = pkg_resources.resource_string(__name__, path)
    return data.decode("utf8")


def add_styling_and_editor(frag):
    """
        Add necessary css and js imports. Initialize last student output
    :param frag:
    :return:
    """
    frag.add_css(resource_string("static/css/pyjudge.css"))
    frag.add_javascript(resource_string("static/js/ace/ace.js"))
    frag.add_javascript(resource_string("static/js/ace/mode-python.js"))
    frag.add_javascript(resource_string("static/js/ace/theme-monokai.js"))
    frag.add_javascript(resource_string("static/js/ace/ext-language_tools.js"))
    frag.add_javascript(resource_string("static/js/ace/snippets/python.js"))
    frag.add_javascript(resource_string("static/js/pyjudge_editor_handler.js"))


grader_utils = b"""
import os
import sys


class NoStd(object):
    def __enter__(self):
        self.stdout = sys.stdout
        self.stdin = sys.stdin
        sys.stdout = open(os.devnull, 'w')
        sys.stdin = open(os.devnull, 'r')
        return self

    def __exit__(self, type, value, traceback):
        sys.stdout = self.stdout
        sys.stdin = self.stdin

"""

grader_code_def = str(b"""import main
from gutils import NoStd

lista = [int(x) for x in input().split()]
# todo o codigo que esteja dentro do NoStd nao tem acesso a stdout nem a stdin (nao meter o print aqui)
with NoStd():
    # exemplo: uma funcao que conta o numero de inteiros pares numa lista
    result = main.conta_pares(lista)
# fazemos print do resultado para ser comparado automaticamente com o resultado esperado deste caso de teste (pode ser dinamico)
print(result)
""", 'utf-8')


class PythonJudgeXBlock(XBlock, ScorableXBlockMixin, CompletableXBlockMixin, StudioEditableXBlockMixin):
    initial_code = String(display_name="initial_code",
                          default="N = input('Qual é o valor de N?')\nprint(N)",
                          scope=Scope.settings,
                          help="O código inicial para este problema")

    grader_code = String(display_name="grader_code",
                         default=grader_code_def,
                         scope=Scope.settings,
                         help="O código do grader")

    model_answer = String(display_name="model_answer",
                          default="",
                          scope=Scope.settings,
                          help="Resposta modelo para este problema")

    student_code = String(display_name="student_code",
                          default="",
                          scope=Scope.user_state,
                          help="A submissão do utilizador para este problema")

    student_score = Float(display_name="student_score",
                          default=-1,
                          scope=Scope.user_state)

    display_name = String(display_name="display_name",
                          default="Editor de Python",
                          scope=Scope.settings,
                          help="Nome do componente na plataforma")

    cohort = String(display_name="cohort",
                    default="",
                    scope=Scope.preferences,
                    help="Turma selecionada para todos os editores")

    no_submission = Boolean(display_name="no_submission",
                            default=False,
                            scope=Scope.content,
                            help="Se True, então este bloco não terá submissão (serve apenas para correr \"ludicamente\" código.")

    grade_mode = String(display_name="grade_mode",
                        default='input/output',
                        scope=Scope.content,
                        help="Modo de avaliação. Input/output é o caso simples de correr o programa para input e verificar se a output obtida é a indicada. Grader implica implementar código de python que execute o código dos alunos e imprima o seu resultado para ser comparado com a output do caso de teste.",
                        values=('input/output', 'python grader'))

    partial_grading = Boolean(display_name="partial_grading",
                              default=False,
                              scope=Scope.content,
                              help="Se devemos correr todos os casos de teste e atribuir uma pontuação igual à percentagem de casos de teste que o programa passou.")

    test_cases = String(display_name="test_cases",
                        default='[["Manuel", "Como te chamas?\\nOlá, Manuel"], ["X ae A-Xii", "Como te chamas?\\nOlá, X ae A-Xii"], ["Menino Joãozinho", "Como te chamas?\\nOlá, Menino Joãozinho"]]',
                        scope=Scope.content,
                        multiline_editor=True,
                        help="Uma lista de listas, estando cada uma das sublistas no formato: [input, output]. Para avaliação com grader, se a input não for lida daqui, então ter apenas um caso de teste vazio [\"\", \"\"].")

    last_output = String(display_name="last_output",
                         default="",
                         scope=Scope.user_state)

    nrsubmissions = Integer(display_name="nrsubmissions",
                            default=0,
                            scope=Scope.user_state)

    editable_fields = ('display_name', 'no_submission', 'grade_mode', 'partial_grading', 'test_cases')
    icon_class = 'problem'
    block_type = 'problem'
    has_author_view = True
    has_score = True

    # ----------- Views -----------
    def student_view(self, _context):
        """
            The view students see
        :param _context:
        :return:
        """
        if not self.student_code:
            self.student_code = self.initial_code
        data = {
            'student_code': self.student_code,
            'xblock_id': self._get_xblock_loc(),
            'no_submission': self.no_submission
        }
        if self.last_output:
            try:
                data["last_output"] = json.loads(self.last_output)
            except ValueError:
                pass
        if self.show_staff_grading_interface():
            data['is_course_staff'] = True
            data['is_course_cohorted'] = is_course_cohorted(self.course_id)
            data['cohorts'] = [group.name for group in get_course_cohorts(course_id=self.course_id)]
            data['cohort'] = self.cohort
            data['submissions'] = self.get_sorted_submissions()

        html = loader.render_django_template('templates/pyjudge_student.html', data)
        frag = Fragment(html)

        if self.show_staff_grading_interface():
            frag.add_css(resource_string("static/css/theme.blue.min.css"))
            frag.add_javascript(resource_string("static/js/jquery.tablesorter.combined.min.js"))

        frag.add_javascript(resource_string("static/js/pyjudge_student.js"))
        frag.initialize_js('PythonJudgeXBlock', data)

        add_styling_and_editor(frag)
        return frag

    def author_view(self, _context):
        html = loader.render_django_template('templates/pyjudge_author.html', {
            'initial_code': self.initial_code,
            'model_answer': self.model_answer,
            'grader_code': self.grader_code,
            'uses_grader': self.grade_mode != 'input/output',
            'xblock_id': self._get_xblock_loc(),
            'no_submission': self.no_submission
        })
        frag = Fragment(html)
        add_styling_and_editor(frag)
        frag.add_javascript(resource_string("static/js/pyjudge_author.js"))
        frag.initialize_js('PythonJudgeXBlock', {'xblock_id': self._get_xblock_loc(),
                                                 'uses_grader': self.grade_mode != 'input/output',
                                                 'no_submission': self.no_submission})
        return frag

    def validate_field_data(self, validation, data):
        try:
            json.loads(data.test_cases)
        except ValueError:
            validation.add(
                ValidationMessage(ValidationMessage.ERROR, u"test_cases tem que ser uma lista de json válida!"))

    # ----------- Handlers -----------
    @XBlock.json_handler
    def save_settings(self, data, _suffix):
        """
            Json handler for ajax post requests modifying the xblock's settings
        :param data:
        :param _suffix:
        :return:
        """
        self.initial_code = data["initial_code"]
        if "model_answer" in data and data["model_answer"]:
            self.model_answer = data["model_answer"]
        if "grader_code" in data:
            self.grader_code = data["grader_code"]
        return {
            'result': 'success'
        }

    @XBlock.json_handler
    def change_cohort(self, data, _suffix):
        self.cohort = data["cohort"]
        return {
            'result': 'success'
        }

    @XBlock.json_handler
    def autosave_code(self, data, _suffix):
        """
            Json Handler for automated periodic ajax requests to save the student's code
        :param data:
        :param _suffix:
        :return:
        """
        if data["student_code"] != self.student_code:
            self.student_code = data["student_code"]
        return {
            'result': 'success'
        }

    @XBlock.json_handler
    def submit_code(self, data, _suffix):
        """
            Triggered when the user presses the submit button.
            We set student_score=0 to count as "has_submitted" and then call rescore
            which then calls our calculate_score method
        :param data:
        :param _suffix:
        :return:
        """
        self.student_code = data["student_code"]

        self.evaluate_submission()
        self.nrsubmissions += 1
        self._publish_grade(self.get_score(), False)

        # store using submissions_api
        submissions_api.create_submission(self.get_student_item_dict(), {
            'code': self.student_code,
            'evaluation': self.last_output,
            'score': int(self.student_score * 100)
        }, attempt_number=1)
        # send back the evaluation as json object
        return json.loads(self.last_output)

    @XBlock.json_handler
    def test_model_solution(self, data, _suffix):
        # cache current values
        student_code = self.student_code
        student_score = self.student_score
        last_output = self.last_output

        if "model_answer" not in data or not data["model_answer"]:
            return {
                'result': 'error',
                'message': 'Empty model_answer.'
            }

        self.student_code = data["model_answer"]
        self.evaluate_submission(True)
        response = self.last_output

        # revert
        self.last_output = last_output
        self.student_code = student_code
        self.student_score = student_score

        return json.loads(response)

    @XBlock.json_handler
    def get_model_answer(self, _data, _suffix):
        """
            Triggered when the user presses the view answer button.
            We check if they have completed the problem and if so send the model answer
        :param data:
        :param _suffix:
        :return:
        """

        if self.student_score < 1.0 and not self.show_staff_grading_interface():
            return {
                'result': 'error',
                'message': 'Ainda não completaste este problema!'
            }
        return {
            'result': 'success',
            'model_answer': self.model_answer
        }

    @XBlock.json_handler
    def run_code(self, data, _suffix):
        """
            Triggered when the "run code" button is pressed. Tests the program against user defined input
        :param data:
        :param _suffix:
        :return:
        """
        self.student_code = data["student_code"]
        input = data["input"]
        files = [{'name': 'main.py', 'content': bytes(self.student_code, 'utf-8')}]

        if self.grade_mode == 'input/output':
            result = epicbox.run('python', 'python3 main.py', files=files, limits=limits, stdin=input)
        else:
            files.append({'name': 'grader.py', 'content': bytes(self.grader_code, 'utf-8')})
            files.append({'name': 'gutils.py', 'content': grader_utils})
            result = epicbox.run('python', 'python3 grader.py', files=files, limits=limits, stdin=input)

        stdout = clean_stdout(result["stdout"])
        stderr = clean_stdout(result["stderr"])
        return {
            'result': 'success',
            'exit_code': result["exit_code"],
            'stdout': stdout,
            'stderr': stderr
        }

    #  ----------- Evaluation -----------
    def evaluate_submission(self, test=False):
        """
            Evaluate this student's latest submission with our test cases
        :return:
        """
        if self.no_submission:
            return {
                'result': 'error',
                'message': 'Este problema não tem avaliação!'
            }
        self.student_score = 0
        simple_grading = self.grade_mode == 'input/output'
        files = [{'name': 'main.py', 'content': bytes(self.student_code, 'utf-8')}]

        ti = 1
        tests_passed = 0

        for i_o in json.loads(self.test_cases):
            expected_output = clean_stdout(i_o[1])
            if simple_grading:
                result = epicbox.run('python', 'python3 main.py', files=files, limits=limits, stdin=i_o[0])
            else:
                files.append({'name': 'grader.py', 'content': bytes(self.grader_code, 'utf-8')})
                files.append({'name': 'gutils.py', 'content': grader_utils})
                result = epicbox.run('python', 'python3 grader.py', files=files, limits=limits, stdin=i_o[0])
            stdout = clean_stdout(result["stdout"])
            stderr = clean_stdout(result["stderr"])
            response = {
                'result': 'error',
                'exit_code': result["exit_code"],
                'test_case': ti,
                'input': i_o[0],
                'expected_output': expected_output,
                'student_output': stdout,
                'stderr': stderr
            }
            if result["exit_code"] != 0 \
                or (not self.partial_grading and stdout.replace("\n", "") != expected_output.replace("\n", "")):
                self.save_output(response)
                # completion interface
                if not test:
                    self.emit_completion(0.0)
                return
            if self.partial_grading and stdout.replace("\n", "") == expected_output.replace("\n", ""):
                tests_passed += 1
            ti += 1
        if not self.partial_grading:
            self.student_score = 1.0
        else:
            self.student_score = tests_passed / (ti - 1)
        # completion interface
        if not test:
            self.emit_completion(self.student_score)
        if not self.partial_grading:
            self.save_output({
                'result': 'success',
                'message': 'O teu programa passou em todos os ' + str(ti - 1) + ' casos de teste!'
            })
        else:
            self.save_output({
                'result': 'success',
                'message': 'O teu programa passou em ' + str(int(self.student_score * 100)) + "% dos testes."
            })

    def save_output(self, output):
        """
            Cache user's last submission's output
        :param output:
        :return:
        """
        self.last_output = json.dumps(output)

    # ----------- Submissions -----------
    def get_sorted_submissions(self):
        """returns student recent assignments sorted on date"""
        assignments = []
        submissions = submissions_api.get_all_submissions(
            self.block_course_id(),
            self.block_id(),
            ITEM_TYPE
        )

        for submission in submissions:
            student = user_by_anonymous_id(submission['student_id'])
            sub = {
                'submission_id': submission['uuid'],
                'username': student.username,
                'fullname': student.profile.name,
                'timestamp': submission['submitted_at'] or submission['created_at'],
                'code': submission['answer']['code'],
                'evaluation': submission['answer']['evaluation'],
                'score': submission['answer']['score'] if 'score' in submission['answer'] else 0
            }
            if is_course_cohorted(self.course_id):
                group = get_cohort(student, self.course_id, assign=False, use_cached=True)
                sub['cohort'] = group.name if group else '(não atribuído)'
            assignments.append(sub)

        assignments.sort(
            key=lambda assignment: assignment['timestamp'], reverse=True
        )
        return assignments

    def get_student_item_dict(self, student_id=None):
        # pylint: disable=no-member
        """
        Returns dict required by the submissions app for creating and
        retrieving submissions for a particular student.
        """
        if student_id is None:
            student_id = self.xmodule_runtime.anonymous_student_id
        return {
            "student_id": student_id,
            "course_id": self.block_course_id(),
            "item_id": self.block_id(),
            "item_type": ITEM_TYPE,
        }

    def block_id(self):
        """
        Return the usage_id of the block.
        """
        return six.text_type(self.scope_ids.usage_id)

    def block_course_id(self):
        """
        Return the course_id of the block.
        """
        return six.text_type(self.course_id)

    def _get_xblock_loc(self):
        """Returns trailing number portion of self.location"""
        return str(self.location).split('@')[-1]

    def show_staff_grading_interface(self):
        """
        Return if current user is staff and not in studio.
        """
        in_studio_preview = self.scope_ids.user_id is None
        return getattr(self.xmodule_runtime, 'user_is_staff', False) and not in_studio_preview and not self.no_submission

    #  ----------- ScorableXBlockMixin -----------
    def has_submitted_answer(self):
        return self.student_score != -1

    def max_score(self):
        if self.no_submission:
            return None
        return 1

    def get_score(self):
        if self.no_submission:
            return None
        return Score(raw_earned=max(self.student_score, 0.0), raw_possible=1.0)

    def set_score(self, score):
        if self.no_submission:
            return
        self.student_score = score.raw_earned / score.raw_possible

    def calculate_score(self):
        if self.no_submission:
            return None
        # we get the previous submission
        subs = submissions_api.get_submissions(self.get_student_item_dict(), 1)
        if len(subs) == 0:
            return self.get_score()
        submission = subs[0]
        # evaluate with the previous code, and store the current one
        current_code = self.student_code
        self.student_code = submission['answer']['code']
        self.evaluate_submission()
        # update the submission (recreate with the same date and code)
        submissions_api.create_submission(self.get_student_item_dict(), {
            'code': self.student_code,
            'evaluation': self.last_output,
            'score': int(self.student_score * 100)
        }, attempt_number=1, submitted_at=submission['submitted_at'])
        # restore the current code
        self.student_code = current_code
        return self.get_score()
