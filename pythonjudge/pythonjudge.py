import os

import pkg_resources
from xblock.core import XBlock
from xblock.fields import Scope, String, List
from web_fragments.fragment import Fragment
import json
import epicbox

epicbox.configure(
    profiles=[
        epicbox.Profile('python', 'python:3.10.0a2-alpine3.12', read_only=True)
    ]
)
limits = {'cputime': 1, 'memory': 64}


class PythonJudgeXBlock(XBlock):
    initial_code = String(display_name="initial_code",
                          default="N = input('Qual é o valor de N?')\nprint(N)",
                          scope=Scope.content,
                          help="O código inicial para este problema")

    student_code = String(display_name="student_code",
                          default="",
                          scope=Scope.user_state,
                          help="A submissão do utilizador para este problema")

    display_name = String(display_name="display_name",
                          default="Editor de Python",
                          scope=Scope.settings,
                          help="Nome do componente na plataforma")

    test_cases = String(display_name="test_cases",
                        default=json.dumps([
                            ["Manuel", "Como te chamas?Olá, Manuel"],
                            ["X ae A-Xii", "Como te chamas?Olá, X ae A-Xii"],
                            ["Menino Joãozinho", "Como te chamas?Olá, Menino Joãozinho"]
                        ]),
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
        self.test_cases = data["test_cases"]
        return {
            'result': 'success',
        }

    @XBlock.json_handler
    def submit_code(self, data, _suffix):
        self.student_code = data["student_code"]
        files = [{'name': 'main.py', 'content': self.student_code}]
        ti = 1
        """for i_o in json.loads(self.test_cases):
            expected_output = i_o[1].replace('\n', ' ').replace('\r', '')
            stdout = epicbox.run('python', 'python3 main.py', files=files, limits=limits, stdin=i_o[0])\
                .replace('\n', ' ').replace('\r', '')
            if stdout != expected_output:
                return {
                    'result': 'error',
                    'test_case': ti,
                    'input': i_o[0],
                    'expected_output': i_o[1],
                    'student_output': expected_output
                }
            ti += 1"""
        return {
            'result': 'success',
            'message': os.getlogin()
            #'message': 'Parabéns! O teu programa passou em todos os ' + ti + ' casos de teste!'
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
