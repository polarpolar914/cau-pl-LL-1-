#warning - missing right parenthesis, :=를 =로 쓴경우, stmts의 맨 마지막에 세미콜론이 있는 경우, 연산자가 여러개 연속해서 나오는 경우
#error - missing assignment operator, operator after assignment operator
#소수는 처리하도록 구현했음
#음수는 decimal에 포함하지 않으며 -는 연산자로만 인식하도록 구현했음 a:= -1;은 에러
#중간에 세미콜론이 없으면 앞뒷줄 연결되었다고 가정하고 연결된 상황에서의 에러 출력 - 각 stmt에 ;이 있는지 여부는 확인하지 않음
#-v 옵션 없을 때 그냥 중간에 (OK)나 경고 에러 메시지만 출력하도록 구현
#TODO - 음수, error일때도 cnt 출력?
import sys
from Parser import Parser

if __name__ == "__main__":
    v = "-v" in sys.argv
    t = "-t" in sys.argv
    file = sys.argv[-1]

    #테스트용 - 제출전 제거
    file = "test.txt"
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