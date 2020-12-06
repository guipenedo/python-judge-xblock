function PythonJudgeXBlock(runtime, element) {
    $(element).find('.cancel-button').bind('click', function() {
        runtime.notify('cancel', {});
    });

    let editor = ace.edit("initial_code");
    editor.setOptions({
        maxLines: 70,
        minLines: 10,
        autoScrollEditorIntoView: true,
        theme: "ace/theme/monokai",
        showPrintMargin: false,
        mode: "ace/mode/python",
        fontSize: "14pt"
    });

    $(element).find('.save-button').bind('click', function() {
        const data = {
            'initial_code': editor.getValue(),
            'display_name': $(display_name).context.value,
            'test_cases': $(test_cases).context.value
        };

        $('.xblock-editor-error-message', element).html();
        $('.xblock-editor-error-message', element).css('display', 'none');
        const handlerUrl = runtime.handlerUrl(element, 'save_settings');
        $.post(handlerUrl, JSON.stringify(data)).done(function(response) {
            if (response.result === 'success') {

            } else {
                $('.xblock-editor-error-message', element).html('Error: '+response.message);
                $('.xblock-editor-error-message', element).css('display', 'block');
            }
        });
    });
}