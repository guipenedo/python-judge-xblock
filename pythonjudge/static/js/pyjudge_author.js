function PythonJudgeXBlock(runtime, element) {
    $(element).find('.cancel-button').bind('click', function() {
        runtime.notify('cancel', {});
    });

    let options = {
        maxLines: 50,
        minLines: 10,
        autoScrollEditorIntoView: true,
        theme: "ace/theme/monokai",
        showPrintMargin: false,
        mode: "ace/mode/python",
        fontSize: "14pt"
    };
    let editor_initial = ace.edit("initial_code");
    editor_initial.setOptions(options);
    let editor_grader = ace.edit("grader_code");
    editor_grader.setOptions(options);

    $(element).find('#save-button').bind('click', function() {
        const data = {
            'initial_code': editor_initial.getValue(),
            'grader_code': editor_grader.getValue(),
        };

        const handlerUrl = runtime.handlerUrl(element, 'save_settings');
        runtime.notify('save', {state: 'start'});
        $.post(handlerUrl, JSON.stringify(data)).done(function(response) {
            if (response.result === 'success') {
                runtime.notify('save', {state: 'end'});
                window.location.reload(true);
            } else {
                runtime.notify('error', {title: gettext("Unable to update settings"), message: response.message});
            }
        });
    });
}
