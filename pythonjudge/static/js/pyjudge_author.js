function PythonJudgeXBlock(runtime, element, context) {
    let id = context.xblock_id;

    let options = {
        maxLines: 50,
        minLines: 10,
        autoScrollEditorIntoView: true,
        theme: "ace/theme/monokai",
        showPrintMargin: false,
        mode: "ace/mode/python",
        fontSize: "14pt"
    };
    let editor_initial = ace.edit("initial_code_" + id);
    editor_initial.setOptions(options);
    let editor_model_answer = ace.edit("model_answer_" + id);
    editor_model_answer.setOptions(options);
    if (context.uses_grader) {
        let editor_grader = ace.edit("grader_code_" + id);
        editor_grader.setOptions(options);
    }

    // save settings
    function save_settings() {
        let data = {
            'initial_code': editor_initial.getValue(),
            'model_answer': editor_model_answer.getValue()
        };
        if (context.uses_grader)
            data['grader_code'] = editor_grader.getValue()

        const handlerUrl = runtime.handlerUrl(element, 'save_settings').replace("/preview", "");
        runtime.notify('save', {state: 'start'});
        $.post(handlerUrl, JSON.stringify(data)).done(function (response) {
            if (response.result === 'success') {
                runtime.notify('save', {state: 'end'});
            } else {
                runtime.notify('error', {title: gettext("Unable to update settings"), message: response.message});
            }
        });
    }
    $(element).find('#save-button_' + id).bind('click', save_settings);

    // submit
    $(element).find('#test_model_answer_' + id).bind('click', function () {
        // save current editors as well
        save_settings();
        $(this).prop("disabled", true);
        const data = {
            'model_answer': editor_model_answer.getValue()
        };
        const handlerUrl = runtime.handlerUrl(element, 'test_model_solution');
        $.post(handlerUrl, JSON.stringify(data)).done((response) => {
            $(this).prop("disabled", false);
            handleEditorResponse(response, $("#code-feedback" + "_" + id));
        });
    });
}
