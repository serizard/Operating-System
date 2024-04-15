import pandas as pd
import numpy as np
import os
import sys
from readyqueue import round_robin, FCFS
from process import process
from CPU import CPU
from tabulate import tabulate

def draw_gantt_chart(running_infos, p_table, end_time):
    # Gantt 차트를 그리기 위한 시간 순서 DataFrame 생성
    time_sequence = pd.DataFrame(np.zeros(shape=(3, end_time+1), dtype=int), index = ['in', 'running', 'out'], columns = range(end_time+1))
    
    # 프로세스 도착 시간과 완료 시간을 time_sequence DataFrame에 표시
    for p in p_table.iterrows():
        arrival_time = p[1].AT
        completion_time = p[1].TT + p[1].AT 
        time_sequence.iloc[0, arrival_time] = p[1].PID
        time_sequence.iloc[2, completion_time] = p[1].PID
    
    # running_infos를 사용하여 프로세스 실행 정보를 time_sequence DataFrame에 표시
    time = min(p_table.loc[:, 'AT'])
    for running_info in running_infos:
        if running_info['start_time'] > time:
            time = running_info['start_time']
        time_sequence.iloc[1,time:time+running_info['duration']] = running_info['name']
        time += running_info['duration']
    
    # time_sequence DataFrame에서 0을 공백으로 대체
    time_sequence = time_sequence.replace(0, ' ')

    # 차트의 최대 길이 설정
    max_length = 21

    # 차트를 여러 줄로 나누어 출력
    print('Gantt Chart')
    for i in range(0, len(time_sequence.columns), max_length):
        start = i
        end = min(i + max_length, len(time_sequence.columns))
        print(tabulate(time_sequence.iloc[:, start:end], headers=range(start, end), tablefmt="grid"))
        print()
    print('\n')
    

def draw_p_table(p_table):
    # 프로세스 테이블 출력
    print('Process Table')
    print(tabulate(p_table, headers=p_table.columns, tablefmt="grid"))
    print('\n')

def show_avgs(p_table):
    # 평균 반환 시간과 평균 대기 시간 출력
    print(f'Average Turnaround Time: {np.mean(p_table.TT)}')
    print(f'Average Waiting Time: {np.mean(p_table.WT)}')


# 명령행 인수에서 입력 파일 경로 가져오기
if len(sys.argv) != 2:
    print("사용법: python main.py <input_file_path>")
    exit()

input_file_path = sys.argv[1]


if not os.path.isfile(input_file_path):
    print(f"입력 파일 {input_file_path}을(를) 찾을 수 없습니다.")
    exit()

# 입력 파일에서 프로세스 정보 읽기
with open(input_file_path, 'r') as file:
    lines = file.readlines()

p_num = int(lines[0].strip())
p_list = []
p_table = pd.DataFrame(columns=['PID', 'AT', 'BT', 'TT', 'WT'])

for line in lines[1:]:
    pid, at, bt = map(int, line.strip().split())
    p_list.append((at, process(pid, bt)))
    p_table = pd.concat([p_table, pd.DataFrame([[pid, at, bt, 0, 0]], columns=p_table.columns)], ignore_index=True)

p_list.sort() # 도착 순서 기준 오름차순 정렬

# 큐 리스트 생성
q0 = round_robin(time_quantum=2, priority=0)
q1 = round_robin(time_quantum=6, priority=1)
q2 = FCFS(priority=2)
q_list = [q0, q1, q2]

running_infos = []
t = 0
processor = CPU() # 프로세서 객체 생성

# 시뮬레이션 실행
# 멈춤 조건: 모든 프로세스 도착 완료 + 모든 readyqueue가 비어 있음 + CPU가 running 중이 아님
while (len(p_list) == 0 and False not in [q.isempty() for q in q_list] and not processor.isrunning) != True:
    # 프로세스 도착 처리
    if len(p_list) != 0 and p_list[0][0] == t:
        while len(p_list) > 0 and p_list[0][0] == t:
            target_p = p_list.pop(0)
            q_list[0].add(target_p[1])
    
    # 프로세스 실행
    if not processor.isrunning:
        p = None
        for idx, q in enumerate(q_list):
            if not q.isempty():
                p, tq = q.dispatch()
                q_idx = idx
                break
        
        if p != None:
            time_consumed, isFinished = p.burst(tq = tq)
            running_infos.append({'name':f'P{p.pid}', 'duration':time_consumed, 'start_time': t})
            
            if not isFinished:
                processor.run(p, return_index=min(q_idx+1, len(q_list)-1), running_time=time_consumed)
            else:
                processor.run(p, return_index=None, running_time=time_consumed)
                p_table.loc[p_table['PID'] == p.pid, 'TT'] = t + time_consumed - p_table.loc[p_table['PID'] == p.pid, 'AT']
                p_table.loc[p_table['PID'] == p.pid, 'WT'] = p_table.loc[p_table['PID'] == p.pid, 'TT'] - p_table.loc[p_table['PID'] == p.pid, 'BT']
    
    # 프로세스 실행 시간 감소 및 종료 처리
    if processor.isrunning:
        processor.running_time -= 1
        if processor.isrunning and processor.running_time == 0:
            p, return_idx = processor.terminate()
            if return_idx != None:
                q_list[return_idx].add(p)
    
    t += 1

# 결과 출력
draw_gantt_chart(running_infos, p_table, t)
draw_p_table(p_table)
show_avgs(p_table)