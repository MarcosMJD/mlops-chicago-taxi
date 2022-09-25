resource "aws_ecr_repository" "repo" {
  name                 = var.ecr_repo_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = false
  }
}

# In practice, the Image build-and-push step is handled separately by the CI/CD pipeline and not the IaC script.
# But because the lambda config would fail without an existing Image URI in ECR,
# we can also build and upload the image. The real or any base image to bootstrap the lambda config, unrelated to our inference logic
resource null_resource ecr_image {
  triggers = {
    python_file = md5(file(var.lambda_function_local_path))
    python_file_2 = md5(file(var.model_service_local_path))
    docker_file = md5(file(var.docker_image_local_path))
  }

  # Interpreter bash for gitbash or linux bash. On Windows, use Powershell or cmd (to fix multiline nor working in cmd/powershell)
  provisioner "local-exec" {
      command = <<EOT
          pwd
          aws ecr get-login-password --region ${var.region} | docker login --username AWS --password-stdin ${var.account_id}.dkr.ecr.${var.region}.amazonaws.com
          docker build -t ${aws_ecr_repository.repo.repository_url}:${var.ecr_image_tag} .
          docker push ${aws_ecr_repository.repo.repository_url}:${var.ecr_image_tag}
      EOT
      interpreter = ["bash", "-c"]
      working_dir = "../sources/production"
   }
}

data aws_ecr_image lambda_image {
// Wait for the image to be uploaded, before lambda config runs
 depends_on = [
   null_resource.ecr_image
 ]
 repository_name = var.ecr_repo_name
 image_tag       = var.ecr_image_tag
}

output "image_uri" {
  description = "uri of the image to be loaded by other services... i.e. lambda"
  value     = "${aws_ecr_repository.repo.repository_url}:${data.aws_ecr_image.lambda_image.image_tag}"
}
