from anytree import AnyNode
class Node(AnyNode): #노드 클래스
    def __init__(self, type, value=None, parent=None): #노드 생성자
        super().__init__(parent=parent)
        self.type = type
        self.value = value

    def __repr__(self): #노드 출력용
        return f"{self.value} (Type: {self.type})"

    #서브트리 전위순회
    def preorder(self):
        ret = []
        if self.value is not None:
            ret.append(self.value)
            self.value = None
        for child in self.children:
            ret += child.preorder()
        return ret