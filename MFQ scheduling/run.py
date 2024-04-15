import os
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import subprocess
import warnings

warnings.filterwarnings('ignore')

# 사용자 입력 받기
user_input = input("랜덤 테스트 케이스를 실행하시겠습니까? (y로 설정할 시 랜덤으로 생성된 5개의 테스트 케이스에 대해 시뮬레이션을 수행하며, n으로 설정할 시 입력 예시에 대해서만 시뮬레이션을 수행합니다.) (y/n): ")

# 사용자 입력에 따라 testing 변수 설정
if user_input.lower() == 'y':
    testing = True
    user_input2 = input("테스트 케이스를 새로 생성하시겠습니까? (y/n): ")
    if user_input2.lower() == 'y':
        generate = True
    elif user_input2.lower() == 'n':
        generate = False
    else:
        print('잘못된 입력값입니다.')
        exit()
elif user_input.lower() == 'n':
    testing = False
else:
    print('잘못된 입력값입니다.')
    exit()

current_dir = os.path.dirname(os.path.abspath(__file__))

# testing이 True일 경우 make_inputs.ipynb 파일 실행
if testing:
    if generate:
        # make_inputs.ipynb 파일 경로
        notebook_path = os.path.join(current_dir, 'test_case', 'make_inputs.ipynb')

        # .ipynb 파일 읽어오기
        with open(notebook_path) as f:
            nb = nbformat.read(f, as_version=4)

        # 노트북 실행을 위한 ExecutePreprocessor 생성
        ep = ExecutePreprocessor(timeout=600, kernel_name='python3')

        # 노트북 실행
        ep.preprocess(nb, {'metadata': {'path': os.path.join(current_dir, 'test_case')}})

    # 테스트 케이스 파일들에 대해 반복 실행
    for i in range(1, 6):
        print(f"Running test case {i}:\n")
        main_path = os.path.join(current_dir, 'main.py')
        test_case_path = os.path.join(current_dir, 'test_case', f'inputs_{i}.txt')
        subprocess.run(["python", main_path, test_case_path])
        print("\n")
else:
    # testing이 False일 경우 현재 디렉토리의 inputs.txt 파일에 대해 실행
    print("Running main program with inputs.txt:\n")
    main_path = os.path.join(current_dir, 'main.py')
    inputs_path = os.path.join(current_dir, 'inputs.txt')
    subprocess.run(["python", main_path, inputs_path])