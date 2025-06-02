from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)

# Virtual file system: directory paths map to a list of entries
vfs = {
    '/': []
}
file_contents = {}  # file paths map to content
current_path = ['/']

def get_full_path():
    return '/'.join(current_path).replace('//', '/')

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/execute', methods=['POST'])
def execute():
    global current_path
    command = request.json.get("command")
    output = ""

    tokens = command.strip().split()
    if not tokens:
        return jsonify({"output": ""})

    cmd = tokens[0]
    args = tokens[1:]

    full_path = get_full_path()

    try:
        if cmd == 'pwd':
            output = full_path
        elif cmd == 'ls':
            output = '  '.join(vfs.get(full_path, []))
        elif cmd == 'cd':
            if not args:
                current_path = ['/']
            elif args[0] == '..':
                if len(current_path) > 1:
                    current_path.pop()
            else:
                new_path = os.path.join(full_path, args[0]).replace('//', '/')
                if new_path in vfs:
                    current_path.append(args[0])
                else:
                    output = f"No such directory: {args[0]}"
        elif cmd == 'mkdir':
            if args:
                new_dir = os.path.join(full_path, args[0]).replace('//', '/')
                if new_dir not in vfs:
                    vfs[new_dir] = []
                    vfs[full_path].append(args[0])
        elif cmd == 'touch':
            if args:
                new_file = args[0]
                full_file_path = os.path.join(full_path, new_file).replace('//', '/')
                if new_file not in vfs[full_path]:
                    vfs[full_path].append(new_file)
                    file_contents[full_file_path] = ""
        elif cmd == 'echo':
            if '>' in args:
                content = ' '.join(args[:args.index('>')])
                file_name = args[args.index('>') + 1]
                full_file_path = os.path.join(full_path, file_name).replace('//', '/')
                if file_name not in vfs[full_path]:
                    vfs[full_path].append(file_name)
                file_contents[full_file_path] = content
            else:
                output = ' '.join(args)
        elif cmd == 'cat':
            if args:
                file_path = os.path.join(full_path, args[0]).replace('//', '/')
                output = file_contents.get(file_path, f"No such file: {args[0]}")
        elif cmd == 'mv':
            if len(args) == 2:
                src = os.path.join(full_path, args[0]).replace('//', '/')
                dst = os.path.join(full_path, args[1]).replace('//', '/')
                if args[0] in vfs[full_path]:
                    vfs[full_path].remove(args[0])
                    vfs[full_path].append(args[1])
                    file_contents[dst] = file_contents.pop(src, "")
        elif cmd == 'rm':
            if args:
                target = os.path.join(full_path, args[0]).replace('//', '/')
                if args[0] in vfs[full_path]:
                    vfs[full_path].remove(args[0])
                    vfs.pop(target, None)
                    file_contents.pop(target, None)
        elif cmd == 'clear':
            return jsonify({"output": "__CLEAR__"})
        else:
            output = f"Command '{cmd}' not found."
    except Exception as e:
        output = f"Error: {str(e)}"

    return jsonify({"output": output})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

