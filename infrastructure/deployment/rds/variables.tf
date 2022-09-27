variable "rds_indentifier" {
  description = "Name of the rds instance"
  default     = "postgres"
}

variable "postgres_db_name" {
  description = "Name of db in rds instance"
  default     = "db"
}

variable "postgres_db_username" {
  description = "User name of rds db"
  default     = "db_user"
}

variable "postgres_db_password" {
  description = "Password of rds db"
  default     = "db_password"
}

variable "postgres_db_vpc_security_group_ids" {
    description = "Security group of rds db"
}
