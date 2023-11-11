#warning - missing right parenthesis, :=를 =로 쓴경우, stmts의 맨 마지막에 세미콜론이 있는 경우, 연산자가 여러개 연속해서 나오는 경우
#error - missing assignment operator, operator after assignment operator
#소수는 처리하도록 구현했음
#음수는 decimal에 포함하지 않으며 -는 연산자로만 인식하도록 구현했음 a:= -1;은 에러
#에러나 경고 메시지는 파싱과정에서 발견되는 순서대로 출력한다. - 미 선언 변수에 대한 에러는 expression에서 발견되므로 expression에서 처리
#중간에 세미콜론이 없으면 앞뒷줄 연결되었다고 가정하고 연결된 상황에서의 에러 출력 - 각 stmt에 ;이 있는지 여부는 확인하지 않음
#-v 옵션 없을 때 그냥 중간에 (OK)나 경고 에러 메시지만 출력하도록 구현
#파싱 과정에서 발생하는 에러나 경고, 렉서가 생성하는 오류와 경고가 있다.
#신텍스 에러로 인해 파싱이 중단되는 경우, 파싱이 중단된 시점이후에 있는 파서가 발견할 수 있는 에러나 경고는 출력하지 않는다. - a:=1)1+1

#invalid identifier는 id 갯수에 불포함, result에도 출력 x
#TODO - 테스트 케이스 만들고 오류 있으면 수정 + 보고서 작성 , 괄호 섞였을때 연산자 중복 확인하기.
#TODO - go_next_stmt()에서 괄호처리, 연산자 다음 숫자나 숫자 다음 연산자일때 ;추가 처리, c언어 식별자 규칙 처리
#숫자로 시작하는 식별자 처리
import sys
import os
from Parser import Parser

if __name__ == "__main__":
    v = "-v" in sys.argv
    t = "-t" in sys.argv
    file = sys.argv[-1]


    #파일 존재 여부 확인
    # 확인하고 싶은 파일의 경로

    # 파일이 존재하는지 확인
    if not os.path.exists(file):
        print(f'{file} 파일이 존재하지 않습니다.')
        exit(1)

    #파일 읽기
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