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

    $(element).find('#save-button_' + id).bind('click', function() {
        let data = {
            'initial_code': editor_initial.getValue(),
            'model_answer': editor_model_answer.getValue()
        };
        if (context.uses_grader)
            data['grader_code'] = editor_grader.getValue()

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


    function replaceNewLines(str) {
        return str.replace(/(?:\r\n|\r|\n)/g, '<br>');
    }

    // helper to visually format difference between outputs
    function formatOutputDiff(expected_out, output) {
        let i = 0, j = 0;
        while (j < output.length) {
            while (i < expected_out.length && expected_out[i] === '\n')
                i++;
            while (j < output.length && output[j] === '\n')
                j++;
            if (i >= expected_out.length || expected_out[i++] !== output[j])
                return output.substr(0, j) + '<span style="color:red;font-weight: bold">' + output[j] + '</span>' + output.substr(j + 1, output.length - j - 1);
            j++;
        }
        let formatted_output = output;
        if (i < expected_out.length)
            formatted_output += '[<span style="color:red;font-weight: bold">' + expected_out.substr(i, expected_out.length - i) + '</span>]';
        return formatted_output
    }

    // submit
    $(element).find('#test_model_answer_' + id).bind('click', function () {
        $(this).disable();
        const data = {
            'model_answer': editor_model_answer.getValue()
        };
        const handlerUrl = runtime.handlerUrl(element, 'test_model_solution');
        $.post(handlerUrl, JSON.stringify(data)).done((response) => {
            $(this).enable();
            if (response.result === 'success') {
                $("#code-feedback" + "_" + id).html("<i aria-hidden=\"true\" class=\"fa fa-check\" style=\"color:green\"></i> " + response.message);
            } else {
                if (response.exit_code === 0 && !response.stderr)
                    $("#code-feedback" + "_" + id).html("<span aria-hidden=\"true\" class=\"fa fa-times\" style=\"color:darkred\"></span> <b><u>Output incorreta no caso de teste " + response.test_case + "</u></b><br/><b>Input:</b> " + response.input + "<br/><b>Output esperada:</b> " + replaceNewLines(response.expected_output) + "<br/><b>=============</b><br/><b>Output do teu programa:</b> (primeira diferença a vermelho)<br/>" + replaceNewLines(formatOutputDiff(response.expected_output, response.student_output)))
                else
                    $("#code-feedback" + "_" + id).html("<span aria-hidden=\"true\" class=\"fa fa-times\" style=\"color:darkred\"></span> <b><u>Erro no caso de teste " + response.test_case + "</u></b><br/><b>Input:</b> " + response.input + "<br/><b>Output esperada:</b> " + replaceNewLines(response.expected_output) + "<br/><b>=============</b><br/><b>Exit code:</b> " + response.exit_code + "<br/><b>Erro do teu programa:</b> " + replaceNewLines(response.stderr))
            }
        });
    });
}
