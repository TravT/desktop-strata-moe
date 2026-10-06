job "strata-moe" {
  datacenters = ["dc1"]
  type        = "service"

  # Target the high-performance GPU node pool (Desktop Node)
  constraint {
    attribute = "${node.class}"
    value     = "gpu"
  }

  group "engine" {
    count = 1

    restart {
      attempts = 3
      interval = "5m"
      delay    = "15s"
      mode     = "fail"
    }

    network {
      port "http" {
        static = 8080
      }
    }

    service {
      name = "strata-moe"
      port = "http"

      tags = [
        "traefik.enable=true",
        "traefik.http.routers.strata.rule=Host(`strata.home.arpa`)",
        "traefik.http.routers.strata.entrypoints=web",
        "ai",
        "moe",
        "frontier"
      ]

      check {
        type     = "http"
        path     = "/health"
        interval = "15s"
        timeout  = "5s"
      }
    }

    task "strata-runner" {
      driver = "raw_exec"

      config {
        command = "/opt/strata/engine/run-coder.sh"
        args = [
          "--port", "8080",
          "--context", "65536",
          "--draft-vocab", "en",
          "--low-ram", "resident"
        ]
      }

      resources {
        cpu    = 8000
        memory = 20480 # 20 GB reserved RAM
      }
    }
  }
}
