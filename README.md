## FuzzWise: Intelligent Initial Corpus Generation for Fuzzing

n mutation-based greybox fuzzing, generating high-quality input seeds for the initial corpus is essential for effective fuzzing. Rather than conducting separate phases for generating a large corpus and subsequently minimizing it, we propose FuzzWise which integrates them into one process to generate the optimal initial corpus of seeds (ICS). FuzzWise leverages a multi-agent framework based on Large Language Models (LLMs). The first LLM agent generates test cases for the target program. The second LLM agent, which functions as a predictive code coverage module, assesses whether each generated test case will enhance the overall coverage of the current corpus. The streamlined process allows each newly generated test seed to be immediately evaluated for its contribution to the overall coverage. FuzzWise employs a predictive approach using an
LLM and eliminates the need for actual execution, saving computational resources and time, particularly in scenarios where the execution is not desirable or even impossible. Our empirical evaluation demonstrates that FuzzWise generates significantly fewer test cases than baseline methods. Despite the lower number of test cases, FuzzWise achieves high code coverage and triggers more runtime errors compared to the baselines. Moreover, it is more time-efficient and coverage-efficient in producing an initial corpus catching more errors.

### Dataset
All data for reproducing the results is available in the dataset folder.

The dataset for FuzzWise has been tested on a subset derived from [FixExal](https://arxiv.org/abs/2206.07796)

### Folder Structure 
```

├── fuzzwise
│   ├── model
│   │    ├──execution.py
│   │    ├──gpt.py
│   │    ├──pipeline.py
│   │    ├──utils.py
|   ├──prompts
│   │    ├──java
│   │    │    ├──codepilot_main-oneshot-prompt.txt
│   │    │    ├──codepilot_oneshot-plan-prompt.txt
│   │    │    ├──cvg_prompt.txt
│   │    │    ├──cvg_prompt_instructions.txt
│   │    │    ├──tgt_coverage_prompt.txt
│   │    │    ├──tgt_coverage_prompt_instructions.txt
│   │    │    ├──tgt_exception_prompt.txt
│   │    │    ├──tgt_exeception_prompt_instructions.txt
│   │    ├──python
│   │    │    ├──codepilot_main-oneshot-prompt.txt
│   │    │    ├──codepilot_oneshot-plan-prompt.txt
│   │    │    ├──cvg_prompt.txt
│   │    │    ├──cvg_prompt_instructions.txt
│   │    │    ├──tgt_coverage_prompt.txt
│   │    │    ├──tgt_coverage_prompt_instructions.txt
│   │    │    ├──tgt_exception_prompt.txt
│   │    │    ├──tgt_exeception_prompt_instructions.txt
│   ├── results
│   │    ├──fuzzwise_results
│   │    │    ├──java
│   │    │    │    ├──cleaned
│   │    │    ├──python
│   │    │    │    ├──cleaned
│   ├── baseline outputs
│   ├── dataset
│   │    ├──java_dataset.json
│   │    ├──python_dataset.json
│   └── README.md
```

## Procedure to fuzz the dataset using FuzzWise

1. Clone the official github repository for FuzzWise
```
git clone https://github.com/fuzzwise/fuzzwise.git
```
2. Add the necessary paths required, programming_language chosen, API keys and endpoints for fuzzing in model/config.yaml
3. Add the code to be tested on in program.py or Main.java depending on the programming language chosen
4. Run the 'model/main.py' file 


