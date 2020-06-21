
class A(object):
    
    def __init__(self):
        super(A, self).__init__()
        self.A = self.B*3
        


class B(A):
    
    B=10
    
    
B()