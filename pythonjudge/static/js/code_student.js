function PythonJudgeXBlock(runtime, element) {
    let editor = ace.edit("student_code");
    editor.setOptions({
        maxLines: 70,
        minLines: 10,
        autoScrollEditorIntoView: true,
        theme: "ace/theme/monokai",
        showPrintMargin: false,
        mode: "ace/mode/python",
        fontSize: "14pt"
    });

    $(element).find('#submit').bind('click', function() {
        const data = {
            'student_code': editor.getValue()
        };

        const handlerUrl = runtime.handlerUrl(element, 'submit_code');
        runtime.notify('save', {state: 'start'});
        $.post(handlerUrl, JSON.stringify(data)).done(function(response) {
            if (response.result === 'success') {
                runtime.notify('save', {state: 'end', title: gettext("O teu programa passou todos os casos de teste! Parabéns!")});
                $("#feedback").html(response.message);
            } else {
                runtime.notify('error', {title: gettext("Erro num dos casos de teste"), message: "O teu programa falhou pelo menos um caso de teste. Vê a janela de output para mais informações."});
                if (response.exit_code === 0 && !response.stderr)
                    $("#feedback").html("Output incorreta no caso de teste " + response.test_case + ":<br/>Input: " + response.input + "<br/>Output esperada: " + response.expected_output + "<br/>=============<br/>Output do teu programa: " + response.student_output)
                else
                    $("#feedback").html("Erro no caso de teste " + response.test_case + ":<br/>Input: " + response.input + "<br/>Output esperada: " + response.expected_output + "<br/>=============<br/>Exit code: " + response.exit_code + "<br/>Erro do teu programa: " + response.stderr)
            }
        });
    });
}