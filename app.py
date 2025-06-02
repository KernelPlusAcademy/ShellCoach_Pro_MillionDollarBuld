from flask import Flask, render_template, request, jsonify
import pexpect
import shlex

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/execute', methods=['POST'])
def execute_command():
    data = request.json
    command = data.get("command")
    try:
        # Use pexpect to run the command safely in a sandbox shell
        child = pexpect.spawn('/bin/bash', ['-c', command], encoding='utf-8', timeout=3)
        child.expect(pexpect.EOF)
        output = child.before
        return jsonify({"output": output})
    except Exception as e:
        return jsonify({"output": f"Error: {str(e)}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
