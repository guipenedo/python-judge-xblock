function PythonJudgeXBlock(runtime, element, context) {
    let id = context.xblock_id;

    let editor_initial = getCodeEditor("initial_code_" + id);
    let editor_model_answer = getCodeEditor("model_answer_" + id);
    let editor_grader;
    if (context.uses_grader)
        editor_grader = getCodeEditor("grader_code_" + id);

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
