import pkg_resources
from xblock.core import XBlock
from xblock.fields import Scope, String, List
from web_fragments.fragment import Fragment


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

    test_cases = List(display_name="test_cases",
                      default=[
                          ["Manuel", "Como te chamas?Olá, Manuel"],
                          ["X ae A-Xii", "Como te chamas?Olá, X ae A-Xii"],
                          ["Menino Joãozinho", "Como te chamas?Olá, Menino Joãozinho"]
                      ],
                      scope=Scope.settings,
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
        frag.add_javascript(self.resource_string("static/js/ace/theme-monokai.js.js"))
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
        frag.add_javascript(self.resource_string("static/js/ace/theme-monokai.js.js"))
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
