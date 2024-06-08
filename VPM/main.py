import os
import numpy as np
import pandas as pd
import random

class TestCaseGenerator:
    def __init__(self):
        self.num_processes = np.random.randint(5, 20)
        self.memory_size = np.random.randint(50, 300)
        self.max_request = np.random.randint(20, 30)
        self.operations = ['in', 'out', 'cpn']

    def generate_test_cases(self):
        unallocated_p = [(i+1, random.randint(1, self.memory_size//3)) for i in range(self.num_processes)]
        allocated_p = []
        test_cases = []

        for _ in range(self.max_request):
            operation = random.choices(self.operations, weights=[0.6, 0.3, 0.1])[0]

            if operation == 'out':
                if allocated_p:
                    target_p = random.choice(allocated_p)
                    p_num, amount = target_p
                    allocated_p.remove(target_p)
                    unallocated_p.append(target_p)
                else:
                    operation = 'in'
            if operation == 'in':
                if unallocated_p:
                    target_p = random.choice(unallocated_p)
                    p_num, amount = target_p
                    allocated_p.append(target_p)
                    unallocated_p.remove(target_p)
                else:
                    continue
            if operation == 'cpn':
                p_num = 0
                amount = 0
            
            test_cases.append((p_num, operation, amount))
        
        test_cases.append((-1, 'exit', 0))

        return test_cases

    def save_to_file(self, file_path):
        test_cases = self.generate_test_cases()

        with open(file_path, 'w') as f:
            f.write(f'{self.num_processes} {self.memory_size}\n')
            for test_case in test_cases:
                f.write(f'{test_case[0]} {test_case[1]} {test_case[2]}\n')


class CircularList:
    def __init__(self, items):
        self.items = items
        self.current_index = 0

    def __iter__(self):
        return self

    def __len__(self):
        return len(self.items)

    def __next__(self):
        if self.current_index >= len(self.items):
            self.current_index = 0
        item = self.items[self.current_index]
        self.current_index += 1
        return item


def update(size_list, pid_list):
    return pd.DataFrame({'partition': range(1, len(size_list)+1), 
                         'start address': np.cumsum([0] + list(size_list[:-1])), 
                         'size': size_list, 
                         'PID': pid_list})


def coalescing_holes(memory):
    size_list = memory['size'].tolist()
    PID_list = memory['PID'].tolist()

    start_idx = None
    end_idx = None
    i = 0
    while True:
        try:
            if PID_list[i] is None:
                if start_idx is None:
                    start_idx = i
                end_idx = i
            else:
                if start_idx is not None:
                    size_list[start_idx:end_idx+1] = [sum(size_list[start_idx:end_idx+1])]
                    PID_list[start_idx:end_idx+1] = [None]
                    start_idx = None
                    end_idx = None
            i += 1
        except IndexError:
            break
    
    if start_idx is not None:
        size_list[start_idx:end_idx+1] = [sum(size_list[start_idx:end_idx+1])]
        PID_list[start_idx:end_idx+1] = [None]

    memory = update(size_list, PID_list)
    return memory


def main():
    results = []
    actions = []
    fit_methods = ['next', 'best']
    start_address = 0

    input_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'input.txt')

    with open(input_file_path, 'r') as file:
        lines = file.readlines()
        num_processes, memory_size = map(int, lines[0].split())
        for line in lines[1:]:
            p, o, a = line.split()
            actions.append((p, o, int(a)))
        file.close()


    print(f'start address = {start_address}')
    for fit_method in fit_methods:
        memory = pd.DataFrame([[1, start_address, memory_size, None]], 
                            columns=['partition', 'start address', 'size', 'PID'])
        if fit_method == 'next':
            last_search_idx = 0
            waiting_list = []
            print(f'Next Fit')

            for action in actions:
                print(f'PID: {action[0]}, operation: {action[1]}, amount: {action[2]}\n')
                print('waiting list before processing a request')
                print(waiting_list)
                print('before processing a request')
                print(memory, '\n')

                p_num, operation, amount = action

                if operation == 'in':
                    size_list = memory['size'].tolist()
                    PID_list = memory['PID'].tolist()
                    status = CircularList(list(zip(size_list, PID_list)))
                    status.current_index = last_search_idx
                    IsAllocated = False

                    for _ in range(len(status)):
                        partition_m_size, PID = next(status)
                        if partition_m_size >= amount and PID is None:
                            insertion_index = status.current_index - 1
                            last_search_idx = status.current_index
                            if size_list[insertion_index] > amount:
                                size_list[insertion_index] -= amount
                            else:
                                size_list.pop(insertion_index)
                                PID_list.pop(insertion_index)
                            size_list.insert(insertion_index, amount)
                            PID_list.insert(insertion_index, p_num)
                            memory = update(size_list, PID_list)
                            IsAllocated = True
                            break

                    if not IsAllocated:
                        waiting_list.append((p_num, amount))

                if operation == 'out':
                    try:
                        remove_idx = memory[memory['PID'] == p_num].index[0]
                        size_list = memory['size'].tolist()
                        PID_list = memory['PID'].tolist()
                        PID_list[remove_idx] = None
                        memory = update(size_list, PID_list)
                    except IndexError:
                        pass

                    for i, (p, _) in enumerate(waiting_list):
                        if p == p_num:
                            del waiting_list[i]
                
                if operation == 'cpn':
                    size_list = memory['size'].tolist()
                    PID_list = memory['PID'].tolist()

                    non_hole_sizes = [size for size, PID in zip(size_list, PID_list) if PID is not None]
                    non_hole_PIDs = [PID for PID in PID_list if PID is not None]

                    size_list = non_hole_sizes + [memory_size - sum(non_hole_sizes)]
                    PID_list = non_hole_PIDs + [None]

                    memory = update(size_list, PID_list)
                
                if operation == 'exit':
                    results.append((len(memory), np.mean(memory['size']), fit_method))
                    break

                print('waiting list after processing a request')
                print(waiting_list)
                print('after processing a request, before coalescing')
                print(memory)
                memory = coalescing_holes(memory)
                print('\nafter coalescing')
                print(memory)

                if waiting_list:
                    for p_num, amount in waiting_list:
                        size_list = memory['size'].tolist()
                        PID_list = memory['PID'].tolist()
                        status = CircularList(list(zip(size_list, PID_list)))
                        status.current_index = last_search_idx

                        for _ in range(len(status)):
                            partition_m_size, PID = next(status)
                            if partition_m_size >= amount and PID is None:
                                insertion_index = status.current_index - 1
                                last_search_idx = status.current_index
                                if size_list[insertion_index] > amount:
                                    size_list[insertion_index] -= amount
                                else:
                                    size_list.pop(insertion_index)
                                    PID_list.pop(insertion_index)
                                size_list.insert(insertion_index, amount)
                                PID_list.insert(insertion_index, p_num)
                                memory = update(size_list, PID_list)
                                waiting_list.remove((p_num, amount))
                
                print('\nafter allocating waiting processes')
                print(memory)
                print('---------------------------------\n')

        if fit_method == 'best':
            waiting_list = []
            print(f'\n\n\n\n\n\n\n\nBest Fit')

            for action in actions:
                print(f'PID: {action[0]}, operation: {action[1]}, amount: {action[2]}\n')
                print('waiting list before processing a request')
                print(waiting_list)
                print('before processing a request')
                print(memory, '\n')
                
                p_num, operation, amount = action

                if operation == 'in':
                    PID_list = memory['PID'].tolist()
                    size_list = sorted([(size, idx) for idx, (size, PID) in enumerate(zip(list(memory['size']), PID_list)) if size >= amount and PID is None])
                    if size_list:
                        insertion_index = size_list[0][1]
                        size_list = memory['size'].tolist()
                        if size_list[insertion_index] > amount:
                            size_list[insertion_index] = size_list[insertion_index] - amount
                        else:
                            size_list.pop(insertion_index)
                            PID_list.pop(insertion_index)
                        size_list.insert(insertion_index, amount)
                        PID_list.insert(insertion_index, p_num)
                        memory = update(size_list, PID_list)
                    else:
                        waiting_list.append((p_num, amount))
                
                if operation == 'out':
                    try:
                        remove_idx = memory[memory['PID'] == p_num].index[0]
                        size_list = memory['size'].tolist()
                        PID_list = memory['PID'].tolist()
                        PID_list[remove_idx] = None
                        memory = update(size_list, PID_list)
                    except IndexError:
                        pass

                    for i, (p, _) in enumerate(waiting_list):
                        if p == p_num:
                            del waiting_list[i]

                if operation == 'cpn':
                    size_list = memory['size'].tolist()
                    PID_list = memory['PID'].tolist()

                    non_hole_sizes = [size for size, PID in zip(size_list, PID_list) if PID is not None]
                    non_hole_PIDs = [PID for PID in PID_list if PID is not None]

                    size_list = non_hole_sizes + [memory_size - sum(non_hole_sizes)]
                    PID_list = non_hole_PIDs + [None]

                    memory = update(size_list, PID_list)
                
                if operation == 'exit':
                    results.append((len(memory), np.mean(memory['size']), fit_method))
                    break
                
                print('waiting list after processing a request')
                print(waiting_list)
                print('after processing a request, before coalescing')
                print(memory)
                memory = coalescing_holes(memory)
                print('\nafter coalescing')
                print(memory)

                if waiting_list:
                    for p_num, amount in waiting_list:
                        PID_list = memory['PID'].tolist()
                        size_list = sorted([(size, idx) for idx, (size, PID) in enumerate(zip(list(memory['size']), PID_list)) if size >= amount and PID is None])
                        if size_list:
                            insertion_index = size_list[0][1]
                            size_list = memory['size'].tolist()
                            if size_list[insertion_index] > amount:
                                size_list[insertion_index] = size_list[insertion_index] - amount
                            else:
                                size_list.pop(insertion_index)
                                PID_list.pop(insertion_index)
                            size_list.insert(insertion_index, amount)
                            PID_list.insert(insertion_index, p_num)
                            memory = update(size_list, PID_list)
                            waiting_list.remove((p_num, amount))
                
                print('\nafter allocating waiting processes')
                print(memory)
                print('---------------------------------\n')


        print('\n\n최종 결과')   
        for result in results:
            print(f'메모리 partition 개수: {result[0]}, 평균 partition 크기: {result[1]}, fit method: {result[2]}-fit')
        

if __name__ == '__main__':
    input = input('Do you want to generate new inputs? (y/n): ')
    if input == 'y':
        generator = TestCaseGenerator()
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'input.txt')
        generator.save_to_file(save_path)
    elif input == 'n':
        pass
    else:
        print('Invalid input')
        exit(1)

    main()