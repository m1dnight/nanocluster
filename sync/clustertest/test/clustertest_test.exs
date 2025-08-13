defmodule ClustertestTest do
  use ExUnit.Case
  doctest Clustertest

  test "greets the world" do
    assert Clustertest.hello() == :world
  end
end
