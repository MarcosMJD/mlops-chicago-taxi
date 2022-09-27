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

variable "volume_size" {
  description = "Size of the root disk"
  default = 20
}

variable "security_groups" {
  description = "List of secirity groups of the instance"
}

variable "tags" {
  description = "Dict of tags of the instance"
  default = {
    Name = "ec2_server"
    Project = "ec2_server_project"
  }
}

variable "user_data" {
  description = "Initialization script"
}
