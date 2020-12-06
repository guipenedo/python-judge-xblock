function PythonJudgeXBlock(runtime, element) {
    let editor = ace.edit("student_code");
    editor.setOptions({
        maxLines: 1000,
        autoScrollEditorIntoView: true,
        theme: "ace/theme/monokai",
        showPrintMargin: false,
        mode: "ace/mode/python"
    });
}