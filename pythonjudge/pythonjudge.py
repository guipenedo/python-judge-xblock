import pkg_resources
from xblock.completable import CompletableXBlockMixin
from xblock.scorable import ScorableXBlockMixin, Score
from xblock.core import XBlock
from xblock.fields import Scope, String, Float, Boolean
from xblock.validation import ValidationMessage
from xblockutils.studio_editable import StudioEditableXBlockMixin
from web_fragments.fragment import Fragment
import json
import epicbox

epicbox.configure(
    profiles=[
        epicbox.Profile('python', 'python:3.10.0a2-alpine3.12')
    ]
)
limits = {'cputime': 1, 'memory': 64}


def clean_stdout(std):
    try:
        std = std.decode('utf-8')
    except (UnicodeDecodeError, AttributeError):
        pass
    return str(std).strip(" \n").replace('\n', '<br/>').replace('\r', '<br/>')


def resource_string(path):
    """Handy helper for getting resources from our kit."""
    data = pkg_resources.resource_string(__name__, path)
    return data.decode("utf8")


class PythonJudgeXBlock(XBlock, ScorableXBlockMixin, CompletableXBlockMixin, StudioEditableXBlockMixin):
    initial_code = String(display_name="initial_code",
                          default="N = input('Qual é o valor de N?')\nprint(N)",
                          scope=Scope.content,
                          help="O código inicial para este problema")

    grader_code = String(display_name="initial_code",
                          default="import main\n\nlista = [int(x) for x in input().split()]\n# os graders recebem a output esperada (se esta existir) a seguir à input\nresult = int(input())\n\n# exemplo: uma função que conta o número de inteiros pares numa lista\nif result == main.conta_pares(lista):\n    print(1.0)\nelse:\n    print(0.0)",
                          scope=Scope.content,
                          help="O código do grader")

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

    grade_mode = String(display_name="grade_mode",
                        default='input/output',
                        scope=Scope.content,
                        help="Modo de avaliação. Input/output é o caso simples de correr o programa para input e verificar se a output obtida é a indicada. Grader implica implementar código de python que execute o código dos alunos e imprima a nota [0, 1].",
                        values=('input/output', 'python grader'))

    partial_grading = Boolean(display_name="partial_grading",
                        default=False,
                        scope=Scope.content,
                        help="(Sem efeito para grading input/output). Se verdadeiro, usa como score a média dos scores para cada caso de teste. Se Falso, usa 0 se um caso for != 1 e 1 caso contrário.",)

    test_cases = String(display_name="test_cases",
                        default='[["Manuel", "Como te chamas?\nOlá, Manuel"], ["X ae A-Xii", "Como te chamas?\nOlá, X ae A-Xii"], ["Menino Joãozinho", "Como te chamas?\nOlá, Menino Joãozinho"]]',
                        scope=Scope.content,
                        multiline_editor=True,
                        help="Uma lista de listas, estando cada uma das sublistas no formato: [input, output]. Para avaliação com grader, se a input não for lida daqui, então ter apenas um caso de teste vazio [\"\", \"\"].")

    last_output = String(display_name="last_output",
                         default="",
                         scope=Scope.user_state)

    editable_fields = ('display_name', 'grade_mode', 'partial_grading', 'test_cases')
    icon_class = 'problem'
    block_type = 'problem'

    def add_fragments(self, frag):
        """
            Add necessary css and js imports. Initialize last student output
        :param frag:
        :return:
        """
        frag.add_css(resource_string("static/css/pyjudge.css"))
        frag.add_javascript(resource_string("static/js/ace/ace.js"))
        frag.add_javascript(resource_string("static/js/ace/mode-python.js"))
        frag.add_javascript(resource_string("static/js/ace/theme-monokai.js"))
        data = {}
        if self.last_output:
            try:
                data = {"last_output": json.loads(self.last_output)}
            except ValueError:
                pass
        frag.initialize_js('PythonJudgeXBlock', data)

    def student_view(self, _context):
        """
            The view students see
        :param _context:
        :return:
        """
        if not self.student_code:
            self.student_code = self.initial_code
        html = resource_string("static/html/pyjudge_student.html")
        frag = Fragment(html.format(self=self))
        frag.add_javascript(resource_string("static/js/pyjudge_student.js"))
        self.add_fragments(frag)
        return frag

    def author_view(self, _context):
        html = resource_string("static/html/pyjudge_author.html")
        frag = Fragment(html.format(self=self))
        frag.add_javascript(resource_string("static/js/pyjudge_author.js"))
        self.add_fragments(frag)
        return frag

    def validate_field_data(self, validation, data):
        try:
            json.loads(data["test_cases"])
        except ValueError:
            validation.add(ValidationMessage(ValidationMessage.ERROR, u"test_cases tem que ser uma lista de json válida!"))

    @XBlock.json_handler
    def save_settings(self, data, _suffix):
        """
            Json handler for ajax post requests modifying the xblock's settings
        :param data:
        :param _suffix:
        :return:
        """
        self.initial_code = data["initial_code"]
        self.grader_code = data["grader_code"]
        return {
            'result': 'success',
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

    def save_output(self, output):
        """
            Cache user's last submission's output
        :param output:
        :return:
        """
        self.last_output = json.dumps(output)

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
        self.student_score = 0
        # rescore even if the score lowers
        self.rescore(False)
        return json.loads(self.last_output)

    def evaluate_submission(self):
        """
            Evaluate this student's latest submission with our test cases
        :return:
        """
        self.student_score = 0
        simple_grading = self.grade_mode == 'input/output'
        files = [{'name': 'main.py', 'content': bytes(self.student_code, 'utf-8')}]
        if simple_grading:
            files.append({'name': 'grader.py', 'content': bytes(self.grader_code, 'utf-8')})
        ti = 1
        grade_sum = 0
        for i_o in json.loads(self.test_cases):
            expected_output = clean_stdout(i_o[1])
            if simple_grading:
                result = epicbox.run('python', 'python3 main.py', files=files, limits=limits, stdin=i_o[0])
            else:
                result = epicbox.run('python', 'python3 grader.py', files=files, limits=limits,
                                     stdin=i_o[0]+"\n"+i_o[1])
            stdout = clean_stdout(result["stdout"])
            stderr = clean_stdout(result["stderr"])
            response = {
                'result': 'error',
                'exit_code': result["exit_code"],
                'test_case': ti,
                'input': i_o[0],
                'expected_output': expected_output,
                'student_output': stdout if simple_grading else None,
                'stderr': stderr
            }
            partial_grade = 0.0
            if not simple_grading:
                try:
                    partial_grade = float(stdout.replace("<br/>", ""))
                except ValueError:
                    pass
            grade_sum += partial_grade
            if result["exit_code"] != 0 \
                    or (simple_grading and stdout.replace("<br/>", "") != expected_output.replace("<br/>", "")) \
                    or (not simple_grading and not self.partial_grading and partial_grade != 1.0):
                self.save_output(response)
                # completion interface
                self.emit_completion(0.0)
                return
            ti += 1
        if simple_grading:
            self.student_score = 1.0
        else:
            self.student_score = grade_sum / (ti - 1)
        # completion interface
        self.emit_completion(self.student_score)
        if simple_grading or not self.partial_grading:
            self.save_output({
                'result': 'success',
                'message': 'O teu programa passou em todos os ' + str(ti - 1) + ' casos de teste!'
            })
        else:
            self.save_output({
                'result': 'success',
                'message': 'O teu programa obteve ' + str(int(self.student_score * 100)) + "%."
            })

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

        result = epicbox.run('python', 'python3 main.py', files=files, limits=limits, stdin=input)
        stdout = clean_stdout(result["stdout"])
        stderr = clean_stdout(result["stderr"])
        return {
            'result': 'success',
            'exit_code': result["exit_code"],
            'stdout': stdout,
            'stderr': stderr
        }

    def has_submitted_answer(self):
        return self.student_score != -1

    def get_score(self):
        return Score(raw_earned=max(self.student_score, 0.0), raw_possible=1.0)

    def set_score(self, score):
        self.student_score = score.raw_earned / score.raw_possible

    def calculate_score(self):
        self.evaluate_submission()
        return self.get_score()
