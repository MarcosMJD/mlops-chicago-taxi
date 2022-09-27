resource "aws_db_instance" "postgres_db" {
  allocated_storage    = 10
  engine               = "postgres"
  engine_version       = "13.7"
  instance_class       = "db.t3.micro"
  identifier           = var.rds_indentifier
  db_name              = var.postgres_db_name
  username             = var.postgres_db_username
  password             = var.postgres_db_password
  skip_final_snapshot  = true
  vpc_security_group_ids = var.postgres_db_vpc_security_group_ids
}

output "endpoint" {
  value = aws_db_instance.postgres_db.endpoint
}
