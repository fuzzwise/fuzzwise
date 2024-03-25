import concurrent.futures
from openai import AzureOpenAI
import gpt_interaction, execution, utils
import re, json, os, ast, time, subprocess

tgt_exception_prompt_path = "C:/Users/hridy/Documents/PhD_Research/ICSE'25/MostRecent/FuzzWise/FuzzWise/text_files/tgt_exception_prompt.txt"
tgt_coverage_prompt_path = "C:/Users/hridy/Documents/PhD_Research/ICSE'25/MostRecent/FuzzWise/FuzzWise/text_files/tgt_coverage_prompt.txt"
cvg_prompt_path = "C:/Users/hridy/Documents/PhD_Research/ICSE'25/MostRecent/FuzzWise/FuzzWise/text_files/cvg_prompt.txt"
tgt_exception_prompt_instructions = "C:/Users/hridy/Documents/PhD_Research/ICSE'25/MostRecent/FuzzWise/FuzzWise/text_files/tgt_exception_prompt_instructions.txt"
tgt_coverage_prompt_instructions = "C:/Users/hridy/Documents/PhD_Research/ICSE'25/MostRecent/FuzzWise/FuzzWise/text_files/tgt_coverage_prompt_instructions.txt"
cvg_prompt_instructions = "C:/Users/hridy/Documents/PhD_Research/ICSE'25/MostRecent/FuzzWise/FuzzWise/text_files/cvg_prompt_instructions.txt"
json_result_path = "C:/Users/hridy/Documents/PhD_Research/ICSE'25/MostRecent/FuzzWise/FuzzWise/test_coverage_result.json"
code_txt_path = "C:/Users/hridy/Documents/PhD_Research/ICSE'25/MostRecent/FuzzWise/FuzzWise/text_files/code.txt"
codepilot_cvg_prompt_path = "C:/Users/hridy/Documents/PhD_Research/ICSE'25/MostRecent/FuzzWise/FuzzWise/text_files/codepilot_main-oneshot-plan-prompt.txt"
codepilot_cvg_instructions = "C:/Users/hridy/Documents/PhD_Research/ICSE'25/MostRecent/FuzzWise/FuzzWise/text_files/codepilot_oneshot-plan-prompt.txt"
input_json_file = f"C:/Users/hridy/Documents/PhD_Research/ICSE'25/MostRecent/FuzzWise/final_dataset/final_dataset.json"
output_folder = "C:/Users/hridy/Documents/PhD_Research/ICSE'25/FuzzWise/fuzzwise_outputs/responses" 

def interactive_testing_pipeline(submission_id, initial_code, time_limit_minutes=5):
    global coverage_status
    coverage_status = False
    generated_test_cases = ""
    generated_test_seeds = ""
    tgt_exception_prompt_instructions_text = utils.read_code(tgt_exception_prompt_instructions)
    tgt_coverage_prompt_instructions_text = utils.read_code(tgt_coverage_prompt_instructions)
    clean_altered_code = utils.remove_comments_and_blank_lines(initial_code)
    updated_code = utils.prepend_exclamation_mark(clean_altered_code)
    coverage_symbols = utils.extract_symbols(updated_code)
    code_length = len(coverage_symbols)
    print("Initial Coverage : ",coverage_symbols)
    start_time = time.time()
    fuzzwise_logs_json_filepath = utils.create_json_file(submission_id)
    while True:
        old_symbols = coverage_symbols
        current_time = time.time()
        elapsed_time_minutes = (current_time - start_time) / 60.0
        print(elapsed_time_minutes)
        if elapsed_time_minutes >= time_limit_minutes:
            print(f"Execution stopped after {time_limit_minutes} minutes.")
            break
        open(tgt_exception_prompt_path, 'w').close()
        open(tgt_coverage_prompt_path, 'w').close()
        if coverage_status == True :
            print("Prompt#1 : Raise Exceptions")
            tgt_prompt_text = utils.add_updated_code(tgt_exception_prompt_instructions_text, clean_altered_code, generated_test_seeds)
            with open(tgt_exception_prompt_path, 'a', encoding='utf-8') as tgt_file:
                tgt_file.write(tgt_prompt_text)
            test_seed, test_mutations,temporary_test_case_storage = gpt_interaction.tgt_chatgpt_interaction(tgt_exception_prompt_path)
            print("TCG RESPONSE")
            test_seed = test_seed.replace('"', '')
            print(test_seed)
            generated_test_seeds += f'{test_seed}\n'
            generated_test_cases = f'{test_mutations}\n'
            cvg_prompt_text = utils.read_code(codepilot_cvg_instructions)
            cvg_prompt_text = utils.insert_code_and_testcase_in_prompt(cvg_prompt_text, initial_code, test_seed)
            with open(cvg_prompt_path, 'w', encoding='utf-8') as cvg_file:
                cvg_file.write(cvg_prompt_text)
            coverage_prediction = gpt_interaction.ccp_chatgpt_interaction(cvg_prompt_path)
            coverage_symbols = utils.extract_symbols(coverage_prediction)
            result_coverage_symbols = coverage_symbols
            if utils.check_all_coverage_symbols(result_coverage_symbols, old_symbols) == True: 
                coverage_status = True
            else : 
                coverage_status = False
            min_length = min(len(old_symbols), len(coverage_symbols))
            for i in range(min_length):
                if old_symbols[i] == '>' and coverage_symbols[i] == '!':
                    coverage_symbols[i] = '>'
                elif old_symbols[i] == '!' and coverage_symbols[i] == '>':
                    coverage_symbols[i] = '>'
                elif old_symbols[i] == '>' and coverage_symbols[i] == '>':
                    coverage_symbols[i] = '>'
                elif old_symbols[i] == '!' and coverage_symbols[i] == '!':
                    coverage_symbols[i] = '!'
            if min_length < code_length:
                coverage_symbols[min_length:code_length] = ['>' for _ in range(min_length, code_length)]
            print("CCP RESPONSE")
            print("Result Coverage : ",result_coverage_symbols) 
            print("New Cumulative Coverage : ",coverage_symbols) 

        else : 
            print("Prompt#2 : Increase Coverage")
            updated_code = utils.add_coverage_symbols_to_code(clean_altered_code, coverage_symbols)
            tgt_prompt_text = utils.add_updated_code(tgt_coverage_prompt_instructions_text, updated_code, generated_test_seeds)
            with open(tgt_coverage_prompt_path, 'a', encoding='utf-8') as tgt_file:
                tgt_file.write(tgt_prompt_text)
            test_seed, test_mutations,temporary_test_case_storage = gpt_interaction.tgt_chatgpt_interaction(tgt_coverage_prompt_path)
            print("TCG RESPONSE")
            test_seed = test_seed.replace('"', '')
            print(test_seed)
            generated_test_seeds += f'{test_seed}\n'
            generated_test_cases = f'{test_mutations}\n'    
            cvg_prompt_text = utils.read_code(codepilot_cvg_instructions)
            cvg_prompt_text = utils.insert_code_and_testcase_in_prompt(cvg_prompt_text, initial_code, test_seed)
            with open(cvg_prompt_path, 'w', encoding='utf-8') as cvg_file:
                cvg_file.write(cvg_prompt_text)
            coverage_prediction = gpt_interaction.ccp_chatgpt_interaction(cvg_prompt_path)
            coverage_symbols = utils.extract_symbols(coverage_prediction)
            result_coverage_symbols = coverage_symbols
            print("Old Cumulative Coverage :", old_symbols)
            if utils.check_all_coverage_symbols(result_coverage_symbols, old_symbols) == True: 
                coverage_status = True
            else:
                coverage_status = False
            min_length = min(len(old_symbols), len(coverage_symbols))
            for i in range(min_length):
                if old_symbols[i] == '>' and coverage_symbols[i] == '!':
                    coverage_symbols[i] = '>'
                elif old_symbols[i] == '!' and coverage_symbols[i] == '>':
                    coverage_symbols[i] = '>'
                elif old_symbols[i] == '>' and coverage_symbols[i] == '>':
                    coverage_symbols[i] = '>'
                elif old_symbols[i] == '!' and coverage_symbols[i] == '!':
                    coverage_symbols[i] = '!'
            if min_length < code_length:
                coverage_symbols[min_length:code_length] = ['>' for _ in range(min_length, code_length)]
            print("CCP RESPONSE")
            print("Result Coverage : ",result_coverage_symbols) 
            print("Cumulative Coverage : ",coverage_symbols)
        result = {
            'test_case': test_seed,
            'test_mutations': temporary_test_case_storage,
            'initial_code': initial_code,
            'covered_code': coverage_prediction,
            'test_seed_coverage': result_coverage_symbols,
            'cumulative_coverage': coverage_symbols
        }
        utils.save_cycle_response(fuzzwise_logs_json_filepath, result)
    generated_test_cases = ast.literal_eval(generated_test_cases)
    formatted_test_cases = execution.format_test_cases(generated_test_cases)
    converted_test_cases = execution.convert_to_desired_format(formatted_test_cases)
    print(type(converted_test_cases))
    execution.execute_java_program(clean_altered_code, converted_test_cases,submission_id)
    print("Execution completed for submission ID:", submission_id)


with open(input_json_file, 'r', encoding='utf-8') as json_file:
    submissions_data = json.load(json_file)
for submission_data in submissions_data:
    submission_id = submission_data['submission_id']
    initial_code = utils.extract_initial_code(submission_id, submissions_data)
    if initial_code:
        print(submission_id)
        interactive_testing_pipeline(submission_id, initial_code)
    else:
        print(f"Initial code not found for submission ID: {submission_id}")
