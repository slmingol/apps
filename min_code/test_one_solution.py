"""
Run solutions from one problem.
"""

import io
import json
import logging
import math
import numpy as np
import os
import pprint
import sys
import testing_util as test_util
import time

# for timing debugging
from datetime import datetime, date
from tqdm import tqdm

from typing import List

def print_results(results, num_progs):
    res = []
    for index in results:
       res.extend(results[index])
    tmp_results = res
    tmp_results = np.copy(tmp_results)
    compile_errors = len(tmp_results[tmp_results==-2])
    runtime_errors = len(tmp_results[tmp_results==-1])
    successes = tmp_results[tmp_results>=0]
    print(f"number of compile errors = {compile_errors} avg amount = {compile_errors / num_progs}")
    print(f"number of runtime errors = {runtime_errors} avg = {runtime_errors / num_progs}")
    print(f"number of test cases run = {len(successes)} ACC (correct / total) = {np.sum(successes) / num_progs}")



def main(args):

    argsdict = vars(args)
    print(pprint.pformat(argsdict))

    with open(args.test_loc, "r") as f:
        problems = json.load(f)

    print(len(problems))
    gpt_codes = {}
    gpt_bleu = {}
    gpt_codebleu = {}
    results = {}
    codes_loc = os.path.join(args.save, f"all_codes.json")
    if not os.path.exists(codes_loc):
        codes_loc = os.path.join(args.save, f"gpt_{args.start}-{args.end}_codes.json")

    if os.path.exists(codes_loc):
        results_loc = os.path.join(args.save, f"gpt2_all_results.json") 
    else:
        results_loc = os.path.join(args.save, f"gpt2_{args.start}-{args.end}_results.json") 
    print(codes_loc, results_loc)

    with open(codes_loc, "r") as f: 
        gpt_codes = json.load(f)

    if args.index:
        problems = [problems[args.index]]
    else:
        if args.start > len(problems) or args.start < 0:
            print(f"start index {args.start} > number of problems {len(problems)}")
            return
        start = args.start
        if args.end is None or args.end > len(problems):
            end = len(problems)
        else:
            end = args.end
        problems = problems[start:end]

    if args.stop_early:
        problems = problems[:args.stop_early]

    # main eval loop
    for index, problem in enumerate(tqdm(problems)):
        try:
            if args.debug:
                print(f"\n\nproblem path = {problem}")
            output_str = gpt_codes[str(index+args.start)]
        except:
            print("CANNOT FIND OUTPUT_STR FOR", problem)
            continue
        prob_path = os.path.join(args.root, problem)

        with open(os.path.join(prob_path, "solutions.json"), "r") as f:
            sols = json.load(f)
        
        if not os.path.exists(args.save):
            os.makedirs(args.save)

        res = []
        for o_idx, o in enumerate(output_str):
            if args.debug:
                print(f"\nTesting solution {o_idx}")
            curr_res = [-2]
            try:
                curr_res = test_util.run_test(prob_path=prob_path, test=o, debug=args.debug)
                fixed = []
                for e in curr_res:
                    if isinstance(e, np.ndarray):
                       e = e.item(0)
                    if isinstance(e, np.bool_):
                        e = bool(e)
                    fixed.append(e)
                curr_res = fixed
                if not np.all(curr_res):
                    print(f"Results were not all True: {curr_res}")
            except Exception as e:
                print(f"test framework exception = {repr(e)}{e}\n")
                break
            finally:
                assert isinstance(curr_res, list)
                res.append(curr_res)

        if args.debug:
            print(f"\nHow to read results [-2] = compile error, [-1] = runtime error [False] = failed test case [True] = passed test case")
            #print(f"results = {res}")

 
        results[index+args.start+args.index] = res
        
        with open(results_loc, "w") as f:
            try:
                print("saving")
                f.write(json.dumps(results))
            except Exception as e:
                import pdb; pdb.set_trace()
                print("didn't save")



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Language Modelling on Code")
    parser.add_argument("-t","--test_loc", default="../data_split/test.json", type=str, help="path to the json containing problem paths to be evaluated.")
    parser.add_argument("-r","--root", default="../", type=str, help="where the data is stored.")
    parser.add_argument("-s","--start", default=0, type=int)
    parser.add_argument("-e","--end", default=None, type=int)
    parser.add_argument("-i", "--index", default=0, type=int)
    parser.add_argument("-lp","--load_prev", action="store_true")
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("--save", type=str, default="../results_all")
    parser.add_argument("--index-override", default=None, type=int)
    parser.add_argument("--stop-early", default=None, type=int)
 
    args = parser.parse_args()

    main(args)
