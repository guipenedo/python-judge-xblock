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

        $('.xblock-editor-error-message', element).html();
        $('.xblock-editor-error-message', element).css('display', 'none');
        const handlerUrl = runtime.handlerUrl(element, 'submit_code');
        $.post(handlerUrl, JSON.stringify(data)).done(function(response) {
            if (response.result === 'success') {
                $("#feedback").text(response.message);
            } else {
                runtime.notify('error', {title: gettext("Erro num dos casos de teste"), message: "O teu programa falhou pelo menos um caso de teste. Vê a janela de output para mais informações."});
                $("#feedback").text("Erro no caso de teste " + response.test_case + ":\nInput: " + response.input + "\nOutput esperada: " + response.expected_output + "\n=============\nOutput do teu programa: " + response.student_output)
            }
        });
    });
}