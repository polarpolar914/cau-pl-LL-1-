import sys
import os
from Parser import Parser

if __name__ == "__main__":
    v = "-v" in sys.argv # -v 옵션 여부
    t = "-t" in sys.argv # -t 테스트용 트리 출력 여부, 변수에 대입할 값 출력 여부
    file = sys.argv[-1] # 파서가 처리할 파일 명

    # 파일이 존재하는지 확인
    if not os.path.exists(file):
        print(f'{file} 파일이 존재하지 않습니다.')
        exit(1)

    #파일 읽기
    with open(file, "r") as in_fp:
        code = in_fp.read()
        if len(code)>=1 and code[-1] == '\n': code = code[:-1]#마지막에 개행문자가 있으면 제거-오류방지
        p = Parser(code, verbose=v, test=t) #verbose: -v 옵션, test: 트리, 변수에 대입할 값 출력
        p.run()