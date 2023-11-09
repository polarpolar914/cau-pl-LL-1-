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
        self.list_message = []  # 에러, 경고 메시지를 저장하는 리스트

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
        error = "(Error) Unknown token - maybe invalid identifier(Does not follow the identifier name rules for language c) or character(!, @, etc.)"
        self.list_message.append(error)
        self.is_error = True
        self.go_to_next_statement()



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
                warning = "(Warning) Continuous identifiers - ignoring identifiers"+"("+self.token_string+")"
                self.list_message.append(warning)
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
                warning = "(Warning) Continuous constants - ignoring constants"+"("+self.token_string+")"
                self.list_message.append(warning)
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
                    warning = "(Warning) Multiple decimal points - ignoring decimal points and digits after the second decimal point("
                    self.is_warning = True
                    while self.index < len(self.source) and (
                            self.source[self.index] == "." or self.source[self.index].isdigit()):
                        warning += self.source[self.index]
                        self.index += 1
                    warning += ")"
                    self.list_message.append(warning)
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
            return True
        else:
            return False

    def detect_one_char_op(self):  # 한 글자 연산자를 감지하는 함수
        one_char_op = self.source[self.index]

        if one_char_op in "+-*/();:=":
            self.token_string = one_char_op
            self.index += 1
            if one_char_op == "+":
                self.next_token = TokenType.ADD_OP

                if (self.verbose): print(self.token_string)
                self.now_stmt += self.token_string

                self.op_cnt += 1

                self.ignore_multiple_op()
            elif one_char_op == "-":
                self.next_token = TokenType.SUB_OP

                if (self.verbose): print(self.token_string)
                self.now_stmt += self.token_string

                self.op_cnt += 1

                self.ignore_multiple_op()
            elif one_char_op == "*":
                self.next_token = TokenType.MULT_OP

                if (self.verbose): print(self.token_string)
                self.now_stmt += self.token_string

                self.op_cnt += 1

                self.ignore_multiple_op()
            elif one_char_op == "/":
                self.next_token = TokenType.DIV_OP

                if (self.verbose): print(self.token_string)
                self.now_stmt += self.token_string

                self.op_cnt += 1

                self.ignore_multiple_op()
            elif one_char_op == ";":
                self.next_token = TokenType.SEMI_COLON

                if (self.verbose): print(self.token_string)
                self.now_stmt += self.token_string

            elif one_char_op == "(":
                self.next_token = TokenType.LEFT_PAREN

                if (self.verbose): print(self.token_string)
                self.now_stmt += self.token_string

                if self.before_token == TokenType.IDENT: # 식별자 다음에 (가 나올 때 - error
                    error = "(Error) There is left parenthesis after identifier"
                    self.list_message.append(error)
                    self.is_error = True

                    self.ignore_multiple_op()
                    self.go_to_next_statement()
                    return True

                self.ignore_multiple_op()
            elif one_char_op == ")":
                self.next_token = TokenType.RIGHT_PAREN

                if (self.verbose): print(self.token_string)
                self.now_stmt += self.token_string

                self.ignore_blank()
            elif one_char_op == "=" or one_char_op == ":":  # =나 :가 나올 때
                self.next_token = TokenType.ASSIGN_OP
                # :=를 =로 쓴경우 - warning
                # :=를 :로 쓴경우 - warning
                # :=로 썼다고 가정하고 계속 진행
                self.token_string = ":="

                if (self.verbose): print(self.token_string)
                self.now_stmt += self.token_string

                if one_char_op == "=":
                    warning = "(Warning) Using = instead of := ==> assuming :="
                    self.list_message.append(warning)
                else:
                    warning = "(Warning) Using : instead of := ==> assuming :="
                    self.list_message.append(warning)
                self.is_warning = True
            return True
        else:
            return False

    def ignore_blank(self):
        while self.index < len(self.source) and ord(self.source[self.index]) <= 32:
            # 공백이면 self.index를 1 증가시키고 self.now_stmt에 공백 추가
            # 공백이 아니면 self.source에서 self.source[self.index]를 제거
            if self.source[self.index] == " ":
                self.now_stmt += " "
                self.index += 1
            else:
                self.source = self.source[:self.index] + self.source[self.index + 1:]

    def ignore_multiple_op(self):  # 연산자가 여러개 연속해서 나올 때 - warning
        self.ignore_blank()
        if self.index < len(self.source) and self.source[self.index] in "+-*/:=":
            # 연산자가 여러개 연속해서 나올 때 - warning
            # )다음에는 당연히 연산자가 나올 수 있으므로 )가 아닐 때만 경고
            warning = "(Warning) Using multiple operators(operater or left_paren) ==> ignoring multiple operators except the first one("
            self.is_warning = True
            while self.index < len(self.source) and self.source[self.index] in "+-*/:=)":
                self.index += 1
                warning += self.source[self.index - 1]

                # ignore_blank() 대용
                while self.index < len(self.source) and ord(self.source[self.index]) <= 32:
                    self.now_stmt += " "
                    warning += " "
                    self.index += 1
            warning += ")"
            self.list_message.append(warning)

    def op_after_assign_op(self):  #:= 다음에 연산자가 나올 때 - error
        self.ignore_blank()
        if self.index < len(self.source) and self.source[self.index] in "+-*/:=;)":
            # 대입 연산자 이후 다른 연산자가 나올때 - error
            error = "(Error) Operator(operater or right_paren, semi_colon) after assignment operator"
            self.list_message.append(error)
            self.is_error = True
            self.go_to_next_statement()
            return True
        else:
            return False

    def go_to_next_statement(self):  # 다음 statement로 이동 - error발생시 파싱을 계속 할수 없으므로 lexer를 변형한 이 함수를 사용
        paren = ""
        while self.index < len(self.source) and self.next_token != TokenType.SEMI_COLON and self.next_token != TokenType.END:
            self.before_token = self.next_token
            self.ignore_blank()  # 공백 무시
            check = self.detect_EOF()  # 파일의 끝을 감지
            if check: continue

            check = self.detect_id()  # 식별자를 감지
            if check:
                # 선언되지 않은 식별자가 나왔을 때 - error
                # 원래는 파서가 발견해야하는 오류 이지만 이미 앞에서 오류가 발생하여 파싱이 중단되었을 경우에는 Lexer가 발견해야함
                if self.token_string not in self.symbol_table:
                    error = "(Error) Using undeclared identifier"
                    self.list_message.append(error)
                    self.is_error = True
                continue

            check = self.detect_const()  # 상수를 감지
            if check: continue

            check = self.detect_two_cahr_op()  # 두 글자 연산자를 감지
            if check: continue

            check = self.detect_one_char_op()  # 한 글자 연산자를 감지
            if check:
                if self.next_token == TokenType.LEFT_PAREN:
                    paren += "("
                elif self.next_token == TokenType.RIGHT_PAREN:
                    if paren == "" or paren[-1] != "(":
                        # 왼쪽 괄호가 없는데 오른쪽 괄호가 나왔을 때 - error
                        error = "(Error) Missing left parenthesis"
                        self.list_message.append(error)
                        self.is_error = True
                    else:
                        paren = paren[:-1]
                continue
        if paren != "" and paren[-1] == "(":
            # 괄호가 닫히지 않은 것 - warning
            warning = "(Warning) Missing right parenthesis"
            self.list_message.append(warning)
            self.is_warning = True

            if self.now_stmt[-1] == ";":
                self.now_stmt = self.now_stmt[:-1] + ");"
            else:
                self.now_stmt += ");"

        if self.next_token == TokenType.SEMI_COLON and self.index == len(self.source):
            # 세미콜론이 나왔는데 파일의 끝이면 - warning
            warning = "(Warning) There is semicolon at the end of the statements ==> ignoring semicolon"
            self.list_message.append(warning)
            self.is_warning = True
            self.index += 1

    def print_stmt_and_cnt(self):
        if not self.verbose:
            print(self.now_stmt)
            # -v 옵션 없을 때
            # ex) ID: 2; CONST: 1; OP: 1;
            print(f"ID: {self.id_cnt}; CONST: {self.const_cnt}; OP: {self.op_cnt};")

            for i in self.list_message:
                print(i)

            if self.is_error == True or self.is_warning == True:
                print()

                self.now_stmt = ""

    def print_remaining_code(self): #테스트용 함수

        print("\n---------remaining source code---------")
        print(self.source[self.index:])
        print("---------------------------------------")
