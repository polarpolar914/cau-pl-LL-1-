from Node import Node
from TokenType import TokenType
from Lexer import Lexer
from anytree import RenderTree
import re
class Parser(Lexer):#파서 클래스
    def __init__(self, input_source, verbose=False, test=False):#파서 생성자
        super().__init__(input_source, verbose=verbose)

        if input_source.replace(" ", "") == "":#입력받은 소스코드가 공백만 있을 때 - error
            error = "(Error) Grammer of this LL(1) parser cannot generate empty source code"
            self.list_message.append(error)
            self.is_error = True
            self.end_of_stmt()
        self.test = test  # 파싱이 정상적으로 되었는지 확인하기 위한 트리 출력, 변수에 대입할 값이 제대로 계산되었는지 확인

    def syntax_error(self):
        error = "(Error) Syntax error - invalid token or invalid token sequence or missing token"
        self.list_message.append(error)
        self.is_error = True
        self.go_to_next_statement()
        if self.next_token != TokenType.SEMI_COLON:
            self.lexical()

    def factor(self, parent=None):
        node = Node("FACTOR", parent=parent)
        if self.next_token == TokenType.LEFT_PAREN:
            self.lexical()
            expr_node = self.expression(node)
            if self.next_token != TokenType.RIGHT_PAREN:
                #오른쪽 괄호가 없을 때 - warning
                self.is_warning = True
                warning = "(Warning) Missing right parenthesis ==> assuming right parenthesis at the end of statement"
                self.list_message.append(warning)
                #해당 statement의 맨 오른쪽에 오른쪽 괄호가 있다고 가정하고 계속 진행함
                #LL(1) 파서이므로 오른쪽 괄호가 없다는 것은 이미 파싱한 부분이 아닌 앞으로 파싱할 부분(오른쪽)에 오류가 있다는 것임 - 에러출력 + 계속파싱
                #오른쪽 괄호가 있는 곳은 맨 오른쪽으로 가정, 맨오른쪽==해당 statement의 끝

                if self.next_token == TokenType.SEMI_COLON:
                    self.now_stmt = self.now_stmt[:-1] + ");"
                    self.token_string = ")"
                    if self.verbose: print(self.token_string)
                    self.token_string = ";"
                    if self.verbose: print(self.token_string)
                else:
                    self.now_stmt = self.now_stmt + ")"
                    self.token_string = ")"
                    if self.verbose: print(self.token_string)
                    self.token_string = "EOF"
                    if self.verbose: print(self.token_string)
                self.go_to_next_statement()
                return node
            self.lexical()
        elif self.next_token == TokenType.IDENT or self.next_token == TokenType.CONST:
            Node(TokenType.get_name(self.next_token), value=self.token_string, parent=node)
            self.lexical()
        else:
            self.syntax_error()
        return node

    def factor_tail(self, parent=None):
        node = Node("FACTOR_TAIL", parent=parent)
        while self.next_token == TokenType.MULT_OP:
            Node(TokenType.get_name(self.next_token), value=self.token_string, parent=node)
            div = False
            if self.token_string == "/":
                div = True
            self.lexical()
            if self.next_token == TokenType.CONST:
                error = "(Error) Invalid expression - division by zero"
                self.list_message.append(error)
                self.is_error = True
            elif self.next_token == TokenType.IDENT:
                if self.token_string in self.symbol_table and self.symbol_table[self.token_string] == 0 and div == True:
                    error = "(Error) Invalid expression - division by zero"
                    self.list_message.append(error)
                    self.is_error = True
            self.factor(node)
        return node

    def term(self, parent=None):
        node = Node("TERM", parent=parent)
        self.factor(node)
        self.factor_tail(node)
        return node

    def term_tail(self, parent=None):
        node = Node("TERM_TAIL", parent=parent)
        while self.next_token == TokenType.ADD_OP:
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
            if re.fullmatch(r'^\d+$', i):
                term += i
            elif re.fullmatch(r'^\d+\.\d+$', i):
                term += i
            elif re.fullmatch(r'^-\d+$', i):
                term += i
            elif re.fullmatch(r'^-\d+\.\d+$', i):
                term += i
            elif i in "+-*/()":
                term += i
            elif i in self.symbol_table and self.symbol_table[i] != "Unknown":
                term += str(self.symbol_table[i])
            elif i in self.symbol_table and self.symbol_table[i] == "invalid identifier name":
                #잘못된 식별자 이름이 사용된 경우 - error
                #이미 앞에서 에러 처리후 go_to_next_statement()호출되었으므로 다음 statement로 넘어감
                return node
            elif not i in self.symbol_table or self.symbol_table[i] == "Unknown":
                #정의되지 않은 변수 참조 - error - 에러이긴 하지만 syntax error가 아니라 semantic error이므로 파싱은 계속 진행
                error = "(Error) Undefined variable is referenced(" + i + ")"
                self.list_message.append(error)
                self.is_error = True
            else:
                #여기에 걸리는 경우는 없음
                error = "Error: Invalid expression"
                self.list_message.append(error)
                return node, "Unknown"
        try:
            result = eval(term)
            node.value = str(result)
            if(self.test):print(f"Result: {result}")
            return node, result
        except:
            return node, "Unknown"

    def statement(self, parent=None):
        node = Node("STATEMENT", parent=parent)
        if self.next_token == TokenType.IDENT:
            self.id_of_now_stmt = self.token_string
            if (self.token_string not in self.symbol_table) or (self.token_string in self.symbol_table and self.symbol_table[self.token_string] == None): self.symbol_table[self.token_string] = "Unknown"
            Node("IDENT", value=self.token_string, parent=node)
            lhs_id = self.token_string
            self.lexical()
            if self.is_error == True:
                if self.next_token != TokenType.SEMI_COLON and self.next_token != TokenType.END:
                    self.go_to_next_statement()
                    self.lexical()
                return node
            if self.next_token == TokenType.ASSIGN_OP:
                if self.op_after_assign_op():
                    #오류 메시지는 self.op_after_assign_op()에서 출력
                    self.go_to_next_statement()
                    return node

            else:
                #<statement> → <ident><assignment_op><expression> 형식이 아닐 때 - error
                error = "(Error) Missing assignment operator"
                self.list_message.append(error)
                self.symbol_table[lhs_id] = "Unknown"
                self.is_error = True
                self.go_to_next_statement()
                if self.next_token != TokenType.SEMI_COLON:self.lexical()
                return node
            Node("ASSIGN_OP", value=self.token_string, parent=node)
            self.lexical()
            if self.is_error == False:
                tmp_node, result = self.expression(node)
                self.symbol_table[lhs_id] = result
            else:
                self.symbol_table[lhs_id] = "Unknown"
        return node

    def statements(self, parent=None):
        node = Node("STATEMENTS", parent=parent)
        while self.next_token != TokenType.END:
            self.statement(node)
            if self.next_token == TokenType.SEMI_COLON:#세미콜론이 나왔을 때
                semi_colon_node = Node("SEMI_COLON", value=self.token_string, parent=node)
                if self.index == len(self.source):  # 마지막 statement일 때
                    warning = "(Warning) There is semicolon at the end of the program ==> ignoring semicolon"
                    self.list_message.append(warning)
                    self.is_warning = True
                    self.now_stmt = self.now_stmt[:-1]
                if not self.verbose : self.end_of_stmt()
                self.lexical()
            elif self.next_token == TokenType.END:
                if not self.verbose : self.end_of_stmt()
                break
            else:
                if self.token_string == ")": # 왼쪽 괄호가 없을 때 - error
                    error = "(Error) Missing left parenthesis"
                    self.list_message.append(error)
                    self.is_error = True
                    self.symbol_table[self.id_of_now_stmt] = "Unknown"
                    self.go_to_next_statement()
                    if not self.verbose : self.end_of_stmt()
                    self.lexical()
                    continue
                elif self.is_error == True: #아래의 에러가 이미 앞쪽에서 처리된 경우 - 앞에서 is_error가 True로 바뀌고 go_to_next_statement()를 호출했으므로 다음 statement로 넘어감
                    continue
                self.syntax_error()
                if not self.verbose : self.end_of_stmt()
                self.lexical()
        if self.now_stmt != "":
            if not self.verbose: self.end_of_stmt()
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
            if len(self.symbol_table) == 0 or (len(self.symbol_table) == 1 and None in self.symbol_table):
                print("There is no identifier")
            for i in self.symbol_table:
                if i != None:
                    print(f" {i}: {self.symbol_table[i]}",end=";")
            print()