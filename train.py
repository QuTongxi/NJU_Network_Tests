import subprocess
import argparse

parser = argparse.ArgumentParser(description="训练脚本")
parser.add_argument("--runs", type=int, default=50, help="运行次数，默认50次")
args = parser.parse_args()


if __name__ == "__main__":
    MAX_RUNS = args.runs
    for i in range(1, MAX_RUNS+1):
        print(f"运行第 {i} 次")
        subprocess.run(["python", "main.py"])
