provider "google" {
  project = "autojobapply-prod"
  region  = "us-central1"
}

resource "google_compute_network" "prod_network" {
  name = "autojobapply-prod-network"
}
