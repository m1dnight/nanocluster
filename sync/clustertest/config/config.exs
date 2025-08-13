import Config


config :libcluster,
  debug: true,
  topologies: [
    gossip_example: [
      strategy: Elixir.Cluster.Strategy.Gossip,
      config: [
        port: 45892,
        if_addr: "0.0.0.0",
        multicast_if: "192.168.1.1",
        multicast_addr: "255.255.255.255",
        multicast_ttl: 1,
        secret: "somepassword"]]]
