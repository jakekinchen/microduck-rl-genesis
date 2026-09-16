import unittest
import numpy as np
import torch
from retool.learning import actor_gradient_diagnostics


class GradientTests(unittest.TestCase):
    def test_conflict_without_mutating_gradients_or_rng(self):
        p=torch.nn.Parameter(torch.tensor([1.,2.]))
        p.grad=torch.tensor([8.,9.]);before=p.grad.clone();rng=torch.get_rng_state().clone()
        result=actor_gradient_diagnostics({'ppo':p.sum(),'retention':-p.sum()},[p])
        self.assertAlmostEqual(result['gradient_cosine']['ppo/retention'],-1.)
        self.assertTrue(torch.equal(p.grad,before));self.assertTrue(torch.equal(torch.get_rng_state(),rng))
        p.square().sum().backward()
        self.assertTrue(torch.equal(p.grad,torch.tensor([10.,13.])))

    def test_zero_gradient_cosine_is_undefined(self):
        p=torch.nn.Parameter(torch.tensor([1.]))
        result=actor_gradient_diagnostics({'a':p.sum(),'zero':p.sum()*0},[p])
        self.assertIsNone(result['gradient_cosine']['a/zero'])

    def test_observing_loss_does_not_change_update(self):
        states=[]
        for inspect in (False,True):
            p=torch.nn.Parameter(torch.tensor([1.,2.]))
            opt=torch.optim.Adam([p],lr=.01)
            a=p.square().mean();b=(p-3).square().mean()
            if inspect:actor_gradient_diagnostics({'a':a,'b':b},[p])
            opt.zero_grad();(a+b).backward();opt.step();states.append(p.detach())
        self.assertTrue(torch.equal(*states))

    def test_nonfinite_loss_rejected(self):
        p=torch.nn.Parameter(torch.tensor([1.]))
        with self.assertRaises(ValueError):actor_gradient_diagnostics({'bad':p.sum()*float('nan')},[p])

    def test_weighted_norms(self):
        p=torch.nn.Parameter(torch.tensor([1.,2.]))
        result=actor_gradient_diagnostics({'a':p.sum(),'b':p.sum()*4},[p])
        self.assertAlmostEqual(result['gradient_l2']['b']/result['gradient_l2']['a'],4.)


if __name__=='__main__':unittest.main()
