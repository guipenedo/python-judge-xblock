function PythonJudgeXBlock(runtime, element, context) {
    let id = context.xblock_id;

    let editor = ace.edit("student_code_" + id);
    editor.setOptions({
        maxLines: 50,
        minLines: 10,
        autoScrollEditorIntoView: true,
        theme: "ace/theme/monokai",
        showPrintMargin: false,
        mode: "ace/mode/python",
        fontSize: "14pt"
    });

    let disabledEditorOptions = {
        maxLines: 50,
        minLines: 10,
        autoScrollEditorIntoView: true,
        theme: "ace/theme/monokai",
        showPrintMargin: false,
        mode: "ace/mode/python",
        fontSize: "14pt",
        readOnly: true
    };

    // helper to disable and enable buttons
    function switchButtons(disabled){
        $(element).find('#submit_' + id).prop("disabled", disabled);
        $(element).find('#run_' + id).prop("disabled", disabled);
        $(element).find('#code-runner-button_' + id).prop("disabled", disabled);
    }

    // submit
    $(element).find('#submit_' + id).bind('click', function() {
        $(element).find('#code-runner_' + id).hide();
        $(element).find('#run_' + id).show();
        const data = {
            'student_code': editor.getValue()
        };
        switchButtons(true);
        const handlerUrl = runtime.handlerUrl(element, 'submit_code');
        $.post(handlerUrl, JSON.stringify(data)).done(function (response) {
            switchButtons(false);
            handleEditorResponse(response, $("#code-feedback_" + id), (result) => {
                if (result === 'success')
                    $("#model_answer_container_" + id).show();
            })
        });
    });

    // run button
    $(element).find('#run_' + id).bind('click', function () {
        $(this).hide();
        $(element).find('#code-runner_' + id).show();
    });

    // run button inside the runner window
    $(element).find('#code-runner-button_' + id).bind('click', function () {
        const data = {
            'student_code': editor.getValue(),
            'input': $('#code-runner-input_' + id).val()
        };
        switchButtons(true);
        const handlerUrl = runtime.handlerUrl(element, 'run_code');
        $.post(handlerUrl, JSON.stringify(data)).done(function (response) {
            switchButtons(false);
            if (response.exit_code === 0 && !response.stderr)
                $("#code-runner-output_" + id).html(replaceNewLines(response.stdout));
            else
                $("#code-runner-output_" + id).html("<u>Erro de execução.</u> Exit code: <b>" + response.exit_code + "</b><br /><b>Output:</b> " + replaceNewLines(response.stdout ? response.stdout : "?") + "<br /><b>Stderr:</b> " + replaceNewLines(response.stderr));

        }).fail(function () {
            switchButtons(false);
            $("#code-runner-output_" + id).text("Erro desconhecido. Por favor tenta novamente mais tarde.");
        });
    });

    // view answer button
    let view_model_answer_editor = ace.edit("view_model_answer_" + id);
    view_model_answer_editor.setOptions(disabledEditorOptions);
    $(element).find('#model_answer_button_' + id)
        .leanModal()
        .on('click', function () {
            const handlerUrl = runtime.handlerUrl(element, 'get_model_answer');
            $.post(handlerUrl, "{}").done(function (response) {
                if (response.result === 'success')
                    view_model_answer_editor.setValue(response.model_answer);
                else
                    view_model_answer_editor.setValue(response.message);
            });
        });

    if(context.is_course_staff) {
        $("#model_answer_container_" + id).show();

        let view_submission_editor = ace.edit("view_student_code_" + id);
        view_submission_editor.setOptions(disabledEditorOptions);

        $(element).find('.view_code_button_' + id)
            .leanModal()
            .on('click', function () {
                let row = $(this).parents("tr");
                $(element).find('#view_code_student_name_' + id).text(row.data('fullname'));
                view_submission_editor.setValue(row.data('student_code'));
                handleEditorResponse(row.data('evaluation'), $("#view_code_feedback_" + id));
            });

        $("#submissions_" + id).tablesorter();
    }


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

    if (context.last_output)
        handleEditorResponse(context.last_output, $("#code-feedback_" + id));
}
