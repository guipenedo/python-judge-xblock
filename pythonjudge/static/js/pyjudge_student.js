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

    function replaceNewLines(str){
        return str.replace(/(?:\r\n|\r|\n)/g, '<br>');
    }

    function formatOutputDiff(expected_out, output){
        let i = 0, j = 0;
        while (j < output.length){
            while (i < expected_out.length && expected_out[i] === '\n')
                i++;
            while (j < output.length && output[j] === '\n')
                j++;
            if (i >= expected_out.length || expected_out[i++] !== output[j])
                return output.substr(0, j) + '<span style="color:red;font-weight: bold">' + output[j] + '</span>' + output.substr(j+1, output.length-j-1);
            j++;
        }
        let formatted_output = output;
        if (i < expected_out.length)
            formatted_output += '[<span style="color:red;font-weight: bold">' + expected_out.substr(i, expected_out.length-i) + '</span>]';
        return formatted_output
    }

    function outputResponse(response, feedbackElement= "#code-feedback") {
        switchButtons(false);
        if (response.result === 'success') {
            $(feedbackElement + "_" + id).html("<i aria-hidden=\"true\" class=\"fa fa-check\" style=\"color:green\"></i> " + response.message);
        } else {
            if (response.exit_code === 0 && !response.stderr)
                $(feedbackElement + "_" + id).html("<span aria-hidden=\"true\" class=\"fa fa-times\" style=\"color:darkred\"></span> <b><u>Output incorreta no caso de teste " + response.test_case + "</u></b><br/><b>Input:</b> " + response.input + "<br/><b>Output esperada:</b> " + replaceNewLines(response.expected_output) + "<br/><b>=============</b><br/><b>Output do teu programa:</b> (primeira diferença a vermelho)<br/>" + replaceNewLines(formatOutputDiff(response.expected_output, response.student_output)))
            else
                $(feedbackElement + "_" + id).html("<span aria-hidden=\"true\" class=\"fa fa-times\" style=\"color:darkred\"></span> <b><u>Erro no caso de teste " + response.test_case + "</u></b><br/><b>Input:</b> " + response.input + "<br/><b>Output esperada:</b> " + replaceNewLines(response.expected_output) + "<br/><b>=============</b><br/><b>Exit code:</b> " + response.exit_code + "<br/><b>Erro do teu programa:</b> " + replaceNewLines(response.stderr))
        }
    }

    function switchButtons(disabled){
        $(element).find('#submit_' + id).prop("disabled", disabled);
        $(element).find('#run_' + id).prop("disabled", disabled);
        $(element).find('#code-runner-button_' + id).prop("disabled", disabled);
    }

    $(element).find('#submit_' + id).bind('click', function() {
        $(element).find('#code-runner_' + id).hide();
        $(element).find('#run_' + id).show();
        const data = {
            'student_code': editor.getValue()
        };
        switchButtons(true);
        const handlerUrl = runtime.handlerUrl(element, 'submit_code');
        $.post(handlerUrl, JSON.stringify(data)).done(function (response) {
            outputResponse(response);
        });
    });


    $(element).find('#run_' + id).bind('click', function () {
        $(this).hide();
        $(element).find('#code-runner_' + id).show();
    });

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

    if(context.is_course_staff) {
        let view_submission_editor = ace.edit("view_student_code_" + id);
        view_submission_editor.setOptions({
            maxLines: 50,
            minLines: 10,
            autoScrollEditorIntoView: true,
            theme: "ace/theme/monokai",
            showPrintMargin: false,
            mode: "ace/mode/python",
            fontSize: "14pt",
            readOnly: true
        });

        $(element).find('.view_code_button_' + id)
            .leanModal()
            .on('click', function () {
                let row = $(this).parents("tr");
                $(element).find('#view_code_student_name_' + id).text(row.data('fullname'));
                view_submission_editor.setValue(row.data('student_code'));
                outputResponse(row.data('evaluation'), "#view_code_feedback")
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
        outputResponse(context.last_output)
}
