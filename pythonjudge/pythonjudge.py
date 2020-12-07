import pkg_resources
from xblock.scorable import ScorableXBlockMixin, Score
from xblock.core import XBlock
from xblock.fields import Scope, String
from web_fragments.fragment import Fragment
import json
import epicbox

epicbox.configure(
    profiles=[
        epicbox.Profile('python', 'python:3.10.0a2-alpine3.12')
    ]
)
limits = {'cputime': 1, 'memory': 64}


def clean_std(std):
    try:
        std = std.decode('utf-8')
    except (UnicodeDecodeError, AttributeError):
        pass
    return str(std).strip(" \n").replace('\n', '<br/>').replace('\r', '')


class PythonJudgeXBlock(XBlock, ScorableXBlockMixin):
    initial_code = String(display_name="initial_code",
                          default="N = input('Qual é o valor de N?')\nprint(N)",
                          scope=Scope.content,
                          help="O código inicial para este problema")

    student_code = String(display_name="student_code",
                          default="",
                          scope=Scope.user_state,
                          help="A submissão do utilizador para este problema")

    student_score = String(display_name="student_score",
                           default=-1,
                           scope=Scope.user_state)

    display_name = String(display_name="display_name",
                          default="Editor de Python",
                          scope=Scope.settings,
                          help="Nome do componente na plataforma")

    test_cases = String(display_name="test_cases",
                        default='[["Manuel", "Como te chamas?Olá, Manuel"], ["X ae A-Xii", "Como te chamas?Olá, X ae A-Xii"], ["Menino Joãozinho", "Como te chamas?Olá, Menino Joãozinho"]]',
                        scope=Scope.content,
                        help="Uma lista de listas, estando cada uma das sublistas no formato: [input, output]")

    # preferences -> theme and general settings per user

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    def student_view(self, _context):
        """
        The primary view of the PythonJudgeXBlock, shown to students
        when viewing courses.
        """
        if not self.student_code:
            self.student_code = self.initial_code
        html = self.resource_string("static/html/code.html")
        frag = Fragment(html.format(self=self))
        frag.add_css(self.resource_string("static/css/code.css"))
        frag.add_javascript(self.resource_string("static/js/ace/ace.js"))
        frag.add_javascript(self.resource_string("static/js/ace/mode-python.js"))
        frag.add_javascript(self.resource_string("static/js/ace/theme-monokai.js"))
        frag.add_javascript(self.resource_string("static/js/code_student.js"))
        frag.initialize_js('PythonJudgeXBlock')
        return frag

    def studio_view(self, _context):
        """
        The primary view of the paellaXBlock, shown to students
        when viewing courses.
        """
        html = self.resource_string("static/html/code_edit.html")
        frag = Fragment(html.format(self=self))
        frag.add_css(self.resource_string("static/css/code.css"))
        frag.add_javascript(self.resource_string("static/js/ace/ace.js"))
        frag.add_javascript(self.resource_string("static/js/ace/mode-python.js"))
        frag.add_javascript(self.resource_string("static/js/ace/theme-monokai.js"))
        frag.add_javascript(self.resource_string("static/js/code_studio.js"))
        frag.initialize_js('PythonJudgeXBlock')
        return frag

    @XBlock.json_handler
    def save_settings(self, data, _suffix):
        self.display_name = data["display_name"]
        self.initial_code = data["initial_code"]
        try:
            json.loads(data["test_cases"])
        except ValueError:
            return {
                'result': 'error',
                'message': 'test_cases tem que ser uma lista de json válida!'
            }
        self.test_cases = data["test_cases"]
        return {
            'result': 'success',
        }

    @XBlock.json_handler
    def autosave_code(self, data, _suffix):
        if data["student_code"] != self.student_code:
            self.student_code = data["student_code"]
        return {
            'result': 'success'
        }

    @XBlock.json_handler
    def submit_code(self, data, _suffix):
        self.student_code = data["student_code"]
        files = [{'name': 'main.py', 'content': bytes(self.student_code, 'utf-8')}]
        ti = 1
        for i_o in json.loads(self.test_cases):
            expected_output = clean_std(i_o[1])
            result = epicbox.run('python', 'python3 main.py', files=files, limits=limits, stdin=i_o[0])
            stdout = clean_std(result["stdout"])
            stderr = clean_std(result["stderr"])
            response = {
                'result': 'error',
                'exit_code': result["exit_code"],
                'test_case': ti,
                'input': i_o[0],
                'expected_output': expected_output,
                'student_output': stdout,
                'stderr': stderr
            }
            if result["exit_code"] != 0 or stdout != expected_output:
                return response
            ti += 1
        return {
            'result': 'success',
            'message': 'O teu programa passou em todos os ' + str(ti) + ' casos de teste!'
        }

    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("PythonJudgeXBlock",
             """<vertical_demo>
                <pdf/>
                </vertical_demo>
             """),
        ]

    def has_submitted_answer(self):
        return self.student_score != -1

    def get_score(self):
        return Score(raw_earned=max(self.student_score, 0), raw_possible=1)

    def set_score(self, score):
        self.student_score = score.raw_earned / score.raw_possible

    def calculate_score(self):
        return self.get_score()
