class TokenType: #토큰 타입들을 나타내 는 클래스
    UNKNOWN = 0
    IDENT = 1
    CONST = 2
    ASSIGN_OP = 3
    SEMI_COLON = 4
    ADD_OP = 5
    SUB_OP = 6
    MULT_OP = 7
    DIV_OP = 8
    LEFT_PAREN = 9
    RIGHT_PAREN = 10
    END = 11

    @classmethod
    def get_name(cls, token_type): #토큰 타입을 문자열로 변환 숫자->문자열
        for name, value in cls.__dict__.items():
            if value == token_type:
                return name
        return "UNKNOWN"
