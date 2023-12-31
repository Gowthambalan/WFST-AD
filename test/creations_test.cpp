/*
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */

#include "catch.hpp"

#include <vector>

#include "gtn/creations.h"
#include "gtn/graph.h"

using namespace gtn;

TEST_CASE("test scalar creation", "[creations]") {
  float weight = static_cast<float>(rand());
  auto g = scalarGraph(weight, Device::CPU, false);
  CHECK(g.numArcs() == 1);
  CHECK(g.label(0) == epsilon);
  CHECK(g.numNodes() == 2);
  CHECK(g.weight(0) == weight);
  CHECK(g.item() == weight);
  CHECK(g.calcGrad() == false);
}

TEST_CASE("test linear creation", "[creations]") {
  auto rand_float = []() {
    return static_cast<float>(rand()) / static_cast<float>(RAND_MAX);
  };

  int M = 5;
  int N = 10;
  std::vector<float> arr;
  for (int i = 0; i < M * N; i++) {
    arr.push_back(rand_float());
  }
  auto g = linearGraph(M, N);
  g.setWeights(arr.data());
  CHECK(g.numNodes() == M + 1);
  CHECK(g.numArcs() == M * N);
  for (int i = 0; i < M; i++) {
    for (int j = 0; j < N; j++) {
      auto idx = i * N + j;
      CHECK(g.label(idx) == j);
      CHECK(g.weight(idx) == arr[idx]);
    }
  }
  CHECK(g.numStart() == 1);
  CHECK(g.numAccept() == 1);
  CHECK(g.isAccept(M));
  CHECK(g.isStart(0));

  CHECK(arr == std::vector<float>(g.weights(), g.weights() + g.numArcs()));
}
