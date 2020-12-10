function PythonJudgeXBlock(runtime, element, data) {
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

    function outputResponse(response) {
        $(element).find('#submit').prop( "disabled", false );
        if (response.result === 'success') {
            runtime.notify('save', {
                state: 'end',
                title: gettext("O teu programa passou todos os casos de teste! Parabéns!")
            });
            $("#feedback").html(response.message);
        } else {
            runtime.notify('error', {
                title: gettext("Erro num dos casos de teste"),
                message: "O teu programa falhou pelo menos um caso de teste. Vê a janela de output para mais informações."
            });
            if (response.exit_code === 0 && !response.stderr)
                $("#feedback").html("<b><u>Output incorreta no caso de teste " + response.test_case + "</u></b><br/><b>Input:</b> " + response.input + "<br/><b>Output esperada:</b> " + response.expected_output + "<br/><b>=============</b><br/><b>Output do teu programa:</b> " + response.student_output)
            else
                $("#feedback").html("<b><u>Erro no caso de teste " + response.test_case + "</u></b><br/><b>Input:</b> " + response.input + "<br/><b>Output esperada:</b> " + response.expected_output + "<br/><b>=============</b><br/><b>Exit code:</b> " + response.exit_code + "<br/><b>Erro do teu programa:</b> " + response.stderr)
        }
    }

    $(element).find('#submit').bind('click', function() {
        const data = {
            'student_code': editor.getValue()
        };
        $(this).prop( "disabled", true );
        const handlerUrl = runtime.handlerUrl(element, 'submit_code');
        runtime.notify('save', {state: 'start'});
        $.post(handlerUrl, JSON.stringify(data)).done(outputResponse);
    });

    //autosave every 10 seconds
    let previous_code = editor.getValue();
    const autosave_handlerurl = runtime.handlerUrl(element, 'autosave_code');
    setInterval(() => {
        if (previous_code !== editor.getValue()){
            previous_code = editor.getValue();
            const data = {
                'student_code': previous_code
            };
            runtime.notify('save', {state: 'start'});
            $.post(autosave_handlerurl, JSON.stringify(data)).done(function() {
                runtime.notify('save', {state: 'end'});
        });
        }
    }, 10*1000);


    if (data.last_output)
        outputResponse(data.last_output)
}