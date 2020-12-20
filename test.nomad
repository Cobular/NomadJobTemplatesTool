job "docker-registry-ui" {
  datacenters = ["home"]
  type        = "service"

  update {
    max_parallel      = 1
    min_healthy_time  = "10s"
    healthy_deadline  = "3m"
    progress_deadline = "10m"
    auto_revert       = true
    canary            = 0
  }

  group "registry-ui" {
    count = 1

    network {
      port "http" {
        to = 80
      }
    }

    task "registry-ui" {
      driver = "docker"

      config {
        image = "joxit/docker-registry-ui:static"

        ports = ["http"]
      }

      env {
        REGISTRY_TITLE = "Jake's Docker Registry"
        REGISTRY_URL   = "http://lenovo.h.jakecover.me:5000"
      }

      resources {
        cpu    = 100
        memory = 128
      }
    }

    service {
      name = "registry-ui"
      port = "http"

      
        tags = [
        "traefik.enable=true",
        "traefik.http.middlewares.registry-ui-mid.headers.customresponseheaders.X-Job=registry-ui",
        "traefik.http.middlewares.registry-ui.headers.customresponseheaders.X-Task=registry-ui",
        "traefik.http.middlewares.registry-ui.headers.customresponseheaders.X-Service=http",
        "traefik.http.routers.registry-ui.rule=Host(`registry-ui.h.jakecover.me`)",
        "traefik.http.services.registry-ui.loadbalancer.sticky=true",
        "traefik.tags=service",
        "traefik.frontend.rule=Host:registry-ui.h.jakecover.me",
        "traefik.http.middlewares.registry-ui-mid-ipwhitelist.ipwhitelist.sourcerange=192.168.0.1/16",
        "traefik.http.routers.registry-ui.middlewares=registry-ui-chain",
        "traefik.http.middlewares.registry-ui-chain.chain.middlewares=registry-ui-mid,registry-ui-mid-ipwhitelist"
      ]
        
    }
  }
}
