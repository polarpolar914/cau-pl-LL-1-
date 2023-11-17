from TokenType import TokenType
import re


class Lexer:
    def __init__(self, input_source, verbose=False):
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
        tmp_flag = False #위의 두 경우를 구분하기 위한 임시 플래그
        if self.before_token == TokenType.IDENT and self.source[self.index - 1] != " ":
            #식별자에 허용되지 않은 문자가 포함되었을 때 - error
            #직전 토큰이 식별자로 인식되었고 그 식별자 다음 공백이 존재하지 않으며 식별자 다음 온 문자가 연산자와 같은 문법상 가능한 문자가 아닌 경우
            error = "(Error) Unknown token - invalid identifier(Does not follow the identifier name rules for language c) (" + self.token_string
            self.next_token = TokenType.IDENT #식별자로 인식
        else:
            # ! @ 같은 이상한 문자가 포함되었을때
            tmp_flag = True
            error = "(Error) Unknown token - invalid character(!, @, etc.) or string with invalid character ("
            self.next_token = TokenType.UNKNOWN #식별자가 아닌 경우 UNKNOWN으로 설정
        while self.index < len(self.source) and self.source[self.index] not in "+-*/();:= ": #연산자나 공백이 나올 때까지 invalid한 문자열이나 식별자로 간주
            error += self.source[self.index]
            self.token_string += self.source[self.index]
            if self.verbose: print(self.token_string)
            self.now_stmt += self.source[self.index]
            self.index += 1
        if tmp_flag: error = self.after_invalid_char(error)
        error += ")"
        self.list_message.append(error)
        self.is_error = True
        self.go_to_next_statement()
        if self.next_token != TokenType.SEMI_COLON: self.lexical()
    def detect_EOF(self):  # 파일의 끝을 감지하는 함수
        if self.index >= len(self.source):
            self.token_string = "EOF"
            self.next_token = TokenType.END
            if self.verbose: print(self.token_string)
            return True
        else:
            return False

    def detect_id(self):  # 식별자를 감지하는 함수
        ident_match = re.match(r"[a-zA-Z_][a-zA-Z0-9_]*", self.source[self.index:]) #정규표현식으로 식별자를 감지
        if ident_match:#식별자가 나왔을 때
            self.token_string = ident_match.group() #token_string에 식별자 문자열 저장
            if self.before_token == TokenType.IDENT: # 식별자가 연속해서 나올 때 - warning
                # 식별자가 연속해서 나올 때 - warning
                warning = "(Warning) Continuous identifiers - ignoring identifiers"+"("

                if self.index < len(self.source) and self.source[self.index] not in "+-*/();:= ": #식별자가 끝날때 까지
                    while self.index < len(self.source) and self.source[self.index] not in "+-*/();:= ":
                        warning += self.source[self.index]
                        self.index += 1

                warning += ")" #warning 메시지 저장

                self.list_message.append(warning)
                self.is_warning = True #warning 발생 여부 플래그 설정
                # 뒤에 나온 식별자는 무시
                # 뒤에 나온 식별자가 정의되었는지 여부는 확인하지 않음 - 해당 에러도 출력하지 않음
                self.index += len(self.token_string)
                self.ignore_blank()
                self.lexical()
                return True
            else:  # 식별자가 연속해서 나오지 않을 때
                self.next_token = TokenType.IDENT #다음 토큰을 식별자로 설정


                if (self.verbose): print(self.token_string) #verbose 옵션에 따라 출력
                self.now_stmt += self.token_string #현재 파싱 중인 statement에 식별자 추가

                self.index += len(self.token_string) #인덱스 증가

                if self.check_id_with_invaild_char(): #식별자에 허용되지 않은 문자가 포함되었을 때 - error
                    self.go_to_next_statement()
                    if self.next_token != TokenType.SEMI_COLON: self.lexical()
                else:
                    self.id_cnt += 1

                # 식별자가 정의되지 않았을 때 "Unknown"으로 설정
                if self.token_string not in self.symbol_table and not self.is_error: self.symbol_table[self.token_string] = "Unknown"

                return True
        else:
            return False

    def detect_const(self):  # 상수를 감지하는 함수
        const_match = re.match(r'-?\d+(\.\d+)?', self.source[self.index:]) #정규표현식으로 상수를 감지
        if const_match:#상수가 나왔을 때
            self.token_string = const_match.group()#token_string에 상수 문자열 저장

            if self.check_id_start_with_digit(self.token_string): #식별자가 숫자로 시작하는지 확인
                # 식별자가 숫자로 시작하면 - error
                # 오류 메시지는 check_id_start_with_digit()에서 저장
                self.go_to_next_statement() #다음 statement로 이동
                if self.next_token != TokenType.SEMI_COLON: self.lexical() #세미콜론이 아니면 다음 토큰을 읽어옴
                return True

            if self.before_token == TokenType.CONST:#상수가 연속해서 나올 때 - warning
                warning = "(Warning) Continuous constants - ignoring constants"+"("+self.token_string+")" #warning 메시지 저장
                self.list_message.append(warning) #warning 메시지 저장
                self.is_warning = True
                # 뒤에 나온 상수는 무시
                self.index += len(self.token_string)
                self.ignore_blank()
                self.lexical()
                return True
            else:#상수가 연속해서 나오지 않을 때
                self.next_token = TokenType.CONST #다음 토큰을 상수로 설정

                if (self.verbose): print(self.token_string) #verbose 옵션에 따라 출력
                self.now_stmt += self.token_string #현재 파싱 중인 statement에 상수 추가

                self.index += len(self.token_string) #인덱스 증가
                self.const_cnt += 1 #상수 개수 증가
                if self.index < len(self.source) and self.source[self.index] == "." and "." in self.token_string:
                    # 소수점이 여러개일 때 - warning
                    # 두번째 소수점 이후 - 앞으로 파싱할 부분이므로 수정 가능
                    # 두번째 소수점 이하는 무시
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
        two_char_op = self.source[self.index:self.index + 2] #두 글자 연산자를 감지
        if two_char_op == ":=": #:=가 나왔을 때
            self.token_string = two_char_op #token_string에 := 저장
            self.next_token = TokenType.ASSIGN_OP #다음 토큰을 ASSIGN_OP으로 설정

            if (self.verbose): print(self.token_string) #verbose 옵션에 따라 출력
            self.now_stmt += self.token_string #현재 파싱 중인 statement에 := 추가

            self.index += 2 #인덱스 증가

            self.op_after_assign_op()  #:= 다음에 연산자가 나올 때 - error
            return True
        else:
            return False

    def detect_one_char_op(self):  # 한 글자 연산자를 감지하는 함수
        one_char_op = self.source[self.index] #한 글자 연산자를 감지

        if one_char_op in "+-*/();:=": #연산자가 나왔을 때
            self.token_string = one_char_op #token_string에 연산자 저장
            self.index += 1 #인덱스 증가
            if one_char_op == "+": #연산자에 따라 다음 토큰 설정
                self.next_token = TokenType.ADD_OP #다음 토큰을 ADD_OP으로 설정

                if (self.verbose): print(self.token_string) #verbose 옵션에 따라 출력
                self.now_stmt += self.token_string #현재 파싱 중인 statement에 연산자 추가

                self.op_cnt += 1 #연산자 개수 증가

                self.ignore_multiple_op() #연산자가 여러개 연속해서 나올 때 - warning
            elif one_char_op == "-": #연산자에 따라 다음 토큰 설정
                self.next_token = TokenType.ADD_OP #다음 토큰을 ADD_OP으로 설정

                if (self.verbose): print(self.token_string) #verbose 옵션에 따라 출력
                self.now_stmt += self.token_string #현재 파싱 중인 statement에 연산자 추가

                self.op_cnt += 1 #연산자 개수 증가

                self.ignore_multiple_op() #연산자가 여러개 연속해서 나올 때 - warning
            elif one_char_op == "*": # 연산자에 따라 다음 토큰 설정
                self.next_token = TokenType.MULT_OP #다음 토큰을 MULT_OP으로 설정

                if (self.verbose): print(self.token_string) #verbose 옵션에 따라 출력
                self.now_stmt += self.token_string #현재 파싱 중인 statement에 연산자 추가

                self.op_cnt += 1 #연산자 개수 증가

                self.ignore_multiple_op() #연산자가 여러개 연속해서 나올 때 - warning
            elif one_char_op == "/": # 연산자에 따라 다음 토큰 설정
                self.next_token = TokenType.MULT_OP #다음 토큰을 MULT_OP으로 설정

                if (self.verbose): print(self.token_string) #verbose 옵션에 따라 출력
                self.now_stmt += self.token_string #현재 파싱 중인 statement에 연산자 추가

                self.op_cnt += 1 #연산자 개수 증가

                self.ignore_multiple_op() #연산자가 여러개 연속해서 나올 때 - warning
            elif one_char_op == ";": # 연산자에 따라 다음 토큰 설정
                self.next_token = TokenType.SEMI_COLON #다음 토큰을 SEMI_COLON으로 설정

                if (self.verbose and self.index < len(self.source)): print(self.token_string)  # verbose 옵션에 따라 출력
                self.now_stmt += self.token_string #현재 파싱 중인 statement에 연산자 추가

            elif one_char_op == "(": # 연산자에 따라 다음 토큰 설정
                self.next_token = TokenType.LEFT_PAREN #다음 토큰을 LEFT_PAREN으로 설정

                if (self.verbose): print(self.token_string) #verbose 옵션에 따라 출력
                self.now_stmt += self.token_string #현재 파싱 중인 statement에 연산자 추가

                if self.before_token == TokenType.IDENT: # 식별자 다음에 (가 나올 때 - error
                    error = "(Error) There is left parenthesis after identifier" #error 메시지 저장
                    self.list_message.append(error) #error 메시지 저장
                    self.is_error = True #error 발생 여부 플래그 설정

                    self.ignore_multiple_op() #연산자가 여러개 연속해서 나올 때 - warning
                    self.go_to_next_statement() #다음 statement로 이동
                    if self.next_token != TokenType.SEMI_COLON: self.lexical() #세미콜론이 아니면 다음 토큰을 읽어옴
                    return True

                self.ignore_multiple_op() #연산자가 여러개 연속해서 나올 때 - warning
            elif one_char_op == ")":# 연산자에 따라 다음 토큰 설정
                self.next_token = TokenType.RIGHT_PAREN #다음 토큰을 RIGHT_PAREN으로 설정

                if (self.verbose): print(self.token_string) #verbose 옵션에 따라 출력
                self.now_stmt += self.token_string #현재 파싱 중인 statement에 연산자 추가

                self.ignore_blank() #공백 무시
            elif one_char_op == "=" or one_char_op == ":":  # =나 :가 나올 때
                self.next_token = TokenType.ASSIGN_OP #다음 토큰을 ASSIGN_OP으로 설정
                # :=를 =로 쓴경우 - warning
                # :=를 :로 쓴경우 - warning
                # :=로 썼다고 가정하고 계속 진행
                self.token_string = ":="

                if (self.verbose): print(self.token_string)
                self.now_stmt += self.token_string

                if one_char_op == "=": # :=를 =로 쓴경우 - warning
                    warning = "(Warning) Using = instead of := ==> assuming :="
                    self.list_message.append(warning)
                elif one_char_op == ":": # :=를 :로 쓴경우 - warning
                    warning = "(Warning) Using : instead of := ==> assuming :="
                    self.list_message.append(warning)
                self.is_warning = True

                self.op_after_assign_op() #:= 다음에 연산자가 나올 때 - error
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
        if self.index < len(self.source) and self.source[self.index] in "+-*/:=)":
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
            error = "(Error) Operator(operater or right_paren, semi_colon, assign_op) after assignment operator"
            self.list_message.append(error)
            self.is_error = True
            self.go_to_next_statement()
            if self.next_token != TokenType.SEMI_COLON: self.lexical()
            return True
        else:
            return False

    def check_id_start_with_digit(self, const): #식별자가 숫자로 시작하는지 확인하는 함수
        # 식별자가 숫자로 시작하면 - error
        if self.index + len(const) < len(self.source) and self.source[self.index + len(const)] not in ".+-*/();:= ":
            self.now_stmt += const
            self.token_string = const
            self.index += len(const)
            error = "(Error) Identifier starts with digit (" + const
            while self.index < len(self.source) and self.source[self.index] not in ".+-*/();:= ":
                error += self.source[self.index]
                self.now_stmt += self.source[self.index]
                self.token_string += self.source[self.index]

                if self.verbose: print(self.token_string)
                self.index += 1
            error += ")"
            self.list_message.append(error)
            self.is_error = True

            self.id_cnt += 1
            self.symbol_table[self.token_string] = "invalid identifier name"
            self.next_token = TokenType.IDENT
            return True
        else:
            return False

    def check_id_with_invaild_char(self): #식별자에 허용되지 않은 문자가 포함되었는지 확인하는 함수
        # 식별자에 허용되지 않은 문자가 포함되었을 때 - error
        if self.index < len(self.source) and self.source[self.index] not in "+-*/();:= ":
            while self.index < len(self.source) and self.source[self.index] not in "+-*/();:= ":
                self.now_stmt += self.source[self.index]
                self.token_string += self.source[self.index]
                if self.verbose: print(self.token_string)
                self.index += 1
            self.is_error = True

            self.symbol_table[self.token_string] = "invalid identifier name"
            error = "(Error) Unknown token - invalid identifier(Does not follow the identifier name rules for language c) (" + self.token_string + ")"
            self.list_message.append(error)
            self.next_token = TokenType.IDENT
            self.id_cnt += 1
            return True
        else:
            return False
    def go_to_next_statement(self):  # 다음 statement로 이동 - error발생시 파싱을 계속 할수 없으므로 lexer를 변형한 이 함수를 사용
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
                    error = "(Error) Using undeclared identifier(" + self.token_string + ")"
                    self.list_message.append(error)
                    self.is_error = True
                continue

            check = self.detect_const()  # 상수를 감지
            if check: continue

            check = self.detect_two_cahr_op()  # 두 글자 연산자를 감지
            if check: continue

            check = self.detect_one_char_op()  # 한 글자 연산자를 감지
            if check: continue

            # ! @ 같은 이상한 문자가 포함되었을때
            # c언어 식별자 규칙에 맞지 않을 때
            tmp_flag = False
            if self.before_token == TokenType.IDENT and self.source[self.index - 1] != " ":
                error = "(Error) Unknown token - invalid identifier(Does not follow the identifier name rules for language c) (" + self.token_string
                self.next_token = TokenType.IDENT
            else:
                tmp_flag = True
                error = "(Error) Unknown token - invalid character(!, @, etc.) or string with invalid character ("
                self.next_token = TokenType.UNKNOWN
            while self.index < len(self.source) and self.source[self.index] not in "+-*/();:=    ":
                error += self.source[self.index]
                self.now_stmt += self.source[self.index]
                self.token_string += self.source[self.index]
                if self.verbose: print(self.token_string)
                self.index += 1
            if tmp_flag: error = self.after_invalid_char(error)
            else:
                self.symbol_table[self.token_string] = "invalid identifier name"
                self.id_cnt += 1
            error += ")"
            self.list_message.append(error)
            self.is_error = True

        if self.next_token == TokenType.SEMI_COLON and self.index == len(self.source):
            # 세미콜론이 나왔는데 파일의 끝이면 - warning
            warning = "(Warning) There is semicolon at the end of the program ==> ignoring semicolon"
            self.now_stmt = self.now_stmt[:-1]
            self.list_message.append(warning)
            self.is_warning = True
            self.index += 1
    def after_invalid_char(self, error):
        while self.index< len(self.source) and self.source[self.index] not in "+-*/();:= ":
            error += self.source[self.index]
            self.token_string += self.source[self.index]
            if self.verbose: print(self.token_string)
            self.now_stmt += self.source[self.index]
            self.index += 1

        if self.index >= len(self.source):
            return error

        if self.source[self.index] not in "+-*/();:= ":
                error += self.source[self.index]
                self.token_string += self.source[self.index]
                if self.verbose: print(self.token_string)
                self.now_stmt += self.source[self.index]
                self.index += 1
        return error
    def end_of_stmt(self):# statement마다 실행되는 함수

        if self.is_error and self.id_of_now_stmt in self.symbol_table and self.symbol_table[self.id_of_now_stmt] != "invalid identifier name":
            # 에러가 발생한 경우 - 해당 statement의 id를 Unknown으로 설정
            self.symbol_table[self.id_of_now_stmt] = "Unknown"

        if not self.verbose:#-v 옵션 없을 때
            print(self.now_stmt)#현재 파싱한 statement 출력
            # -v 옵션 없을 때
            # ex) ID: 2; CONST: 1; OP: 1;
            print(f"ID: {self.id_cnt}; CONST: {self.const_cnt}; OP: {self.op_cnt};")

            for i in self.list_message:#에러, 경고 메시지 출력
                print(i)

            if self.is_error == True or self.is_warning == True:
                print()

            if self.is_warning == False and self.is_error == False:  # 에러, 경고가 없을 때
                if not self.verbose: print("(OK)\n") #OK 출력

            # 다음 statement로 넘어가기 전에 now_stme, id_cnt, const_cnt, op_cnt, is_error, is_warning, list_message 초기화
            self.now_stmt = ""
            self.id_cnt, self.const_cnt, self.op_cnt = 0, 0, 0
            self.is_error, self.is_warning, self.before_token = False, False, None
            self.list_message = []

