function PythonJudgeXBlock(runtime, element, data) {
    let editor = ace.edit("student_code");
    editor.setOptions({
        maxLines: 50,
        minLines: 10,
        autoScrollEditorIntoView: true,
        theme: "ace/theme/monokai",
        showPrintMargin: false,
        mode: "ace/mode/python",
        fontSize: "14pt"
    });

    function outputResponse(response) {
        switchButtons(false);
        if (response.result === 'success') {
            $("#feedback").html(response.message);
        } else {
            if (response.exit_code === 0 && !response.stderr)
                $("#feedback").html("<b><u>Output incorreta no caso de teste " + response.test_case + "</u></b><br/><b>Input:</b> " + response.input + "<br/><b>Output esperada:</b> " + response.expected_output + "<br/><b>=============</b><br/><b>Output do teu programa:</b> " + response.student_output)
            else
                $("#feedback").html("<b><u>Erro no caso de teste " + response.test_case + "</u></b><br/><b>Input:</b> " + response.input + "<br/><b>Output esperada:</b> " + response.expected_output + "<br/><b>=============</b><br/><b>Exit code:</b> " + response.exit_code + "<br/><b>Erro do teu programa:</b> " + response.stderr)
        }
    }

    function switchButtons(disabled){
        $(element).find('#submit').prop("disabled", disabled);
        $(element).find('#run').prop("disabled", disabled);
        $(element).find('#code-runner-button').prop("disabled", disabled);
    }

    $(element).find('#submit').bind('click', function() {
        $(element).find('#code-runner').hide();
        $(element).find('#run').show();
        const data = {
            'input': editor.getValue()
        };
        switchButtons(true);
        const handlerUrl = runtime.handlerUrl(element, 'submit_code');
        $.post(handlerUrl, JSON.stringify(data)).done(outputResponse);
    });


    $(element).find('#run').bind('click', function () {
        $(this).hide();
        $(element).find('#code-runner').show();
    });

    $(element).find('#code-runner-button').bind('click', function () {
        const data = {
            'student_code': editor.getValue()
        };
        switchButtons(true);
        const handlerUrl = runtime.handlerUrl(element, 'run_code');
        $.post(handlerUrl, JSON.stringify(data)).done(function (response) {
            switchButtons(false);
            if (response.result === 'success') {
                if (response.exit_code === 0 && !response.stderr)
                    $("#code-runner-output").html("<u>Erro de execução.</u> Exit code: <b>" + response.exit_code + "</b><br /><b>Output:</b> " + response.stdout +"<br /><b>Stderr:</b> " + response.stderr);
                else
                    $("#code-runner-output").html(response.stdout);
            } else {
                $("#code-runner-output").text("Erro desconhecido. Por favor tenta novamente mais tarde.");
            }
        });
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
            $.post(autosave_handlerurl, JSON.stringify(data));
        }
    }, 10*1000);


    if (data.last_output)
        outputResponse(data.last_output)
}