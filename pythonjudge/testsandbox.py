import epicbox

epicbox.configure(
    profiles=[
        epicbox.Profile('python', 'python:3.10.0a2-alpine3.12')
    ]
)
files = [{'name': 'main.py', 'content': b'print(42)'}]
limits = {'cputime': 1, 'memory': 64}
result = epicbox.run('python', 'python3 main.py', files=files, limits=limits, stdin='14 5')
print(result)