"""
Copyright (c) Facebook, Inc. and its affiliates.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""

import math
import unittest
import gtn
import gtn.criterion

def emissions_graph(emissions_vec, T, N, logprobs=False):
    if not logprobs:
        emissions_vec = [-math.inf if e == 0 else math.log(e) for e in emissions_vec]
    g = gtn.linear_graph(T, N)
    g.set_weights(emissions_vec)
    return g


class CriterionsTestCase(unittest.TestCase):
    def test_ctc_criterion(self):
        # These test cases are taken from wav2letter: https:#fburl.com/msom2e4v

        # Test case 1

        emissions = emissions_graph([1.0, 0.0, 0.0, 1.0, 1.0, 0.0], 3, 2)

        loss = gtn.criterion.ctc_loss(emissions, [0, 0], 1)
        self.assertEqual(loss.item(), 0.0)

        # Should be 0 since scores are normalized
        z = gtn.forward_score(emissions)
        self.assertEqual(z.item(), 0.0)

        # Test case 2
        T = 3
        N = 4
        emissions = emissions_graph([0.25] * (T * N), T, N)

        expected_loss = math.log(0.25 * 0.25 * 0.25 * 5)

        loss = gtn.criterion.ctc_loss(emissions, [1, 2], N - 1)
        self.assertAlmostEqual(-loss.item(), expected_loss)

        # Test case 3
        T = 5
        N = 6
        target = [0, 1, 2, 1, 0]

        # generate CTC graph

        # fmt: off
        emissions_vec = [
            0.633766,  0.221185, 0.0917319, 0.0129757,  0.0142857,  0.0260553,
            0.111121,  0.588392, 0.278779,  0.0055756,  0.00569609, 0.010436,
            0.0357786, 0.633813, 0.321418,  0.00249248, 0.00272882, 0.0037688,
            0.0663296, 0.643849, 0.280111,  0.00283995, 0.0035545,  0.00331533,
            0.458235,  0.396634, 0.123377,  0.00648837, 0.00903441, 0.00623107,
        ]
        # fmt: on

        emissions = emissions_graph(emissions_vec, T, N)

        # The log probabilities are already normalized,
        # so this should be close to 0
        z = gtn.forward_score(emissions)
        self.assertTrue(abs(z.item()) < 1e-5)

        loss = gtn.criterion.ctc_loss(emissions, target, N - 1)
        expected_loss = 3.34211
        self.assertAlmostEqual(loss.item(), expected_loss, places=5)

        # Check the gradients
        gtn.backward(loss)

        # fmt: off
        expected_grad = [
            -0.366234, 0.221185,  0.0917319, 0.0129757,  0.0142857,  0.0260553,
            0.111121,  -0.411608, 0.278779,  0.0055756,  0.00569609, 0.010436,
            0.0357786, 0.633813,  -0.678582, 0.00249248, 0.00272882, 0.0037688,
            0.0663296, -0.356151, 0.280111,  0.00283995, 0.0035545,  0.00331533,
            -0.541765, 0.396634,  0.123377,  0.00648837, 0.00903441, 0.00623107
        ]
        # fmt: on
        all_close = True
        grad = emissions.grad()
        grad_weights = grad.weights_to_list()
        # Note: expected grad from TF is w.r.t to unnormalized inputs while
        # gtn::criterion::ctcLoss takes logProbs as input
        for i in range(T):
            off = i * N
            exp_sum = sum(emissions_vec[off : off + N])
            for j in range(N):
                g = sum(
                    [
                        grad_weights[off + k]
                        * (int(j == k) - emissions_vec[off + j] / exp_sum)
                        for k in range(N)
                    ]
                )
                all_close = all_close and (abs(expected_grad[off + j] - g) < 1e-5)
        self.assertTrue(all_close)

        # Test case 4
        # This test case is  taken from Tensor Flow CTC implementation
        # tinyurl.com/y9du5v5a
        T = 5
        N = 6
        target = [0, 1, 1, 0]

        # fmt: off
        emissions_vec = [
            0.30176,  0.28562,  0.0831517, 0.0862751, 0.0816851, 0.161508,
            0.24082,  0.397533, 0.0557226, 0.0546814, 0.0557528, 0.19549,
            0.230246, 0.450868, 0.0389607, 0.038309,  0.0391602, 0.202456,
            0.280884, 0.429522, 0.0326593, 0.0339046, 0.0326856, 0.190345,
            0.423286, 0.315517, 0.0338439, 0.0393744, 0.0339315, 0.154046,
        ]
        # fmt: on

        emissions = emissions_graph(emissions_vec, T, N)

        # The log probabilities are already normalized,
        # so this should be close to 0
        z = gtn.forward_score(emissions)
        self.assertTrue(abs(z.item()) < 1e-5)

        loss = gtn.criterion.ctc_loss(emissions, target, N - 1)
        expected_loss = 5.42262
        self.assertAlmostEqual(loss.item(), expected_loss, places=4)

        # Check the gradients
        gtn.backward(loss)
        # fmt: off
        expected_grad = [
            -0.69824,  0.28562,   0.0831517, 0.0862751, 0.0816851, 0.161508,
            0.24082,   -0.602467, 0.0557226, 0.0546814, 0.0557528, 0.19549,
            0.230246,  0.450868,  0.0389607, 0.038309,  0.0391602, -0.797544,
            0.280884,  -0.570478, 0.0326593, 0.0339046, 0.0326856, 0.190345,
            -0.576714, 0.315517,  0.0338439, 0.0393744, 0.0339315, 0.154046,
        ]
        # fmt: on

        all_close = True
        grad = emissions.grad()
        grad_weights = grad.weights_to_list()

        # Note: expected grad from TF is w.r.t to unnormalized inputs while
        # gtn::criterion::ctcLoss takes logProbs as input
        for i in range(T):
            off = i * N
            exp_sum = sum(emissions_vec[off : off + N])
            for j in range(N):
                g = sum(
                    [
                        grad_weights[off + k]
                        * (int(j == k) - emissions_vec[off + j] / exp_sum)
                        for k in range(N)
                    ]
                )
                all_close = all_close and (abs(expected_grad[off + j] - g) < 1e-5)
        self.assertTrue(all_close)

    def test_asg_criterion(self):
        # This test cases is taken from wav2letter: https://fburl.com/msom2e4v
        T = 5
        N = 6

        # fmt: off
        targets = [
            [2, 1, 5, 1, 3],
            [4, 3, 5],
            [3, 2, 2, 1],
        ]

        expected_loss = [
            7.7417464256287,
            6.4200420379639,
            8.2780694961548,
        ]

        emissions_vecs = [
            [-0.4340, -0.0254, 0.3667,  0.4180,  -0.3805, -0.1707, 0.1060, 0.3631,
            -0.1122, -0.3825, -0.0031, -0.3801, 0.0443,  -0.3795, 0.3194, -0.3130,
            0.0094,  0.1560,  0.1252,  0.2877,  0.1997,  -0.4554, 0.2774, -0.2526,
            -0.4001, -0.2402, 0.1295,  0.0172,  0.1805,  -0.3299],

            [
                0.3298,  -0.2259, -0.0959, 0.4909,  0.2996,  -0.2543,
                -0.2863, 0.3239,  -0.3988, 0.0732,  -0.2107, -0.4739,
                -0.0906, 0.0480,  -0.1301, 0.3975,  -0.3317, -0.1967,
                0.4372,  -0.2006, 0.0094,  0.3281,  0.1873,  -0.2945,
                0.2399,  0.0320,  -0.3768, -0.2849, -0.2248, 0.3186,
            ],

            [
                0.0225,  -0.3867, -0.1929, -0.2904, -0.4958, -0.2533,
                0.4001,  -0.1517, -0.2799, -0.2915, 0.4198,  0.4506,
                0.1446,  -0.4753, -0.0711, 0.2876,  -0.1851, -0.1066,
                0.2081,  -0.1190, -0.3902, -0.1668, 0.1911,  -0.2848,
                -0.3846, 0.1175,  0.1052,  0.2172,  -0.0362, 0.3055,
            ],
        ]

        emissions_grads = [
            [
                0.1060, 0.1595,  -0.7639, 0.2485,  0.1118, 0.1380, 0.1915, -0.7524,
                0.1539, 0.1175,  0.1717,  0.1178,  0.1738, 0.1137, 0.2288, 0.1216,
                0.1678, -0.8057, 0.1766,  -0.7923, 0.1902, 0.0988, 0.2056, 0.1210,
                0.1212, 0.1422,  0.2059,  -0.8160, 0.2166, 0.1300,
            ],

            [
                0.2029, 0.1164,  0.1325,  0.2383, -0.8032, 0.1131,  0.1414, 0.2602,
                0.1263, -0.3441, -0.3009, 0.1172, 0.1557,  0.1788,  0.1496, -0.5498,
                0.0140, 0.0516,  0.2306,  0.1219, 0.1503,  -0.4244, 0.1796, -0.2579,
                0.2149, 0.1745,  0.1160,  0.1271, 0.1350,  -0.7675,
            ],

            [
                0.2195,  0.1458,  0.1770, -0.8395, 0.1307,  0.1666, 0.2148,  0.1237,
                -0.6613, -0.1223, 0.2191, 0.2259,  0.2002,  0.1077, -0.8386, 0.2310,
                0.1440,  0.1557,  0.2197, -0.1466, -0.5742, 0.1510, 0.2160,  0.1342,
                0.1050,  -0.8265, 0.1714, 0.1917,  0.1488,  0.2094,
            ],
        ]
        # fmt: on
        transitions = gtn.Graph()
        transitions.add_node(True)
        for i in range(1, N + 1):
            transitions.add_node(False, True)
            transitions.add_arc(0, i, i - 1)  # p(i | <s>)

        for i in range(N):
            for j in range(N):
                transitions.add_arc(j + 1, i + 1, i)  # p(i | j)

        for b in range(len(targets)):
            target = targets[b]
            emissions_vec = emissions_vecs[b]
            emissions_grad = emissions_grads[b]

            fal = gtn.Graph()
            fal.add_node(True)
            for l in range(1, len(target) + 1):
                fal.add_node(False, l == len(target))
                fal.add_arc(l - 1, l, target[l - 1])
                fal.add_arc(l, l, target[l - 1])

            emissions = emissions_graph(emissions_vec, T, N, True)

            loss = gtn.subtract(
                gtn.forward_score(gtn.compose(emissions, transitions)),
                gtn.forward_score(
                    gtn.compose(gtn.compose(fal, transitions), emissions)
                ),
            )

            self.assertAlmostEqual(loss.item(), expected_loss[b], places=3)

            # Check the gradients
            gtn.backward(loss)

            all_close = True
            grad = emissions.grad()
            grad_weights = grad.weights_to_list()
            for i in range(T * N):
                g = grad_weights[i]
                all_close = all_close and (abs(emissions_grad[i] - g) < 1e-4)
            self.assertTrue(all_close)

        all_close = True
        # fmt: off
        trans_grad = [
            0.3990,  0.3396,  0.3486, 0.3922,  0.3504,  0.3155,  0.3666,  0.0116,
            -1.6678, 0.3737,  0.3361, -0.7152, 0.3468,  0.3163,  -1.1583, -0.6803,
            0.3216,  0.2722,  0.3694, -0.6688, 0.3047,  -0.8531, -0.6571, 0.2870,
            0.3866,  0.3321,  0.3447, 0.3664,  -0.2163, 0.3039,  0.3640,  -0.6943,
            0.2988,  -0.6722, 0.3215, -0.1860,
         ]
        # fmt: on

        grad = transitions.grad()
        grad_weights = grad.weights_to_list()
        for i in range(N * N):
            g = grad_weights[i + N]
            all_close = all_close and (abs(trans_grad[i] - g) < 1e-4)
        self.assertTrue(all_close)

    def test_asg_viterbi_path(self):
        # Test adapted from wav2letter https://tinyurl.com/yc6nxex9
        T = 4
        N = 3

        # fmt: off
        input = [
            0, 0, 7,
            5, 4, 3,
            5, 8, 5,
            5, 4, 3,
        ]
        trans = [
            0, 2, 0,
            0, 0, 2,
            2, 0, 0,
        ]
        expectedPath = [2, 1, 1, 0]
        # fmt: on

        transitions = gtn.Graph()
        transitions.add_node(True)
        for i in range(1, N + 1):
            transitions.add_node(False, True)
            transitions.add_arc(0, i, i - 1)  # p(i | <s>)

        for i in range(N):
            for j in range(N):
                transitions.add_arc(j + 1, i + 1, i, i, trans[i * N + j])  # p(i | j)

        emissions = emissions_graph(input, T, N, True)

        path = gtn.viterbi_path(gtn.compose(emissions, transitions))

        self.assertEqual(path.labels_to_list(), expectedPath)


if __name__ == "__main__":
    unittest.main()
