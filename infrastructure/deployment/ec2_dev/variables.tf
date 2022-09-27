variable "ssh_key_filename" {
  description = "Filename for storing ssh private key"
  default = "ec2_ssh_key.pem"
}

variable "key_name" {
  description = "Name of the ssh key pair"
  default = "ec2_ssh_key"
}

variable "instance_type" {
  description = "Instance type"
  default     = "t3.micro"
}

variable "security_groups" {
  description = "List of secirity groups of the instance"
}

variable "tags" {
  description = "Dict of tags of the instance"
  default = {
    Name = "development"
    Project = "chicago-taxi"
  }
}

variable "ec2_iam_role_name" {
  description = "Name of the ec2 iam role"
  default     = "ec2_iam_role"
}

variable "ec2_instance_profile_name" {
  description = "Name of the ec2 instance profile"
  default     = "ec2_instance_profile"
}

variable "s3_iam_role_policy_name" {
  description = "Name of the s3 iam role policy"
  default     = "s3_iam_role_policy"
}

variable "s3_bucket_name" {
  description = "Name of the bucket"
}


variable "user_data" {
  description = "Initialization script"
}
