#warning - missing right parenthesis, :=를 =로 쓴경우, stmts의 맨 마지막에 세미콜론이 있는 경우, 연산자가 여러개 연속해서 나오는 경우
#error - missing assignment operator, operator after assignment operator
#소수는 처리하도록 구현했음
#TODO - left 괄호 없음
#질문 할 것 - -v옵션 없을때 에러나 경고 출력하는지, ok출력하는지
import sys
from Parser import Parser

if __name__ == "__main__":
    v = "-v" in sys.argv
    t = "-t" in sys.argv
    file = sys.argv[-1]

    #테스트용 - 제출전 제거
    file = "test.py"
    v = False
    t = False

    with open(file, "r") as in_fp:
        code = in_fp.read()

        for i in range(len(code)-1, -1, -1): #코드의 맨 뒤에서부터 공백 제거 - statements의 맨 마지막에 세미콜론이 있는 경우를 판별하기 위한 전처리
            if ord(code[i]) <= 32:
                code = code[:i]
            else:
                break

        p = Parser(code, verbose=v, test=t) #verbose: -v 옵션, test: 트리, 변수에 대입할 값 출력

        code = code.replace("\n", "") #출력용으로 statement들을 저장
        p.statement_list = code.split(";")
        for i in range(len(p.statement_list)-1):
            p.statement_list[i] += ";"
        p.run()