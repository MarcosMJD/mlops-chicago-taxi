resource "aws_s3_bucket" "s3_bucket" {
  bucket  = var.s3_bucket_name
  acl     = "private"
}

output "name" {
  value = aws_s3_bucket.s3_bucket.bucket
}