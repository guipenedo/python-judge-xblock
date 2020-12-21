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
    let editor_grader = ace.edit("grader_code_" + id);
    editor_grader.setOptions(options);

    $(element).find('#save-button_' + id).bind('click', function() {
        const data = {
            'initial_code': editor_initial.getValue(),
            'grader_code': editor_grader.getValue(),
        };

        const handlerUrl = runtime.handlerUrl(element, 'save_settings').replace("/preview", "");
        runtime.notify('save', {state: 'start'});
        $.post(handlerUrl, JSON.stringify(data)).done(function(response) {
            if (response.result === 'success') {
                runtime.notify('save', {state: 'end'});
            } else {
                runtime.notify('error', {title: gettext("Unable to update settings"), message: response.message});
            }
        });
    });
}
