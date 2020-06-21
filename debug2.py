"""


"""
import scipy

def exponentialApproximation(A, B, tau, T, N):
    """returns A exp ( -t / tau) + B evaluated at times 0, T/N, 2T/N ... T """
    ts = scipy.linspace(0.0, T, N)    # start, stop, steps, returns time steps for dlic box
    
    freqs = A*scipy.exp(-ts/tau)+B
    return (freqs.tolist(),ts.tolist())
    
    