from TokenType import TokenType
import re


class Lexer:
    def __init__(self, input_source, verbose=False, test=False):
        self.token_string = ""  # 현재 토큰의 문자열
        self.next_token = None  # 다음 토큰의 타입
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

    def lexical(self):  # 다음 토큰을 읽어오는 함수
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

        #위의 모든 경우에 해당하지 않으면 에러 - 잘못된 토큰 - !, @, # ... 등의 특수문자가 들어있거나 소수점이 여러개인 경우
        print("(Error) Invalid token - There may be invalid character(s) like !, @, # ...etc in the source code or deximal point(.) may be more than one")
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
            self.next_token = TokenType.IDENT
            if (self.verbose): print(self.token_string)
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
            if self.token_string.count('.') < 2:
                self.next_token = TokenType.CONST
                if (self.verbose): print(self.token_string)
                self.index += len(self.token_string)
                self.const_cnt += 1
                return True
        else:
            return False

    def detect_two_cahr_op(self):  # 두 글자 연산자를 감지하는 함수
        two_char_op = self.source[self.index:self.index + 2]
        if two_char_op == ":=":
            self.token_string = two_char_op
            self.next_token = TokenType.ASSIGN_OP
            if (self.verbose): print(self.token_string)
            self.index += 2
            self.ignore_blank()
            if self.index < len(self.source) and self.source[self.index] in "+-*/:=;)":
                # 대입 연산자 이후 다른 연산자가 나올때 - error
                print("(Error) Operator(operater or left_paren) after assignment operator")
                self.is_error = True
                self.go_to_next_statement()
                if self.id_of_now_stmt in self.symbol_table:
                    self.symbol_table[self.id_of_now_stmt] = "Unknown"

            return True
        else:
            return False

    def detect_one_char_op(self):  # 한 글자 연산자를 감지하는 함수
        one_char_op = self.source[self.index]
        if one_char_op in "+-*/();=":
            self.token_string = one_char_op
            if one_char_op == "+":
                self.next_token = TokenType.ADD_OP
                if (self.verbose): print(self.token_string)
                self.op_cnt += 1
            elif one_char_op == "-":
                self.next_token = TokenType.SUB_OP
                if (self.verbose): print(self.token_string)
                self.op_cnt += 1
            elif one_char_op == "*":
                self.next_token = TokenType.MULT_OP
                if (self.verbose): print(self.token_string)
                self.op_cnt += 1
            elif one_char_op == "/":
                self.next_token = TokenType.DIV_OP
                if (self.verbose): print(self.token_string)
                self.op_cnt += 1
            elif one_char_op == ";":
                self.next_token = TokenType.SEMI_COLON
                if (self.verbose): print(self.token_string)
            elif one_char_op == "(":
                self.next_token = TokenType.LEFT_PAREN
                if (self.verbose): print(self.token_string)
            elif one_char_op == ")":
                self.next_token = TokenType.RIGHT_PAREN
                if (self.verbose): print(self.token_string)
            elif one_char_op == "=":
                self.token_string = ":="
                self.next_token = TokenType.ASSIGN_OP
                if (self.verbose): print(self.token_string)
                print("(Warning) Using = instead of := ==> assuming :=")
                self.is_warning = True
            self.index += 1
            self.ignore_blank()
            if self.source[self.index - 1] != ")" and self.index < len(self.source) and self.source[
                self.index] in "+-*/:=":
                # 연산자가 여러개 연속해서 나올 때 - warning
                # )다음에는 당연히 연산자가 나올 수 있으므로 )가 아닐 때만 경고
                print(
                    "(Warning) Using multiple operators(operater or left_paren) ==> ignoring multiple operators except the first one")
                self.is_warning = True
                while self.index < len(self.source) and self.source[self.index] in "+-*/:=)":
                    self.index += 1
                    self.ignore_blank()
            return True
        else:
            return False

    def ignore_blank(self):
        while self.index < len(self.source) and ord(self.source[self.index]) <= 32:
            self.index += 1

    def go_to_next_statement(self):  # 다음 statement로 이동
        while self.index < len(self.source):
            if self.source[self.index] == ";":
                return
            self.index += 1
