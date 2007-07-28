"""
chi2p_test.py


    Copyright (c) 2004 Transpose, LLC
    Contained code is licensed under the MIT license:

        http://www.opensource.org/licenses/mit-license.php

    Portions are Copyright (c) 2002-2003 Python Software Foundation, and
    used under the PSF license:

        http://cvs.sf.net/viewcvs.py/spambayes/spambayes/LICENSE.txt



This inverse chi-square method has some unusual characteristics.

PART 1: Effective Size Factor

Most importantly, it can accept an "effective size factor" or ESF. 

The concept of ESF is useful when the chi square random variable is
comprised of the product of multiple nonindependent chi square RV's.

The idea is that if the RV's are nonindependent, then it is "as if" there
are fewer RV's than there really are. For instance, say there are 10 RV's,
but they are paired into 5 pairs such that each member of a pair
always has the same values as the other member. Then, in effect, there
are really only 5 truly random RV's.

In that case, in order to calculate the real p-value associated with a 
particular product, we make the following changes. 
a) the effective degrees of freedom is 5 
rather than 10, and b) we should use the square root of the product 
of the RV's rather than the product itself.

When fed into an inverse-chi-square calculating algorithm, those
adjustments will result in exactly the true p-value for that case.

What we are saying is that the "effective size" of this group of RV's
is 5 rather than 10, because of the redundancy, and that redundancy
can be perfectly taken into account by halving the degrees of freedom
and taking the square root of the product. This is denoted by saying
that the ESF is .5.

Now consider a case that is less well-defined; that is, there is some
interaction between the RV's, but it isn't that half of them are
duplicates of the other half. Intuively it seems that it might be
useful to try to find an ESF that compensates for that interaction
the way ESF=.5 compensates for the interaction in our example.

In practice, it has been found that that assumption appears to be correct. 
For an example, see:
http://portal.acm.org/citation.cfm?id=299444&jmp=cit&dl=GUIDE&dl=ACM
in which this concept is successfully used for protein classification.

In addition, Gary Robinson's informal testing of using ESF in the 
context of spam classification, where the chi-square RV's are 
generated from word probabilities, indicates that it is 
helpful in that context as well. (A pointer to formal test
results will be placed here when they are available.)

So, the inverse chi-square function given here, chi2p(), accepts
an ESF parameter and makes the corresponding adjustments.

PART 2: The algorithms

This code uses two different approaches to protein classification, depending
on the degrees of freedom.

For small degrees of freedom (< 25) we use the an algorithm from the
protein classification paper cited above. This formula takes
the ESF into account by means of interpolation, and so gives
an approximate result even for non-integer effective sizes. It
is also quite fast for small DF. However it becomes very slow
for large DF.

For larger degrees of freedom we use Tim Peter's approach from the
SpamBayes spam filter. Tim's algorithm assumes that the degrees of freedom
is even (a correct assumption for the "traditional" use of chi-square in
spam filtering). The current version of the code does not
interpolate to approximate the exact effective size, but rather rounds
the effective size to the nearest even degrees of freedom. Because
the effective sizes are found empirically in practical applications 
and are therefore not really exact, it is felt that this is acceptable.

"""


import math


        
def _chi2pManyTokens(fChi, iDF, fESF=1.0): 
    """
    Use instead of _chi2pFewTokens
    for large values of iDF*fESF. Suggested
    cutoff is 25.0, but certainly should cutoff
    by 100.0.
    
    Except for the code involving fESF, and some renaming 
    of variables, this is almost exactly the
    same as Tim Peters' SpamBayes chi function.
    """
    MAX_ALLOWABLE_M = 700.0
    
    def makeAdjustments():
        global fM
        global iAdjustedDF
        iHalfDF = iDF / 2    
        iAdjustedHalfDF = max(1,int(fESF * iHalfDF + .5))
        fAdjustedProp =  float(iAdjustedHalfDF) / iHalfDF
        fAdjustedChi = fChi * fAdjustedProp
        iAdjustedDF = iAdjustedHalfDF * 2
        assert iDF & 1 == 0
        # If chi is very large, exp(-m) will underflow to 0; Tim says the
        # results are meaningless in this case; otherwise they should be good.
        fM = fAdjustedChi / 2.0
     
    makeAdjustments()
       
    if fM > MAX_ALLOWABLE_M:
        fESF = fESF * (700.0 / fM)
        makeAdjustments()
    
    fSum = fTerm = math.exp(-fM)
    assert fSum > 0.0
    for i in range(1, iAdjustedDF/2):
        fTerm *= fM / i
        fSum += fTerm
    # With small chi and large df, accumulated roundoff error, plus error in
    # the platform exp(), can cause this to spill a few ULP above 1.0.  For
    # example, chi2p(100, 300) on my box has sum == 1.0 + 2.0**-52 at this
    # point.  Returning a value even a teensy bit over 1.0 is no good.
    return min(fSum, 1.0)

def factorial(i):
    if not hasattr(factorial, 'lstFactorial'):
        factorial.lstFactorial = [None] * 1000
    if factorial.lstFactorial[i] is None:
        iProduct = 1
        for iFactor in xrange(1, i+1):
            iProduct *= iFactor
        factorial.lstFactorial[i] = iProduct
    return factorial.lstFactorial[i]

def _chi2pFewTokens(fChi, iChiDF, fESF=1.0):
    """
    This is more efficient than _chi2pManyTokens for 
    small values of iChiDF*fESF, and is more
    accurate. However it can't handle values of iChiDF*fESF
    > some amount I don't recall at the time of writing this
    docstring. It works up to at least iChiDF*fESF==100.0,
    though _chi2pManyTokens is significantly faster at that point.    
    """
        
    fAdjustedProduct = math.exp((fESF * (-fChi)/2.0))
    iActualSize = iChiDF / 2
                    
    fEffectiveSize = float(iActualSize) * fESF

    assert fAdjustedProduct != 0.0, 'df is: %i, fChi is %f, fESF is %f, iActualSize is %i, fEffectiveSize is %f' \
                                % (iChiDF, fChi, fESF, iActualSize, fEffectiveSize, )

    fSum = 0.0
    for i in xrange(int(fEffectiveSize)):
        fSum += (-math.log(fAdjustedProduct))**i / factorial(i)
    fFirstTerm = fAdjustedProduct * fSum
    fSecondTerm = fAdjustedProduct * \
                  (fEffectiveSize - int(fEffectiveSize)) * \
                  ((-math.log(fAdjustedProduct))**int(fEffectiveSize)) / \
                  factorial(int(fEffectiveSize))
    fResult = fFirstTerm + fSecondTerm
    return fResult

def chi2p(fChi, iChiDF, fESF=1.0, fUseFactorialForUnder=25.0):
    
    if (float(iChiDF) * fESF) < 25.0:
        fResult = _chi2pFewTokens(fChi, iChiDF, fESF)
    else:
        fResult = _chi2pManyTokens(fChi, iChiDF, fESF)
    return fResult

if __name__ == '__main__':
    import unittest
    
    class TestChi(unittest.TestCase):
        def testRightSmallDFResult(self):
            self.assertEqual(0.28240645151038829, chi2p(-2*(math.log(.3**10)), 2*10, .5))
            
        def testRightBigDFResult(self):
            self.assertEqual(0.1336918921570289, chi2p(-2*(math.log(.3**60)), 2*60, .5))

            
    unittest.main()

