from handcalcs import handcalc

if False:
    import Dimensions

class Parameters:
    def __init__(self,Dims):
        self.Dims = Dims
    
    def dim_params_method(self):
        @handcalc(override="long")
        def dim_params_func(b0,t0,b1,t1):
            """Calculate the dimensional variables beta, 
            2*gamma and tau"""
            beta = b1 / b0 #Ratio of brace to chord width, where 0.35 <= beta <= 1.0
            twogamma = b0 / t0 #Ratio of chord width to 2*thickness, where 10 <= 2*gamma <= 35
            tau = t1 / t0 #Ratio of brace to chord thickness, where 0.25 < tau <= 1.0
            return beta, twogamma, tau
        self.dim_params_latex, (self.beta, self.twogamma, self.tau) = dim_params_func(
                                                self.Dims.b0, self.Dims.t0, 
                                                self.Dims.b1, self.Dims.t1)