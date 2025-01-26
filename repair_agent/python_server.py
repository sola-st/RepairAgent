from flask import Flask, request, jsonify
import os

from apply_changes import apply_changes
app = Flask(__name__)

def execute_tests(path):
    # Implement your test logic here
    print("PATH:::::::", path)
    exec_results = os.system("./execute_tests.sh {} > test_results_temp".format(path))
    print(exec_results)
    return exec_results

@app.route('/read_file', methods=['GET'])
def read_file():
    file_path = os.path.join("/home/ubuntu/gitbug-java/", request.args.get('file_path'))
    if not file_path:
        return jsonify({"error": "file_path parameter is required"}), 400
    
    if not os.path.exists(file_path):
        return jsonify({"error": "File does not exist"}), 404
    
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        return jsonify({"content": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/patch', methods=['POST'])
def write_file():
    data = request.get_json()    
    try:
        apply_changes(data)
        return jsonify({"message": "Patch applied succefully"})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

@app.route('/execute_tests', methods=['POST'])
def execute_tests_endpoint():
    data = request.get_json()
    path = data.get('path')
    print("HERE PRINT THE FUCKING DATA:", data)    
    if not path:
        return jsonify({"error": "path parameter is required"}), 400
    
    try:
        result = execute_tests(path)
        with open("test_results_temp") as trt:
            result = trt.read()
        return jsonify({"message": result})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host="10.27.91.248", port=5000)