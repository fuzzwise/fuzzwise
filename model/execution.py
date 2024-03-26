import subprocess
import os

def format_test_cases(raw_input):
    formatted_test_cases = []
    current_case = []
    for line in raw_input:
        if "Test Case Input:" in line:
            if current_case:
                formatted_case = f"{os.linesep.join(current_case)}"
                formatted_test_cases.append(formatted_case)
            current_case = [line.strip()]
        else:
            current_case.append(line.strip())
    if current_case:
        formatted_case = f"{os.linesep.join(current_case)}"
        formatted_test_cases.append(formatted_case)
    return formatted_test_cases

def convert_to_desired_format(formatted_test_cases):
    converted_test_cases = []
    for index, case in enumerate(formatted_test_cases, start=1):
        lines = case.split('\n')
        input_lines = [line for line in lines if line.strip()]
        converted_case = f"Test Case {index} Input:\n{os.linesep.join(input_lines)}"
        converted_test_cases.append(converted_case)
    return converted_test_cases


def execute_java_program(code, test_cases, submission_id):
    with open('Main.java', 'w', encoding='utf-8') as java_file:
        java_file.write(code)

    # Compile the Java program
    compile_result = subprocess.run(['javac', 'Main.java'])
    if compile_result.returncode != 0:
        print("Java compilation failed. Check for errors.")
        return

    outputs = []
    for index, test_case in enumerate(test_cases, start=1):
        # Extract the relevant input lines
        input_lines = test_case.split('\n')[2:]  # Skip the first two lines containing "Test Case X Input:"
        input_data = ''.join(input_lines).strip()

        process = subprocess.run(['java', 'Main'], input=input_data, capture_output=True, text=True)
        output = f"Test Case {index} Input:\n{input_data}\n"
        if process.stdout:
            output += f"Output:\n{process.stdout}"
        if process.stderr:
            output += f"Error:\n{process.stderr}"
        outputs.append(output)
    output_filepath = f"C:/Users/hridy/Documents/PhD_Research/ICSE'25/FuzzWise/fuzzwise_outputs/execution_logs/{submission_id}_output.txt"
    with open(output_filepath, 'w', encoding='utf-8') as output_file:
        for output in outputs:
            output_file.write(output)