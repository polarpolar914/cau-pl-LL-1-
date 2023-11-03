from Node import Node
from TokenType import TokenType
from Lexer import Lexer
from anytree import RenderTree
import re
class Parser(Lexer):#파서 클래스
    def __init__(self, input_source, verbose=False, test=False):#파서 생성자
        super().__init__(input_source, verbose=verbose, test=test)

        if input_source.replace(" ", "") == "":#입력받은 소스코드가 공백만 있을 때 - error
            print("(Error) Grammer of this LL(1) parser cannot generate empty source code")
            exit(1)
        self.test = test  # 파싱이 정상적으로 되었는지 확인하기 위한 트리 출력, 변수에 대입할 값이 제대로 계산되었는지 확인
        self.statement_list = []  # statement들을 저장하는 리스트 - 출력용
        self.statement_index = 0  # 출력용

    def error_recovery(self):
        print("Syntax error encountered. Trying to recover...")
        while self.index < len(self.source):
            if self.source[self.index] in ';+-*/()':
                return
            self.index += 1

    def factor(self, parent=None):
        node = Node("FACTOR", parent=parent)
        if self.next_token == TokenType.LEFT_PAREN:
            self.lexical()
            expr_node = self.expression(node)
            if self.next_token != TokenType.RIGHT_PAREN:
                #오른쪽 괄호가 없을 때 - warning
                self.is_warning = True
                print("(Warning) Missing right parenthesis ==> assuming right parenthesis at the end of statement")
                #해당 statement의 맨 오른쪽에 오른쪽 괄호가 있다고 가정하고 계속 진행함
                #LL(1) 파서이므로 오른쪽 괄호가 없다는 것은 이미 파싱한 부분이 아닌 앞으로 파싱할 부분(오른쪽)에 오류가 있다는 것임 - 에러출력 + 계속파싱
                #오른쪽 괄호가 있는 곳은 맨 오른쪽으로 가정, 맨오른쪽==해당 statement의 끝
                self.index += 1
                return node
            self.lexical()
        elif self.next_token == TokenType.IDENT or self.next_token == TokenType.CONST:
            Node(TokenType.get_name(self.next_token), value=self.token_string, parent=node)
            self.lexical()
        else:
            self.error_recovery()
        return node

    def factor_tail(self, parent=None):
        node = Node("FACTOR_TAIL", parent=parent)
        while self.next_token in (TokenType.MULT_OP, TokenType.DIV_OP):
            Node(TokenType.get_name(self.next_token), value=self.token_string, parent=node)
            self.lexical()
            self.factor(node)
        return node

    def term(self, parent=None):
        node = Node("TERM", parent=parent)
        self.factor(node)
        self.factor_tail(node)
        return node

    def term_tail(self, parent=None):
        node = Node("TERM_TAIL", parent=parent)
        while self.next_token in (TokenType.ADD_OP, TokenType.SUB_OP):
            Node(TokenType.get_name(self.next_token), value=self.token_string, parent=node)
            self.lexical()
            self.term(node)
        return node

    def expression(self, parent=None):
        node = Node("EXPRESSION", parent=parent)
        self.term(node)
        self.term_tail(node)

        RHS = node.preorder()
        term = ""
        for i in RHS:
            if re.compile(r'-?\d+(\.\d+)?').fullmatch(i):  #숫자일 때
                term += i
            elif i in "+-*/()":
                term += i
            elif i in self.symbol_table and self.symbol_table[i] != "Unknown":
                term += str(self.symbol_table[i])
            elif not i in self.symbol_table or self.symbol_table[i] == "Unknown":
                #정의되지 않은 변수 참조 - error - 에러이긴 하지만 syntax error가 아니라 semantic error이므로 파싱은 계속 진행
                print("(Error) Undefined variable is referenced")
                self.is_error = True
            else:
                print("Error: Invalid expression")
                return node, None
        try:
            result = eval(term)
            if(self.test):print(f"Result: {result}")
            return node, result
        except:
            return node, "Unknown"

    def statement(self, parent=None):
        if(not self.verbose):print(self.statement_list[self.statement_index])#현재 파싱 중인 statement 출력
        self.id_of_now_stmt = None
        self.statement_index += 1

        self.id_cnt, self.const_cnt, self.op_cnt = 0, 0, 0
        self.is_error, self.is_warning, self.warning_msg_list, self.error_msg_list = False, False, [], []
        node = Node("STATEMENT", parent=parent)
        if self.next_token == TokenType.IDENT:
            self.id_of_now_stmt = self.token_string
            if (self.token_string not in self.symbol_table) or (self.token_string in self.symbol_table and self.symbol_table[self.token_string] == None): self.symbol_table[self.token_string] = "Unknown"
            Node("IDENT", value=self.token_string, parent=node)
            lhs_id = self.token_string
            self.id_cnt += 1
            self.lexical()
            if self.next_token != TokenType.ASSIGN_OP:
                #<statement> → <ident><assignment_op><expression> 형식이 아닐 때 - error
                print("(Error) Missing assignment operator")
                self.symbol_table[lhs_id] = "Unknown"
                self.is_error = True
                #error일때도 cnt 출력?
                #TODO
                return
            Node("ASSIGN_OP", value=self.token_string, parent=node)
            self.lexical()
            if self.is_error == False:
                tmp_node, result = self.expression(node)
                self.symbol_table[lhs_id] = result
            else:
                self.symbol_table[lhs_id] = "Unknown"
            if not self.verbose:
                # error일때도 cnt 출력?
                # TODO
                #-v 옵션 없을 때
                #ex) ID: 2; CONST: 1; OP: 1;
                print(f"ID: {self.id_cnt}; CONST: {self.const_cnt}; OP: {self.op_cnt};")
        return node

    def statements(self, parent=None):
        node = Node("STATEMENTS", parent=parent)
        while self.next_token != TokenType.END:
            self.statement(node)

            if self.next_token == TokenType.SEMI_COLON:#세미콜론이 나왔을 때
                semi_colon_node = Node("SEMI_COLON", value=self.token_string, parent=node)

                if self.is_warning == False and self.is_error == False: #에러, 경고가 없을 때
                    if self.index == len(self.source): #마지막 statement일 때
                        print("(Warning) There is semicolon at the end of the statements ==> ignoring semicolon")
                    else: #마지막 statement가 아닐 때
                        print("(OK)")
                self.lexical()
            elif self.next_token == TokenType.END:
                if self.is_warning == False and self.is_error == False: #에러, 경고가 없을 때
                    print("(OK)")
                break
            else:
                if self.is_error == True: #아래의 에러가 이미 앞쪽에서 처리된 경우
                    return
                # ! @ 같은 이상한 문자가 포함되었을때
                # c언어 식별자 규칙에 맞지 않을 때
                # 식별자 사이에 공백이 있을 때
                # 숫자 사이에 공백이 있을 때
                # 소수점이 여러개일때

                if self.token_string == ")": # 왼쪽 괄호가 없을 때 - error
                    print("(Error) Missing left parenthesis")
                    self.is_error = True
                    self.go_to_next_statement()
                    return
                self.error_recovery()
                return
        return node

    def program(self):
        root = Node("PROGRAM")
        self.statements(root)
        return root

    def run(self):
        self.lexical()
        tree = self.program()
        if self.test: #테스트용 트리 출력
            for pre, _, node in RenderTree(tree):
                print(f"{pre}{node}")
        if not self.verbose: # -v 옵션 없을 때 식별자별로 값 출력
            print("Result ==>",end="")
            for i in self.symbol_table:
                print(f" {i}: {self.symbol_table[i]}",end=";")
            print()