import utils
import pipeline

# Load configuration from YAML
config_path = 'config.yaml'
config = utils.load_config('config.yaml')

# Load the appropriate language-specific paths
paths = utils.get_language_specific_paths(config)

# Read the correct program file based on the selected language
if config['language'].lower() == 'java':
    program_file_path = config['paths']['java_program']
else:
    program_file_path = config['paths']['python_program']

# Read initial code from the specified program file
with open(program_file_path, 'r', encoding='utf-8') as file:
    initial_code = file.read()

# Set the submission ID
submission_id = "test"

# Call the interactive testing pipeline
pipeline.interactive_testing_pipeline(submission_id, initial_code, config, config_path)
