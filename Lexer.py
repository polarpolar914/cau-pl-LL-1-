from TokenType import TokenType
import re


class Lexer:
    def __init__(self, input_source, verbose=False, test=False):
        self.token_string = ""  # 현재 토큰의 문자열
        self.next_token = None  # 다음 토큰의 타입
        self.before_token = None  # 이전 토큰의 타입
        self.source = input_source  # 입력받은 소스코드
        self.index = 0  # 현재 읽고 있는 문자의 인덱스
        self.id_cnt = 0  # 각 statement에서의 id, const, op의 개수
        self.const_cnt = 0
        self.op_cnt = 0
        self.verbose = verbose  # -v옵션에 따라 출력 방식 결정
        self.symbol_table = {}  # 변수의 이름과 값을 저장하는 심볼 테이블
        self.is_error = False  # 에러가 발생했는지 여부
        self.is_warning = False  # 경고가 발생했는지 여부
        self.id_of_now_stmt = None  # 현재 파싱 중인 statement의 id
        self.now_stmt = ""  # 현재 파싱 중인 statement

    def lexical(self):  # 다음 토큰을 읽어오는 함수
        self.before_token = self.next_token

        self.ignore_blank() #공백 무시

        check = self.detect_EOF() #파일의 끝을 감지
        if check: return

        check = self.detect_id() #식별자를 감지
        if check: return

        check = self.detect_const() #상수를 감지
        if check: return

        check = self.detect_two_cahr_op() #두 글자 연산자를 감지
        if check: return

        check = self.detect_one_char_op() #한 글자 연산자를 감지
        if check: return

        # ! @ 같은 이상한 문자가 포함되었을때
        # c언어 식별자 규칙에 맞지 않을 때
        print("(Error) Unknown token - maybe invalid identifier(Does not follow the identifier name rules for language c) or character(!, @, etc.)")
        self.is_error = True
        self.go_to_next_statement()
        self.print_stmt_and_cnt()



    def detect_EOF(self):  # 파일의 끝을 감지하는 함수
        if self.index >= len(self.source):
            self.token_string = "EOF"
            self.next_token = TokenType.END
            if self.verbose: print(self.token_string)
            return True
        else:
            return False

    def detect_id(self):  # 식별자를 감지하는 함수
        ident_match = re.match(r"[a-zA-Z_][a-zA-Z0-9_]*", self.source[self.index:])
        if ident_match:
            self.token_string = ident_match.group()
            if self.before_token == TokenType.IDENT: # 식별자가 연속해서 나올 때 - warning
                # 식별자가 연속해서 나올 때 - warning
                print("(Warning) Continuous identifiers - ignoring identifiers after the first one")
                self.is_warning = True
                # 뒤에 나온 식별자는 무시
                # 뒤에 나온 식별자가 정의되었는지 여부는 확인하지 않음 - 해당 에러도 출력하지 않음
                self.index += len(self.token_string)
                self.ignore_blank()
                self.lexical()
                return True
            else:  # 식별자가 연속해서 나오지 않을 때
                self.next_token = TokenType.IDENT

                if (self.verbose): print(self.token_string)
                self.now_stmt += self.token_string

                self.index += len(self.token_string)
                if self.token_string not in self.symbol_table: self.symbol_table[self.token_string] = "Unknown"
                self.id_cnt += 1
                return True
        else:
            return False

    def detect_const(self):  # 상수를 감지하는 함수
        const_match = re.match(r'-?\d+(\.\d+)?', self.source[self.index:])
        if const_match:
            self.token_string = const_match.group()
            if self.before_token == TokenType.CONST:#상수가 연속해서 나올 때 - warning
                print("(Warning) Continuous constants - ignoring constants after the first one")
                self.is_warning = True
                # 뒤에 나온 상수는 무시
                self.index += len(self.token_string)
                self.ignore_blank()
                self.lexical()
                return True
            else:#상수가 연속해서 나오지 않을 때
                self.next_token = TokenType.CONST

                if (self.verbose): print(self.token_string)
                self.now_stmt += self.token_string

                self.index += len(self.token_string)
                self.const_cnt += 1
                if self.index < len(self.source) and self.source[self.index] == ".":
                    # 소수점이 여러개일 때 - warning
                    # 두번째 소수점 이후 - 앞으로 파싱할 부분이므로 수정 가능
                    print(
                        "(Warning) Multiple decimal points - ignoring decimal points and digits in the token after second decimal point")
                    self.is_warning = True
                    while self.index < len(self.source) and (
                            self.source[self.index] == "." or self.source[self.index].isdigit()):
                        self.index += 1
                    self.ignore_blank()
            return True
        else:
            return False

    def detect_two_cahr_op(self):  # 두 글자 연산자를 감지하는 함수
        two_char_op = self.source[self.index:self.index + 2]
        if two_char_op == ":=":
            self.token_string = two_char_op
            self.next_token = TokenType.ASSIGN_OP

            if (self.verbose): print(self.token_string)
            self.now_stmt += self.token_string

            self.index += 2
            self.ignore_blank()
            if self.index < len(self.source) and self.source[self.index] in "+-*/:=;)":
                # 대입 연산자 이후 다른 연산자가 나올때 - error
                print("(Error) Operator(operater or right_paren) after assignment operator")
                self.is_error = True
                self.go_to_next_statement()
                self.print_stmt_and_cnt()
            return True
        else:
            return False

    def detect_one_char_op(self):  # 한 글자 연산자를 감지하는 함수
        one_char_op = self.source[self.index]
        if one_char_op in "+-*/();:=":
            self.token_string = one_char_op
            if one_char_op == "+":
                self.next_token = TokenType.ADD_OP

                if (self.verbose): print(self.token_string)
                self.now_stmt += self.token_string

                self.op_cnt += 1
            elif one_char_op == "-":
                self.next_token = TokenType.SUB_OP

                if (self.verbose): print(self.token_string)
                self.now_stmt += self.token_string

                self.op_cnt += 1
            elif one_char_op == "*":
                self.next_token = TokenType.MULT_OP

                if (self.verbose): print(self.token_string)
                self.now_stmt += self.token_string

                self.op_cnt += 1
            elif one_char_op == "/":
                self.next_token = TokenType.DIV_OP

                if (self.verbose): print(self.token_string)
                self.now_stmt += self.token_string

                self.op_cnt += 1
            elif one_char_op == ";":
                self.next_token = TokenType.SEMI_COLON

                if (self.verbose): print(self.token_string)
                self.now_stmt += self.token_string

            elif one_char_op == "(":
                self.next_token = TokenType.LEFT_PAREN

                if (self.verbose): print(self.token_string)
                self.now_stmt += self.token_string

            elif one_char_op == ")":
                self.next_token = TokenType.RIGHT_PAREN

                if (self.verbose): print(self.token_string)
                self.now_stmt += self.token_string

            elif one_char_op == "=":
                # =를 :=로 쓴경우 - warning
                # :=로 썼다고 가정하고 계속 진행
                self.token_string = ":="
                self.next_token = TokenType.ASSIGN_OP

                if (self.verbose): print(self.token_string)
                self.now_stmt += self.token_string

                print("(Warning) Using = instead of := ==> assuming :=")
                self.is_warning = True
            elif one_char_op == ":":
                # :를 :=로 쓴경우 - warning
                # :=로 썼다고 가정하고 계속 진행
                self.token_string = ":="
                self.next_token = TokenType.ASSIGN_OP

                if (self.verbose): print(self.token_string)
                self.now_stmt += self.token_string

                print("(Warning) Using : instead of := ==> assuming :=")
                self.is_warning = True
            self.index += 1
            self.ignore_blank()
            if self.source[self.index - 1] != ")" and self.index < len(self.source) and self.source[
                self.index] in "+-*/:=":
                # 연산자가 여러개 연속해서 나올 때 - warning
                # )다음에는 당연히 연산자가 나올 수 있으므로 )가 아닐 때만 경고
                print("(Warning) Using multiple operators(operater or left_paren) ==> ignoring multiple operators except the first one")
                self.is_warning = True
                while self.index < len(self.source) and self.source[self.index] in "+-*/:=)":
                    self.index += 1
                    self.ignore_blank()
            return True
        else:
            return False

    def ignore_blank(self):
        while self.index < len(self.source) and ord(self.source[self.index]) <= 32:
            self.now_stmt += " "
            self.index += 1

    def go_to_next_statement(self):  # 다음 statement로 이동
        while self.index < len(self.source):
            if self.source[self.index] == ";":
                return
            self.ignore_blank()  # 공백 무시
            self.detect_EOF()  # 파일의 끝을 감지
            self.detect_id()  # 식별자를 감지
            self.detect_const()  # 상수를 감지
            self.detect_two_cahr_op()  # 두 글자 연산자를 감지
            self.detect_one_char_op()  # 한 글자 연산자를 감지

    def print_stmt_and_cnt(self):
        if not self.verbose:
            print(self.now_stmt)
            # -v 옵션 없을 때
            # ex) ID: 2; CONST: 1; OP: 1;
            print(f"ID: {self.id_cnt}; CONST: {self.const_cnt}; OP: {self.op_cnt};")
